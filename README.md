# AI Usage Log

A Streamlit-based application for tracking and analyzing AI tool usage within an organization. This application allows employees to log their AI tool usage, including time spent, purpose, and outcomes, and provides visualization features for analyzing the data.

## Features

- **Data Entry:** Log AI tool usage with details such as employee name, manager, tool used, purpose, duration, and outcomes
- **Analytics Dashboard:** Visualize usage patterns through charts and tables
- **Flexible Storage Options:** Store data in CSV or SQLite database
- **Environment Configuration:** Easily configure storage options via environment variables
- **Weekly Digest Email:** Automatically sends a weekly email summarizing key usage statistics, including charts and insights, to configured recipients.

## Analytics

The application provides the following analytics features:

- **Purpose Distribution:** Visualize the distribution of AI tool usage purposes using pie charts.
- **Duration Analysis:** Analyze the total and average duration of tasks by AI tool.
- **Time Saved Analysis:** Compare the time taken with and without AI assistance, including total and average time saved.
- **Tool Effectiveness Benchmarking:** Evaluate AI tools based on average time saved, satisfaction, and workflow impact.
- **Complexity vs Impact:** Understand the relationship between task complexity and workflow impact.
- **Satisfaction vs Efficiency:** Explore the correlation between user satisfaction and time saved.
- **Manager/Team Insights:** Gain insights into team performance, including average time saved and satisfaction by manager.
- **Purpose-based Use Cases:** Analyze average time saved, satisfaction, and workflow impact for different purposes.
- **Trend & Seasonality Analysis:** Identify trends in AI tool usage over time, including daily and weekly patterns.

## Usage

### Running the Application

1. Clone this repository:
   ```bash
   git clone https://github.com/suhailskhan/ai-usage-log
   cd ai-usage-log
   ```

2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv/bin/activate
   pip install -r requirements.txt
   ```

3. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```
By default, the application will use SQLite storage. See [Storage Configuration](#storage-configuration) for more details.

### Storage Configuration

The application supports three storage types:

1. **CSV Storage:** Simple file-based storage
2. **SQLite Storage (Default):** Local database file storage

Configure storage via environment variables:

```bash
# For SQLite (default)
export STORAGE_TYPE=SQLite

# For CSV
export STORAGE_TYPE=CSV
```

## Application Structure

- `app.py`: Main Streamlit application with UI and visualization logic
- `storage.py`: Data storage abstraction with support for multiple backends
- `requirements.txt`: Python dependencies

## Screenshots

### Survey

![Survey Screenshot](screenshots/survey.png)

### All Statistics

![Statistics Screenshot](screenshots/statistics.png)

### Statistics by Manager

![Statistics by Manager Screenshot](screenshots/statistics%20by%20manager.png)

### Purpose Breakdown & Duration by AI Tool

![Purpose Breakdown & Duration by AI Tool](screenshots/Screenshot%202025-05-21%20at%201.38.55%E2%80%AFPM.png)

### Time Saved Analysis

![Time Saved Analysis](screenshots/Screenshot%202025-05-21%20at%201.39.01%E2%80%AFPM.png)

### Tool Effectiveness Benchmarking & Complexity vs Impact

![Tool Effectiveness Benchmarking & Complexity vs Impact](screenshots/Screenshot%202025-05-21%20at%201.39.08%E2%80%AFPM.png)

### Satisfaction vs Efficiency

![Satisfaction vs Efficiency](screenshots/Screenshot%202025-05-21%20at%201.39.14%E2%80%AFPM.png)

### Purpose vs AI Tool: Avg Time Saved Heatmap

![Purpose vs AI Tool: Avg Time Saved Heatmap](screenshots/Screenshot%202025-05-21%20at%201.39.19%E2%80%AFPM.png)

### Trend & Seasonality Analysis

![Trend & Seasonality Analysis](screenshots/Screenshot%202025-05-21%20at%201.39.23%E2%80%AFPM.png)

### Weekly Average Time Saved

![Weekly Average Time Saved](screenshots/Screenshot%202025-05-21%20at%201.39.27%E2%80%AFPM.png)

### Raw Data

![Raw Data Screenshot](screenshots/raw%20data.png)

### Digest Email

![Email Screenshot](screenshots/email.png)

