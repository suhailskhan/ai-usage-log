import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from storage import get_storage

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

    with st.form("usage_form"):
        name = st.text_input("Name")
        manager = st.text_input("Manager’s Name")
        ai_tool = st.selectbox("AI Tool", ["ChatGPT", "GitHub Copilot"])
        purpose = st.selectbox("Purpose", ["Development", "Writing", "Other"])
        duration = st.number_input("Duration (minutes)", min_value=1)
        result = st.text_input("Result/Outcome")
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Submit")

        # Make all fields except notes mandatory
        if submitted:
            if not all([
                name.strip(),
                manager.strip(),
                ai_tool.strip(),
                purpose.strip(),
                result.strip()
            ]):
                st.toast("There was a problem with submission.", icon="⚠️")
                st.warning("Please fill in all required fields.")
            else:
                entry = {
                    'Name': name,
                    'Manager': manager,
                    'AI Tool': ai_tool,
                    'Purpose': purpose,
                    'Duration': duration,
                    'Result/Outcome': result,
                    'Notes': notes
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
        st.subheader("Distribution by Purpose")
        
        # Count entries by purpose
        purpose_counts = df['Purpose'].value_counts()
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(purpose_counts, labels=purpose_counts.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        st.pyplot(fig)
        
        # Add numeric breakdown
        st.subheader("Purpose Breakdown")
        purpose_df = pd.DataFrame({
            'Purpose': purpose_counts.index,
            'Count': purpose_counts.values,
            'Percentage': (purpose_counts.values / purpose_counts.sum() * 100).round(1)
        })
        st.dataframe(purpose_df)
        
        # Other potential visualizations
        st.subheader("Duration by AI Tool")
        tool_duration = df.groupby('AI Tool')['Duration'].sum().reset_index()
        st.bar_chart(tool_duration.set_index('AI Tool'))
