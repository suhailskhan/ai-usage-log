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
from analytics_utils import (
    prepare_dataframe,
    filter_last_n_days,
    calculate_basic_stats,
    create_pivot_table
)

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
    
    # Prepare and filter dataframe
    df = prepare_dataframe(entries)
    df = filter_last_n_days(df, 7)
    
    if df.empty:
        return "No usage data available for the past week.", []
    
    # Calculate basic stats using shared utility
    basic_stats = calculate_basic_stats(df)
    
    # Format stats
    stats = f"Here are this week's stats (past 7 days):\n"
    stats += f"- Average time saved per task: {basic_stats.get('avg_time_saved', 0):.1f} minutes\n"
    stats += "- Average usage duration per tool:\n"
    for tool, avg in basic_stats.get('avg_duration_per_tool', {}).items():
        stats += f"    - {tool}: {avg:.1f} minutes\n"

    # --- Matplotlib charts ---
    chart_imgs = []
    # 1. Pie chart: Distribution by Purpose
    purpose_distribution = basic_stats.get('purpose_distribution', {})
    if purpose_distribution:
        fig1, ax1 = plt.subplots()
        ax1.pie(purpose_distribution.values(), labels=purpose_distribution.keys(), autopct='%1.1f%%', startangle=90)
        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png', bbox_inches='tight')
        plt.close(fig1)
        buf1.seek(0)
        img1 = base64.b64encode(buf1.read()).decode('utf-8')
        chart_imgs.append(("Purpose Distribution", img1))
    
    # 2. Bar chart: Duration by AI Tool
    total_duration_per_tool = basic_stats.get('total_duration_per_tool', {})
    if total_duration_per_tool:
        fig2, ax2 = plt.subplots()
        tools = list(total_duration_per_tool.keys())
        durations = list(total_duration_per_tool.values())
        ax2.bar(tools, durations)
        ax2.set_ylabel('Total Duration (min)')
        buf2 = io.BytesIO()
        plt.savefig(buf2, format='png', bbox_inches='tight')
        plt.close(fig2)
        buf2.seek(0)
        img2 = base64.b64encode(buf2.read()).decode('utf-8')
        chart_imgs.append(("Total Duration by AI Tool", img2))
    
    # 3. Heatmap: Average Time Saved by Purpose and AI Tool
    heatmap_df = create_pivot_table(df, "Purpose", "AI Tool", "Time Saved")
    if heatmap_df is not None and not heatmap_df.empty:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        import seaborn as sns
        sns.heatmap(heatmap_df, annot=True, fmt=".1f", cmap="Blues", cbar_kws={'label': 'Avg Time Saved (min)'}, ax=ax3)
        buf3 = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf3, format='png', bbox_inches='tight')
        plt.close(fig3)
        buf3.seek(0)
        img3 = base64.b64encode(buf3.read()).decode('utf-8')
        chart_imgs.append(("Average Time Saved by Purpose and AI Tool", img3))
    
    return stats, chart_imgs

def send_email():
    stats, chart_imgs = fetch_stats()
    # Convert line breaks and leading spaces in stats to HTML for indentation
    def text_to_html(text):
        html = ""
        for line in text.splitlines():
            # Replace leading spaces with &nbsp; for indentation
            leading_spaces = len(line) - len(line.lstrip(' '))
            html += "&nbsp;" * leading_spaces + line.lstrip(' ') + "<br>"
        return html
    stats_html = text_to_html(stats)
    html_charts = ""
    for title, img in chart_imgs:
        html_charts += f'<div style="margin-bottom: 32px;"><h3 style="margin-bottom: 8px;">{title}</h3><img src="data:image/png;base64,{img}" style="max-width:600px;"></div>'
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        for recipient in RECIPIENTS:
            message = f"""\
Subject: Weekly AI Usage Digest\nTo: {recipient}\nMIME-Version: 1.0\nContent-Type: text/html\n\n<html><body>\n<div>\n<div style='margin-bottom: 24px;'>{stats_html}</div>\n<p style='margin-bottom: 24px;'>Access the app at: <a href='{STREAMLIT_APP_URL}'>{STREAMLIT_APP_URL}</a></p>\n<hr style='margin: 32px 0;'>\n<div style='display: flex; flex-wrap: wrap; gap: 32px;'>\n{html_charts}\n</div>\n</div>\n</body></html>\n"""
            server.sendmail(SMTP_USERNAME, recipient, message)

def main():
    send_email()

if __name__ == "__main__":
    main()
