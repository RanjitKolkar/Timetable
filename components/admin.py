import streamlit as st
import pandas as pd
import json
import os

# Load all data from JSON
with open("data/timetable.json") as f:
    timetables = json.load(f)
with open("data/faculties.json") as f:
    faculties = json.load(f)
with open("data/subjects.json") as f:
    subjects = json.load(f)

days = ["Time", "MON", "TUE", "WED", "THU", "FRI"]
time_slots = [
    "10.00 - 11.00",
    "11.00 - 12.00",
    "12.00 - 01.00",
    "01.00 - 02.00",
    "02.00 - 03.00",
    "03.00 - 04.00",
    "04.00 - 05.00",
    "05.00 - 06.00"
]

ADMIN_PASSWORD = "a"  # 🔐 Hardcoded

# Helper to write JSON
def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def save_updated_timetable(program, semester, updated_df):
    timetables[program][semester] = updated_df.values.tolist()
    save_json(timetables, "data/timetable.json")

def show_timetable_editor():
    st.title("📋 Timetable Editor (Admin Panel)")

    password = st.text_input("🔐 Enter Admin Password", type="password")
    if password != ADMIN_PASSWORD:
        st.warning("Access Denied. Please enter the correct password.")
        st.stop()
    st.success("✅ Access Granted")

    col1, col2 = st.columns(2)
    with col1:
        program = st.selectbox("Select Program", list(timetables.keys()), key="a_prog")
    with col2:
        semester = st.selectbox("Select Semester", ["Semester I", "Semester III"], key="a_sem")

    data = timetables[program][semester]
    df = pd.DataFrame(data, columns=days)

    st.markdown("### ✏️ Click on any cell to edit (Format: Subject (Initials))")
    edited_df = st.data_editor(df, num_rows="fixed", use_container_width=True, key="edit_table")

    if st.button("✅ Save Changes"):
        save_updated_timetable(program, semester, edited_df)
        st.success("✅ Timetable updated and saved to timetable.json")

    with st.expander("👨‍🏫 Faculty Reference"):
        st.table(pd.DataFrame(faculties.items(), columns=["Code", "Faculty"]))

    # 🔧 Master Editor Section
    st.markdown("## 🛠️ Master Data Editor")

    with st.expander("👨‍🏫 Edit Faculties"):
        st.markdown("### Faculty List Editor")
        faculty_df = pd.DataFrame(list(faculties.items()), columns=["Code", "Faculty Name"])
        edited_faculty_df = st.data_editor(faculty_df, num_rows="dynamic", use_container_width=True, key="edit_faculties")

        if st.button("💾 Save Faculty List"):
            faculties.clear()
            for _, row in edited_faculty_df.iterrows():
                code = row["Code"].strip()
                name = row["Faculty Name"].strip()
                if code and name:
                    faculties[code] = name
            save_json(faculties, "data/faculties.json")
            st.success("✅ Faculty list saved to faculties.json")

    with st.expander("📚 Edit Subjects"):
        prog = st.selectbox("Select Program", list(subjects.keys()), key="sub_prog")
        sem = st.selectbox("Select Semester", ["Semester I", "Semester III"], key="sub_sem")

        sub_data = subjects[prog][sem]
        sub_df = pd.DataFrame(list(sub_data.items()), columns=["Code", "Subject Name"])
        edited_sub_df = st.data_editor(sub_df, num_rows="dynamic", use_container_width=True, key="edit_subjects")

        if st.button("💾 Save Subjects for Selected Program/Semester"):
            subjects[prog][sem].clear()
            for _, row in edited_sub_df.iterrows():
                code = row["Code"].strip()
                name = row["Subject Name"].strip()
                if code and name:
                    subjects[prog][sem][code] = name
            save_json(subjects, "data/subjects.json")
            st.success(f"✅ Subjects saved to subjects.json for {prog} - {sem}")

if __name__ == "__main__":
    show_timetable_editor()
