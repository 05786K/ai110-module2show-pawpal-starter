from datetime import time

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner & Pets")

# Persist the Owner (with its pets and tasks) across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time=60)
owner = st.session_state.owner
scheduler = Scheduler()

owner.name = st.text_input("Owner name", value=owner.name)

# --- Adding a Pet: calls Owner.add_pet() ---
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
if st.button("Add pet"):
    owner.add_pet(Pet(name=pet_name, species=species, breed="", age=0))

if owner.pets:
    st.write("Pets:", ", ".join(p.name for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add tasks to a pet; they feed into the scheduler.")

# --- Scheduling a Task: calls Pet.add_task() ---
if owner.pets:
    pet_index = st.selectbox(
        "Add task to which pet?",
        options=range(len(owner.pets)),
        format_func=lambda i: owner.pets[i].name,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        # Time of day gives tasks a clock position so the scheduler can order
        # them and detect overlapping windows (conflicts).
        task_time = st.time_input("Time of day", value=time(9, 0))

    # Frequency drives recurrence: completing a daily/weekly task spawns the next.
    frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

    if st.button("Add task"):
        try:
            owner.pets[pet_index].add_task(
                Task(
                    description=task_title,
                    duration=int(duration),
                    priority=priority,
                    time=task_time.strftime("%H:%M"),
                    frequency=frequency,
                )
            )
        except ValueError as err:
            # e.g. an exact duplicate task, or invalid input — warn, don't crash.
            st.warning(str(err))

    # --- Current tasks: filter by pet/status, and mark tasks done. ---
    st.markdown("#### Current tasks")
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        # collect_tasks(pet_name=...) scopes the view to one pet.
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with fcol2:
        # filter_tasks(status) narrows by completion status.
        status_filter = st.selectbox("Show status", ["all", "pending", "done"])

    scope = None if pet_filter == "All pets" else pet_filter
    visible = scheduler.filter_tasks(scheduler.collect_tasks(owner, pet_name=scope), status_filter)
    visible_ids = {id(t) for t in visible}

    if not visible:
        st.caption("No tasks match this filter.")
    for p in owner.pets:
        shown = [t for t in p.tasks if id(t) in visible_ids]
        if not shown:
            continue
        st.write(f"**{p.name}**")
        # Snapshot the list so completing a task (which appends a new one) is safe.
        for i, t in enumerate(list(p.tasks)):
            if id(t) not in visible_ids:
                continue
            text_col, btn_col = st.columns([5, 1])
            text_col.text(t.get_details())
            if not t.completed and btn_col.button("Done", key=f"done_{pet_index}_{p.name}_{i}"):
                # Marks complete and, for daily/weekly, queues the next occurrence.
                scheduler.complete_task(p, t)
                st.rerun()
else:
    st.caption("Add a pet first to attach tasks.")

st.divider()

st.subheader("Build Schedule")

available_time = st.number_input(
    "Available time today (minutes)", min_value=0, max_value=1440, value=owner.available_time
)

if st.button("Generate schedule"):
    owner.set_available_time(int(available_time))
    # Retrieve tasks across the owner's pets and explain the plan.
    tasks = scheduler.collect_tasks(owner)
    if not tasks:
        st.warning("No tasks yet. Add some above.")
    else:
        st.text(scheduler.explain_plan(tasks, owner.available_time))
