import sys
from datetime import date

from tabulate import tabulate

from formatting import priority_badge, status_icon, type_icon
from pawpal_system import Owner, Pet, Task, Scheduler

# The Windows console defaults to cp1252, which can't encode emoji. Force UTF-8
# so the formatted output renders everywhere. (No-op if already UTF-8.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def task_table(tasks: list[Task]) -> str:
    """Render tasks as a structured grid using tabulate (Challenge 4)."""
    rows = [
        [
            status_icon(t.completed),
            f"{type_icon(t.description)} {t.description}",
            t.time or "anytime",
            f"{t.duration} min",
            priority_badge(t.priority),
        ]
        for t in tasks
    ]
    headers = ["Status", "Task", "Time", "Duration", "Priority"]
    return tabulate(rows, headers=headers, tablefmt="rounded_grid")

# Create two pets and an owner with a daily time budget.
cat = Pet(name="Whiskers", species="Cat", breed="Siamese", age=3)
doggy = Pet(name="Buddy", species="Dog", breed="Golden Retriever", age=5)
mickyOwner = Owner(name="Micky", available_time=60, preferences={"walks": True, "grooming": False})

# Tasks are added deliberately OUT OF time order to prove sort_by_time() works.
# Priorities are mixed (and durations vary within a priority) to show
# sort_tasks() ordering high -> medium -> low, shorter duration breaking ties.
# Feed Whiskers and Feed Buddy share the 08:00 slot on purpose (a conflict).
cat.add_task(Task(description="Play with Whiskers", duration=15, priority="low", time="17:00"))
cat.add_task(Task(description="Feed Whiskers", duration=5, priority="high", time="08:00", frequency="daily"))
cat.add_task(Task(description="Give Whiskers meds", duration=5, priority="high", time="07:30"))
cat.add_task(Task(description="Brush Whiskers", duration=10, priority="low", time="16:00"))
doggy.add_task(Task(description="Walk Buddy", duration=10, priority="medium", time="09:00"))
doggy.add_task(Task(description="Feed Buddy", duration=7, priority="high", time="08:00", frequency="daily"))
doggy.add_task(Task(description="Groom Buddy", duration=20, priority="medium", time="10:00"))

# Register the pets under the owner.
mickyOwner.add_pet(cat)
mickyOwner.add_pet(doggy)

scheduler = Scheduler()
tasks = scheduler.collect_tasks(mickyOwner)

# Sorting by time (tasks were added out of order above).
print("📅  Tasks sorted by time of day")
print(task_table(scheduler.sort_by_time(tasks)))

# Advanced priority sorting: high -> medium -> low, shorter duration breaks ties
# within a priority (e.g. the two 5-min high tasks come before the 7-min one).
print("\n⭐  Tasks sorted by priority (High → Low)")
print(task_table(scheduler.sort_tasks(tasks)))

# Filtering by status and by pet.
cat.tasks[0].mark_complete()  # mark "Play with Whiskers" done for the demo
print("\n⏳  Pending tasks only")
print(task_table(scheduler.filter_tasks(tasks, "pending")))
print("\n🐕  Buddy's tasks only")
print(task_table(scheduler.collect_tasks(mickyOwner, pet_name="Buddy")))

# Overlapping times are flagged as warnings.
print("\n" + "=" * 56)
print("🗓️  Today's Schedule")
print(scheduler.explain_plan(tasks, mickyOwner.available_time))
print("=" * 56)

# Completing a recurring task spawns its next occurrence.
feed_buddy = doggy.tasks[1]  # "Feed Buddy", frequency="daily"
next_feed = scheduler.complete_task(doggy, feed_buddy, today=date.today())
print("\n🔁  Recurring task auto-rescheduled")
print(f"  Completed: {status_icon(feed_buddy.completed)}  {feed_buddy.get_details()}")
if next_feed:
    print(f"  Next up:   {status_icon(next_feed.completed)}  {next_feed.get_details()}")
