"""
Visualization utilities for the AI Usage Log application.
Contains functions for creating charts, tables, and statistics visualizations.
"""
import streamlit as st
import plotly.express as px
from analytics_utils import (
    calculate_tool_effectiveness,
    calculate_complexity_analysis,
    calculate_manager_insights,
    calculate_purpose_insights,
    create_pivot_table
)


def create_purpose_distribution_chart(filtered_df):
    """Create purpose distribution pie chart"""
    st.subheader("Distribution by Purpose")
    purpose_counts = filtered_df['Purpose'].value_counts().reset_index()
    purpose_counts.columns = ['Purpose', 'Count']
    fig = px.pie(purpose_counts, names='Purpose', values='Count', title='Purpose Distribution')
    st.plotly_chart(fig, use_container_width=True)


def create_heatmap_chart(filtered_df, title_prefix=""):
    """Create purpose vs AI tool heatmap showing average duration"""
    st.subheader("Purpose vs AI Tool: Average Duration Heatmap")
    heatmap_df = create_pivot_table(filtered_df, "Purpose", "AI Tool", "Duration")
    if heatmap_df is not None and not heatmap_df.empty:
        fig = px.imshow(
            heatmap_df,
            text_auto=True,
            color_continuous_scale="Blues",
            aspect="auto",
            labels=dict(x="AI Tool", y="Purpose", color="Avg Duration (min)")
        )
        title = f"{title_prefix}Average Duration by Purpose and AI Tool" if title_prefix else "Average Duration by Purpose and AI Tool"
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


def create_trend_analysis_charts(filtered_df, title_prefix=""):
    """Create trend and seasonality analysis charts"""
    st.subheader("Trend & Seasonality Analysis")
    
    # Daily submissions trend
    daily_counts = filtered_df.resample('D', on='Timestamp').size().reset_index(name='Count')
    title = f"{title_prefix}Daily Submissions" if title_prefix else "Daily Submission Count"
    fig = px.line(daily_counts, x="Timestamp", y="Count", title=title)
    st.plotly_chart(fig, use_container_width=True)
    
    # Weekly average duration trend
    weekly_avg_duration = filtered_df.resample('W', on='Timestamp')["Duration"].mean().reset_index()
    title = f"{title_prefix}Weekly Avg Duration" if title_prefix else "Weekly Average Duration"
    fig2 = px.line(weekly_avg_duration, x="Timestamp", y="Duration", title=title)
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
    create_trend_analysis_charts(filtered_df, title_prefix)


def render_user_statistics(filtered_df, username):
    """Render statistics filtered by user"""
    title_prefix = f"{username}: "
    create_purpose_distribution_chart(filtered_df)
    create_heatmap_chart(filtered_df, title_prefix)
    create_duration_by_tool_chart(filtered_df)
    create_tool_effectiveness_table(filtered_df)
    create_trend_analysis_charts(filtered_df, title_prefix)
