import schedule
import time
import smtplib
import ssl
import os
from dotenv import load_dotenv
import pandas as pd
from storage import get_storage
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64

# Load environment variables from .env file
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENTS = os.getenv("RECIPIENTS").split(",")
STREAMLIT_APP_URL = os.getenv("STREAMLIT_APP_URL")

def fetch_stats():
    # Load entries from SQLite database
    storage = get_storage("SQLite")
    entries = storage.load()
    if not entries:
        return "No usage data available for the past week.", []
    df = pd.DataFrame(entries)
    # Ensure Timestamp is datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    # Filter for the past 7 days
    one_week_ago = datetime.now() - timedelta(days=7)
    df = df[df["Timestamp"] >= one_week_ago]
    if df.empty:
        return "No usage data available for the past week.", []
    # Compute average time saved
    df["Time Saved"] = df["Time Without AI"] - df["Duration"]
    avg_time_saved = df["Time Saved"].mean()
    # Compute average usage duration per tool
    avg_duration_per_tool = df.groupby("AI Tool")["Duration"].mean()
    # Format stats
    stats = f"Here are this week's stats (past 7 days):\n"
    stats += f"- Average time saved per task: {avg_time_saved:.1f} minutes\n"
    stats += "- Average usage duration per tool:\n"
    for tool, avg in avg_duration_per_tool.items():
        stats += f"    - {tool}: {avg:.1f} minutes\n"

    # --- Matplotlib charts ---
    chart_imgs = []
    # 1. Pie chart: Distribution by Purpose
    if 'Purpose' in df.columns:
        purpose_counts = df['Purpose'].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(purpose_counts, labels=purpose_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Purpose Distribution')
        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png', bbox_inches='tight')
        plt.close(fig1)
        buf1.seek(0)
        img1 = base64.b64encode(buf1.read()).decode('utf-8')
        chart_imgs.append(("Purpose Distribution", img1))
    # 2. Bar chart: Duration by AI Tool
    if 'AI Tool' in df.columns:
        tool_duration = df.groupby('AI Tool')["Duration"].sum()
        fig2, ax2 = plt.subplots()
        tool_duration.plot(kind='bar', ax=ax2)
        ax2.set_ylabel('Total Duration (min)')
        ax2.set_title('Total Duration by AI Tool')
        buf2 = io.BytesIO()
        plt.savefig(buf2, format='png', bbox_inches='tight')
        plt.close(fig2)
        buf2.seek(0)
        img2 = base64.b64encode(buf2.read()).decode('utf-8')
        chart_imgs.append(("Total Duration by AI Tool", img2))
    # 3. Bar chart: Time Saved per Task
    if 'Time Saved' in df.columns:
        fig3, ax3 = plt.subplots()
        df["Time Saved"].plot(kind='bar', ax=ax3)
        ax3.set_ylabel('Time Saved (min)')
        ax3.set_title('Time Saved per Task')
        buf3 = io.BytesIO()
        plt.savefig(buf3, format='png', bbox_inches='tight')
        plt.close(fig3)
        buf3.seek(0)
        img3 = base64.b64encode(buf3.read()).decode('utf-8')
        chart_imgs.append(("Time Saved per Task", img3))
    return stats, chart_imgs

def send_email():
    stats, chart_imgs = fetch_stats()
    # Convert line breaks in stats to <br> for HTML formatting
    stats_html = stats.replace('\n', '<br>')
    html_charts = ""
    for title, img in chart_imgs:
        html_charts += f'<h3>{title}</h3><img src="data:image/png;base64,{img}" style="max-width:600px;"><br><br>'
    message = f"""\
Subject: Weekly AI Usage Digest\nMIME-Version: 1.0\nContent-Type: text/html\n\n<html><body><div>{stats_html}</div><p>Access the app at: <a href='{STREAMLIT_APP_URL}'>{STREAMLIT_APP_URL}</a></p>{html_charts}</body></html>\n"""
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        for recipient in RECIPIENTS:
            server.sendmail(SMTP_USERNAME, recipient, message)

def main():
    send_email
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
