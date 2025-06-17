import sqlite3
import random
import os
from faker import Faker
from datetime import datetime, timedelta

# Constants from storage.py and app.py
DB_FILE = 'data/ai_usage_log.db'
TABLE_NAME = 'entries'

AI_TOOLS = ["GitHub Copilot", "ChatGPT", "Claude", "Windsurf"]
PURPOSES = ["Development", "Writing", "Research", "Learning"]
RESULT_OUTCOMES = ["Completed successfully", "Partially completed", "Blocked", "Not applicable"]
NOTES_SAMPLES = [
    "Helped to quickly scaffold the project.",
    "Identified a subtle bug in the algorithm.",
    "Generated comprehensive documentation for the API.",
    "Provided useful examples for a new library.",
    "Assisted in refactoring a complex module.",
    "Reduced development time significantly.",
    "Offered alternative approaches to a problem.",
    "Streamlined the testing process.",
    "Facilitated learning a new programming concept.",
    "Improved code quality and readability."
]

# Add a fixed list of managers to allow repeats
MANAGERS = [
    "Alice Wonderland", 
    "Bob The Builder", 
    "Charlie Brown", 
    "Diana Prince", 
    "Edward Scissorhands"
]

fake = Faker()

def ensure_data_directory():
    """Ensure the data directory exists, create it if it doesn't."""
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")

def create_connection(db_file):
    """ create a database connection to the SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

def seed_data(conn, num_rows=100):
    """ Seed data into the entries table with simplified structure """
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute(f"DELETE FROM {TABLE_NAME}")
    conn.commit()

    for _ in range(num_rows):
        name = fake.name()
        manager = random.choice(MANAGERS)
        ai_tool = random.choice(AI_TOOLS)
        purpose = random.choice(PURPOSES)
        duration = random.randint(5, 120)  # Duration in minutes
        result_outcome = random.choice(RESULT_OUTCOMES)
        notes = random.choice(NOTES_SAMPLES) + " " + fake.sentence(nb_words=10)

        # Generate a timestamp from last month until now
        days_offset = random.randint(0, 30)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.randint(0, 59)
        seconds_offset = random.randint(0, 59)
        timestamp_dt = datetime.now() - timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset, seconds=seconds_offset)
        timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')

        sql = f'''INSERT INTO {TABLE_NAME}
                  (Name, Manager, AI_Tool, Purpose, Duration, Result_Outcome, Notes, Timestamp)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
        entry = (name, manager, ai_tool, purpose, duration, result_outcome, notes, timestamp_str)

        cursor.execute(sql, entry)

    conn.commit()
    print(f"Successfully seeded {num_rows} rows into {TABLE_NAME}.")

if __name__ == '__main__':
    ensure_data_directory()
    conn = create_connection(DB_FILE)
    if conn is not None:
        # Ensure table exists with simplified schema
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS entries (
            Name TEXT, Manager TEXT, AI_Tool TEXT, Purpose TEXT, Duration INTEGER, 
            Result_Outcome TEXT, Notes TEXT, Timestamp TEXT
        )''')
        
        # Add new columns if missing (for legacy tables that might have old schema)
        cols = [col[1] for col in c.execute("PRAGMA table_info(entries)").fetchall()]
        
        # Keep legacy columns for backwards compatibility but don't populate them in new entries
        if 'Task_Complexity' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Task_Complexity TEXT")
        if 'Satisfaction' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Satisfaction INTEGER")
        if 'Time_Without_AI' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Time_Without_AI INTEGER")
        if 'Workflow_Impact' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Workflow_Impact TEXT")
        if 'Result_Outcome' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Result_Outcome TEXT")
        if 'Timestamp' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Timestamp TEXT")
        conn.commit()

        seed_data(conn)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

