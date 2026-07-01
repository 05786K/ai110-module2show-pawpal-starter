from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Owner:
    name: str
    available_time: int = 0  # minutes available per day
    preferences: dict = field(default_factory=dict)

    def set_available_time(self, minutes: int) -> None:
        """Set the total time the owner has for pet care today."""
        raise NotImplementedError

    def update_preferences(self, prefs: dict) -> None:
        """Merge new preference key/values into this owner's preferences."""
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int

    def update_info(self, **info) -> None:
        """Update one or more pet fields (name, species, breed, age)."""
        raise NotImplementedError


@dataclass
class Task:
    name: str
    duration: int  # minutes
    priority: str  # e.g. "high" | "medium" | "low"  (type still TBD)
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        raise NotImplementedError

    def update_task(self, **fields) -> None:
        """Update one or more task fields (name, duration, priority)."""
        raise NotImplementedError

    def get_details(self) -> str:
        """Return a human-readable one-line summary of the task."""
        raise NotImplementedError


class Scheduler:
    """Builds and explains a daily care plan from a list of tasks."""

    def __init__(self, available_time: int = 0) -> None:
        self.tasks: list[Task] = []
        self.available_time = available_time

    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler's task list."""
        raise NotImplementedError

    def sort_tasks(self) -> list[Task]:
        """Return tasks ordered by scheduling priority (e.g. priority, duration)."""
        raise NotImplementedError

    def generate_plan(self) -> list[Task]:
        """Return the subset of tasks that fit within available_time."""
        raise NotImplementedError

    def explain_plan(self) -> str:
        """Return a human-readable explanation of why the plan was chosen."""
        raise NotImplementedError
