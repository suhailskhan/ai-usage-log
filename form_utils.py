"""
Form utilities for the AI Usage Log application.

This module contains form validation, rendering, and data processing functions
for the AI usage tracking application.
"""
import datetime
import streamlit as st

# Legacy mappings - kept for backwards compatibility but no longer used
WORKFLOW_IMPACT_MAP = {
    "Little to none": 1,
    "Minor improvement": 2,
    "Moderate improvement": 3,
    "Considerable improvement": 4,
    "Significant improvement": 5
}
REVERSE_WORKFLOW_IMPACT_MAP = {v: k for k, v in WORKFLOW_IMPACT_MAP.items()}

TASK_COMPLEXITY_MAP = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3
}
REVERSE_TASK_COMPLEXITY_MAP = {v: k for k, v in TASK_COMPLEXITY_MAP.items()}

def validate_form_submission(name, manager_val, ai_tool_val, purpose_val, result, duration):
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
        result.strip()
    ]
    
    if not all(required_fields):
        return False, "Please fill in all required fields."
    
    if duration <= 0:
        return False, "Duration must be greater than 0."
    
    return True, ""

def create_entry_dict(name, manager_val, ai_tool_val, purpose_val, duration, result, notes):
    """Create entry dictionary from form data."""
    return {
        'Name': name,
        'Manager': manager_val,
        'AI Tool': ai_tool_val,
        'Purpose': purpose_val,
        'Duration': duration,
        'Result/Outcome': result,
        'Notes': notes,
        'Timestamp': datetime.datetime.now().isoformat()
    }

def render_usage_form(form_key, manager_choices, tool_choices, purpose_choices, 
                     default_data=None, submit_button_text="Submit", show_cancel=False):
    """
    Render the usage form with optional default data.
    
    Args:
        form_key (str): Unique key for the form
        manager_choices (list): List of available manager choices
        tool_choices (list): List of available AI tool choices
        purpose_choices (list): List of available purpose choices
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
            manager_choices,
            default=default_data.get('manager', []),
            max_selections=1,
            accept_new_options=True,
        )
        ai_tool = st.multiselect(
            "AI Tool",
            tool_choices,
            default=default_data.get('ai_tool', []),
            max_selections=1,
            accept_new_options=True,
        )
        purpose = st.multiselect(
            "Purpose",
            purpose_choices,
            default=default_data.get('purpose', []),
            max_selections=1,
            accept_new_options=True,
        )
        duration = st.number_input("Duration (minutes)", min_value=0, value=default_data.get('duration', 0))
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
        'result': result,
        'notes': notes
    }
    
    return form_data, submitted, cancelled
