import streamlit as st
import pandas as pd
import json
import os
import re
import difflib

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

ADMIN_PASSWORD = "ab"  # 🔐 Hardcoded

# Helper to write JSON
def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def save_updated_timetable(program, semester, updated_df):
    timetables[program][semester] = updated_df.values.tolist()
    save_json(timetables, "data/timetable.json")

# ------------------ Clash Checker Logic ------------------
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

# ----------------- Admin Panel -------------------
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

    # ----------- Faculty Editor -------------
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

    # ----------- Subject Editor -------------
    with st.expander("📚 Edit Subjects"):
        prog = st.selectbox("Select Program", list(subjects.keys()), key="sub_prog")
        sem = st.selectbox("Select Semester", ["Semester I", "Semester III"], key="sub_sem")

        # Safe access to nested dict
        sub_data = subjects.get(prog, {}).get(sem, {})
        if not sub_data:
            st.warning(f"No subject data found for {prog} - {sem}. You can add subjects below.")

        sub_df = pd.DataFrame(list(sub_data.items()), columns=["Code", "Subject Name"])
        edited_sub_df = st.data_editor(sub_df, num_rows="dynamic", use_container_width=True, key="edit_subjects")

        if st.button("💾 Save Subjects for Selected Program/Semester"):
            # Ensure program and semester dicts exist
            if prog not in subjects:
                subjects[prog] = {}
            if sem not in subjects[prog]:
                subjects[prog][sem] = {}

            subjects[prog][sem].clear()
            for _, row in edited_sub_df.iterrows():
                code = row["Code"].strip()
                name = row["Subject Name"].strip()
                if code and name:
                    subjects[prog][sem][code] = name
            save_json(subjects, "data/subjects.json")
            st.success(f"✅ Subjects saved to subjects.json for {prog} - {sem}")

    # -------------- Clash Checker Section ------------------
    st.markdown("---")
    st.markdown("## 🔍 Faculty Clash Checker")

    if st.button("🚨 Check for Clashes Across All Timetables"):
        clashes, common = check_clashes(timetables)

        if clashes:
            st.error("❌ Faculty Clashes Found:")
            for c in clashes:
                st.markdown(
                    f"- `{c[0]}` has a clash:\n"
                    f"`{c[1]} - {c[2]} - {c[3]}` ⛔ overlaps with `{c[4]} - {c[5]} - {c[6]}` at **{c[7]} {c[8]}**"
                )
        else:
            st.success("✅ No faculty clashes found.")

        if common:
            st.info("ℹ️ Common Subjects (not treated as clash):")

            consolidated = {}  # key: (subject_code, faculty), value: set of "Program - Semester"

            for subj1, subj2, (faculty, _, _) in common:
                subject_code = subj1 if len(subj1) >= len(subj2) else subj2
                key = (subject_code, faculty)

                if key not in consolidated:
                    consolidated[key] = set()

                for prog, sems in timetables.items():
                    for sem, table in sems.items():
                        for row in table:
                            for cell in row[1:]:
                                if f"({faculty})" in cell and (subj1 in cell or subj2 in cell):
                                    consolidated[key].add(f"{prog} - {sem}")

            display_list = []

            for (subject_code, faculty), progsem_set in consolidated.items():
                # Find subject name from subjects.json
                subject_name = None
                for prog, sem_data in subjects.items():
                    for sem, sub_map in sem_data.items():
                        if subject_code in sub_map:
                            subject_name = sub_map[subject_code]
                            break
                    if subject_name:
                        break

                subject_display = subject_name if subject_name else subject_code
                program_list = ", ".join(sorted(progsem_set))
                display_list.append((subject_display.lower(), f"- 📚 **{subject_display} ({subject_code})** handled by `{faculty}` in **{program_list}**"))

            # Sort by subject_display (case-insensitive)
            display_list.sort()

            for _, line in display_list:
                st.markdown(line)


# If running directly
if __name__ == "__main__":
    show_timetable_editor()
