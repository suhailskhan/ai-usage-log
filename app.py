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

import streamlit as st
st.set_page_config(page_title="AI Tool Usage")
import pandas as pd
from storage import get_storage
import datetime

# Set storage type here
storage = get_storage("SQLite")

def load_entries():
    return storage.load()

def save_entries(entries):
    storage.save(entries)

# Initialize session state for entries
def init_state():
    if 'entries' not in st.session_state:
        st.session_state.entries = load_entries()

init_state()

# Create tabs for data entry and visualization
tab1, tab2 = st.tabs(["Survey", "Statistics"])

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
        duration = st.number_input("Duration (minutes)", min_value=1)
        complexity = st.selectbox(
            "What was the complexity level of the task?",
            ["(Select complexity)", "Easy", "Medium", "Hard"]
        )
        satisfaction = st.slider("Rate your confidence in the tools’s final output.", 1, 5, 3)
        time_without_ai = st.number_input("About how much time might the task have taken you to complete without AI assistance? (minutes)", min_value=1)
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
            workflow_impact_val = workflow_impact if workflow_impact != "(Select impact)" else ""
            if not all([
                name.strip(),
                manager_val.strip(),
                ai_tool_val.strip(),
                purpose_val.strip(),
                result.strip(),
                complexity_val.strip(),
                str(satisfaction).strip(),
                str(time_without_ai).strip(),
                workflow_impact_val.strip()
            ]):
                st.toast("There was a problem with submission.", icon="⚠️")
                st.warning("Please fill in all required fields.")
            else:
                entry = {
                    'Name': name,
                    'Manager': manager_val,
                    'AI Tool': ai_tool_val,
                    'Purpose': purpose_val,
                    'Duration': duration,
                    'Task Complexity': complexity_val,
                    "Satisfaction": satisfaction,
                    "Time Without AI": time_without_ai,
                    "Workflow Impact": workflow_impact_val,
                    'Result/Outcome': result,
                    'Notes': notes,
                    'Timestamp': datetime.datetime.now().isoformat()
                }
                st.session_state.entries.append(entry)
                save_entries(st.session_state.entries)
                st.toast("Submitted!", icon="✅")

with tab2:
    st.title("AI Tool Usage - Statistics")

    df = pd.DataFrame(st.session_state.entries)
    if df.empty:
        st.write("No data available for visualization.")
    else:
        # Pills for statistics views
        stats_option_map = {
            0: ":material/filter_alt: By Manager",
            1: "Raw Data"
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
            filtered_df = df.copy()
            if filtered_df.empty:
                st.write("No data available for visualization.")
            else:
                st.subheader("Distribution by Purpose")
                import plotly.express as px
                purpose_counts = filtered_df['Purpose'].value_counts().reset_index()
                purpose_counts.columns = ['Purpose', 'Count']
                fig = px.pie(purpose_counts, names='Purpose', values='Count', title='Purpose Distribution')
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("Purpose Breakdown")
                purpose_df = pd.DataFrame({
                    'Purpose': purpose_counts['Purpose'],
                    'Count': purpose_counts['Count'],
                    'Percentage': (purpose_counts['Count'] / purpose_counts['Count'].sum() * 100).round(1)
                })
                st.dataframe(purpose_df)
                st.subheader("Duration by AI Tool")
                tool_duration = filtered_df.groupby('AI Tool')['Duration'].sum().reset_index()
                st.bar_chart(tool_duration.set_index('AI Tool'))
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
                        st.subheader("Distribution by Purpose")
                        import plotly.express as px
                        purpose_counts = filtered_df['Purpose'].value_counts().reset_index()
                        purpose_counts.columns = ['Purpose', 'Count']
                        fig = px.pie(purpose_counts, names='Purpose', values='Count', title='Purpose Distribution')
                        st.plotly_chart(fig, use_container_width=True)
                        st.subheader("Purpose Breakdown")
                        purpose_df = pd.DataFrame({
                            'Purpose': purpose_counts['Purpose'],
                            'Count': purpose_counts['Count'],
                            'Percentage': (purpose_counts['Count'] / purpose_counts['Count'].sum() * 100).round(1)
                        })
                        st.dataframe(purpose_df)
                        st.subheader("Duration by AI Tool")
                        tool_duration = filtered_df.groupby('AI Tool')['Duration'].sum().reset_index()
                        st.bar_chart(tool_duration.set_index('AI Tool'))
        elif stats_selection == 1:
            st.toast("Showing raw data.")
            st.session_state['last_stats_selection'] = 1
            df = pd.DataFrame(st.session_state.entries)
            st.subheader("Data:")
            if df.empty:
                st.write("No submissions yet.")
            else:
                st.dataframe(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.info("To download a CSV of this data, hover over the table and click the Download button at the top right.")
