from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

# Priority labels mapped to a sort rank (lower rank = scheduled first).
# Anything unrecognized falls back to the lowest priority.
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
LOWEST_RANK = max(PRIORITY_RANK.values()) + 1


def _time_to_minutes(time_str: str) -> int | None:
    """Convert an 'HH:MM' time-of-day string to minutes since midnight.

    Returns None only for an empty string (''), which means 'unscheduled'.
    Anything non-empty must be a well-formed, in-range clock time: raises
    ValueError otherwise so bad input fails loudly instead of silently
    sorting to the end of the day. Parsing to minutes (instead of comparing
    raw strings) keeps sorting correct even when a time isn't zero-padded,
    e.g. '9:00' vs '17:00'.
    """
    if not time_str:
        return None
    try:
        hours_str, minutes_str = time_str.split(":")
        hours, minutes = int(hours_str), int(minutes_str)
    except (ValueError, AttributeError):
        raise ValueError(f"invalid time {time_str!r} (expected 'HH:MM')") from None
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"time {time_str!r} out of range (00:00-23:59)")
    return hours * 60 + minutes


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight back to a zero-padded 'HH:MM' string.

    Inverse of _time_to_minutes for the scheduled range, so a slot computed as
    an integer can be handed back to the UI (and re-parsed) as a clock time.
    """
    hours, mins = divmod(minutes, 60)
    return f"{hours:02d}:{mins:02d}"


def _time_sort_key(task: Task) -> float:
    """Chronological sort key: minutes since midnight, with unscheduled
    ('') tasks pushed to the end via infinity. Parses the time exactly once."""
    minutes = _time_to_minutes(task.time)
    return float("inf") if minutes is None else minutes


@dataclass
class Task:
    description: str
    duration: int  # minutes
    priority: str  # "high" | "medium" | "low"
    time: str = ""  # time of day, e.g. "08:00" ("" = not yet scheduled)
    frequency: str = "daily"  # e.g. "daily" | "weekly" | "once"
    completed: bool = False
    due_date: "date | None" = None  # calendar day this instance is due

    def __post_init__(self) -> None:
        # Validate on construction so no invalid Task can exist. replace() and
        # the demo/app all funnel through here.
        self._validate()

    def _validate(self) -> None:
        """Enforce field invariants: positive duration and a valid/empty time."""
        if self.duration <= 0:
            raise ValueError("duration must be a positive number of minutes")
        # Raises on a malformed or out-of-range time; '' (unscheduled) is fine.
        _time_to_minutes(self.time)

    def mark_complete(self) -> None:
        """Mark this task as done so the scheduler skips it."""
        self.completed = True

    def update_task(self, **fields) -> None:
        """Update editable task fields by keyword (not completion status)."""
        # 'completed' is intentionally excluded — use mark_complete() for that.
        editable = {"description", "duration", "priority", "time", "frequency"}
        for key, value in fields.items():
            if key not in editable:
                raise AttributeError(f"'{key}' is not an editable Task field")
            setattr(self, key, value)
        # setattr bypasses __post_init__, so re-check invariants after editing.
        self._validate()

    def get_details(self) -> str:
        """Return a one-line human-readable summary of the task."""
        # Prefix the time of day when set; append a done marker when complete.
        when = f"{self.time} - " if self.time else ""
        status = " [done]" if self.completed else ""
        due = f" (due {self.due_date})" if self.due_date else ""
        return f"{when}{self.description} ({self.duration} min) [priority: {self.priority}]{due}{status}"

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict.

        due_date is a datetime.date (not JSON-serializable), so it's stored as
        an ISO string ('2026-07-02') — or None when the task has no due date.
        Every other field is already a plain JSON type.
        """
        return {
            "description": self.description,
            "duration": self.duration,
            "priority": self.priority,
            "time": self.time,
            "frequency": self.frequency,
            "completed": self.completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a Task from to_dict() output.

        Construction runs __post_init__, so a corrupt saved value (bad duration
        or time) still fails validation on load rather than sneaking in.
        """
        due = data.get("due_date")
        return cls(
            description=data["description"],
            duration=data["duration"],
            priority=data["priority"],
            time=data.get("time", ""),
            frequency=data.get("frequency", "daily"),
            completed=data.get("completed", False),
            due_date=date.fromisoformat(due) if due else None,
        )


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Enforce field invariants: age can't be negative."""
        if self.age < 0:
            raise ValueError("age cannot be negative")

    def update_info(self, **info) -> None:
        """Update the pet's detail fields (name, species, breed, age) by keyword."""
        # Restricted to details so a stray key can't wipe the tasks list.
        details = {"name", "species", "breed", "age"}
        for key, value in info.items():
            if key not in details:
                raise AttributeError(f"'{key}' is not an editable Pet detail")
            setattr(self, key, value)
        # setattr bypasses __post_init__, so re-check invariants after editing.
        self._validate()

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet, rejecting an exact duplicate.

        A duplicate is a task equal in every field (Task is a dataclass, so ==
        compares all fields). This blocks accidentally adding the same task
        twice but never blocks a recurring respawn from complete_task, which
        differs by due_date/completed.
        """
        if task in self.tasks:
            raise ValueError(
                f"duplicate task {task.description!r} already exists for {self.name}"
            )
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a specific task instance from this pet.

        Matches by identity (the exact object), not by value, so removing one
        of several equal-looking tasks deletes only the one the caller holds.
        Raises ValueError if the task isn't attached to this pet.
        """
        for i, existing in enumerate(self.tasks):
            if existing is task:
                del self.tasks[i]
                return
        raise ValueError(f"task {task.description!r} is not attached to {self.name}")

    def to_dict(self) -> dict:
        """Serialize this pet and its tasks to a JSON-friendly dict."""
        return {
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a Pet (and its tasks) from to_dict() output."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            breed=data["breed"],
            age=data["age"],
        )
        # Restore tasks directly rather than via add_task: the saved data is
        # already de-duplicated, and this preserves exactly what was persisted.
        pet.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return pet


@dataclass
class Owner:
    name: str
    available_time: int = 0  # minutes available per day
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Construction bypasses set_available_time, so guard the invariant here.
        if self.available_time < 0:
            raise ValueError("available_time cannot be negative")

    def set_available_time(self, minutes: int) -> None:
        """Set how many minutes the owner has for pet care today."""
        # Guard against negative input so scheduling math stays sane.
        if minutes < 0:
            raise ValueError("available_time cannot be negative")
        self.available_time = minutes

    def update_preferences(self, prefs: dict) -> None:
        """Merge new key/values into the owner's preferences (keeps existing ones)."""
        self.preferences.update(prefs)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner, rejecting a duplicate name.

        Two pets with the same name (case-insensitive) are treated as the same
        pet, so this blocks adding "Mochi" twice while still allowing distinct
        names. Mirrors Pet.add_task's duplicate guard.
        """
        if any(existing.name.lower() == pet.name.lower() for existing in self.pets):
            raise ValueError(f"a pet named {pet.name!r} already exists")
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets as one flat list."""
        # This is the single access point the Scheduler pulls from.
        return [task for pet in self.pets for task in pet.tasks]

    def to_dict(self) -> dict:
        """Serialize the whole owner graph (owner -> pets -> tasks) to a dict."""
        return {
            "name": self.name,
            "available_time": self.available_time,
            "preferences": self.preferences,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild a full Owner (with pets and tasks) from to_dict() output."""
        owner = cls(
            name=data["name"],
            available_time=data.get("available_time", 0),
            preferences=dict(data.get("preferences", {})),
        )
        owner.pets = [Pet.from_dict(p) for p in data.get("pets", [])]
        return owner

    def save_to_json(self, path: str = "data.json") -> None:
        """Persist this owner (with pets and tasks) to a JSON file.

        Owner is the aggregate root, so saving it captures the entire state.
        """
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=2)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Load an owner previously saved with save_to_json().

        Raises FileNotFoundError if the file doesn't exist, so a first-run
        caller can catch it and start from a fresh Owner instead.
        """
        with open(path, "r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))


class Scheduler:
    """The 'brain': retrieves tasks across an owner's pets, organizes them by
    priority, and builds/explains a daily plan that fits the available time."""

    def collect_tasks(self, owner: Owner, pet_name: str | None = None) -> list[Task]:
        """Retrieve care tasks across the owner's pets, optionally one pet only.

        With no pet_name, delegates to Owner.all_tasks() so Owner stays the
        source of truth. With a pet_name, returns just that pet's tasks
        (case-insensitive match) — handy for a per-pet view in the UI.
        """
        if pet_name is None:
            return owner.all_tasks()
        return [
            task
            for pet in owner.pets
            if pet.name.lower() == pet_name.lower()
            for task in pet.tasks
        ]

    def filter_tasks(self, tasks: list[Task], status: str = "all") -> list[Task]:
        """Return tasks matching a completion status: 'all', 'pending', or 'done'."""
        if status == "all":
            return list(tasks)
        if status == "pending":
            return [t for t in tasks if not t.completed]
        if status == "done":
            return [t for t in tasks if t.completed]
        raise ValueError(f"unknown status '{status}' (use 'all', 'pending', or 'done')")

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return a new list ordered by priority, then shortest duration."""
        # Sorting a copy leaves the caller's original order untouched.
        return sorted(
            tasks,
            key=lambda t: (PRIORITY_RANK.get(t.priority, LOWEST_RANK), t.duration),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return a new list ordered by time of day; unscheduled tasks go last.

        Times are 'HH:MM' strings, so the lambda key sorts on minutes since
        midnight. Tasks with no time ('') have no clock position, so they fall
        to the end as 'anytime' items instead of sorting to the top.
        """
        return sorted(tasks, key=_time_sort_key)

    def next_due_date(self, task: Task, from_date: date | None = None) -> date | None:
        """Return the date a recurring task should next occur after from_date.

        Daily tasks recur the next day; weekly tasks a week later, computed with
        timedelta so month/year rollovers are handled correctly. Non-recurring
        or unrecognized frequencies return None. from_date defaults to today but
        is injectable so tests can pin a fixed date.
        """
        base = from_date or date.today()
        steps = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
        step = steps.get(task.frequency)
        return base + step if step else None

    def complete_task(
        self, pet: Pet, task: Task, today: date | None = None
    ) -> Task | None:
        """Mark a task done and, if it recurs, spawn its next occurrence.

        Marks the given task complete, then for a daily/weekly task creates a
        fresh copy (not completed, no due-date yet cleared) dated to the next
        occurrence and attaches it to the same pet. Returns the new Task, or
        None for a one-off task. This is how completion and Task.frequency
        interact: finishing today's walk automatically queues tomorrow's.
        """
        task.mark_complete()
        # Advance from the task's own due date when it has one, so completing a
        # recurring task repeatedly keeps moving the date forward instead of
        # always landing on today + 1. Anchor to `today` only the first time.
        next_date = self.next_due_date(task, task.due_date or today)
        if next_date is None:
            return None
        # replace() copies every field, then overrides just what changed.
        next_task = replace(task, completed=False, due_date=next_date)
        pet.add_task(next_task)
        return next_task

    def find_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return pairs of scheduled, not-done tasks whose time windows overlap.

        Each task occupies [start, start + duration) minutes on the clock; two
        tasks conflict when those windows intersect. Unscheduled ('') or
        completed tasks are ignored. This only reports overlaps (warn-only per
        the design) — it never drops a task from the plan.
        """
        timed = [
            (t, _time_to_minutes(t.time))
            for t in tasks
            if not t.completed and _time_to_minutes(t.time) is not None
        ]
        conflicts: list[tuple[Task, Task]] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                (a, a_start), (b, b_start) = timed[i], timed[j]
                a_end, b_end = a_start + a.duration, b_start + b.duration
                # Half-open intervals overlap iff each starts before the other ends.
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))
        return conflicts

    def find_free_slot(
        self,
        tasks: list[Task],
        duration: int,
        day_start: str = "06:00",
        day_end: str = "22:00",
        earliest: str | None = None,
    ) -> str | None:
        """Return the earliest 'HH:MM' start time that fits a `duration`-minute
        task without overlapping any scheduled, not-done task.

        Sweeps the day from `day_start` (or `earliest`, whichever is later) to
        `day_end`, treating each scheduled + incomplete task as a busy
        [start, start + duration) window. Returns the first gap large enough to
        hold `duration` minutes and still finish by `day_end`, or None if the
        day is too full. Unscheduled ('') and completed tasks don't occupy the
        clock, so they're ignored — the same rule find_conflicts() uses. This
        turns conflict *detection* into a concrete suggestion the owner can act
        on.
        """
        if duration <= 0:
            raise ValueError("duration must be a positive number of minutes")
        window_start = _time_to_minutes(day_start)
        window_end = _time_to_minutes(day_end)
        # `earliest` lets a caller demand a slot no sooner than a given time.
        if earliest:
            window_start = max(window_start, _time_to_minutes(earliest))

        # Busy [start, end) windows from scheduled, not-done tasks, by start time.
        busy = []
        for task in tasks:
            start = _time_to_minutes(task.time)
            if task.completed or start is None:
                continue
            busy.append((start, start + task.duration))
        busy.sort()

        # Advance a cursor over the day, keeping it at the earliest free minute.
        cursor = window_start
        for start, end in busy:
            # A busy block entirely behind the cursor can't affect us.
            if end <= cursor:
                continue
            # Enough room between the cursor and this block? Take it.
            if start - cursor >= duration:
                break
            # Otherwise skip past this block and keep looking.
            cursor = max(cursor, end)

        # Valid only if the task still finishes within the day window.
        if cursor + duration <= window_end:
            return _minutes_to_time(cursor)
        return None

    def generate_plan(self, tasks: list[Task], available_time: int) -> list[Task]:
        """Return the not-done tasks that fit within available_time, in priority order."""
        # available_time can arrive here directly (bypassing the Owner setter),
        # so guard it so a negative budget fails loudly instead of silently
        # producing an empty plan.
        if available_time < 0:
            raise ValueError("available_time cannot be negative")
        # Greedily pack sorted tasks, keeping each one that still fits the budget.
        plan: list[Task] = []
        remaining = available_time
        for task in self.sort_tasks(tasks):
            # Completed tasks are already handled, so they never enter the plan.
            if task.completed:
                continue
            # Skip anything that would overflow the remaining time budget.
            if task.duration <= remaining:
                plan.append(task)
                remaining -= task.duration
        return plan

    def explain_plan(self, tasks: list[Task], available_time: int) -> str:
        """Return a human-readable plan showing scheduled and skipped tasks."""
        # Reuse generate_plan() so the explanation always matches the real plan.
        plan = self.generate_plan(tasks, available_time)
        planned_ids = {id(t) for t in plan}

        lines = [f"Daily plan ({available_time} min available):"]
        # Tasks are *selected* by priority, but an owner reads the day in clock
        # order, so display the winners sorted by time of day.
        for task in self.sort_by_time(plan):
            lines.append(f"  - {task.get_details()}")
        used = sum(task.duration for task in plan)
        lines.append(f"Total scheduled time: {used} min")

        # Warn about overlapping time windows without changing the plan.
        conflicts = self.find_conflicts(plan)
        if conflicts:
            lines.append("Conflicts (overlapping times):")
            for a, b in conflicts:
                lines.append(f"  - {a.description} overlaps {b.description}")

        # List anything skipped and why, so the reasoning is transparent.
        skipped = [t for t in tasks if id(t) not in planned_ids]
        if skipped:
            lines.append("Skipped:")
            for task in skipped:
                reason = "already done" if task.completed else "not enough time left"
                lines.append(f"  - {task.get_details()} ({reason})")
        return "\n".join(lines)
