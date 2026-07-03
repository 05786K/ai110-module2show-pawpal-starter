# AI Interactions Log

> **Stretch features only.** 
The following features were added: 

- **`Scheduler.find_free_slot()`** — sweeps the day and returns the earliest conflict-free `HH:MM` start time that fits a task of a given duration, powering the "suggest a free time" button and actionable conflict fixes.
- **`Pet.remove_task()`** — deletes a specific task by identity so the owner can resolve a conflict by dropping the task they don't want.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked it to add an algorithmic capability beyond the basics (a "next available slot" feature), and later to add a delete function on tasks so a conflict can be resolved by removing an unwanted task.

**What did the agent do?**

It added `Scheduler.find_free_slot()` and `Pet.remove_task()` in `pawpal_system.py`, wired them into the Streamlit UI (a "suggest a free time" button, conflict-fix suggestions, and a delete button per task), wrote matching tests, and ran the suite to confirm 100% coverage.

**What did you have to verify or fix manually?**

I reviewed the logic and confirmed the tests passed. I also went ahead and tested the application UI to ensure the new features were behaving correctly. 

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| |                             Option A       |                   Option B                    |
|-|----------|----------|
| **Model / tool used** |       Claude         |                   ChatGPT                     |
| **Prompt** |  Implement `complete_task()` so 
                that finishing a daily/weekly 
                task marks it done and automatically
                schedules the next occurrence.
                Handle 'once' tasks and calendar rollovers. |     Same Prompt                        |
| **Response summary** |

                Added a `next_due_date()` helper using `timedelta(days=1)` / `timedelta(weeks=1)`, and a `complete_task()` that marks the task done and spawns a fresh copy via `dataclasses.replace`, anchoring the next date on the task's**own`due_date`**. | chatGPT: computed the next date inline as `date.today() + timedelta(...)` directly inside `complete_task()`, with no separate helper.| 
|**What was useful**   | Accuracy across month/year rollover | It was short and simple |
| **Problems noticed** | More code and complexity | Difficult to reuse and maintainability |
| **Decision** | Choose Claude | Denied gpt response |

**Which approach did you use in your final implementation and why?**
    I used Option A in my final implementation. The deciding factor was correctness on repeated completions. By calculating the next occurrence from the task's existing due_date, recurring tasks stay on a consistent schedule even if they are completed early or late. It also separates the date calculation into a helper, making the code easier to reuse, test, and extend with additional recurrence types in the future. 
<!-- Your conclusion -->
