# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    My initial UML design consisted of four main classes which are owner, pet, task and scheduler. An Owner owns one or more Pets, a Pet has multiple Tasks, and the Scheduler uses those tasks to create a Schedule.

- What classes did you include, and what responsibilities did you assign to each?
    I brainstormed the following classes:
        1. Owner
            Attributes: name, availableTime, preferences and pets
            Methods: setAvailableTime(), updatePreferences(), addPet()
        2. Pet
            Attributes: name, species, breed, age
            Methods: updateInfo()
        3. Task
            Attributes: name, duration, priority, time, frequency, completed
            Methods: markComplete(), updateTask(), getDetails()
        4. Scheduler
            Methods: sortTasks(), generatePlan(), explainPlan()
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

    Yes. My initial design identified the main classes, but it didn't show how they worked together. Using the AI copilot, I added the connections by giving Pet a tasks list with an add_task() method, adding Owner.all_tasks(), and creating Scheduler.collect_tasks() so tasks could flow from the owner and pet into the scheduler.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

    My scheduler weighs several constraints:
    1. Available time: generate_plan() greedily packs tasks and stops adding one once it would exceed the owner's available minutes for the day.
    2. Priority: sort_tasks() orders tasks high -> medium -> low so the most
       important care wins the limited time, with shorter duration breaking ties.
    3. Completion status: completed tasks are skipped so the plan only shows what
       still needs doing.
    4. Time of day: sort_by_time() presents the chosen plan in clock order, and
       find_conflicts() flags tasks whose time windows overlap.
 
- How did you decide which constraints mattered most?

    I treated available time as the hard constraint because a plan that doesn't fit the owner's day is useless. Next priority goes to when everything can't fit, the scheduler should keep the most important tasks, so priority drives selection and shorter duration only breaks ties. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

    My scheduler uses a greedy algorithm that sorts tasks by priority and then by shortest duration. It adds tasks one at a time as long as they fit within the remaining time. This approach is simple and efficient, but it isn't always optimal because it can leave unused time when a skipped task prevents smaller tasks from being considered.

- Why is that tradeoff reasonable for this scenario?

    For a single owner planning one day with only a few tasks, this limitation is usually small. The main goal is to create a schedule that's easy to understand. Using a greedy approach prioritizes the most important tasks first until there's no time left, making the schedule simple to explain through explain_plan().

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    I used Claude in all parts after I had the design brainstormed. 
- What kinds of prompts or questions were most helpful?
    I noticed that when I explicitly referenced a file name, the answers to my prompts were more productive. Also, the more specific and clear the prompts were, the more helpful answers I would get. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    Claude suggested I persist the app's data to a JSON file instead of relying on Streamlit's in-memory session state, so a pet owner's pets and tasks would survive a page refresh. I didn't accept it as-is: for this project's scope — a single-user demo where a session's data doesn't need to outlive the session — in-memory state kept the code simpler and avoided file I/O and edge cases (stale files, concurrent writes). I noted that if PawPal+ ever needed real users returning across sessions, file or database persistence would be the right next step. 
    
- How did you evaluate or verify what the AI suggested?
    I didn't accept suggestions blindly. I first made sure I understood why each one worked, then verified it in three ways: by writing and running a pytest suite (59 tests with 100% coverage), testing real workflows in the Streamlit app, and checking that each suggestion fit the project's scope. If a test failed or the output looked wrong, I traced the issue and fixed it instead of assuming the AI was correct.
---

## 4. Testing and Verification

**a. What you tested**

- **What behaviors did you test?** 
    I tested the core scheduling logic: priority/time sorting, filtering by status and pet, greedy plan generation within available time, plan explanation, time-conflict detection, and daily/weekly recurrence. I also tested input validation (bad durations/times, negative available time) and duplicate-task rejection — 59 tests at 100% coverage.
- **Why were these tests important?** 
    These behaviors are the "brain" of the app, a bug here produces a wrong daily plan without crashing, so it would go unnoticed. Testing edge cases (overlaps, invalid input, recurrence rollover) proves the scheduler is correct and fails loudly on bad data instead of silently misbehaving.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    Since all 59 tests passed with 100% coverage, I'm very confident the scheduler works correctly. I also verified it by manually testing the app and confirming that the generated plans matched my expectations.
- What edge cases would you test next if you had more time?
    Tasks that cross midnight, conflicts involving three or more overlapping tasks, and ties between tasks with the same priority and duration.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    I think all parts went smooth. I had fun working on the scheduling logic.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    I would definitely add data persistence so pets and tasks aren't lost after a page refresh, make conflict detection suggest available time slots, and add support for editing existing pets and tasks in the UI.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    I think designing the system first made AI much more useful. A clear class structure allowed me to write specific prompts and evaluate suggestions instead of accepting them blindly. 
