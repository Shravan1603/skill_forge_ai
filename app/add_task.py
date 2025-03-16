import streamlit as st
import pandas as pd
from datetime import datetime
import time
from util import success_msg, delete_msg
from db import init_db

# Custom CSS for colourful visuals
st.markdown("""
    <style>
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 10px 20px;
    }
    .stSuccess {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .stError {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    .stInfo {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #bee5eb;
    }
    .priority-high {
        color: red;
        font-weight: bold;
    }
    .priority-medium {
        color: orange;
        font-weight: bold;
    }
    .priority-low {
        color: green;
        font-weight: bold;
    }
    .status-pending {
        color: #ffc107;
        font-weight: bold;
    }
    .status-in-progress {
        color: #17a2b8;
        font-weight: bold;
    }
    .status-completed {
        color: #28a745;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def add_task(conn, user_id):
    st.subheader("➕ Add Task")
    
    # Input fields for adding a new task
    topic_col, from_col, due_col = st.columns([2, 1, 1])
    with topic_col:
        title = st.text_input("Enter Title*", placeholder="e.g., Learn Python")
    with from_col:
        from_date = st.date_input("From Date*")
    with due_col:
        due_date = st.date_input("Due Date*")
   
    cat_col, rec_col, pri_col = st.columns([1, 1, 1])
    with cat_col:    
        category = st.selectbox(
            "Category*", 
            ["Programming", "Mathematics", "Science",  "Engineering", "Language Learning", "Personal Development", 
            "Technology"]
        )
    with rec_col:
        recurrence = st.selectbox("Recurrence", ["None", "Daily", "Weekly", "Monthly"])
    with pri_col:
        priority = st.selectbox("Priority*", ["High", "Medium", "Low"])

    # Additional fields
    description = st.text_area("Description", placeholder="Add a detailed description of the task...")
    tags = st.text_input("Tags", placeholder="e.g., Python, Math, Study")

    # Save Task button
    if st.button("💾 Save Task"):
        if not title or not from_date or not due_date or not priority:
            st.error("Please fill in all required fields (marked with *).")
        elif from_date > due_date:
            st.error("❌ 'From Date' cannot be later than 'Due Date'.")
        else:
            try:
                conn.execute(
                    """
                    INSERT INTO topic (user_id, title, description, from_date, due_date, status, priority, progress, category, recurrence, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, title, description, from_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d"), "Not Started", priority, 0, category, recurrence, tags)
                )
                conn.commit()
                st.success("🎉 Task saved successfully!")
                st.rerun()  # Refresh the page to reflect changes
            except Exception as e:
                st.error(f"❌ Error saving task: {str(e)}")
    st.divider()  
    
    # Use an accordion to show/hide tasks
    with st.expander("📋 Tasks", expanded=False):
        display_tasks(conn, user_id)

def display_tasks(conn, user_id):
    try:
        # Fetch tasks for the logged-in user
        tasks = conn.execute("SELECT * FROM topic WHERE user_id = ?", (user_id,)).fetchall()
        
        if tasks:
            # Define the column names based on the database schema
            columns = [
                "topic_id", "user_id", "title", "description", "from_date", "due_date", 
                "status", "priority", "progress", "category", "recurrence", "tags",
                "created_at", "updated_at"  # Include all columns from the database
            ]
            
            # Create a DataFrame with the fetched tasks
            df = pd.DataFrame(tasks, columns=columns)
            df["from_date"] = pd.to_datetime(df["from_date"]).dt.date
            df["due_date"] = pd.to_datetime(df["due_date"]).dt.date
            
            # Display the table with editable options
            edited_df = st.data_editor(
                df,
                column_config={
                    "topic_id": None,  # Hide the ID column
                    "user_id": None,  # Hide the UserID column
                    "from_date": st.column_config.DateColumn("From Date", format="YYYY-MM-DD"),
                    "due_date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
                    "priority": st.column_config.SelectboxColumn("Priority", options=["None","High", "Medium", "Low"]),
                    "status": st.column_config.SelectboxColumn("Status", options=["Not Started", "Pending", "In Progress", "Completed"]),
                    "progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100),
                    "recurrence": st.column_config.SelectboxColumn("Recurrence", options=["None", "Daily", "Weekly", "Monthly"]),
                    "category": st.column_config.SelectboxColumn(
                        "Category", 
                        options=[
                            "None", "Programming", "Mathematics", "Science", "Literature", "History", 
                            "Art", "Music", "Finance", "Health & Fitness", "Business", 
                            "Design", "Engineering", "Language Learning", "Personal Development", 
                            "Travel", "Cooking", "Sports", "Technology", "Gaming", "Photography"
                        ]
                    )
                },
                key="tasks_table"
            )
            
            # Save changes to the database
            if st.button("💾 Save Changes"):
                try:
                    for index, row in edited_df.iterrows():
                        conn.execute(
                            """
                            UPDATE topic 
                            SET title = ?, description = ?, from_date = ?, due_date = ?, status = ?, priority = ?, progress = ?, category = ?, recurrence = ?, tags = ?
                            WHERE topic_id = ? AND user_id = ?
                            """,
                            (
                                row["title"], row["description"], row["from_date"].strftime("%Y-%m-%d"), 
                                row["due_date"].strftime("%Y-%m-%d"), row["status"], row["priority"], 
                                row["progress"], row["category"], row["recurrence"], row["tags"], 
                                row["topic_id"], user_id
                            )
                        )
                    conn.commit()
                    st.success("🎉 Tasks updated successfully!")
                except Exception as e:
                    st.error(f"❌ Error updating tasks: {str(e)}")
            st.divider()  
            
            # Delete Task option
            col1, col2 = st.columns(2)
            with col1:
                task_to_delete = st.selectbox("Select a task to delete", df["title"])
            with col2:    
                if st.button("🗑️ Delete Task"):
                    try:
                        conn.execute("DELETE FROM topic WHERE title = ? AND user_id = ?", (task_to_delete, user_id))
                        conn.commit()
                        st.success(f"✅ Task '{task_to_delete}' deleted successfully!")
                        st.rerun()  # Refresh the page to reflect changes
                    except Exception as e:
                        st.error(f"❌ Error deleting task: {str(e)}")
        else:
            st.info("ℹ️ No tasks found. Add a task to get started!")
    except Exception as e:
        st.error(f"❌ Error fetching tasks: {str(e)}")