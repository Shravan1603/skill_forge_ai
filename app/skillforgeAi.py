import streamlit as st
import sqlite3
import hashlib  # For password hashing
import secrets  # For generating salt
from dashboard import show_dashboard
from add_task import add_task
from schedule import generate_schedule
from slots import get_time_slot
from model import llm_model
 
import db

# Initialize database connection
conn = db.init_db()
# Initialize the model and memory
if 'llm' not in st.session_state or 'memory' not in st.session_state:
    try:
        st.session_state['llm'], st.session_state['memory'] = llm_model()
    except Exception as e:
        st.error(f"Failed to initialize model: {str(e)}")
        st.stop()


# Password Hashing with hashlib
def hash_password(password):
    salt = secrets.token_hex(16)  # Generate a random salt
    salted_password = salt + password
    hashed_password = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
    return f"{salt}:{hashed_password}"

def check_password(hashed_password, user_password):
    salt, stored_hash = hashed_password.split(':')
    salted_password = salt + user_password
    computed_hash = hashlib.sha256(salted_password.encode('utf-8')).hexdigest()
    return computed_hash == stored_hash

# User Authentication
def register_user(username, password):
    try:
        hashed_password = hash_password(password)
        c = conn.cursor()
        c.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose a different username.")
        return False
    except Exception as e:
        st.error(f"Error registering user: {str(e)}")
        return False

def authenticate_user(username, password):
    try:
        c = conn.cursor()
        c.execute("SELECT user_id, password FROM user WHERE username = ?", (username,))
        user = c.fetchone()
        if user and check_password(user[1], password):
            return user[0]
        return None
    except Exception as e:
        st.error(f"Error authenticating user: {str(e)}")
        return None

# Session State Management
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'  # Default to landing page

# Custom CSS for styling
st.markdown(
    """
    <style>
    .title {
        font-size: 48px;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 20px;
    }
    .description {
        font-size: 20px;
        color: #333333;
        text-align: center;
        margin-bottom: 40px;
    }
    .button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 10px;
        text-align: center;
        display: block;
        margin: 0 auto;
        width: 200px;
    }
    .button:hover {
        background-color: #45a049;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    .footer {
        text-align: center;
        color: #777777;
        font-size: 14px;
        margin-top: 40px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Render the appropriate page based on session state
if st.session_state['page'] == 'landing':
    # Landing Page Content
    st.markdown('<div class="title">SkillForgeAI</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="description">
            <strong>SkillForgeAI</strong> is your AI-powered companion for mastering new skills and achieving your goals. 
            Whether you're learning to code, improving communication, or mastering data science, SkillForgeAI provides 
            personalized insights, task management, and progress tracking to help you succeed.
            <br><br>
            With <strong>SkillForgeAI</strong>, you can:
            <ul>
                <li>📊 <strong>Dashboard</strong>: Track your progress, view upcoming tasks, and get AI-generated insights to stay on top of your learning journey.</li>
                <li>🎯 <strong>New Learning Skills</strong>: Add new skills you want to learn, and let SkillForgeAI break them down into manageable subtasks.</li>
                <li>⏰ <strong>Time Slots</strong>: Define your available time slots, and SkillForgeAI will automatically generate a personalized schedule for you.</li>
                <li>🤖 <strong>AI-Powered Automation</strong>: SkillForgeAI intelligently generates subtasks and schedules based on your time slots, ensuring you make the most of your time.</li>
            </ul>
            Start your skill-building journey today and let <strong>SkillForgeAI</strong> guide you every step of the way!
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Call-to-Action Button
    if st.button("Get Started", key="get_started", help="Click to start your skill-building journey"):
        st.session_state['page'] = 'login'  # Redirect to the login page
        st.rerun()  # Force the app to rerun and update the page

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

elif st.session_state['page'] == 'login':
    # Login Page Content
    st.markdown('<div class="title">Login to SkillForgeAI</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="description">
            Welcome back! Please log in to continue your skill-building journey.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Login Form
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            user_id = authenticate_user(username, password)
            if user_id:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['user_id'] = user_id
                st.session_state['page'] = 'dashboard'  # Redirect to the dashboard
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

    # Registration Form in an Expander
    with st.expander("Don't have an account? Register here"):
        with st.form("register_form"):
            st.subheader("Register")
            new_user = st.text_input("Username", key="register_username")
            new_password = st.text_input("Password", type="password", key="register_password")
            register_button = st.form_submit_button("Register")

            if register_button:
                if register_user(new_user, new_password):
                    st.success("Account created successfully! Please login.")
                    st.session_state['page'] = 'login'  # Redirect to the login page
                    st.rerun()

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

elif st.session_state['page'] == 'dashboard':
    st.sidebar.header("Dashboard")
     
    panel_option = st.sidebar.radio("Select Option", ["Dashboard", "Task", "Time Slots", "Generate Schedule"])
    # Today's Tasks
    if panel_option == "Dashboard":
        show_dashboard(conn, st.session_state['user_id'])

    # Add Task
    if panel_option == "Task":
        add_task(conn, st.session_state['user_id'])

    # Time Slots
    if panel_option == "Time Slots":
        get_time_slot(conn)

    # Schedule Task
    if panel_option == "Generate Schedule":
        generate_schedule(conn)

       
    # Logout Button
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['user_id'] = None
        st.session_state['points'] = 0
        st.session_state['page'] = 'landing'  # Redirect to the landing page
        st.success("Logged out successfully!")
        st.rerun()  # Force the app to rerun and update the page
        

    