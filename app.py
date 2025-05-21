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
st.set_page_config(page_title="AI Tool Usage", page_icon="📊")
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
            # Require duration and time_without_ai to be greater than 0
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
            ]) or duration <= 0 or time_without_ai <= 0 or workflow_impact_num is None or complexity_num is None:
                st.toast("There was a problem with submission.", icon="⚠️")
                st.warning("Please fill in all required fields and ensure minutes are greater than 0.")
            else:
                entry = {
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
                st.session_state.entries.append(entry)
                save_entries(st.session_state.entries)
                st.toast("Submitted!", icon="✅")

with tab2:
    st.title("AI Tool Usage - Statistics")

    df = pd.DataFrame(st.session_state.entries)
    if not df.empty and 'Workflow Impact' in df.columns:
        df['Workflow Impact'] = df['Workflow Impact'].map(REVERSE_WORKFLOW_IMPACT_MAP).fillna(df['Workflow Impact'])
    if not df.empty and 'Task Complexity' in df.columns:
        df['Task Complexity'] = df['Task Complexity'].map(REVERSE_TASK_COMPLEXITY_MAP).fillna(df['Task Complexity'])
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

                st.subheader("Time Saved Analysis")
                filtered_df["Time Saved"] = filtered_df["Time Without AI"] - filtered_df["Duration"]
                total_time_saved = filtered_df["Time Saved"].sum()
                avg_time_saved = filtered_df["Time Saved"].mean()
                st.metric("Total Time Saved (minutes)", f"{total_time_saved:.1f}")
                st.metric("Average Time Saved per Task (minutes)", f"{avg_time_saved:.1f}")
                st.bar_chart(filtered_df["Time Saved"], use_container_width=True)

                st.subheader("Tool Effectiveness Benchmarking")
                tool_stats = filtered_df.groupby("AI Tool").agg({
                    "Time Saved": "mean",
                    "Satisfaction": "mean",
                    "Workflow Impact": lambda x: x.value_counts().index[0] if not x.empty else None
                }).reset_index()
                tool_stats.rename(columns={
                    "Time Saved": "Avg Time Saved",
                    "Satisfaction": "Avg Satisfaction",
                    "Workflow Impact": "Most Common Workflow Impact"
                }, inplace=True)
                st.dataframe(tool_stats)

                st.subheader("Complexity vs Impact")
                complexity_stats = filtered_df.groupby("Task Complexity").agg({
                    "Time Saved": "mean",
                    "Satisfaction": "mean"
                }).reset_index()
                complexity_stats.rename(columns={
                    "Time Saved": "Avg Time Saved",
                    "Satisfaction": "Avg Satisfaction"
                }, inplace=True)
                st.dataframe(complexity_stats)
                st.subheader("Satisfaction vs Efficiency")
                if not filtered_df["Time Saved"].isnull().all():
                    fig = px.scatter(filtered_df, x="Time Saved", y="Satisfaction", color="AI Tool", hover_data=["Purpose", "Manager"])
                    fig.update_layout(title="Satisfaction vs Time Saved by AI Tool")
                    st.plotly_chart(fig, use_container_width=True)

                st.subheader("Manager/Team Insights")
                manager_stats = filtered_df.groupby("Manager").agg({
                    "Time Saved": "mean",
                    "Satisfaction": "mean",
                    "Duration": "count"
                }).reset_index()
                manager_stats.rename(columns={
                    "Time Saved": "Avg Time Saved",
                    "Satisfaction": "Avg Satisfaction",
                    "Duration": "# Tasks"
                }, inplace=True)
                st.dataframe(manager_stats)

                st.subheader("Purpose-based Use Cases")
                purpose_stats = filtered_df.groupby("Purpose").agg({
                    "Time Saved": "mean",
                    "Satisfaction": "mean",
                    "Workflow Impact": lambda x: x.value_counts().index[0] if not x.empty else None,
                    "Duration": "count"
                }).reset_index()
                purpose_stats.rename(columns={
                    "Time Saved": "Avg Time Saved",
                    "Satisfaction": "Avg Satisfaction",
                    "Workflow Impact": "Most Common Workflow Impact",
                    "Duration": "# Tasks"
                }, inplace=True)
                st.dataframe(purpose_stats)

                st.subheader("Purpose vs AI Tool: Average Time Saved Heatmap")
                heatmap_df = filtered_df.pivot_table(
                    index="Purpose",
                    columns="AI Tool",
                    values="Time Saved",
                    aggfunc="mean"
                )
                if not heatmap_df.empty:
                    import plotly.express as px
                    fig = px.imshow(
                        heatmap_df,
                        text_auto=True,
                        color_continuous_scale="Blues",
                        aspect="auto",
                        labels=dict(x="AI Tool", y="Purpose", color="Avg Time Saved (min)")
                    )
                    fig.update_layout(title="Average Time Saved by Purpose and AI Tool")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Not enough data for heatmap.")

                st.subheader("Trend & Seasonality Analysis")
                # Ensure timestamp is datetime
                filtered_df["Timestamp"] = pd.to_datetime(filtered_df["Timestamp"])
                import plotly.express as px
                # Daily submissions trend
                daily_counts = filtered_df.resample('D', on='Timestamp').size().reset_index(name='Count')
                fig = px.line(daily_counts, x="Timestamp", y="Count", title="Daily Submission Count")
                st.plotly_chart(fig, use_container_width=True)
                # Weekly average time saved trend
                weekly_avg_ts = filtered_df.resample('W', on='Timestamp')["Time Saved"].mean().reset_index()
                fig2 = px.line(weekly_avg_ts, x="Timestamp", y="Time Saved", title="Weekly Average Time Saved")
                st.plotly_chart(fig2, use_container_width=True)
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

                        st.subheader("Time Saved Analysis")
                        filtered_df["Time Saved"] = filtered_df["Time Without AI"] - filtered_df["Duration"]
                        total_time_saved = filtered_df["Time Saved"].sum()
                        avg_time_saved = filtered_df["Time Saved"].mean()
                        st.metric("Total Time Saved (minutes)", f"{total_time_saved:.1f}")
                        st.metric("Average Time Saved per Task (minutes)", f"{avg_time_saved:.1f}")
                        st.bar_chart(filtered_df["Time Saved"], use_container_width=True)

                        st.subheader("Tool Effectiveness Benchmarking")
                        tool_stats = filtered_df.groupby("AI Tool").agg({
                            "Time Saved": "mean",
                            "Satisfaction": "mean",
                            "Workflow Impact": lambda x: x.value_counts().index[0] if not x.empty else None
                        }).reset_index()
                        tool_stats.rename(columns={
                            "Time Saved": "Avg Time Saved",
                            "Satisfaction": "Avg Satisfaction",
                            "Workflow Impact": "Most Common Workflow Impact"
                        }, inplace=True)
                        st.dataframe(tool_stats)

                        st.subheader("Complexity vs Impact")
                        complexity_stats = filtered_df.groupby("Task Complexity").agg({
                            "Time Saved": "mean",
                            "Satisfaction": "mean"
                        }).reset_index()
                        complexity_stats.rename(columns={
                            "Time Saved": "Avg Time Saved",
                            "Satisfaction": "Avg Satisfaction"
                        }, inplace=True)
                        st.dataframe(complexity_stats)
                        
                        # --- By-Manager: Satisfaction vs Efficiency ---
                        st.subheader("Satisfaction vs Efficiency")
                        import plotly.express as px
                        fig = px.scatter(filtered_df, x="Time Saved", y="Satisfaction", color="AI Tool", hover_data=["Purpose"])
                        fig.update_layout(title=f"{selected_manager}: Satisfaction vs Time Saved")
                        st.plotly_chart(fig, use_container_width=True)

                        # --- By-Manager: Purpose vs AI Tool Heatmap ---
                        st.subheader("Purpose vs AI Tool: Avg Time Saved Heatmap")
                        heatmap_df_m = filtered_df.pivot_table(
                            index="Purpose", columns="AI Tool", values="Time Saved", aggfunc="mean"
                        )
                        if not heatmap_df_m.empty:
                            fig_hm = px.imshow(
                                heatmap_df_m,
                                text_auto=True,
                                color_continuous_scale="Blues",
                                labels=dict(x="AI Tool", y="Purpose", color="Avg Time Saved (min)")
                            )
                            fig_hm.update_layout(title=f"{selected_manager}: Avg Time Saved by Purpose & Tool")
                            st.plotly_chart(fig_hm, use_container_width=True)
                        else:
                            st.info("Not enough data for manager-level heatmap.")

                        # --- By-Manager: Trend & Seasonality ---
                        st.subheader("Trend & Seasonality Analysis")
                        filtered_df["Timestamp"] = pd.to_datetime(filtered_df["Timestamp"])
                        # Daily count for this manager
                        daily_counts_m = filtered_df.resample('D', on='Timestamp').size().reset_index(name='Count')
                        fig_dc = px.line(daily_counts_m, x="Timestamp", y="Count", title=f"{selected_manager}: Daily Submissions")
                        st.plotly_chart(fig_dc, use_container_width=True)
                        # Weekly avg time saved for this manager
                        weekly_avg_m = filtered_df.resample('W', on='Timestamp')["Time Saved"].mean().reset_index()
                        fig_wa = px.line(weekly_avg_m, x="Timestamp", y="Time Saved", title=f"{selected_manager}: Weekly Avg Time Saved")
                        st.plotly_chart(fig_wa, use_container_width=True)

with tab3:
    st.title("AI Tool Usage - Raw Data")
    df = pd.DataFrame(st.session_state.entries)
    if not df.empty and 'Workflow Impact' in df.columns:
        df['Workflow Impact'] = df['Workflow Impact'].map(REVERSE_WORKFLOW_IMPACT_MAP).fillna(df['Workflow Impact'])
    if not df.empty and 'Task Complexity' in df.columns:
        df['Task Complexity'] = df['Task Complexity'].map(REVERSE_TASK_COMPLEXITY_MAP).fillna(df['Task Complexity'])
    st.subheader("Data:")
    if df.empty:
        st.write("No submissions yet.")
    else:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.info("To download a CSV of this data, hover over the table and click the Download button at the top right.")
