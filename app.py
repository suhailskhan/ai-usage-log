import datetime
import os
import sys
import time

import pandas as pd
import plotly.express as px
import streamlit as st
import extra_streamlit_components as stx
from dotenv import load_dotenv

from analytics_utils import prepare_dataframe as analytics_prepare_dataframe
from auth import create_jwt, validate_jwt
from auth_middleware import (
    require_auth, 
    with_auth_context, 
    auth_button, 
    AuthGuard, 
    AuthContext,
    get_auth_status
)
from form_utils import (
    WORKFLOW_IMPACT_MAP,
    REVERSE_WORKFLOW_IMPACT_MAP,
    TASK_COMPLEXITY_MAP,
    REVERSE_TASK_COMPLEXITY_MAP,
    validate_form_submission,
    create_entry_dict,
    render_usage_form
)
from storage import get_storage
from visualization_utils import (
    render_all_statistics,
    render_manager_statistics
)

load_dotenv()

# Check for required JWT secret in deployed environments
if os.getenv("DEPLOYED") == "true":
    if not os.getenv("JWT_SECRET"):
        print("ERROR: JWT_SECRET environment variable is required in deployed environments", file=sys.stderr)
        sys.exit(1)

# Environment-aware JWT cookie settings
def get_cookie_settings():
    if os.getenv("DEPLOYED") == "true":
        return {
            "secure": True,
            "same_site": "Strict"
        }
    else:  # local development
        return {
            "secure": False,
            "same_site": "Lax"
        }

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

st.set_page_config(page_title="AI Tool Usage", page_icon="📊")
st.title("AI Tool Usage")

# Create CookieManager instance with a unique key
cookie_manager = stx.CookieManager(key="auth_cookie_manager")

# Read JWT from cookie on app load
cookies = cookie_manager.get_all()
jwt_cookie = cookies.get('ai_usage_auth')
if jwt_cookie:
    payload = validate_jwt(jwt_cookie)
    if payload:
        st.session_state['jwt'] = jwt_cookie
        # st.toast("JWT from cookie validated successfully!", icon="✅")
    else:
        st.session_state.pop('jwt', None)
        # st.toast("JWT from cookie is invalid or expired.", icon="⚠️")

with st.sidebar:
    # Get current auth status
    auth_context = AuthContext.from_session_state()
    
    if auth_context.is_authenticated:
        # Show logged-in user info and logout button
        st.success(f"👤 Logged in as: **{auth_context.username}**")
        
        if st.button("🚪 Log out", use_container_width=True):
            # Clear session state
            st.session_state.pop('jwt', None)
            # Clear cookie (safely handle case where cookie doesn't exist)
            try:
                cookie_manager.delete('ai_usage_auth')
            except KeyError:
                # Cookie doesn't exist, which is fine
                pass
            st.session_state.show_jwt_toast = "Logged out successfully!"
            st.session_state.jwt_toast_icon = "👋"
            # Set a flag to trigger rerun after the cookie is deleted
            st.session_state.logout_success = True
    else:
        # Show login form
        with st.form("jwt_form", clear_on_submit=True):
            name_input = st.text_input(
                "🔑 Mock login",
                placeholder="Enter name",
                help="Enter your name and press Enter/Return to log in",
                key="jwt_name_form_input"
            )
            submitted = st.form_submit_button("Log in", use_container_width=True)
            
            if submitted:
                name_input = name_input.strip()
                if not name_input:
                    st.session_state.show_jwt_toast = "Please enter a name first."
                    st.session_state.jwt_toast_icon = "⚠️"
                else:
                    token = create_jwt(subject=name_input)
                    payload = validate_jwt(token)
                    if payload:
                        st.session_state["jwt"] = token
                        # Store JWT in secure cookie using the CookieManager instance
                        cookie_settings = get_cookie_settings()
                        cookie_manager.set(
                            cookie="ai_usage_auth",
                            val=token,
                            max_age=60*60*24*365,  # 1 year
                            secure=cookie_settings["secure"],
                            same_site=cookie_settings["same_site"]
                        )
                        st.session_state.show_jwt_toast = f"Token generated for {name_input}!"
                        st.session_state.jwt_toast_icon = "✅"
                        # Set a flag to trigger rerun after the cookie is set
                        st.session_state.login_success = True
                    else:
                        st.session_state.show_jwt_toast = "Token validation failed."
                        st.session_state.jwt_toast_icon = "❌"

# Show JWT toast if flag is set
if 'show_jwt_toast' in st.session_state:
    st.toast(st.session_state.show_jwt_toast, icon=st.session_state.jwt_toast_icon)
    del st.session_state.show_jwt_toast
    del st.session_state.jwt_toast_icon

# Handle login/logout success - rerun after cookie operations complete
if 'login_success' in st.session_state or 'logout_success' in st.session_state:
    st.session_state.pop('login_success', None)
    st.session_state.pop('logout_success', None)
    time.sleep(0.25)
    st.rerun()

def load_entries():
    return storage.load()

def save_entries(entries):
    storage.save(entries)

# Initialize session state for entries
if 'entries' not in st.session_state:
    st.session_state.entries = load_entries()

# Helper function for statistics visualization
def prepare_dataframe(entries):
    """Prepare and clean the dataframe for analysis"""
    return analytics_prepare_dataframe(entries, REVERSE_WORKFLOW_IMPACT_MAP, REVERSE_TASK_COMPLEXITY_MAP)

# Create tabs for data entry, visualization, raw data
tab1, tab2, tab3 = st.tabs(["Survey", "Statistics", "Raw Data"])

with tab1:
    # Check if we have a duplicated entry to pre-fill
    duplicate_data = st.session_state.get('duplicate_entry', {})
    
    # Show a message if form is pre-filled from duplication
    if duplicate_data:
        st.info("📋 Form pre-filled from duplicated entry. You can modify any fields before submitting.")

    # Render the form
    form_data, submitted, cancelled = render_usage_form("usage_form", MANAGER_CHOICES, TOOL_CHOICES, PURPOSE_CHOICES, duplicate_data)

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
    # Show duplicate toast if flag is set
    if 'show_duplicate_toast' in st.session_state:
        st.toast(st.session_state.show_duplicate_toast, icon="📋")
        del st.session_state.show_duplicate_toast
    
    df = prepare_dataframe(st.session_state.entries)
    
    if df.empty:
        st.write("No submissions yet.")
    else:  
        # Enable row selection for duplication
        event = st.dataframe(
            df,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Always show buttons, but disable when no row is selected
        has_selection = bool(event.selection.rows)
        selected_index = event.selection.rows[0] if has_selection else None
        
        # Create three columns for the buttons
        col1, col2, col3 = st.columns(3)
            
        with col1:
            duplicate_clicked = st.button(
                "📋 Duplicate Entry", 
                help="This will pre-fill the survey with data from the selected entry" if has_selection else "Select a row to duplicate an entry",
                disabled=not has_selection
            )
            
            if duplicate_clicked and has_selection:
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
            # Edit button - always show, middleware handles all auth and selection logic
            original_entry = st.session_state.entries[selected_index] if has_selection else None
            entry_name = original_entry['Name'] if original_entry else None
            
            edit_clicked = auth_button(
                auth_context=AuthContext.from_session_state(),
                label="✏️ Edit Entry",
                entry_name=entry_name,
                require_entry_ownership=True,
                help="This will open an edit form for the selected entry"
            )
                
            if edit_clicked and has_selection:
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
            # Delete button - always show, middleware handles all auth and selection logic
            original_entry = st.session_state.entries[selected_index] if has_selection else None
            entry_name = original_entry['Name'] if original_entry else None
            
            delete_clicked = auth_button(
                auth_context=AuthContext.from_session_state(),
                label="🗑️ Delete Entry",
                entry_name=entry_name,
                require_entry_ownership=True,
                type="secondary",
                help="This will permanently delete the selected entry"
            )
                
            if delete_clicked and has_selection:
                # Show confirmation dialog
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
                    # Protected delete confirmation using AuthGuard
                    with AuthGuard(
                        require_entry_ownership=True, 
                        entry_name=entry_info['name']
                    ) as auth_context:
                        if auth_context.is_authorized and st.button("✅ Yes, Delete", type="primary"):
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
            original_entry = st.session_state.entries[edit_data['index']]
            
            # Use AuthGuard context manager for the entire edit section
            with AuthGuard(
                message="Please log in to edit entries",
                require_entry_ownership=True,
                entry_name=original_entry['Name']
            ) as auth_context:
                
                if not auth_context.is_authorized:
                    # Clear edit state if not authorized
                    del st.session_state.edit_entry
                    st.rerun()
                
                st.divider()
                st.subheader("Edit Entry")
                st.info("✏️ Modify the fields below and click 'Save Changes' to update the entry.")
                
                # Render the edit form
                form_data, submitted, cancelled = render_usage_form("edit_form", MANAGER_CHOICES, TOOL_CHOICES, PURPOSE_CHOICES, edit_data, "💾 Save Changes", show_cancel=True)

                if submitted:
                    st.rerun()
                
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
