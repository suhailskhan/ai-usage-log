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
        workflow_impact_map: Optional mapping for workflow impact reverse lookup
        task_complexity_map: Optional mapping for task complexity reverse lookup
    
    Returns:
        Cleaned pandas DataFrame
    """
    df = pd.DataFrame(entries)
    if df.empty:
        return df
        
    # Apply reverse mappings if provided
    if workflow_impact_map and 'Workflow Impact' in df.columns:
        df['Workflow Impact'] = df['Workflow Impact'].map(workflow_impact_map).fillna(df['Workflow Impact'])
    if task_complexity_map and 'Task Complexity' in df.columns:
        df['Task Complexity'] = df['Task Complexity'].map(task_complexity_map).fillna(df['Task Complexity'])
    
    # Calculate time saved and ensure timestamp is datetime
    df["Time Saved"] = df["Time Without AI"] - df["Duration"]
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
        'avg_time_saved': df["Time Saved"].mean() if "Time Saved" in df.columns else 0,
        'avg_duration': df["Duration"].mean() if "Duration" in df.columns else 0,
        'avg_satisfaction': df["Satisfaction"].mean() if "Satisfaction" in df.columns else 0,
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
    
    agg_dict = {}
    if "Time Saved" in df.columns:
        agg_dict["Time Saved"] = "mean"
    if "Satisfaction" in df.columns:
        agg_dict["Satisfaction"] = "mean"
    if "Workflow Impact" in df.columns:
        agg_dict["Workflow Impact"] = lambda x: x.value_counts().index[0] if not x.empty else None
    
    if not agg_dict:
        return pd.DataFrame()
    
    tool_stats = df.groupby("AI Tool").agg(agg_dict).reset_index()
    
    # Rename columns for clarity
    rename_dict = {
        "Time Saved": "Avg Time Saved",
        "Satisfaction": "Avg Satisfaction",
        "Workflow Impact": "Most Common Workflow Impact"
    }
    tool_stats.rename(columns=rename_dict, inplace=True)
    
    return tool_stats


def calculate_complexity_analysis(df):
    """
    Calculate task complexity analysis.
    
    Args:
        df: pandas DataFrame with usage data
    
    Returns:
        DataFrame with complexity analysis
    """
    if df.empty or "Task Complexity" not in df.columns:
        return pd.DataFrame()
    
    agg_dict = {}
    if "Time Saved" in df.columns:
        agg_dict["Time Saved"] = "mean"
    if "Satisfaction" in df.columns:
        agg_dict["Satisfaction"] = "mean"
    
    if not agg_dict:
        return pd.DataFrame()
    
    complexity_stats = df.groupby("Task Complexity").agg(agg_dict).reset_index()
    
    # Rename columns for clarity
    rename_dict = {
        "Time Saved": "Avg Time Saved",
        "Satisfaction": "Avg Satisfaction"
    }
    complexity_stats.rename(columns=rename_dict, inplace=True)
    
    return complexity_stats


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
    
    agg_dict = {"Duration": "count"}  # Count of tasks
    if "Time Saved" in df.columns:
        agg_dict["Time Saved"] = "mean"
    if "Satisfaction" in df.columns:
        agg_dict["Satisfaction"] = "mean"
    
    manager_stats = df.groupby("Manager").agg(agg_dict).reset_index()
    
    # Rename columns for clarity
    rename_dict = {
        "Time Saved": "Avg Time Saved",
        "Satisfaction": "Avg Satisfaction",
        "Duration": "# Tasks"
    }
    manager_stats.rename(columns=rename_dict, inplace=True)
    
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
    
    agg_dict = {"Duration": "count"}  # Count of tasks
    if "Time Saved" in df.columns:
        agg_dict["Time Saved"] = "mean"
    if "Satisfaction" in df.columns:
        agg_dict["Satisfaction"] = "mean"
    if "Workflow Impact" in df.columns:
        agg_dict["Workflow Impact"] = lambda x: x.value_counts().index[0] if not x.empty else None
    
    purpose_stats = df.groupby("Purpose").agg(agg_dict).reset_index()
    
    # Rename columns for clarity
    rename_dict = {
        "Time Saved": "Avg Time Saved",
        "Satisfaction": "Avg Satisfaction",
        "Workflow Impact": "Most Common Workflow Impact",
        "Duration": "# Tasks"
    }
    purpose_stats.rename(columns=rename_dict, inplace=True)
    
    return purpose_stats
