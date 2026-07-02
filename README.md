# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
========================================================
Today's Schedule
Daily plan (60 min available):
  - 08:00 - Feed Whiskers (5 min) [priority: high]
  - 08:15 - Feed Buddy (7 min) [priority: high]
  - 09:00 - Walk Buddy (10 min) [priority: medium]
  - 17:00 - Play with Whiskers (15 min) [priority: low]
Total scheduled time: 37 min
========================================================
```

## 🧪 Testing PawPal+

```bash

The suite covers sorting, daily/weekly recurrence, and time-conflict detection, plus input validation and duplicate-task rejection — 59 tests at 100% coverage.

# Run the full test suite:
python -m pytest
  ```
  collected 59 items                                                                                                                                          

  tests\test_pawpal.py ...........................................................                                                                      [100%]

  ==================================================================== 59 passed in 0.08s ====================================================================
  ```
# Run with coverage:
pytest --cov
```
Sample test output:
plugins: anyio-4.14.0, cov-7.1.0
collected 59 items                                                                                                                                          

tests\test_pawpal.py ...........................................................                                                                      [100%]

====================================================================== tests coverage ======================================================================
_____________________________________________________ coverage: platform win32, python 3.13.13-final-0 _____________________________________________________

Name                   Stmts   Miss  Cover
------------------------------------------
conftest.py                0      0   100%
pawpal_system.py         162      0   100%
tests\test_pawpal.py     273      0   100%
------------------------------------------
TOTAL                    435      0   100%
==================================================================== 59 passed in 0.22s ====================================================================

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

All methods below live on the `Scheduler` class.

| Feature           | Method(s)                                       | Notes                                                        |
|-------------------|-------------------------------------------------|--------------------------------------------------------------|
| Task sorting      | `sort_tasks()`, `sort_by_time()`                | Priority order for selection; time-of-day order for display. |
| Filtering         | `filter_tasks()`, `collect_tasks(pet_name=...)` | By completion status or by pet name.                         |
| Conflict handling | `find_conflicts()`                              | Flags overlapping time windows (warning only).               |
| Recurring tasks   | `complete_task()`, `next_due_date()`            | Spawns the next daily/weekly occurrence via `timedelta`.     |


## Features
- **Priority-based planning** — `generate_plan()` greedily packs tasks into the owner's available minutes, choosing higher-priority (and, as a tiebreaker, shorter) tasks first so the most important care happens when time is tight.
- **Sorting by priority** — `sort_tasks()` orders tasks by priority rank, then by shortest duration.
- **Sorting by time of day** — `sort_by_time()` orders tasks chronologically (parsing `HH:MM` to minutes), pushing unscheduled tasks to the end as "anytime" items.
- **Filtering** — `filter_tasks()` narrows by status (`all` / `pending` / `done`); `collect_tasks(pet_name=...)` scopes tasks to a single pet.
- **Conflict warnings** — `find_conflicts()` detects overlapping time windows between scheduled, incomplete tasks and reports them as warnings without dropping any task from the plan.
- **Daily & weekly recurrence** — completing a recurring task (`complete_task()`) automatically spawns its next occurrence, with `next_due_date()` advancing the due date by a day or a week via `timedelta`.
- **Plan explanation** — `explain_plan()` produces a human-readable breakdown of what was scheduled, the total time used, any conflicts, and what was skipped and why.
- **Input validation** — tasks reject non-positive durations and malformed/out-of-range times; owners reject negative available time, so invalid data fails loudly at construction.
- **Interactive Streamlit UI** — [`app.py`](app.py) surfaces sorting, filtering, conflict banners, and a schedule table wired to the `Scheduler`.

## 📸 Demo Walkthrough

### Main UI features & user actions

  - **Owner & Pets** — set the owner's name and **add pets** (name, species). Added pets are listed and persist across reruns.
  - **Tasks** — attach a task to a chosen pet with a title, **duration**, **priority** (low/medium/high), **time of day**, and **frequency** (daily/weekly/once). Duplicate and invalid tasks are rejected with a warning instead of crashing.
  - **Current tasks** — **filter** by pet and by status (all/pending/done), **sort** the view by time of day or by priority, and **mark tasks done** with a button (which queues the next occurrence for recurring tasks). An early banner warns if any tasks overlap.
  - **Build Schedule** — set the day's **available time** and **generate a plan**: a schedule table (Time / Pet / Task / Duration / Priority), a success summary of time used vs. free, per-conflict warning banners, a skipped-tasks breakdown, and a full text explanation.

### Example workflow

  1. Set the **owner name**, then add a pet — e.g. "Mochi" (dog).
  2. Add a task to Mochi: *Morning walk*, 20 min, high priority, 08:00, daily.
  3. Add a second task: *Feed*, 10 min, high priority, 08:15, daily.
  4. In **Current tasks**, sort by *Time of day* and see both listed; a heads-up warns they overlap.
  5. Under **Build Schedule**, set available time to 60 minutes and click **Generate schedule**.
  6. View today's schedule: a table in clock order, a "✅ 2 tasks scheduled — 30 of 60 min used" summary, and a conflict banner for the walk/feed overlap.
  7. Click **Done** on *Morning walk* — it's marked complete and tomorrow's walk is auto-created (daily recurrence).

### Key Scheduler behaviors shown

  - **Priority selection** — when time is short, `generate_plan()` keeps higher-priority (then shorter) tasks and skips the rest, listing skipped items with reasons.
  - **Sorting** — tasks display in clock order via `sort_by_time()`, while selection uses `sort_tasks()` (priority-first).
  - **Conflict warnings** — `find_conflicts()` flags overlapping time windows as individual warning banners; the plan is never silently altered.
  - **Recurrence** — completing a daily/weekly task spawns its next occurrence via `complete_task()` / `next_due_date()`.
  - **Filtering** — `filter_tasks()` and `collect_tasks(pet_name=...)` drive the pet/status views.

### Sample CLI output from running main.py
```
=== Tasks sorted by time of day ===
  08:00 - Feed Whiskers (5 min) [priority: high]
  08:00 - Feed Buddy (7 min) [priority: high]
  09:00 - Walk Buddy (10 min) [priority: medium]
  17:00 - Play with Whiskers (15 min) [priority: low]

=== Pending tasks only ===
  08:00 - Feed Whiskers (5 min) [priority: high]
  09:00 - Walk Buddy (10 min) [priority: medium]
  08:00 - Feed Buddy (7 min) [priority: high]

=== Buddy's tasks only ===
  09:00 - Walk Buddy (10 min) [priority: medium]
  08:00 - Feed Buddy (7 min) [priority: high]

========================================================
Today's Schedule
Daily plan (60 min available):
  - 08:00 - Feed Whiskers (5 min) [priority: high]
  - 08:00 - Feed Buddy (7 min) [priority: high]
  - 09:00 - Walk Buddy (10 min) [priority: medium]
Total scheduled time: 22 min
Conflicts (overlapping times):
  - Feed Whiskers overlaps Feed Buddy
Skipped:
  - 17:00 - Play with Whiskers (15 min) [priority: low] [done]
  ```
**Screenshots**:

![PawPal+ screenshot 1](images/image1.jpg)

![PawPal+ screenshot 2](images/image2.jpg)


