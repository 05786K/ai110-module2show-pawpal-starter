from pawpal_system import Pet, Task


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
