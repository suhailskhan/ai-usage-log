# AI Usage Log

A Streamlit-based application for tracking and analyzing AI tool usage within an organization. This application allows employees to log their AI tool usage, including time spent, purpose, and outcomes, and provides visualization features for analyzing the data.

## Features

- **Data Entry:** Log AI tool usage with details such as employee name, manager, tool used, purpose, duration, and outcomes
- **Analytics Dashboard:** Visualize usage patterns through charts and tables
- **Flexible Storage Options:** Store data in CSV or SQLite database
- **Environment Configuration:** Easily configure storage options via environment variables

## Screenshots

TODO: Add screenshots

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
