from __future__ import annotations

from dataclasses import dataclass, field

# Priority labels mapped to a sort rank (lower rank = scheduled first).
# Anything unrecognized falls back to the lowest priority.
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
LOWEST_RANK = max(PRIORITY_RANK.values()) + 1


@dataclass
class Task:
    description: str
    duration: int  # minutes
    priority: str  # "high" | "medium" | "low"
    time: str = ""  # time of day, e.g. "08:00" ("" = not yet scheduled)
    frequency: str = "daily"  # e.g. "daily" | "weekly"
    completed: bool = False

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

    def get_details(self) -> str:
        """Return a one-line human-readable summary of the task."""
        # Prefix the time of day when set; append a done marker when complete.
        when = f"{self.time} - " if self.time else ""
        status = " [done]" if self.completed else ""
        return f"{when}{self.description} ({self.duration} min) [priority: {self.priority}]{status}"


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def update_info(self, **info) -> None:
        """Update the pet's detail fields (name, species, breed, age) by keyword."""
        # Restricted to details so a stray key can't wipe the tasks list.
        details = {"name", "species", "breed", "age"}
        for key, value in info.items():
            if key not in details:
                raise AttributeError(f"'{key}' is not an editable Pet detail")
            setattr(self, key, value)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    available_time: int = 0  # minutes available per day
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

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
        """Register a pet under this owner."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets as one flat list."""
        # This is the single access point the Scheduler pulls from.
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain': retrieves tasks across an owner's pets, organizes them by
    priority, and builds/explains a daily plan that fits the available time."""

    def collect_tasks(self, owner: Owner) -> list[Task]:
        """Retrieve every care task across all of the owner's pets."""
        # Delegates to Owner.all_tasks() so Owner stays the source of truth.
        return owner.all_tasks()

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return a new list ordered by priority, then shortest duration."""
        # Sorting a copy leaves the caller's original order untouched.
        return sorted(
            tasks,
            key=lambda t: (PRIORITY_RANK.get(t.priority, LOWEST_RANK), t.duration),
        )

    def generate_plan(self, tasks: list[Task], available_time: int) -> list[Task]:
        """Return the not-done tasks that fit within available_time, in priority order."""
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
        used = 0
        for task in plan:
            used += task.duration
            lines.append(f"  - {task.get_details()}")
        lines.append(f"Total scheduled time: {used} min")

        # List anything skipped and why, so the reasoning is transparent.
        skipped = [t for t in tasks if id(t) not in planned_ids]
        if skipped:
            lines.append("Skipped:")
            for task in skipped:
                reason = "already done" if task.completed else "not enough time left"
                lines.append(f"  - {task.get_details()} ({reason})")
        return "\n".join(lines)
