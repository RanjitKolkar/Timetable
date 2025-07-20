import streamlit as st
import pandas as pd
import json
import difflib
import re
from data.timetable import days, time_slots

# Load/Save
def load_timetable():
    with open("data/timetable.json") as f:
        return json.load(f)

def save_timetable(timetable):
    with open("data/timetable.json", "w") as f:
        json.dump(timetable, f, indent=2)

# Clash Checker Logic
def check_clashes(timetable_data):
    faculty_schedule = {}
    common_subjects = set()
    clashes = []

    for program, semesters in timetable_data.items():
        for semester, table in semesters.items():
            for row_idx, row in enumerate(table):
                time_slot = row[0]
                for col_idx in range(1, len(row)):
                    cell = row[col_idx]
                    if "(" in cell and ")" in cell:
                        matches = list(re.finditer(r"(\w+)\s*\((\w+)\)", cell))
                        for match in matches:
                            subject, faculty = match.groups()
                            key = (faculty, days[col_idx], time_slot)
                            if key in faculty_schedule:
                                other = faculty_schedule[key]
                                if difflib.SequenceMatcher(None, subject, other["subject"]).ratio() > 0.8:
                                    common_subjects.add((subject, other["subject"], key))
                                else:
                                    clashes.append((faculty, program, semester, subject, other["program"], other["semester"], other["subject"], days[col_idx], time_slot))
                            else:
                                faculty_schedule[key] = {
                                    "subject": subject,
                                    "program": program,
                                    "semester": semester
                                }
    return clashes, common_subjects

# Admin Panel Main
def show_timetable_editor():
    st.header("🛠️ Admin Panel - Timetable Editor")

    # --- Password Check ---
    password = st.text_input("Enter Admin Password", type="password")
    if password != "a":
        st.warning("Please enter the correct admin password to access editing features.")
        st.stop()

    # --- Timetable Load & Edit ---
    timetable_data = load_timetable()
    program = st.selectbox("Select Program", list(timetable_data.keys()))
    semester = st.selectbox("Select Semester", list(timetable_data[program].keys()))
    
    st.markdown(f"### 📋 Editing: `{program}` - `{semester}`")
    df = pd.DataFrame(timetable_data[program][semester], columns=days)
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    if st.button("💾 Save Timetable"):
        timetable_data[program][semester] = edited_df.values.tolist()
        save_timetable(timetable_data)
        st.success("✅ Timetable saved successfully.")

    # --- Clash Checker ---
    st.markdown("---")
    st.markdown("### 🔍 Check for Faculty Clashes")

    if st.button("Check for Clashes"):
        clashes, common = check_clashes(timetable_data)

        if clashes:
            st.error("❌ Clashes found:")
            for c in clashes:
                st.markdown(
                    f"- `{c[0]}` has clash:\n"
                    f"`{c[1]} - {c[2]} - {c[3]}` ⛔ overlaps with `{c[4]} - {c[5]} - {c[6]}` at **{c[7]} {c[8]}**"
                )
        else:
            st.success("✅ No faculty clashes found.")

        if common:
            st.info("ℹ️ Common Subjects (not considered clash):")
            for s1, s2, (faculty, day, time) in common:
                st.markdown(f"- `{s1}` ≈ `{s2}` for `{faculty}` at **{day} {time}**")
