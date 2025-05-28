import datetime
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from analytics_utils import prepare_dataframe as analytics_prepare_dataframe
from storage import get_storage
from visualization_utils import (
    render_all_statistics,
    render_manager_statistics
)

st.set_page_config(page_title="AI Tool Usage", page_icon="📊")

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

def render_usage_form(form_key, default_data=None, submit_button_text="Submit", show_cancel=False):
    """
    Render the usage form with optional default data.
    
    Args:
        form_key (str): Unique key for the form
        default_data (dict): Default values for form fields
        submit_button_text (str): Text for the submit button
        show_cancel (bool): Whether to show a cancel button
        
    Returns:
        tuple: (form_data, submitted, cancelled) where form_data contains all form values
    """
    if default_data is None:
        default_data = {}
    
    with st.form(form_key, clear_on_submit=(form_key == "usage_form")):
        name = st.text_input("Name", value=default_data.get('name', ''))
        manager = st.multiselect(
            "Manager",
            MANAGER_CHOICES,
            default=default_data.get('manager', []),
            max_selections=1,
            accept_new_options=True,
        )
        ai_tool = st.multiselect(
            "AI Tool",
            TOOL_CHOICES,
            default=default_data.get('ai_tool', []),
            max_selections=1,
            accept_new_options=True,
        )
        purpose = st.multiselect(
            "Purpose",
            PURPOSE_CHOICES,
            default=default_data.get('purpose', []),
            max_selections=1,
            accept_new_options=True,
        )
        duration = st.number_input("Duration (minutes)", min_value=0, value=default_data.get('duration', 0))
        complexity_options = ["(Select complexity)", "Easy", "Medium", "Hard"]
        complexity_default_index = 0
        if default_data.get('complexity') in complexity_options:
            complexity_default_index = complexity_options.index(default_data.get('complexity'))
        complexity = st.selectbox(
            "What was the complexity level of the task?",
            complexity_options,
            index=complexity_default_index
        )
        satisfaction = st.slider("Rate your confidence in the tools's final output.", 1, 5, default_data.get('satisfaction', 3))
        time_without_ai = st.number_input("About how much time might the task have taken you to complete without AI assistance? (minutes)", min_value=0, value=default_data.get('time_without_ai', 0))
        workflow_impact_options = [
            "(Select impact)",
            "Little to none",
            "Minor improvement",
            "Moderate improvement",
            "Considerable improvement",
            "Significant improvement"
        ]
        workflow_impact_default_index = 0
        if default_data.get('workflow_impact') in workflow_impact_options:
            workflow_impact_default_index = workflow_impact_options.index(default_data.get('workflow_impact'))
        workflow_impact = st.selectbox(
            "Estimate the impact that this use of AI tools has had on your overall workflow.",
            workflow_impact_options,
            index=workflow_impact_default_index
        )
        result = st.text_input("Describe the result/outcome.", value=default_data.get('result', ''))
        notes = st.text_area("Additional notes (optional):", value=default_data.get('notes', ''))
        
        # Form buttons
        if show_cancel:
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button(submit_button_text, type="primary")
            with col2:
                cancelled = st.form_submit_button("❌ Cancel Edit")
        else:
            submitted = st.form_submit_button(submit_button_text)
            cancelled = False
    
    # Package form data
    form_data = {
        'name': name,
        'manager': manager,
        'ai_tool': ai_tool,
        'purpose': purpose,
        'duration': duration,
        'complexity': complexity,
        'satisfaction': satisfaction,
        'time_without_ai': time_without_ai,
        'workflow_impact': workflow_impact,
        'result': result,
        'notes': notes
    }
    
    return form_data, submitted, cancelled

# Create tabs for data entry, visualization, raw data
tab1, tab2, tab3 = st.tabs(["Survey", "Statistics", "Raw Data"])

with tab1:
    st.title("AI Tool Usage - Survey")

    # Check if we have a duplicated entry to pre-fill
    duplicate_data = st.session_state.get('duplicate_entry', {})
    
    # Show a message if form is pre-filled from duplication
    if duplicate_data:
        st.info("📋 Form pre-filled from duplicated entry. You can modify any fields before submitting.")

    # Render the form
    form_data, submitted, cancelled = render_usage_form("usage_form", duplicate_data)

    # Make all fields except notes mandatory
    if submitted:
        # Clear the duplicate data after form submission attempt
        if 'duplicate_entry' in st.session_state:
            del st.session_state.duplicate_entry
            
        # Extract single values from multiselects
        manager_val = form_data['manager'][0] if form_data['manager'] else ""
        ai_tool_val = form_data['ai_tool'][0] if form_data['ai_tool'] else ""
        purpose_val = form_data['purpose'][0] if form_data['purpose'] else ""
        complexity_val = form_data['complexity'] if form_data['complexity'] != "(Select complexity)" else ""
        complexity_num = TASK_COMPLEXITY_MAP.get(complexity_val, None)
        workflow_impact_val = form_data['workflow_impact'] if form_data['workflow_impact'] != "(Select impact)" else ""
        workflow_impact_num = WORKFLOW_IMPACT_MAP.get(workflow_impact_val, None)
        
        is_valid, error_message = validate_form_submission(
            form_data['name'], manager_val, ai_tool_val, purpose_val, form_data['result'], 
            complexity_val, form_data['satisfaction'], form_data['time_without_ai'], 
            workflow_impact_val, form_data['duration'], workflow_impact_num, complexity_num
        )
        
        if not is_valid:
            st.toast("There was a problem with submission.", icon="⚠️")
            st.warning(error_message)
        else:
            entry = create_entry_dict(
                form_data['name'], manager_val, ai_tool_val, purpose_val, form_data['duration'], 
                complexity_num, form_data['satisfaction'], form_data['time_without_ai'], 
                workflow_impact_num, form_data['result'], form_data['notes']
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
    
    # Show duplicate toast if flag is set
    if 'show_duplicate_toast' in st.session_state:
        st.toast(st.session_state.show_duplicate_toast, icon="📋")
        del st.session_state.show_duplicate_toast
    
    df = prepare_dataframe(st.session_state.entries)
    
    if df.empty:
        st.write("No submissions yet.")
    else:
        st.subheader("Data:")
        st.markdown("💡 **Tip:** Click the checkbox (appears on hover) at the far left of any row to select it → Duplicate, Edit, and Delete buttons will appear")
            
        # Enable row selection for duplication
        event = st.dataframe(
            df,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Show duplicate, edit, and delete buttons when a row is selected
        if event.selection.rows:
            selected_index = event.selection.rows[0]
            selected_entry = df.iloc[selected_index]
            
            # Create three columns for the buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 Duplicate Selected Entry", help="This will pre-fill the survey with data from the selected entry"):
                    # Store the selected entry data in session state for form pre-filling
                    original_entry = st.session_state.entries[selected_index]
                    
                    # Handle manager - only include if it's in the current choices, otherwise empty
                    manager_val = original_entry['Manager']
                    manager_default = [manager_val] if manager_val in MANAGER_CHOICES else []
                    
                    # Handle AI tool - only include if it's in the current choices, otherwise empty
                    ai_tool_val = original_entry['AI Tool']
                    ai_tool_default = [ai_tool_val] if ai_tool_val in TOOL_CHOICES else []
                    
                    # Handle purpose - only include if it's in the current choices, otherwise empty
                    purpose_val = original_entry['Purpose']
                    purpose_default = [purpose_val] if purpose_val in PURPOSE_CHOICES else []
                    
                    st.session_state.duplicate_entry = {
                        'name': original_entry['Name'],
                        'manager': manager_default,
                        'ai_tool': ai_tool_default,
                        'purpose': purpose_default,
                        'duration': original_entry['Duration'],
                        'complexity': REVERSE_TASK_COMPLEXITY_MAP.get(original_entry['Task Complexity'], 'Easy'),
                        'satisfaction': original_entry['Satisfaction'],
                        'time_without_ai': original_entry['Time Without AI'],
                        'workflow_impact': REVERSE_WORKFLOW_IMPACT_MAP.get(original_entry['Workflow Impact'], 'Little to none'),
                        'result': original_entry['Result/Outcome'],
                        'notes': original_entry.get('Notes', '')
                    }
                    
                    # Format the date from the timestamp
                    timestamp = original_entry['Timestamp']
                    if isinstance(timestamp, str):
                        try:
                            date_obj = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime('%m/%d/%Y')
                        except:
                            formatted_date = timestamp.split('T')[0] if 'T' in timestamp else timestamp
                    else:
                        formatted_date = str(timestamp)
                    
                    name = original_entry['Name']
                    # Set a flag to show toast after rerun
                    st.session_state.show_duplicate_toast = f"{name}'s entry from {formatted_date} has been copied. Switch to the Survey tab to submit."
                    st.rerun()
            
            with col2:
                if st.button("✏️ Edit Selected Entry", help="This will open an edit form for the selected entry"):
                    # Store the selected entry data in session state for editing
                    original_entry = st.session_state.entries[selected_index]
                    
                    # Handle manager - only include if it's in the current choices, otherwise empty
                    manager_val = original_entry['Manager']
                    manager_default = [manager_val] if manager_val in MANAGER_CHOICES else []
                    
                    # Handle AI tool - only include if it's in the current choices, otherwise empty
                    ai_tool_val = original_entry['AI Tool']
                    ai_tool_default = [ai_tool_val] if ai_tool_val in TOOL_CHOICES else []
                    
                    # Handle purpose - only include if it's in the current choices, otherwise empty
                    purpose_val = original_entry['Purpose']
                    purpose_default = [purpose_val] if purpose_val in PURPOSE_CHOICES else []
                    
                    st.session_state.edit_entry = {
                        'index': selected_index,
                        'name': original_entry['Name'],
                        'manager': manager_default,
                        'ai_tool': ai_tool_default,
                        'purpose': purpose_default,
                        'duration': original_entry['Duration'],
                        'complexity': REVERSE_TASK_COMPLEXITY_MAP.get(original_entry['Task Complexity'], 'Easy'),
                        'satisfaction': original_entry['Satisfaction'],
                        'time_without_ai': original_entry['Time Without AI'],
                        'workflow_impact': REVERSE_WORKFLOW_IMPACT_MAP.get(original_entry['Workflow Impact'], 'Little to none'),
                        'result': original_entry['Result/Outcome'],
                        'notes': original_entry.get('Notes', '')
                    }
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Delete Selected Entry", help="This will permanently delete the selected entry", type="secondary"):
                    # Show confirmation dialog
                    original_entry = st.session_state.entries[selected_index]
                    name = original_entry['Name']
                    
                    # Format the date from the timestamp for display
                    timestamp = original_entry['Timestamp']
                    if isinstance(timestamp, str):
                        try:
                            date_obj = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime('%m/%d/%Y')
                        except:
                            formatted_date = timestamp.split('T')[0] if 'T' in timestamp else timestamp
                    else:
                        formatted_date = str(timestamp)
                    
                    # Store the entry to delete in session state for confirmation
                    st.session_state.entry_to_delete = {
                        'index': selected_index,
                        'name': name,
                        'date': formatted_date
                    }
                    st.rerun()
            
            # Show confirmation dialog if an entry is marked for deletion
            if 'entry_to_delete' in st.session_state:
                entry_info = st.session_state.entry_to_delete
                st.warning(f"⚠️ Are you sure you want to delete {entry_info['name']}'s entry from {entry_info['date']}? This action cannot be undone.")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("✅ Yes, Delete", type="primary"):
                        # Delete the entry
                        del st.session_state.entries[entry_info['index']]
                        save_entries(st.session_state.entries)
                        del st.session_state.entry_to_delete
                        st.toast(f"Deleted {entry_info['name']}'s entry from {entry_info['date']}", icon="🗑️")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancel"):
                        del st.session_state.entry_to_delete
                        st.rerun()

        # Show edit form if an entry is being edited
        if 'edit_entry' in st.session_state:
            edit_data = st.session_state.edit_entry
            st.divider()
            st.subheader("Edit Entry")
            st.info("✏️ Modify the fields below and click 'Save Changes' to update the entry.")
            
            # Render the edit form
            form_data, submitted, cancelled = render_usage_form("edit_form", edit_data, "💾 Save Changes", show_cancel=True)

            if submitted:
                # Extract single values from multiselects
                manager_val = form_data['manager'][0] if form_data['manager'] else ""
                ai_tool_val = form_data['ai_tool'][0] if form_data['ai_tool'] else ""
                purpose_val = form_data['purpose'][0] if form_data['purpose'] else ""
                complexity_val = form_data['complexity'] if form_data['complexity'] != "(Select complexity)" else ""
                complexity_num = TASK_COMPLEXITY_MAP.get(complexity_val, None)
                workflow_impact_val = form_data['workflow_impact'] if form_data['workflow_impact'] != "(Select impact)" else ""
                workflow_impact_num = WORKFLOW_IMPACT_MAP.get(workflow_impact_val, None)
                
                is_valid, error_message = validate_form_submission(
                    form_data['name'], manager_val, ai_tool_val, purpose_val, form_data['result'], 
                    complexity_val, form_data['satisfaction'], form_data['time_without_ai'], 
                    workflow_impact_val, form_data['duration'], workflow_impact_num, complexity_num
                )
                
                if not is_valid:
                    st.toast("There was a problem with saving changes.", icon="⚠️")
                    st.warning(error_message)
                else:
                    # Get the original timestamp to preserve it
                    original_entry = st.session_state.entries[edit_data['index']]
                    
                    # Update the entry
                    updated_entry = create_entry_dict(
                        form_data['name'], manager_val, ai_tool_val, purpose_val, form_data['duration'], 
                        complexity_num, form_data['satisfaction'], form_data['time_without_ai'], 
                        workflow_impact_num, form_data['result'], form_data['notes']
                    )
                    # Preserve the original timestamp
                    updated_entry['Timestamp'] = original_entry['Timestamp']
                    
                    # Replace the entry in the list
                    st.session_state.entries[edit_data['index']] = updated_entry
                    save_entries(st.session_state.entries)
                    del st.session_state.edit_entry
                    st.toast("Entry updated successfully!", icon="✅")
                    st.rerun()

            if cancelled:
                del st.session_state.edit_entry
                st.rerun()

        st.caption("💾 To download CSV: hover over the table and click the Download button at the top right.")
