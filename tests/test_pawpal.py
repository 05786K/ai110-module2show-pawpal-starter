from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def test_task_completion():
    # A new task starts incomplete; mark_complete() should flip it to done.
    task = Task(description="Feed Whiskers", duration=5, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_task_addition():
    # Adding a task to a pet should grow that pet's task list by one.
    pet = Pet(name="Buddy", species="dog", breed="Golden Retriever", age=5)
    assert len(pet.tasks) == 0
    pet.add_task(Task(description="Walk Buddy", duration=10, priority="medium"))
    assert len(pet.tasks) == 1


def test_sort_by_time_puts_unscheduled_last():
    # Times are compared chronologically, and '' (unscheduled) sorts to the end.
    scheduler = Scheduler()
    evening = Task(description="Play", duration=15, priority="low", time="17:00")
    morning = Task(description="Feed", duration=5, priority="high", time="9:00")
    anytime = Task(description="Brush", duration=5, priority="low")
    ordered = scheduler.sort_by_time([evening, anytime, morning])
    assert ordered == [morning, evening, anytime]


def test_filter_tasks_by_status():
    scheduler = Scheduler()
    done = Task(description="Feed", duration=5, priority="high")
    done.mark_complete()
    pending = Task(description="Walk", duration=10, priority="medium")
    tasks = [done, pending]
    assert scheduler.filter_tasks(tasks, "pending") == [pending]
    assert scheduler.filter_tasks(tasks, "done") == [done]
    assert scheduler.filter_tasks(tasks, "all") == tasks


def test_collect_tasks_scoped_to_pet():
    scheduler = Scheduler()
    cat = Pet(name="Whiskers", species="cat", breed="Siamese", age=3)
    dog = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    cat.add_task(Task(description="Feed cat", duration=5, priority="high"))
    dog.add_task(Task(description="Walk dog", duration=10, priority="medium"))
    owner = Owner(name="Micky")
    owner.add_pet(cat)
    owner.add_pet(dog)
    scoped = scheduler.collect_tasks(owner, pet_name="buddy")  # case-insensitive
    assert [t.description for t in scoped] == ["Walk dog"]


def test_next_due_date_uses_timedelta():
    scheduler = Scheduler()
    today = date(2026, 7, 1)
    daily = Task(description="Feed", duration=5, priority="high", frequency="daily")
    weekly = Task(description="Bath", duration=20, priority="low", frequency="weekly")
    once = Task(description="Vet", duration=30, priority="high", frequency="once")
    assert scheduler.next_due_date(daily, today) == date(2026, 7, 2)
    assert scheduler.next_due_date(weekly, today) == date(2026, 7, 8)
    assert scheduler.next_due_date(once, today) is None


def test_complete_task_spawns_next_occurrence():
    scheduler = Scheduler()
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    daily = Task(description="Walk", duration=10, priority="medium", frequency="daily")
    pet.add_task(daily)
    today = date(2026, 7, 1)
    new_task = scheduler.complete_task(pet, daily, today=today)
    # Original is marked done; a fresh, pending copy is queued for tomorrow.
    assert daily.completed is True
    assert new_task is not None
    assert new_task.completed is False
    assert new_task.due_date == date(2026, 7, 2)
    assert pet.tasks == [daily, new_task]


def test_repeated_completion_advances_due_date():
    # Completing the recurring task twice should land two days out, not repeat
    # today + 1 each time (regression: due date must chain off the task's own).
    scheduler = Scheduler()
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    daily = Task(description="Walk", duration=10, priority="medium", frequency="daily")
    pet.add_task(daily)
    first = scheduler.complete_task(pet, daily, today=date(2026, 7, 1))
    assert first.due_date == date(2026, 7, 2)
    second = scheduler.complete_task(pet, first)  # no today passed; chains off due_date
    assert second.due_date == date(2026, 7, 3)


def test_complete_task_once_does_not_recur():
    scheduler = Scheduler()
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    once = Task(description="Vet visit", duration=30, priority="high", frequency="once")
    pet.add_task(once)
    result = scheduler.complete_task(pet, once, today=date(2026, 7, 1))
    assert once.completed is True
    assert result is None
    assert pet.tasks == [once]  # no new instance added


def test_find_conflicts_detects_overlap():
    scheduler = Scheduler()
    a = Task(description="Feed", duration=30, priority="high", time="08:00")  # 08:00-08:30
    b = Task(description="Walk", duration=10, priority="medium", time="08:15")  # overlaps
    c = Task(description="Play", duration=15, priority="low", time="09:00")  # clear
    conflicts = scheduler.find_conflicts([a, b, c])
    assert conflicts == [(a, b)]
