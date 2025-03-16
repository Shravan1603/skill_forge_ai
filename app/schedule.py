import streamlit as st
import datetime
import sqlite3
import pandas as pd
from groq import Groq
from langchain_community.tools import DuckDuckGoSearchRun
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Helper functions
def search_duckduckgo(query, max_results=3):
    """Search DuckDuckGo for relevant resources."""
    try:
        search = DuckDuckGoSearchRun()
        results = search.invoke(query, max_results=max_results)
        return results
    except Exception as e:
        st.error(f"❌ Error searching DuckDuckGo: {str(e)}")
        return []

def fetch_task_details(conn, topic_id):
    """Fetch details of a specific task from the database."""
    query = """
        SELECT title, due_date, status, progress, priority, category 
        FROM topic 
        WHERE topic_id = ? AND status in ('Not Started', 'Pending', 'In Progress')
        ORDER BY priority DESC
    """
    return conn.execute(query, (topic_id,)).fetchall()

def fetch_available_slots(conn, date):
    """Fetch available slots for a specific date from the database."""
    query_slot = """
        SELECT date, time_slot 
        FROM slot 
        WHERE date = ? 
        ORDER BY time_slot DESC
    """
    return conn.execute(query_slot, (date,)).fetchall()

def generate_schedule_prompt(category, task_name, from_date, due_date, search_results, available_slots):
    """Generate the prompt for the LLM."""
    return f"""
    Create a detailed breakdown of the {category} - '{task_name}' with subtopics.
    Assign estimated durations to each subtopic, and create a schedule to complete it between {from_date} and {due_date}.
    Check the available slots - {available_slots} for the day.

    Here are some relevant resources from DuckDuckGo:
    {search_results}

    Format the output as a table with exactly 3 columns:
    1. Subtopic: The name of the subtopic.
    2. Duration: The estimated duration (e.g., 30 minutes, 1 hour).
    3. Suggested Time Slot: A suggested time slot (e.g., 10:00 AM - 10:30 AM).

    Separate columns using the '|' symbol. For example:
    Subtopic | Duration | Suggested Time Slot
    ---------|----------|--------------------
    Introduction | 30 minutes | 16-Mar-2025  10:00 AM - 10:30 AM
    Practice Problems | 1 hour | 16-Mar-2025  10:30 AM - 11:30 AM
    Review | 30 minutes | 17-Mar-2025  11:30 AM - 12:00 PM
    """

def save_schedule_to_db(conn, df, due_date, selected_task_id):
    """Save the generated schedule to the database."""
    try:
        # Check if user is logged in
        if 'user_id' not in st.session_state:
            st.error("❌ User not logged in. Please log in to save the schedule.")
            return

        # Check if DataFrame is empty
        if df.empty:
            st.warning("⚠️ No data to save. The schedule is empty.")
            return

        cursor = conn.cursor()
        for row in df.itertuples(index=False):
            date_str = str(due_date)
            time_slot = row[2]
            subtopic = row[0]
            completed = row[3] if len(row) > 3 else False

            # Insert into the database
            cursor.execute("""
                INSERT INTO schedule (user_id, topic_id, date, time_slot, subtopics, is_completed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (st.session_state['user_id'], selected_task_id, date_str, time_slot, subtopic, completed))

        # Commit the transaction
        conn.commit()
        st.success("📁 Schedule saved to database!")

    except sqlite3.Error as e:
        st.error(f"❗ Error saving schedule to database: {str(e)}")
    except Exception as e:
        st.error(f"❗ An unexpected error occurred: {str(e)}")

def display_saved_schedules(conn):
    """Display saved schedules from the database."""
    st.markdown("### 🗂 Saved Schedules")
    cur = conn.cursor()
    cur.execute("""
        SELECT s.date, s.time_slot, t.title, s.subtopics, s.is_completed 
        FROM schedule s
        JOIN topic t ON s.topic_id = t.topic_id
        WHERE s.user_id = ?
    """, (st.session_state['user_id'],))
    saved_schedules = cur.fetchall()

    if saved_schedules:
        saved_df = pd.DataFrame(saved_schedules, columns=["Date", "Time Slot", "Task", "Subtopics", "Completed"])
        
        # Calculate percentage completed
        total_subtopics = len(saved_df)
        completed_subtopics = saved_df['Completed'].sum()
        completion_percentage = (completed_subtopics / total_subtopics) * 100 if total_subtopics > 0 else 0

        st.write(f"### 📊 Completion Status: {completion_percentage:.2f}%")

        # Display the DataFrame with colourful styling
        st.dataframe(
            saved_df.style
            .set_properties(**{'background-color': '#e8f5e9', 'color': '#2e7d32', 'border': '1px solid #ddd'})
            .apply(lambda x: ['background-color: #f0f4c3' if x.name % 2 == 0 else '' for i in x], axis=1)
        )

        # Add a button to mark subtopics as completed
        subtopic_to_mark = st.selectbox("Mark a subtopic as completed", saved_df['Subtopics'].tolist())
        if st.button("Mark as Completed"):
            cur.execute("""
                UPDATE schedule 
                SET is_completed = TRUE 
                WHERE subtopics = ? AND user_id = ?
            """, (subtopic_to_mark, st.session_state['user_id']))
            conn.commit()
            st.success(f"✅ Subtopic '{subtopic_to_mark}' marked as completed!")
            st.rerun()

    else:
        st.info("ℹ️ No saved schedules yet. Generate one above!")

def generate_schedule(conn):
    st.title("📅 SkillForgeAI- Task Scheduler ")
    col1, col2  = st.columns([1, 1 ])
    
    # Input: Task details
    tasks = conn.execute(
        "SELECT topic_id, title, due_date, category, status, progress, priority FROM topic WHERE status != 'Completed' AND user_id = ? ORDER BY priority DESC",
        (st.session_state['user_id'],)
    ).fetchall()

    task_options = {task[1]: task[0] for task in tasks}  # Ensure the dictionary is correctly populated
    
    if not task_options:
        st.warning("⚠️ No pending tasks found. Please add tasks to the database.")
        return
    
    with col1:  
        selected_task_name = st.selectbox("📝 Select Task", list(task_options.keys()))
        selected_task_id = task_options.get(selected_task_name)
        
        if selected_task_id is None:
            st.error("❌ No task selected or task not found.")
            return
        
        # Fetch task details for the selected task
        task_details = fetch_task_details(conn, selected_task_id)
        if not task_details:
            st.error("❌ No task details found for the selected task.")
            return
        
        category = st.text_input("🏷️ Category", value=task_details[0][5])
    
    with col2:
        # Set default due_date to today if task_details is empty
        due_date = datetime.datetime.now().date() if not task_details else datetime.datetime.strptime(task_details[0][1], "%Y-%m-%d").date()
        from_date = st.date_input("📅 Select From Date", value=datetime.datetime.now().date())
        due_date = st.date_input("📅 Select Due Date", value=due_date)
    
    # Fetch available slots
    available_slots = fetch_available_slots(conn, due_date)
    st.divider()
    # LLM Selection
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1: 
        # st.markdown("### 🧠 Select LLM")
        llm_provider = st.selectbox(
            "🧠 Select LLM Provider",
            ["Groq" ]
        )
    with col2:    
        model_name = st.text_input("Enter Model Name", value="mixtral-8x7b-32768" if llm_provider == "Groq" else "gpt-3.5-turbo")
     
    if st.button("🚀 Generate Schedule") and selected_task_name:
        # Initialize the selected LLM
        if llm_provider == "Groq":
            llm = Groq(api_key=st.secrets["general"]["groq_api_key"])
        
        # elif llm_provider == "Hugging Face":
        #     llm = HuggingFacePipeline.from_model_id(model_id=model_name, task="text-generation")
        # elif llm_provider == "OpenAI":
        #     llm = ChatOpenAI(model=model_name, api_key=os.getenv("OPENAI_API_KEY"))
        # elif llm_provider == "Ollama":
        #     llm = Ollama(model=model_name)
        # elif llm_provider == "Google Gemini":
        #     llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=os.getenv("GOOGLE_API_KEY"))
        else:
            st.error("❌ Invalid LLM provider selected.")
            return

        # Store the LLM in session state
        st.session_state['llm'] = llm

        # Search DuckDuckGo for relevant resources
        search_query = f"{category} {selected_task_name} resources"
        search_results = search_duckduckgo(search_query, max_results=3)

        # Prepare the prompt for the LLM
        prompt = generate_schedule_prompt(category, selected_task_name, from_date, due_date, search_results, available_slots)

        try:
            with st.spinner("⏳ Generating schedule..."):   
                # Use the selected LLM to generate the schedule
                if llm_provider == "Groq":
                    response = llm.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=model_name,
                    )
                    schedule_text = response.choices[0].message.content
                else:
                    response = llm.invoke(prompt)
                    schedule_text = response

                st.success("✅ Schedule generated!")

            # Display the schedule
            st.markdown("### 📌 Your AI-Generated Schedule")

            # Parse the schedule text into a table
            schedule_lines = schedule_text.strip().split('\n')

            # Skip the first two rows (header and separator) and process the rest
            schedule_data = [line.split('|')[1:] for line in schedule_lines[2:] if '|' in line]

            # Parse the schedule text into a table
            schedule_data = [row[:3] for row in schedule_data if len(row) >= 3]

            # Create the DataFrame
            df = pd.DataFrame(schedule_data, columns=["Subtopic", "Duration", "Time Slot"])
            df['Subtopic'] = '🔹 ' + df['Subtopic']

            # Add a column for marking subtopics as completed
            df['Completed'] = False

            # Display the DataFrame with colourful styling
            st.dataframe(
                df.style
                .set_properties(**{'background-color': '#f0f0f0', 'color': '#333333', 'border': '1px solid #ddd'})
                .apply(lambda x: ['background-color: #e8f5e9' if x.name % 2 == 0 else '' for i in x], axis=1)
            )   

            # Store the DataFrame in session state
            st.session_state['df'] = df

            # Save schedule to DB
            save_schedule_to_db(conn, df, due_date, selected_task_id)

        except Exception as e:
            st.error(f"❗ Error generating schedule: {str(e)}")

    with st.expander("✏️ View Schedule", expanded=False):
        # Display saved schedules
        display_saved_schedules(conn)