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
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
