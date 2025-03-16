from datetime import datetime, timedelta
import streamlit as st
import sqlite3
import pandas as pd

def validate_time_slot(slot):
    """Validate the time slot format (e.g., 10:00 AM - 11:00 AM)."""
    try:
        start_time, end_time = slot.split(" - ")
        datetime.strptime(start_time.strip(), "%I:%M %p")
        datetime.strptime(end_time.strip(), "%I:%M %p")
        return True
    except ValueError:
        return False

def is_overlap(slot1, slot2):
    """Check if two time slots overlap."""
    start1, end1 = [datetime.strptime(t.strip(), "%I:%M %p") for t in slot1.split(" - ")]
    start2, end2 = [datetime.strptime(t.strip(), "%I:%M %p") for t in slot2.split(" - ")]
    return not (end1 <= start2 or end2 <= start1)

def get_time_slot(conn):
    st.subheader("📋 Task and Slot Management")

    # Fetch tasks from the database
    tasks = conn.execute("SELECT * FROM topic WHERE user_id = ?", (st.session_state['user_id'],)).fetchall()
    task_options = {task[0]: task[2] for task in tasks}  # {topic_id: title}

    col1, col2, col3 = st.columns(3)
    # Select task and date range
    with col1:
        selected_task_id = st.selectbox("📋 Select Task", options=list(task_options.keys()), format_func=lambda x: task_options[x])
    with col2:
        from_date = st.date_input("📅 From Date")
    with col3:    
        due_date = st.date_input("📅 Due Date", min_value=from_date)

    if from_date > due_date:
        st.error("❌ Due Date must be after From Date.")
        return

    # Display slots for the selected task and date range
    st.subheader("📅 Time Slots")
    slots = conn.execute(
        "SELECT slot_id, date, time_slot FROM slot WHERE topic_id = ? AND date BETWEEN ? AND ?",
        (selected_task_id, from_date, due_date)
    ).fetchall()

    # Add New Slots
    with st.expander("➕ Add New Slots", expanded=False):
        slot_date = st.date_input("📅 Slot Date", min_value=from_date, max_value=due_date)
        col1, col2, col3 = st.columns(3)
        with col1:
            start_time = st.time_input("⏰ Start Time", value=datetime.strptime("09:00 AM", "%I:%M %p").time())
        with col2:
            end_time = st.time_input("⏰ End Time", value=datetime.strptime("05:00 PM", "%I:%M %p").time())
        with col3:
            interval = st.number_input("⏱️ Interval (minutes)", min_value=15, max_value=120, value=30)

        recurrence = st.selectbox("🔁 Recurrence", ["None", "Daily", "Weekly", "Monthly"])

        if st.button("🔄 Generate Slots"):
            current_date = slot_date
            while current_date <= due_date:
                current_time = datetime.combine(current_date, start_time)
                end_time_dt = datetime.combine(current_date, end_time)
                while current_time < end_time_dt:
                    slot = f"{current_time.strftime('%I:%M %p')} - {(current_time + timedelta(minutes=interval)).strftime('%I:%M %p')}"
                    
                    # Check for overlapping slots
                    existing_slots = [s[0] for s in conn.execute(
                        "SELECT time_slot FROM slot WHERE topic_id = ? AND date = ?",
                        (selected_task_id, current_date)
                    ).fetchall()]
                    if any(is_overlap(slot, existing_slot) for existing_slot in existing_slots):
                        st.warning(f"⚠️ Overlapping slot detected: {slot}")
                    else:
                        conn.execute(
                            "INSERT INTO slot (user_id, topic_id, date, time_slot) VALUES (?, ?, ?, ?)",
                            (st.session_state['user_id'], selected_task_id, current_date, slot)
                        )
                        conn.commit()
                        st.success(f"✅ Slot saved: {slot}")
                    current_time += timedelta(minutes=interval)

                # Update current_date based on recurrence
                if recurrence == "Daily":
                    current_date += timedelta(days=1)
                elif recurrence == "Weekly":
                    current_date += timedelta(weeks=1)
                elif recurrence == "Monthly":
                    current_date = current_date.replace(month=current_date.month + 1)
                else:
                    break  # No recurrence

            st.rerun()

    if slots:
        slots_df = pd.DataFrame(slots, columns=["ID", "Date", "Time Slot"])
        slots_df["Date"] = pd.to_datetime(slots_df["Date"]).dt.date

        # Edit Slots
        with st.expander("✏️ Edit Slots", expanded=False):
            edited_df = st.data_editor(
                slots_df,
                column_config={
                    "ID": None,  # Hide the ID column
                    "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                    "Time Slot": st.column_config.TextColumn("Time Slot")
                },
                key="slots_editor",
                num_rows="dynamic",
                use_container_width=True
            )

            if st.button("💾 Save Changes"):
                for index, row in edited_df.iterrows():
                    conn.execute(
                        "UPDATE slot SET date = ?, time_slot = ? WHERE slot_id = ?",
                        (row["Date"].strftime("%Y-%m-%d"), row["Time Slot"], row["ID"])
                    )
                conn.commit()
                st.success("✅ Slots updated successfully!")
                st.rerun()

        # Delete Slots
        with st.expander("🗑️ Delete Slots", expanded=False):
            slots_to_delete = st.multiselect(
                "Select slots to delete",
                options=edited_df[["ID", "Date", "Time Slot"]].to_dict("records"),
                format_func=lambda x: f"{x['Date']} - {x['Time Slot']}"
            )
            if st.button("❌ Delete Selected Slots"):
                for slot in slots_to_delete:
                    conn.execute("DELETE FROM slot WHERE slot_id = ?", (slot["ID"],))
                conn.commit()
                st.success("✅ Selected slots deleted successfully!")
                st.rerun()
    else:
        st.info("ℹ️ No slots available for the selected task and date range.")

    # View Slots by Date
    with st.expander("📅 View Slots by Date", expanded=False):
        view_date = st.date_input("Select Date to View Slots", min_value=from_date, max_value=due_date)
        slots_on_date = conn.execute(
            "SELECT slot_id, time_slot FROM slot WHERE topic_id = ? AND date = ?",
            (selected_task_id, view_date)
        ).fetchall()

        if slots_on_date:
            st.write(f"Slots on {view_date}:")
            for slot in slots_on_date:
                st.write(f"- {slot[1]}")
        else:
            st.info(f"ℹ️ No slots available on {view_date}.")

    # Conflict Checker
    with st.expander("🔍 Check Slot Availability", expanded=False):
        check_slot = st.text_input("Enter Slot to Check (e.g., 10:00 AM - 11:00 AM)")
        if st.button("🔎 Check"):
            if not validate_time_slot(check_slot):
                st.error("❌ Invalid time slot format. Please use the format '10:00 AM - 11:00 AM'.")
            else:
                existing_slots = [s[0] for s in conn.execute(
                    "SELECT time_slot FROM slot WHERE topic_id = ? AND date BETWEEN ? AND ?",
                    (selected_task_id, from_date, due_date)
                ).fetchall()]
                if any(is_overlap(check_slot, existing_slot) for existing_slot in existing_slots):
                    st.error("⚠️ Slot conflict detected!")
                else:
                    st.success("✅ Slot is available!")