import os
from dotenv import load_dotenv
load_dotenv()

def get_env_choices(var_name, default=None):
    value = os.getenv(var_name)
    if value:
        return [v.strip() for v in value.split(",") if v.strip()]
    return default if default is not None else []

MANAGER_CHOICES = get_env_choices("MANAGER_CHOICES", ["Manager 1", "Manager 2"])
TOOL_CHOICES = get_env_choices("TOOL_CHOICES", ["ChatGPT", "GitHub Copilot"])
PURPOSE_CHOICES = get_env_choices("PURPOSE_CHOICES", ["Development", "Writing", "Other"])

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "SQLite")

import streamlit as st
st.set_page_config(page_title="AI Tool Usage", page_icon="📊")
import pandas as pd
from storage import get_storage
import datetime
from analytics_utils import (
    prepare_dataframe as analytics_prepare_dataframe,
    calculate_tool_effectiveness,
    calculate_complexity_analysis,
    calculate_manager_insights,
    calculate_purpose_insights,
    create_pivot_table
)

# Set storage type here
storage = get_storage(STORAGE_TYPE)

def load_entries():
    return storage.load()

def save_entries(entries):
    storage.save(entries)

# Helper functions for statistics visualization
def prepare_dataframe(entries):
    """Prepare and clean the dataframe for analysis"""
    return analytics_prepare_dataframe(entries, REVERSE_WORKFLOW_IMPACT_MAP, REVERSE_TASK_COMPLEXITY_MAP)

def create_purpose_distribution_chart(filtered_df):
    """Create purpose distribution pie chart"""
    st.subheader("Distribution by Purpose")
    import plotly.express as px
    purpose_counts = filtered_df['Purpose'].value_counts().reset_index()
    purpose_counts.columns = ['Purpose', 'Count']
    fig = px.pie(purpose_counts, names='Purpose', values='Count', title='Purpose Distribution')
    st.plotly_chart(fig, use_container_width=True)

def create_heatmap_chart(filtered_df, title_prefix=""):
    """Create purpose vs AI tool heatmap"""
    st.subheader("Purpose vs AI Tool: Average Time Saved Heatmap")
    heatmap_df = create_pivot_table(filtered_df, "Purpose", "AI Tool", "Time Saved")
    if heatmap_df is not None and not heatmap_df.empty:
        import plotly.express as px
        fig = px.imshow(
            heatmap_df,
            text_auto=True,
            color_continuous_scale="Blues",
            aspect="auto",
            labels=dict(x="AI Tool", y="Purpose", color="Avg Time Saved (min)")
        )
        title = f"{title_prefix}Average Time Saved by Purpose and AI Tool" if title_prefix else "Average Time Saved by Purpose and AI Tool"
        fig.update_layout(title=title)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for heatmap.")

def create_duration_by_tool_chart(filtered_df):
    """Create duration by AI tool bar chart"""
    st.subheader("Duration by AI Tool")
    tool_duration = filtered_df.groupby('AI Tool')['Duration'].sum().reset_index()
    st.bar_chart(tool_duration.set_index('AI Tool'))

def create_tool_effectiveness_table(filtered_df):
    """Create tool effectiveness benchmarking table"""
    st.subheader("Tool Effectiveness Benchmarking")
    tool_stats = calculate_tool_effectiveness(filtered_df)
    if not tool_stats.empty:
        st.dataframe(tool_stats)

def create_complexity_vs_impact_table(filtered_df):
    """Create complexity vs impact analysis table"""
    st.subheader("Complexity vs Impact")
    complexity_stats = calculate_complexity_analysis(filtered_df)
    if not complexity_stats.empty:
        st.dataframe(complexity_stats)

def create_satisfaction_vs_efficiency_chart(filtered_df, title_prefix=""):
    """Create satisfaction vs efficiency scatter plot"""
    st.subheader("Satisfaction vs Efficiency")
    if not filtered_df["Time Saved"].isnull().all():
        import plotly.express as px
        hover_data = ["Purpose", "Manager"] if "Manager" in filtered_df.columns else ["Purpose"]
        fig = px.scatter(filtered_df, x="Time Saved", y="Satisfaction", color="AI Tool", hover_data=hover_data)
        title = f"{title_prefix}Satisfaction vs Time Saved" if title_prefix else "Satisfaction vs Time Saved by AI Tool"
        fig.update_layout(title=title)
        st.plotly_chart(fig, use_container_width=True)

def create_trend_analysis_charts(filtered_df, title_prefix=""):
    """Create trend and seasonality analysis charts"""
    st.subheader("Trend & Seasonality Analysis")
    import plotly.express as px
    
    # Daily submissions trend
    daily_counts = filtered_df.resample('D', on='Timestamp').size().reset_index(name='Count')
    title = f"{title_prefix}Daily Submissions" if title_prefix else "Daily Submission Count"
    fig = px.line(daily_counts, x="Timestamp", y="Count", title=title)
    st.plotly_chart(fig, use_container_width=True)
    
    # Weekly average time saved trend
    weekly_avg_ts = filtered_df.resample('W', on='Timestamp')["Time Saved"].mean().reset_index()
    title = f"{title_prefix}Weekly Avg Time Saved" if title_prefix else "Weekly Average Time Saved"
    fig2 = px.line(weekly_avg_ts, x="Timestamp", y="Time Saved", title=title)
    st.plotly_chart(fig2, use_container_width=True)

def create_manager_insights_table(filtered_df):
    """Create manager/team insights table"""
    st.subheader("Manager/Team Insights")
    manager_stats = calculate_manager_insights(filtered_df)
    if not manager_stats.empty:
        st.dataframe(manager_stats)

def create_purpose_insights_table(filtered_df):
    """Create purpose-based use cases table"""
    st.subheader("Purpose-based Use Cases")
    purpose_stats = calculate_purpose_insights(filtered_df)
    if not purpose_stats.empty:
        st.dataframe(purpose_stats)

def render_all_statistics(filtered_df):
    """Render all statistics charts and tables"""
    create_purpose_distribution_chart(filtered_df)
    create_heatmap_chart(filtered_df)
    create_duration_by_tool_chart(filtered_df)
    create_tool_effectiveness_table(filtered_df)
    create_complexity_vs_impact_table(filtered_df)
    create_satisfaction_vs_efficiency_chart(filtered_df)
    create_manager_insights_table(filtered_df)
    create_purpose_insights_table(filtered_df)
    create_trend_analysis_charts(filtered_df)

def render_manager_statistics(filtered_df, manager_name):
    """Render statistics filtered by manager"""
    title_prefix = f"{manager_name}: "
    create_purpose_distribution_chart(filtered_df)
    create_heatmap_chart(filtered_df, title_prefix)
    create_duration_by_tool_chart(filtered_df)
    create_tool_effectiveness_table(filtered_df)
    create_complexity_vs_impact_table(filtered_df)
    create_satisfaction_vs_efficiency_chart(filtered_df, title_prefix)
    create_trend_analysis_charts(filtered_df, title_prefix)

# Initialize session state for entries
def init_state():
    if 'entries' not in st.session_state:
        st.session_state.entries = load_entries()

init_state()

# Workflow Impact mapping
WORKFLOW_IMPACT_MAP = {
    "Little to none": 1,
    "Minor improvement": 2,
    "Moderate improvement": 3,
    "Considerable improvement": 4,
    "Significant improvement": 5
}
REVERSE_WORKFLOW_IMPACT_MAP = {v: k for k, v in WORKFLOW_IMPACT_MAP.items()}

# Task Complexity mapping
TASK_COMPLEXITY_MAP = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3
}
REVERSE_TASK_COMPLEXITY_MAP = {v: k for k, v in TASK_COMPLEXITY_MAP.items()}

# Helper functions for form validation and entry creation
def validate_form_submission(name, manager_val, ai_tool_val, purpose_val, result, 
                           complexity_val, satisfaction, time_without_ai, 
                           workflow_impact_val, duration, workflow_impact_num, complexity_num):
    """
    Validate form submission data.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = [
        name.strip(),
        manager_val.strip(),
        ai_tool_val.strip(),
        purpose_val.strip(),
        result.strip(),
        complexity_val.strip(),
        str(satisfaction).strip(),
        str(time_without_ai).strip(),
        workflow_impact_val.strip()
    ]
    
    if not all(required_fields):
        return False, "Please fill in all required fields."
    
    if duration <= 0 or time_without_ai <= 0:
        return False, "Duration and time without AI must be greater than 0."
    
    if workflow_impact_num is None or complexity_num is None:
        return False, "Please select valid options for complexity and workflow impact."
    
    return True, ""

def create_entry_dict(name, manager_val, ai_tool_val, purpose_val, duration, 
                     complexity_num, satisfaction, time_without_ai, 
                     workflow_impact_num, result, notes):
    """Create entry dictionary from form data."""
    return {
        'Name': name,
        'Manager': manager_val,
        'AI Tool': ai_tool_val,
        'Purpose': purpose_val,
        'Duration': duration,
        'Task Complexity': complexity_num,
        "Satisfaction": satisfaction,
        "Time Without AI": time_without_ai,
        "Workflow Impact": workflow_impact_num,
        'Result/Outcome': result,
        'Notes': notes,
        'Timestamp': datetime.datetime.now().isoformat()
    }

# Create tabs for data entry, visualization, raw data
tab1, tab2, tab3 = st.tabs(["Survey", "Statistics", "Raw Data"])

with tab1:
    st.title("AI Tool Usage - Survey")

    with st.form("usage_form", clear_on_submit=True):
        name = st.text_input("Name")
        manager = st.multiselect(
            "Manager",
            MANAGER_CHOICES,
            max_selections=1,
            accept_new_options=True,
        )
        ai_tool = st.multiselect(
            "AI Tool",
            TOOL_CHOICES,
            max_selections=1,
            accept_new_options=True,
        )
        purpose = st.multiselect(
            "Purpose",
            PURPOSE_CHOICES,
            max_selections=1,
            accept_new_options=True,
        )
        duration = st.number_input("Duration (minutes)", min_value=0)
        complexity = st.selectbox(
            "What was the complexity level of the task?",
            ["(Select complexity)", "Easy", "Medium", "Hard"]
        )
        satisfaction = st.slider("Rate your confidence in the tools’s final output.", 1, 5, 3)
        time_without_ai = st.number_input("About how much time might the task have taken you to complete without AI assistance? (minutes)", min_value=0)
        workflow_impact = st.selectbox(
            "Estimate the impact that this use of AI tools has had on your overall workflow.",
            [
                "(Select impact)",
                "Little to none",
                "Minor improvement",
                "Moderate improvement",
                "Considerable improvement",
                "Significant improvement"
            ]
        )
        result = st.text_input("Describe the result/outcome.")
        notes = st.text_area("Additional notes (optional):")
        submitted = st.form_submit_button("Submit")

        # Make all fields except notes mandatory
        if submitted:
            # Extract single values from multiselects
            manager_val = manager[0] if manager else ""
            ai_tool_val = ai_tool[0] if ai_tool else ""
            purpose_val = purpose[0] if purpose else ""
            complexity_val = complexity if complexity != "(Select complexity)" else ""
            complexity_num = TASK_COMPLEXITY_MAP.get(complexity_val, None)
            workflow_impact_val = workflow_impact if workflow_impact != "(Select impact)" else ""
            workflow_impact_num = WORKFLOW_IMPACT_MAP.get(workflow_impact_val, None)
            
            is_valid, error_message = validate_form_submission(
                name, manager_val, ai_tool_val, purpose_val, result, 
                complexity_val, satisfaction, time_without_ai, 
                workflow_impact_val, duration, workflow_impact_num, complexity_num
            )
            
            if not is_valid:
                st.toast("There was a problem with submission.", icon="⚠️")
                st.warning(error_message)
            else:
                entry = create_entry_dict(
                    name, manager_val, ai_tool_val, purpose_val, duration, 
                    complexity_num, satisfaction, time_without_ai, 
                    workflow_impact_num, result, notes
                )
                st.session_state.entries.append(entry)
                save_entries(st.session_state.entries)
                st.toast("Submitted!", icon="✅")

with tab2:
    st.title("AI Tool Usage - Statistics")

    df = prepare_dataframe(st.session_state.entries)
    if df.empty:
        st.write("No data available for visualization.")
    else:
        # Pills for statistics views
        stats_option_map = {
            0: ":material/filter_alt: By Manager"
        }
        stats_selection = st.pills(
            "Statistics View",
            options=stats_option_map.keys(),
            format_func=lambda option: stats_option_map[option],
            selection_mode="single",
        )

        # If no pill is selected, show unfiltered stats (default to all data)
        if stats_selection is None:
            # Show toast only if a pill was previously selected
            if 'last_stats_selection' in st.session_state and st.session_state['last_stats_selection'] is not None:
                st.toast("Showing all statistics.")
            st.session_state['last_stats_selection'] = None
            render_all_statistics(df)
        elif stats_selection == 0:
            st.toast("Showing statistics by manager.")
            st.session_state['last_stats_selection'] = 0
            managers = sorted(df['Manager'].dropna().unique())
            if not managers:
                st.write("No managers available to select.")
            else:
                selected_manager = st.selectbox("Select Manager", ["(Select a manager)"] + managers)
                if selected_manager == "(Select a manager)":
                    st.info("Please select a manager to view statistics.")
                else:
                    filtered_df = df[df['Manager'] == selected_manager]
                    if filtered_df.empty:
                        st.write("No data available for visualization.")
                    else:
                        render_manager_statistics(filtered_df, selected_manager)

with tab3:
    st.title("AI Tool Usage - Raw Data")
    df = prepare_dataframe(st.session_state.entries)
    st.subheader("Data:")
    if df.empty:
        st.write("No submissions yet.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.info("To download a CSV of this data, hover over the table and click the Download button at the top right.")
