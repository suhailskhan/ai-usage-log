import streamlit as st
import pandas as pd

# Initialize session state for entries
def init_state():
    if 'entries' not in st.session_state:
        st.session_state.entries = []

init_state()

st.title("AI Tool Usage Logger")

# Reactive input fields
name = st.text_input("Employee Name")
manager = st.text_input("Manager's Name")
ai_tool = st.selectbox("AI Tool", ["ChatGPT", "GitHub Copilot"])
purpose = st.selectbox("Purpose", ["Development", "Writing", "Other"])
duration = st.number_input("Duration (minutes)", min_value=0)
result = st.text_input("Result/Outcome")
notes = st.text_area("Notes (optional)")

# Add entry to session state list
if st.button("Add Entry"):
    st.session_state.entries.append({
        'Name': name,
        'Manager': manager,
        'AI Tool': ai_tool,
        'Purpose': purpose,
        'Duration': duration,
        'Result/Outcome': result,
        'Notes': notes
    })

# Display current log
df = pd.DataFrame(st.session_state.entries)
st.subheader("Current Log Entries")
if df.empty:
    st.write("No entries yet.")
else:
    st.dataframe(df)
    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="ai_usage_log.csv", mime="text/csv")
