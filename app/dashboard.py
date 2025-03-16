import streamlit as st
import pandas as pd
import plotly.express as px

def show_dashboard(conn, user_id):
    """
    Display the user's dashboard with task summaries, visualizations, and progress tracking.
    """
    st.title("📊 Dashboard")
    st.subheader("Your Tasks for Today")

    try:
        # Fetch tasks for the logged-in user
        tasks = conn.execute(
            """
            SELECT topic_id, title, status, progress, priority, category 
            FROM topic 
            WHERE user_id = ? AND status != 'Completed'
            ORDER BY priority DESC
            """,
            (user_id,)
        ).fetchall()

        if tasks:
            # Summary Card
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task[3] == 100)  # Progress = 100
            pending_tasks = total_tasks - completed_tasks

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tasks", total_tasks)
            with col2:
                st.metric("Completed Tasks", completed_tasks)
            with col3:
                st.metric("Pending Tasks", pending_tasks)

            # Task List in Tabular Format
            st.write("### Task List")
            task_df = pd.DataFrame(tasks, columns=["ID", "Title", "Status", "Progress", "Priority", "Category"])

            # Add a color-coded priority column
            def priority_color(priority):
                if priority == "High":
                    return "🔴 High"
                elif priority == "Medium":
                    return "🟠 Medium"
                elif priority == "Low":
                    return "🟢 Low"
                else:
                    return priority

            task_df["Priority"] = task_df["Priority"].apply(priority_color)

            # Display the table
            st.dataframe(task_df, use_container_width=True)

            # Visualizations
            st.write("### Task Distribution")
            pri_col1, cat_col2 = st.columns(2)
            with pri_col1:
                priority_counts = task_df.groupby("Priority").size().reset_index(name="Count")
                fig1 = px.pie(priority_counts, values="Count", names="Priority", title="Tasks by Priority")
                st.plotly_chart(fig1)

            with cat_col2:
                category_counts = task_df.groupby("Category").size().reset_index(name="Count")
                fig2 = px.bar(category_counts, x="Category", y="Count", title="Tasks by Category", color="Category")
                st.plotly_chart(fig2)

            # # Progress Over Time Visualization
            # st.write("### Progress Over Time")
            # try:
            #     progress_data = conn.execute(
            #         """
            #         SELECT date, AVG(progress) as avg_progress
            #         FROM time_tracking
            #         WHERE user_id = ?
            #         GROUP BY date
            #         ORDER BY date
            #         """,
            #         (user_id,)
            #     ).fetchall()

            #     if progress_data:
            #         progress_df = pd.DataFrame(progress_data, columns=["Date", "Average Progress"])
            #         fig3 = px.line(progress_df, x="Date", y="Average Progress", title="Average Progress Over Time")
            #         st.plotly_chart(fig3)
            #     else:
            #         st.info("No progress data available.")
            # except Exception as e:
            #     st.error(f"Error fetching progress data: {str(e)}")

        else:
            st.info("🎉 No tasks for today. Add a task to get started!")

    except Exception as e:
        st.error(f"Error fetching tasks: {str(e)}")
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div class="footer">
            © 2025 SkillForgeAI. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )
