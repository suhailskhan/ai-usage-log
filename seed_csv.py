import csv
import random
from faker import Faker
from datetime import datetime, timedelta

# Constants (copied from seed_db.py)
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
MANAGERS = [
    "Alice Wonderland", 
    "Bob The Builder", 
    "Charlie Brown", 
    "Diana Prince", 
    "Edward Scissorhands"
]
TASK_COMPLEXITY_MAP = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3
}
WORKFLOW_IMPACT_MAP = {
    "Little to none": 1,
    "Minor improvement": 2,
    "Moderate improvement": 3,
    "Considerable improvement": 4,
    "Significant improvement": 5
}

fake = Faker()

CSV_FILE = 'data/ai_usage_log.csv'
FIELDNAMES = [
    'Name', 'Manager', 'AI_Tool', 'Purpose', 'Duration', 'Task_Complexity', 'Satisfaction',
    'Time_Without_AI', 'Workflow_Impact', 'Result_Outcome', 'Notes', 'Timestamp'
]

def seed_csv(num_rows=100):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _ in range(num_rows):
            name = fake.name()
            manager = random.choice(MANAGERS)
            ai_tool = random.choice(AI_TOOLS)
            purpose = random.choice(PURPOSES)
            duration = random.randint(5, 120)
            task_complexity_key = random.choice(list(TASK_COMPLEXITY_MAP.keys()))
            satisfaction = random.randint(1, 5)
            time_without_ai = duration + random.randint(10, 240)
            workflow_impact_key = random.choice(list(WORKFLOW_IMPACT_MAP.keys()))
            result_outcome = random.choice(RESULT_OUTCOMES)
            notes = random.choice(NOTES_SAMPLES) + " " + fake.sentence(nb_words=10)
            days_offset = random.randint(0, 30)
            hours_offset = random.randint(0, 23)
            minutes_offset = random.randint(0, 59)
            seconds_offset = random.randint(0, 59)
            timestamp_dt = datetime.now() - timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset, seconds=seconds_offset)
            timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
            row = {
                'Name': name,
                'Manager': manager,
                'AI_Tool': ai_tool,
                'Purpose': purpose,
                'Duration': duration,
                'Task_Complexity': task_complexity_key,
                'Satisfaction': satisfaction,
                'Time_Without_AI': time_without_ai,
                'Workflow_Impact': workflow_impact_key,
                'Result_Outcome': result_outcome,
                'Notes': notes,
                'Timestamp': timestamp_str
            }
            writer.writerow(row)
    print(f"Successfully seeded {num_rows} rows into {CSV_FILE}.")

if __name__ == '__main__':
    seed_csv()
