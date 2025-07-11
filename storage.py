import os
import sqlite3
import pandas as pd

CSV_FILE = 'data/ai_usage_log.csv'
DB_FILE = 'data/ai_usage_log.db'

class Storage:
    def load(self):
        raise NotImplementedError
    def save(self, entries):
        raise NotImplementedError

class CSVStorage(Storage):
    def load(self):
        if os.path.exists(CSV_FILE):
            return pd.read_csv(CSV_FILE).to_dict('records')
        return []
    def save(self, entries):
        pd.DataFrame(entries).to_csv(CSV_FILE, index=False)

class SQLiteStorage(Storage):
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self._ensure_table()
    def _ensure_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS entries (
            Name TEXT, Manager TEXT, AI_Tool TEXT, Purpose TEXT, Duration INTEGER, 
            Result_Outcome TEXT, Notes TEXT, Timestamp TEXT,
            Task_Complexity TEXT, Satisfaction INTEGER, Time_Without_AI INTEGER, Workflow_Impact INTEGER
        )''')
        # Add new columns if missing (for legacy tables)
        cols = [col[1] for col in c.execute("PRAGMA table_info(entries)").fetchall()]
        if 'Task_Complexity' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Task_Complexity TEXT")
        if 'Satisfaction' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Satisfaction INTEGER")
        if 'Time_Without_AI' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Time_Without_AI INTEGER")
        if 'Workflow_Impact' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Workflow_Impact INTEGER")
        if 'Result_Outcome' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Result_Outcome TEXT")
        if 'Timestamp' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Timestamp TEXT")
        self.conn.commit()
    def load(self):
        c = self.conn.cursor()
        c.execute("SELECT Name, Manager, AI_Tool, Purpose, Duration, Result_Outcome, Notes, Timestamp FROM entries")
        rows = c.fetchall()
        return [{
            'Name': r[0],
            'Manager': r[1],
            'AI Tool': r[2],
            'Purpose': r[3],
            'Duration': r[4],
            'Result/Outcome': r[5],
            'Notes': r[6],
            'Timestamp': r[7]
        } for r in rows]
    def save(self, entries):
        c = self.conn.cursor()
        c.execute("DELETE FROM entries")
        for e in entries:
            c.execute("INSERT INTO entries (Name, Manager, AI_Tool, Purpose, Duration, Result_Outcome, Notes, Timestamp) VALUES (?,?,?,?,?,?,?,?)", (
                e['Name'],
                e['Manager'],
                e['AI Tool'],
                e['Purpose'],
                e['Duration'],
                e['Result/Outcome'],
                e['Notes'],
                e.get('Timestamp')
            ))
        self.conn.commit()

def get_storage(storage_type):
    """
    Returns a storage instance based on the specified storage type.

    Args:
        storage_type (str): The type of storage to use. Supported values are 'CSV' and 'SQLite'.

    Returns:
        An instance of CSVStorage if storage_type is 'CSV', or SQLiteStorage if storage_type is 'SQLite'.

    Raises:
        NameError: If the required storage class is not defined.
        (Note: No explicit error is raised for unsupported storage_type in the current implementation.)
    """
    if storage_type == 'CSV':
        return CSVStorage()
    elif storage_type == 'SQLite':
        return SQLiteStorage()
