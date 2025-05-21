import os
import sqlite3
import pandas as pd

CSV_FILE = 'ai_usage_log.csv'
DB_FILE = 'ai_usage_log.db'

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
            Name TEXT, Manager TEXT, AI_Tool TEXT, Purpose TEXT, Duration INTEGER, [Task_Complexity] TEXT, [Satisfaction] INTEGER, [Time_Without_AI] INTEGER, [Workflow_Impact] TEXT, Result_Outcome TEXT, Notes TEXT, Timestamp TEXT
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
            c.execute("ALTER TABLE entries ADD COLUMN Workflow_Impact TEXT")
        if 'Timestamp' not in cols:
            c.execute("ALTER TABLE entries ADD COLUMN Timestamp TEXT")
        self.conn.commit()
    def load(self):
        c = self.conn.cursor()
        c.execute("SELECT Name, Manager, AI_Tool, Purpose, Duration, Task_Complexity, Satisfaction, Time_Without_AI, Workflow_Impact, Result_Outcome, Notes, Timestamp FROM entries")
        rows = c.fetchall()
        return [{
            'Name': r[0],
            'Manager': r[1],
            'AI Tool': r[2],
            'Purpose': r[3],
            'Duration': r[4],
            'Task Complexity': r[5],
            'Satisfaction': r[6],
            'Time Without AI': r[7],
            'Workflow Impact': r[8],
            'Result/Outcome': r[9],
            'Notes': r[10],
            'Timestamp': r[11]
        } for r in rows]
    def save(self, entries):
        c = self.conn.cursor()
        c.execute("DELETE FROM entries")
        for e in entries:
            c.execute("INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                e['Name'],
                e['Manager'],
                e['AI Tool'],
                e['Purpose'],
                e['Duration'],
                e.get('Task Complexity'),
                e.get('Satisfaction'),
                e.get('Time Without AI'),
                e.get('Workflow Impact'),
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
