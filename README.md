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
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

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

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
