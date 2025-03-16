import sqlite3

def init_db():
    conn = sqlite3.connect('scheduler.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS user (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS topic (
                    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,  -- Renamed from 'topic' to 'title' for clarity
                    description TEXT,
                    from_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT DEFAULT 'Pending' CHECK(status IN ('Not Started', 'Pending', 'In Progress', 'Completed')),
                    priority TEXT DEFAULT 'Medium' CHECK(priority IN ('Low', 'Medium', 'High')),
                    progress INTEGER DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
                    category TEXT,
                    tags TEXT,
                    recurrence TEXT CHECK(recurrence IN ('None', 'Daily', 'Weekly', 'Monthly')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS slot (
                    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    time_slot TEXT NOT NULL,  -- Renamed from 'slot' to 'time_slot' for clarity
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, date, time_slot),
                    FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(topic_id) REFERENCES topic(topic_id) ON DELETE CASCADE
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS schedule (
                    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    topic_id INTEGER NOT NULL,
                    subtopics TEXT NOT NULL,
                    reminder TEXT,
                    is_completed BOOLEAN DEFAULT FALSE,  -- Renamed from 'completed' to 'is_completed'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(topic_id) REFERENCES topic(topic_id) ON DELETE CASCADE
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS time_tracking (
                    time_tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    time_spent INTEGER NOT NULL CHECK(time_spent >= 0),  -- Time spent in seconds
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(topic_id) REFERENCES topic(topic_id) ON DELETE CASCADE
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_result (
                    quiz_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic_id INTEGER NOT NULL,
                    subtopics TEXT,
                    num_questions INTEGER NOT NULL CHECK(num_questions >= 0),
                    score INTEGER NOT NULL CHECK(score >= 0),
                    total_questions INTEGER NOT NULL CHECK(total_questions >= 0),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(topic_id) REFERENCES topic(topic_id) ON DELETE CASCADE
                )''')
    
    # Create indexes for faster queries
    c.execute('''CREATE INDEX IF NOT EXISTS idx_topic_user_id ON topic(user_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_slot_user_id ON slot(user_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_schedule_user_id ON schedule(user_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_time_tracking_user_id ON time_tracking(user_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_quiz_result_user_id ON quiz_result(user_id)''')
    
    conn.commit()
    return conn