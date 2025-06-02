"""
Shared analytics utilities for AI Usage Log application.
Contains common data processing and statistics calculation functions.
"""
import pandas as pd
from datetime import datetime, timedelta


def prepare_dataframe(entries, workflow_impact_map=None, task_complexity_map=None):
    """
    Prepare and clean the dataframe for analysis.
    
    Args:
        entries: List of entry dictionaries
        workflow_impact_map: Optional mapping for workflow impact reverse lookup (kept for backwards compatibility)
        task_complexity_map: Optional mapping for task complexity reverse lookup (kept for backwards compatibility)
    
    Returns:
        Cleaned pandas DataFrame
    """
    df = pd.DataFrame(entries)
    if df.empty:
        return df
        
    # Legacy field handling for backwards compatibility with old data
    if workflow_impact_map and 'Workflow Impact' in df.columns:
        df['Workflow Impact'] = df['Workflow Impact'].map(workflow_impact_map).fillna(df['Workflow Impact'])
    if task_complexity_map and 'Task Complexity' in df.columns:
        df['Task Complexity'] = df['Task Complexity'].map(task_complexity_map).fillna(df['Task Complexity'])
    
    # Ensure timestamp is datetime
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    
    return df


def filter_last_n_days(df, days=7):
    """
    Filter dataframe to include only entries from the last N days.
    
    Args:
        df: pandas DataFrame with Timestamp column
        days: Number of days to include (default: 7)
    
    Returns:
        Filtered pandas DataFrame
    """
    if df.empty or 'Timestamp' not in df.columns:
        return df
        
    cutoff_date = datetime.now() - timedelta(days=days)
    return df[df["Timestamp"] >= cutoff_date]


def calculate_basic_stats(df):
    """
    Calculate basic statistics from the dataframe.
    
    Args:
        df: pandas DataFrame with usage data
    
    Returns:
        Dictionary containing basic statistics
    """
    if df.empty:
        return {}
    
    stats = {
        'total_entries': len(df),
        'avg_duration': df["Duration"].mean() if "Duration" in df.columns else 0,
    }
    
    # Tool-specific stats
    if "AI Tool" in df.columns:
        stats['avg_duration_per_tool'] = df.groupby("AI Tool")["Duration"].mean().to_dict()
        stats['total_duration_per_tool'] = df.groupby("AI Tool")["Duration"].sum().to_dict()
    
    # Purpose distribution
    if "Purpose" in df.columns:
        stats['purpose_distribution'] = df['Purpose'].value_counts().to_dict()
    
    return stats


def create_pivot_table(df, index, columns, values, aggfunc="mean"):
    """
    Create a pivot table with error handling.
    
    Args:
        df: pandas DataFrame
        index: Column for pivot table index
        columns: Column for pivot table columns
        values: Column for pivot table values
        aggfunc: Aggregation function (default: "mean")
    
    Returns:
        Pivot table DataFrame or None if creation fails
    """
    try:
        if all(col in df.columns for col in [index, columns, values]):
            return df.pivot_table(
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            )
    except Exception:
        pass
    return None


def calculate_tool_effectiveness(df):
    """
    Calculate tool effectiveness metrics.
    
    Args:
        df: pandas DataFrame with usage data
    
    Returns:
        DataFrame with tool effectiveness metrics
    """
    if df.empty or "AI Tool" not in df.columns:
        return pd.DataFrame()
    
    agg_dict = {
        "Duration": ["mean", "count"]  # Average duration and task count
    }
    
    tool_stats = df.groupby("AI Tool").agg(agg_dict).reset_index()
    
    # Flatten column names
    tool_stats.columns = ["AI Tool", "Avg Duration", "# Tasks"]
    
    return tool_stats


def calculate_complexity_analysis(df):
    """
    Calculate task complexity analysis (legacy function - returns empty for backwards compatibility).
    
    Args:
        df: pandas DataFrame with usage data
    
    Returns:
        Empty DataFrame (complexity analysis no longer supported)
    """
    return pd.DataFrame()


def calculate_manager_insights(df):
    """
    Calculate manager/team insights.
    
    Args:
        df: pandas DataFrame with usage data
    
    Returns:
        DataFrame with manager insights
    """
    if df.empty or "Manager" not in df.columns:
        return pd.DataFrame()
    
    agg_dict = {
        "Duration": ["count", "mean"]  # Count of tasks and average duration
    }
    
    manager_stats = df.groupby("Manager").agg(agg_dict).reset_index()
    
    # Flatten column names
    manager_stats.columns = ["Manager", "# Tasks", "Avg Duration"]
    
    return manager_stats


def calculate_purpose_insights(df):
    """
    Calculate purpose-based insights.
    
    Args:
        df: pandas DataFrame with usage data
    
    Returns:
        DataFrame with purpose insights
    """
    if df.empty or "Purpose" not in df.columns:
        return pd.DataFrame()
    
    agg_dict = {
        "Duration": ["count", "mean"]  # Count of tasks and average duration
    }
    
    purpose_stats = df.groupby("Purpose").agg(agg_dict).reset_index()
    
    # Flatten column names
    purpose_stats.columns = ["Purpose", "# Tasks", "Avg Duration"]
    
    return purpose_stats
