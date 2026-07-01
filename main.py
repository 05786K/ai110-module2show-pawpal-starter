from pawpal_system import Owner, Pet, Task, Scheduler

# Create two pets and an owner with a daily time budget.
cat = Pet(name="Whiskers", species="Cat", breed="Siamese", age=3)
doggy = Pet(name="Buddy", species="Dog", breed="Golden Retriever", age=5)
mickyOwner = Owner(name="Micky", available_time=60, preferences={"walks": True, "grooming": False})

# Give each pet its own care tasks, each with a time of day.
cat.add_task(Task(description="Feed Whiskers", duration=5, priority="high", time="08:00"))
cat.add_task(Task(description="Play with Whiskers", duration=15, priority="low", time="17:00"))
doggy.add_task(Task(description="Walk Buddy", duration=10, priority="medium", time="09:00"))
doggy.add_task(Task(description="Feed Buddy", duration=7, priority="high", time="08:15"))

# Register the pets under the owner.
mickyOwner.add_pet(cat)
mickyOwner.add_pet(doggy)

# Pull every task across the owner's pets into one list.
scheduler = Scheduler()
tasks = scheduler.collect_tasks(mickyOwner)

# Build and print the day's plan within the available time.
print("========================================================")
print("Today's Schedule")
print(scheduler.explain_plan(tasks, mickyOwner.available_time))
print("========================================================")
