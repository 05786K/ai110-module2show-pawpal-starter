import os
from datetime import time

import streamlit as st
from formatting import priority_badge, status_icon, type_icon
from pawpal_system import Owner, Pet, Task, Scheduler


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app. This is a pet care planning assistant that helps a pet owner plan care tasks for their pet(s) based on constraints like time, priority, and preferences.
"""
)

# with st.expander("Scenario", expanded=True):
#     st.markdown(
#         """
# **PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
# for their pet(s) based on constraints like time, priority, and preferences.
# """
#     )


# with st.expander("What you need to build", expanded=True):
#     st.markdown(
#         """
# At minimum, your system should:
# - Represent pet care tasks (what needs to happen, how long it takes, priority)
# - Represent the pet and the owner (basic info and preferences)
# - Build a plan/schedule for a day that chooses and orders tasks based on constraints
# - Explain the plan (why each task was chosen and when it happens)
# """
#     )

# st.divider()

st.subheader("Owner & Pets")

# Data persists to this file between runs (see Owner.save_to_json/load_from_json).
DATA_FILE = "data.json"

# Load saved state on first load; fall back to a fresh Owner if there's no file
# yet (first run) or it can't be parsed.
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
    except (FileNotFoundError, ValueError, KeyError):
        st.session_state.owner = Owner(name="Jordan", available_time=60)
owner = st.session_state.owner
scheduler = Scheduler()


# --- Reset: wipe all saved data and start from a clean default owner. ---
# Tucked in the sidebar behind a confirm checkbox so it can't be hit by
# accident — it's destructive and irreversible.
with st.sidebar:
    st.markdown("### ⚠️ Reset all data")
    st.caption("Deletes every pet, task, and setting. This cannot be undone.")
    confirm_reset = st.checkbox("I understand this erases everything")
    if st.button("Reset all data", disabled=not confirm_reset):
        # Remove the on-disk save so a reload can't resurrect the old state,
        # then drop the in-memory owner. On rerun, the load block above finds
        # no file and rebuilds the seeded default owner.
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.pop("owner", None)
        st.rerun()


def persist() -> None:
    """Auto-save the whole owner graph so changes survive a refresh/restart."""
    owner.save_to_json(DATA_FILE)


# Persist the name only when it actually changes (avoids writing every rerun).
new_name = st.text_input("Owner name", value=owner.name)
if new_name != owner.name:
    owner.name = new_name
    persist()

# --- Adding a Pet: calls Owner.add_pet() ---
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
if st.button("Add pet"):
    try:
        owner.add_pet(Pet(name=pet_name, species=species, breed="", age=0))
        persist()
    except ValueError as err:
        # e.g. a pet with this name already exists — warn, don't crash.
        st.warning(str(err))

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

    # Suggest the earliest conflict-free slot for a task of this duration,
    # checked against every task the owner already has scheduled.
    if st.button("🔍 Suggest a free time"):
        slot = scheduler.find_free_slot(scheduler.collect_tasks(owner), int(duration))
        if slot:
            st.info(
                f"Earliest free {int(duration)}-min slot: **{slot}** — no overlap "
                f"with existing tasks. Set **Time of day** to {slot}, then add the task."
            )
        else:
            st.warning(
                "No free slot fits that duration in the day (06:00–22:00). "
                "Try a shorter task or completing something first."
            )

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
            persist()
        except ValueError as err:
            # e.g. an exact duplicate task, or invalid input — warn, don't crash.
            st.warning(str(err))

    # --- Current tasks: filter by pet/status, sort, and mark tasks done. ---
    st.markdown("#### Current tasks")
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        # collect_tasks(pet_name=...) scopes the view to one pet.
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with fcol2:
        # filter_tasks(status) narrows by completion status.
        status_filter = st.selectbox("Show status", ["all", "pending", "done"])
    with fcol3:
        # Surface both Scheduler orderings so the owner can reorder the view.
        sort_choice = st.selectbox("Sort by", ["Time of day", "Priority"])

    scope = None if pet_filter == "All pets" else pet_filter
    visible = scheduler.filter_tasks(scheduler.collect_tasks(owner, pet_name=scope), status_filter)
    visible_ids = {id(t) for t in visible}

    # Heads-up on overlaps before the owner even builds a plan, computed across
    # the pending tasks in view so conflicts are caught early.
    conflicts = scheduler.find_conflicts(visible)
    if conflicts:
        st.warning(
            f"⚠️ {len(conflicts)} time conflict(s) among these tasks — "
            "see details when you build the schedule below."
        )

    if not visible:
        st.caption("No tasks match this filter.")
    for p in owner.pets:
        shown = [t for t in p.tasks if id(t) in visible_ids]
        if not shown:
            continue
        # Apply the chosen Scheduler ordering to this pet's visible tasks.
        if sort_choice == "Time of day":
            shown = scheduler.sort_by_time(shown)
        else:
            shown = scheduler.sort_tasks(shown)
        st.write(f"**{p.name}**")
        for t in shown:
            text_col, done_col, del_col = st.columns([5, 1, 1])
            # Status + task-type icons make each row scannable at a glance.
            text_col.write(f"{status_icon(t.completed)} {type_icon(t.description)} {t.get_details()}")
            # Key on id(t): stable across reruns (session_state keeps the same
            # objects) and unique even after sorting reorders the rows.
            if not t.completed and done_col.button("Done", key=f"done_{p.name}_{id(t)}"):
                # Marks complete and, for daily/weekly, queues the next occurrence.
                scheduler.complete_task(p, t)
                persist()
                st.rerun()
            # Delete removes the task outright — handy for resolving a conflict
            # by dropping the task the owner doesn't want.
            if del_col.button("🗑️", key=f"del_{p.name}_{id(t)}", help="Delete this task"):
                p.remove_task(t)
                persist()
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
    persist()  # remember the updated available time
    # Retrieve tasks across the owner's pets and build the plan.
    tasks = scheduler.collect_tasks(owner)
    if not tasks:
        st.warning("No tasks yet. Add some above.")
    else:
        plan = scheduler.generate_plan(tasks, owner.available_time)
        # Map each task back to its pet so the table can name the pet.
        pet_of = {id(t): p.name for p in owner.pets for t in p.tasks}

        if not plan:
            st.warning(
                "None of your pending tasks fit in the available time. "
                "Add more minutes above, or shorten/complete some tasks."
            )
        else:
            # Tasks are *selected* by priority, but an owner reads the day in
            # clock order — so display the winners sorted by time of day.
            ordered = scheduler.sort_by_time(plan)
            st.table(
                [
                    {
                        "Time": t.time or "Anytime",
                        "Pet": pet_of.get(id(t), "—"),
                        "Task": f"{type_icon(t.description)} {t.description}",
                        "Duration (min)": t.duration,
                        "Priority": priority_badge(t.priority),
                    }
                    for t in ordered
                ]
            )
            used = sum(t.duration for t in plan)
            st.success(
                f"✅ {len(plan)} task(s) scheduled — {used} of "
                f"{owner.available_time} min used ({owner.available_time - used} min free)."
            )

        # Warn about overlapping time windows without changing the plan. Each
        # warning is its own banner so the owner sees exactly which pair clashes
        # and what to do about it.
        conflicts = scheduler.find_conflicts(plan)
        if conflicts:
            st.markdown("#### ⚠️ Schedule conflicts")
            for a, b in conflicts:
                # Suggest where the second task could move: the earliest free
                # slot checked against every other planned task (a included).
                others = [t for t in plan if t is not b]
                alt = scheduler.find_free_slot(others, b.duration)
                fix = (
                    f" Try moving **{b.description}** to **{alt}**."
                    if alt
                    else " No free slot is available — consider shortening one task."
                )
                st.warning(
                    f"**{a.description}** ({a.time}, {a.duration} min) overlaps "
                    f"**{b.description}** ({b.time}, {b.duration} min).\n\n"
                    f"These run at the same time.{fix}"
                )

        # List anything skipped and why, so the reasoning is transparent.
        planned_ids = {id(t) for t in plan}
        skipped = [t for t in tasks if id(t) not in planned_ids]
        if skipped:
            with st.expander(f"Skipped tasks ({len(skipped)})"):
                for t in skipped:
                    reason = "already done" if t.completed else "not enough time left"
                    st.write(f"- **{pet_of.get(id(t), '—')}** — {t.get_details()}  _({reason})_")

        # Keep the original text explanation available for a full, copyable view.
        with st.expander("Full text explanation"):
            st.text(scheduler.explain_plan(tasks, owner.available_time))
