from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler

# Create two pets and an owner with a daily time budget.
cat = Pet(name="Whiskers", species="Cat", breed="Siamese", age=3)
doggy = Pet(name="Buddy", species="Dog", breed="Golden Retriever", age=5)
mickyOwner = Owner(name="Micky", available_time=60, preferences={"walks": True, "grooming": False})

# Tasks are added deliberately OUT OF time order to prove sort_by_time() works.
# Feed Whiskers and Feed Buddy share the 08:00 slot on purpose (a conflict).
cat.add_task(Task(description="Play with Whiskers", duration=15, priority="low", time="17:00"))
cat.add_task(Task(description="Feed Whiskers", duration=5, priority="high", time="08:00", frequency="daily"))
doggy.add_task(Task(description="Walk Buddy", duration=10, priority="medium", time="09:00"))
doggy.add_task(Task(description="Feed Buddy", duration=7, priority="high", time="08:00", frequency="daily"))

# Register the pets under the owner.
mickyOwner.add_pet(cat)
mickyOwner.add_pet(doggy)

scheduler = Scheduler()
tasks = scheduler.collect_tasks(mickyOwner)

# Sorting by time (tasks were added out of order above). 
print("=== Tasks sorted by time of day ===")
for t in scheduler.sort_by_time(tasks):
    print(f"  {t.get_details()}")

# Filtering by status and by pet. 
cat.tasks[0].mark_complete()  # mark "Play with Whiskers" done for the demo
print("\n=== Pending tasks only ===")
for t in scheduler.filter_tasks(tasks, "pending"):
    print(f"  {t.get_details()}")
print("\n=== Buddy's tasks only ===")
for t in scheduler.collect_tasks(mickyOwner, pet_name="Buddy"):
    print(f"  {t.get_details()}")

# Overlapping times are flagged as warnings.
print("\n========================================================")
print("Today's Schedule")
print(scheduler.explain_plan(tasks, mickyOwner.available_time))
print("========================================================")

# Completing a recurring task spawns its next occurrence.
feed_buddy = doggy.tasks[1]  # "Feed Buddy", frequency="daily"
next_feed = scheduler.complete_task(doggy, feed_buddy, today=date.today())
print("\n=== Recurring task auto-rescheduled ===")
print(f"  Completed: {feed_buddy.get_details()}")
if next_feed:
    print(f"  Next up:   {next_feed.get_details()}")
