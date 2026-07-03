from datetime import date

import pytest

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


# ---------------------------------------------------------------------------
# Sorting correctness — tasks come back in chronological order
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    # Fed in scrambled order (and one time isn't zero-padded) — must come back
    # strictly by clock time, not by insertion order or string comparison.
    scheduler = Scheduler()
    evening = Task(description="Play", duration=15, priority="low", time="17:00")
    morning = Task(description="Feed", duration=5, priority="high", time="08:00")
    midmorning = Task(description="Walk", duration=10, priority="medium", time="9:00")
    midday = Task(description="Lunch", duration=5, priority="low", time="12:30")
    ordered = scheduler.sort_by_time([evening, morning, midday, midmorning])
    assert [t.time for t in ordered] == ["08:00", "9:00", "12:30", "17:00"]


def test_sort_by_time_does_not_mutate_input():
    # Sorting returns a new list; the caller's original order is preserved.
    scheduler = Scheduler()
    a = Task(description="Play", duration=15, priority="low", time="17:00")
    b = Task(description="Feed", duration=5, priority="high", time="08:00")
    original = [a, b]
    scheduler.sort_by_time(original)
    assert original == [a, b]


def test_sort_by_time_empty_list():
    assert Scheduler().sort_by_time([]) == []


def test_sort_tasks_orders_by_priority_then_duration():
    # High before medium before low; within a priority, shorter first.
    scheduler = Scheduler()
    low = Task(description="Play", duration=15, priority="low")
    high_long = Task(description="Groom", duration=20, priority="high")
    high_short = Task(description="Feed", duration=5, priority="high")
    medium = Task(description="Walk", duration=10, priority="medium")
    ordered = scheduler.sort_tasks([low, high_long, medium, high_short])
    assert ordered == [high_short, high_long, medium, low]


def test_sort_tasks_unknown_priority_sinks_to_bottom():
    # An unrecognized priority falls back to the lowest rank instead of crashing.
    scheduler = Scheduler()
    weird = Task(description="Mystery", duration=5, priority="urgent")
    high = Task(description="Feed", duration=5, priority="high")
    ordered = scheduler.sort_tasks([weird, high])
    assert ordered == [high, weird]


# ---------------------------------------------------------------------------
# Recurrence — completing a daily task creates one for the following day
# ---------------------------------------------------------------------------

def test_daily_completion_creates_task_for_following_day():
    scheduler = Scheduler()
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    daily = Task(description="Feed", duration=5, priority="high", time="08:00", frequency="daily")
    pet.add_task(daily)
    today = date(2026, 7, 1)

    new_task = scheduler.complete_task(pet, daily, today=today)

    # Original is done; a fresh, pending copy is queued for the *next day*.
    assert daily.completed is True
    assert new_task is not None
    assert new_task.completed is False
    assert new_task.due_date == date(2026, 7, 2)  # the following day
    # The copy carries over the task's identity fields...
    assert (new_task.description, new_task.time, new_task.frequency) == ("Feed", "08:00", "daily")
    # ...and is actually attached to the pet.
    assert pet.tasks == [daily, new_task]


def test_weekly_completion_creates_task_seven_days_later():
    scheduler = Scheduler()
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    weekly = Task(description="Bath", duration=20, priority="low", frequency="weekly")
    pet.add_task(weekly)
    new_task = scheduler.complete_task(pet, weekly, today=date(2026, 7, 1))
    assert new_task.due_date == date(2026, 7, 8)


def test_next_due_date_handles_month_rollover():
    scheduler = Scheduler()
    daily = Task(description="Feed", duration=5, priority="high", frequency="daily")
    weekly = Task(description="Bath", duration=20, priority="low", frequency="weekly")
    # Daily crossing a month boundary.
    assert scheduler.next_due_date(daily, date(2026, 7, 31)) == date(2026, 8, 1)
    # Weekly crossing a month boundary.
    assert scheduler.next_due_date(weekly, date(2026, 7, 28)) == date(2026, 8, 4)


def test_recurring_respawn_not_blocked_by_duplicate_guard():
    # add_task rejects exact duplicates, but a respawned occurrence differs by
    # due_date/completed, so completing a recurring task must still succeed.
    scheduler = Scheduler()
    pet = Pet(name="Cat", species="cat", breed="Siamese", age=3)
    daily = Task(description="Feed", duration=5, priority="high", time="08:00", frequency="daily")
    pet.add_task(daily)
    new_task = scheduler.complete_task(pet, daily, today=date(2026, 7, 1))
    assert new_task is not None
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Conflict detection — overlapping / identical times are flagged
# ---------------------------------------------------------------------------

def test_find_conflicts_flags_identical_times():
    # Two tasks scheduled at the exact same time-of-day overlap by definition.
    scheduler = Scheduler()
    a = Task(description="Feed cat", duration=5, priority="high", time="08:00")
    b = Task(description="Feed dog", duration=7, priority="high", time="08:00")
    assert scheduler.find_conflicts([a, b]) == [(a, b)]


def test_find_conflicts_back_to_back_do_not_overlap():
    # Half-open windows: 08:00-08:30 then 08:30-08:40 touch but don't overlap.
    scheduler = Scheduler()
    a = Task(description="Feed", duration=30, priority="high", time="08:00")
    b = Task(description="Walk", duration=10, priority="medium", time="08:30")
    assert scheduler.find_conflicts([a, b]) == []


def test_find_conflicts_ignores_completed_and_unscheduled():
    scheduler = Scheduler()
    done = Task(description="Feed", duration=30, priority="high", time="08:00")
    done.mark_complete()
    anytime = Task(description="Brush", duration=30, priority="low")  # no time
    live = Task(description="Walk", duration=10, priority="medium", time="08:10")
    # `done` would overlap `live`, but it's completed; `anytime` has no clock slot.
    assert scheduler.find_conflicts([done, anytime, live]) == []


def test_find_conflicts_reports_all_overlapping_pairs():
    scheduler = Scheduler()
    a = Task(description="A", duration=60, priority="high", time="08:00")  # 08:00-09:00
    b = Task(description="B", duration=30, priority="high", time="08:15")  # 08:15-08:45
    c = Task(description="C", duration=30, priority="high", time="08:30")  # 08:30-09:00
    # All three windows mutually overlap, so every pair is reported.
    conflicts = scheduler.find_conflicts([a, b, c])
    assert conflicts == [(a, b), (a, c), (b, c)]


# ---------------------------------------------------------------------------
# Next available slot — suggest the earliest conflict-free start time
# ---------------------------------------------------------------------------

def test_find_free_slot_returns_day_start_when_empty():
    # Nothing scheduled: the first slot is the start of the day window.
    scheduler = Scheduler()
    assert scheduler.find_free_slot([], duration=30) == "06:00"


def test_find_free_slot_finds_gap_between_tasks():
    # 08:00-08:30 busy, 09:00-10:00 busy. A 20-min task fits from 08:30.
    scheduler = Scheduler()
    a = Task(description="Feed", duration=30, priority="high", time="08:00")
    b = Task(description="Walk", duration=60, priority="medium", time="09:00")
    assert scheduler.find_free_slot([a, b], duration=20, day_start="08:00") == "08:30"


def test_find_free_slot_skips_gap_too_small():
    # Only a 15-min gap between 08:30 and 09:00 — a 30-min task must land later.
    scheduler = Scheduler()
    a = Task(description="Feed", duration=30, priority="high", time="08:00")  # 08:00-08:30
    b = Task(description="Walk", duration=60, priority="medium", time="08:45")  # 08:45-09:45
    # Gap 08:30-08:45 is only 15 min; task goes after the second block, at 09:45.
    assert scheduler.find_free_slot([a, b], duration=30, day_start="08:00") == "09:45"


def test_find_free_slot_respects_earliest():
    # `earliest` pushes the search past a time even when earlier slots are free.
    scheduler = Scheduler()
    assert scheduler.find_free_slot([], duration=30, earliest="14:00") == "14:00"


def test_find_free_slot_ignores_completed_and_unscheduled():
    # Completed / unscheduled tasks don't occupy the clock, so 06:00 stays free.
    scheduler = Scheduler()
    done = Task(description="Feed", duration=120, priority="high", time="06:00")
    done.mark_complete()
    anytime = Task(description="Brush", duration=120, priority="low")  # no time
    assert scheduler.find_free_slot([done, anytime], duration=30) == "06:00"


def test_find_free_slot_handles_nested_busy_block():
    # A short task fully inside a longer one: once the cursor has passed the
    # long block, the nested block is already behind it and is skipped.
    scheduler = Scheduler()
    long = Task(description="Groom", duration=60, priority="high", time="08:00")  # 08:00-09:00
    nested = Task(description="Feed", duration=15, priority="high", time="08:15")  # 08:15-08:30
    slot = scheduler.find_free_slot([long, nested], duration=30, day_start="08:00")
    assert slot == "09:00"


def test_find_free_slot_returns_none_when_day_full():
    # A task that can't finish by day_end has nowhere to go.
    scheduler = Scheduler()
    block = Task(description="All day", duration=600, priority="high", time="12:00")  # 12:00-22:00
    assert scheduler.find_free_slot([block], duration=60, day_start="12:00") is None


def test_find_free_slot_rejects_non_positive_duration():
    with pytest.raises(ValueError):
        Scheduler().find_free_slot([], duration=0)


# ---------------------------------------------------------------------------
# Plan generation & explanation
# ---------------------------------------------------------------------------

def test_generate_plan_greedily_fits_smaller_task_after_skipping_big_one():
    # Budget 12: high(5) fits, high(10) overflows and is skipped, medium(3) still fits.
    scheduler = Scheduler()
    high_short = Task(description="Feed", duration=5, priority="high")
    high_long = Task(description="Groom", duration=10, priority="high")
    medium = Task(description="Walk", duration=3, priority="medium")
    plan = scheduler.generate_plan([high_long, high_short, medium], available_time=12)
    assert plan == [high_short, medium]


def test_generate_plan_with_zero_time_is_empty():
    scheduler = Scheduler()
    task = Task(description="Feed", duration=5, priority="high")
    assert scheduler.generate_plan([task], available_time=0) == []


def test_generate_plan_skips_completed_tasks():
    scheduler = Scheduler()
    done = Task(description="Feed", duration=5, priority="high")
    done.mark_complete()
    assert scheduler.generate_plan([done], available_time=60) == []


def test_generate_plan_rejects_negative_time():
    with pytest.raises(ValueError):
        Scheduler().generate_plan([], available_time=-1)


def test_explain_plan_reports_conflicts_and_skips():
    scheduler = Scheduler()
    a = Task(description="Feed cat", duration=5, priority="high", time="08:00")
    b = Task(description="Feed dog", duration=7, priority="high", time="08:00")  # conflict
    big = Task(description="Long groom", duration=100, priority="low", time="10:00")  # won't fit
    text = scheduler.explain_plan([a, b, big], available_time=30)
    assert "Conflicts (overlapping times):" in text
    assert "Skipped:" in text
    assert "not enough time left" in text


# ---------------------------------------------------------------------------
# collect_tasks / filter_tasks edge cases
# ---------------------------------------------------------------------------

def test_collect_tasks_owner_with_no_pets():
    assert Scheduler().collect_tasks(Owner(name="Nobody")) == []


def test_collect_tasks_unknown_pet_name_returns_empty():
    scheduler = Scheduler()
    owner = Owner(name="Micky")
    owner.add_pet(Pet(name="Buddy", species="dog", breed="Golden", age=5))
    assert scheduler.collect_tasks(owner, pet_name="Ghost") == []


def test_filter_tasks_invalid_status_raises():
    with pytest.raises(ValueError):
        Scheduler().filter_tasks([], status="archived")


# ---------------------------------------------------------------------------
# Validation: times must be well-formed and in range
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_time", ["25:00", "12:99", "-1:30", "abc", "8", "8:", ":30", "8:00:00"])
def test_task_rejects_malformed_or_out_of_range_time(bad_time):
    with pytest.raises(ValueError):
        Task(description="x", duration=5, priority="high", time=bad_time)


@pytest.mark.parametrize("ok_time", ["00:00", "9:00", "08:05", "23:59", ""])
def test_task_accepts_valid_or_empty_time(ok_time):
    # Should not raise. Empty string means 'unscheduled'.
    Task(description="x", duration=5, priority="high", time=ok_time)


def test_update_task_revalidates_time():
    task = Task(description="x", duration=5, priority="high", time="08:00")
    with pytest.raises(ValueError):
        task.update_task(time="99:99")


# ---------------------------------------------------------------------------
# Validation: positive duration, non-negative age / available_time
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_duration", [0, -1, -60])
def test_task_rejects_non_positive_duration(bad_duration):
    with pytest.raises(ValueError):
        Task(description="x", duration=bad_duration, priority="high")


def test_update_task_rejects_non_positive_duration():
    task = Task(description="x", duration=5, priority="high")
    with pytest.raises(ValueError):
        task.update_task(duration=0)


def test_update_task_unknown_field_raises():
    task = Task(description="x", duration=5, priority="high")
    with pytest.raises(AttributeError):
        task.update_task(completed=True)


def test_pet_rejects_negative_age():
    with pytest.raises(ValueError):
        Pet(name="Buddy", species="dog", breed="Golden", age=-1)


def test_update_info_updates_valid_fields():
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    pet.update_info(name="Max", age=6)
    assert (pet.name, pet.age) == ("Max", 6)


def test_update_info_unknown_field_raises():
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    with pytest.raises(AttributeError):
        pet.update_info(tasks=[])


def test_set_available_time_updates_value():
    owner = Owner(name="Micky")
    owner.set_available_time(90)
    assert owner.available_time == 90


def test_update_preferences_merges_without_dropping_existing():
    owner = Owner(name="Micky", preferences={"walks": True})
    owner.update_preferences({"grooming": False})
    assert owner.preferences == {"walks": True, "grooming": False}


def test_owner_rejects_negative_available_time_on_construction():
    with pytest.raises(ValueError):
        Owner(name="Micky", available_time=-10)


def test_set_available_time_rejects_negative():
    owner = Owner(name="Micky")
    with pytest.raises(ValueError):
        owner.set_available_time(-5)


# ---------------------------------------------------------------------------
# Persistence — save/load owner graph to JSON, round-tripping cleanly
# ---------------------------------------------------------------------------

def _sample_owner():
    owner = Owner(name="Jordan", available_time=90, preferences={"walks": True})
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    pet.add_task(Task(description="Walk", duration=10, priority="medium", time="09:00"))
    done = Task(description="Feed", duration=5, priority="high", time="08:00")
    done.mark_complete()
    done.due_date = date(2026, 7, 2)
    pet.add_task(done)
    owner.add_pet(pet)
    return owner


def test_task_dict_round_trip_preserves_due_date():
    task = Task(description="Feed", duration=5, priority="high", time="08:00", frequency="daily")
    task.due_date = date(2026, 7, 2)
    restored = Task.from_dict(task.to_dict())
    assert restored == task  # dataclass == compares every field, incl. date


def test_task_dict_round_trip_with_no_due_date():
    task = Task(description="Brush", duration=5, priority="low")
    restored = Task.from_dict(task.to_dict())
    assert restored == task
    assert restored.due_date is None


def test_owner_dict_round_trip_rebuilds_full_graph():
    owner = _sample_owner()
    restored = Owner.from_dict(owner.to_dict())
    assert restored == owner  # owner, pets, and tasks all compare equal


def test_save_and_load_from_json_file(tmp_path):
    owner = _sample_owner()
    path = tmp_path / "data.json"
    owner.save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))
    assert loaded == owner
    # The saved due_date survives as a real date, not a string.
    assert loaded.pets[0].tasks[1].due_date == date(2026, 7, 2)


def test_load_from_json_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(str(tmp_path / "does_not_exist.json"))


def test_from_dict_defaults_for_minimal_data():
    # Missing optional keys fall back to sensible defaults (empty/pending).
    owner = Owner.from_dict({"name": "Solo"})
    assert owner.available_time == 0
    assert owner.pets == []
    task = Task.from_dict({"description": "x", "duration": 5, "priority": "high"})
    assert task.time == "" and task.completed is False and task.due_date is None


def test_load_rejects_corrupt_value(tmp_path):
    # A persisted bad duration must fail validation on load, not slip through.
    path = tmp_path / "bad.json"
    path.write_text(
        '{"name": "Jordan", "pets": [{"name": "Buddy", "species": "dog", '
        '"breed": "", "age": 0, "tasks": [{"description": "x", "duration": 0, '
        '"priority": "high"}]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        Owner.load_from_json(str(path))


# ---------------------------------------------------------------------------
# Duplicate-task rejection
# ---------------------------------------------------------------------------

def test_add_task_rejects_exact_duplicate():
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    pet.add_task(Task(description="Walk", duration=10, priority="medium", time="09:00"))
    with pytest.raises(ValueError):
        pet.add_task(Task(description="Walk", duration=10, priority="medium", time="09:00"))
    assert len(pet.tasks) == 1


def test_remove_task_deletes_only_that_instance():
    # remove_task matches by identity, so only the held object is dropped.
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    walk = Task(description="Walk", duration=10, priority="medium", time="09:00")
    feed = Task(description="Feed", duration=5, priority="high", time="08:00")
    pet.add_task(walk)
    pet.add_task(feed)
    pet.remove_task(walk)
    assert pet.tasks == [feed]


def test_remove_task_not_attached_raises():
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    stray = Task(description="Ghost", duration=5, priority="low")
    with pytest.raises(ValueError):
        pet.remove_task(stray)


def test_add_task_allows_near_duplicate_differing_by_one_field():
    pet = Pet(name="Buddy", species="dog", breed="Golden", age=5)
    pet.add_task(Task(description="Walk", duration=10, priority="medium", time="09:00"))
    # Same everything but a different duration — not an exact duplicate.
    pet.add_task(Task(description="Walk", duration=15, priority="medium", time="09:00"))
    assert len(pet.tasks) == 2


def test_add_pet_rejects_duplicate_name_case_insensitive():
    # Two pets with the same name (ignoring case) are the same pet — reject the
    # second so the owner can't accidentally register a duplicate.
    owner = Owner(name="Micky")
    owner.add_pet(Pet(name="Buddy", species="dog", breed="Golden", age=5))
    with pytest.raises(ValueError):
        owner.add_pet(Pet(name="buddy", species="cat", breed="Siamese", age=3))
    assert len(owner.pets) == 1
