import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from data.timetable import time_slots
# Load JSON data directly
with open("data/timetable.json") as f:
    timetables = json.load(f)
with open("data/faculties.json") as f:
    faculties = json.load(f)
with open("data/subjects.json") as f:
    subjects = json.load(f)

days = ["Time", "MON", "TUE", "WED", "THU", "FRI"]

# Light pastel colors for subjects
subject_colors = {
    "P1": "#d6eaf8", "P2": "#d1f2eb", "P3": "#f9e79f", "P4": "#f5cba7", "P5": "#f7dc6f",
    "L1": "#fadbd8", "L2": "#e8daef", "L3": "#d5f5e3", "L4": "#fcf3cf", "L5": "#f0b27a"
}

def highlight_cells(val):
    val = str(val)
    if "Lunch" in val:
        return "background-color: lightgray; font-weight: bold; text-align: center"
    elif "Library" in val:
        return "background-color: #f2f2f2; font-style: italic"
    elif val.strip():
        subject_code = val.split()[0]
        color = subject_colors.get(subject_code, "#e6f7ff")
        return f"background-color: {color}; font-weight: bold"
    return ""

def extract_faculty_codes(timetable):
    faculty_involved = set()
    for row in timetable:
        for cell in row[1:]:
            if "(" in cell and ")" in cell:
                code = cell.split("(")[-1].replace(")", "").strip()
                if code:
                    faculty_involved.add(code)
    return sorted(list(faculty_involved))

def get_subject_summary(timetable):
    subject_counts = defaultdict(int)
    for row in timetable:
        for cell in row[1:]:
            if cell.strip() and "Lunch" not in cell and "Library" not in cell:
                subject = cell.split()[0]
                subject_counts[subject] += 1
    return subject_counts

def show_timetable_viewer():
    st.title("📚 Timetable Viewer")

    col1, col2 = st.columns(2)
    with col1:
        program = st.selectbox("Select Program", list(timetables.keys()), key="v_prog")
    with col2:
        semester = st.selectbox("Select Semester", ["Semester I", "Semester III"], key="v_sem")

    data = timetables[program][semester]
    df = pd.DataFrame(data, columns=days)

    

    # Clean and limit to valid rows
    filtered_data = []
    for row in data:
        if any(cell.strip() for cell in row[1:]):  # Keep rows that have at least one subject
            filtered_data.append(row)
        if len(filtered_data) == len(time_slots):  # Stop after 7 time slots
            break

    df = pd.DataFrame(filtered_data, columns=days)

    
    st.markdown("### 🗓️ Weekly Timetable")
    styled_df = df.style.applymap(highlight_cells, subset=pd.IndexSlice[:, df.columns[1:]])
    st.dataframe(styled_df, use_container_width=True, height=420)

        # Faculty involved
    st.markdown("### 👨‍🏫 Faculty Involved")
    faculty_codes = extract_faculty_codes(data)
    filtered_faculty = {code: faculties.get(code, "Unknown") for code in faculty_codes}
    st.table(pd.DataFrame(list(filtered_faculty.items()), columns=["Code", "Faculty"]))

    # Faculty-specific filter
    st.markdown("### 🔍 Filter Timetable by Faculty (Optional)")
    filter_by_faculty = st.checkbox("Show Faculty wise Timetable")

    if filter_by_faculty:
        selected_faculty = st.selectbox("Select Faculty Code", faculty_codes)
        # Filter the timetable
        filtered = []
        for row in data:
            new_row = [row[0]]
            for cell in row[1:]:
                if f"({selected_faculty})" in cell:
                    new_row.append(cell)
                else:
                    new_row.append("")
            filtered.append(new_row)
        df_filtered = pd.DataFrame(filtered, columns=days)
        st.markdown(f"### 📋 Timetable for Faculty: **{selected_faculty} - {faculties.get(selected_faculty)}**")
        styled_df = df_filtered.style.applymap(highlight_cells, subset=pd.IndexSlice[:, df_filtered.columns[1:]])
        st.dataframe(styled_df, use_container_width=True, height=420)

    # Subject summary
    st.markdown("### 📊 Subject-wise Class Distribution")
    subject_summary = get_subject_summary(data)
    subj_name_dict = subjects.get(program, {}).get(semester, {})
    
    if subject_summary:
        summary_data = []
        for subject in sorted(subject_summary):  # sorted by code
            count = subject_summary[subject]
            name = subj_name_dict.get(subject, "Unknown Subject")
            color = subject_colors.get(subject, "#ffffff")
            color_patch = f"<div style='background-color:{color};width:50px;height:20px;border:1px solid #ccc'></div>"
            summary_data.append((subject, name, count, color_patch))
        st.markdown(
            pd.DataFrame(summary_data, columns=["Code", "Subject", "No. of Classes", "Color"])
            .to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    else:
        st.info("No subjects found in this timetable.")


    st.markdown("### 📊 Subject-wise Class Distribution")
    subject_summary = get_subject_summary(data)
    subj_name_dict = subjects.get(program, {}).get(semester, {})

    if subject_summary:
        summary_data = []
        for subject in sorted(subject_summary):  # sorted by code
            count = subject_summary[subject]
            name = subj_name_dict.get(subject, "Unknown Subject")
            color = subject_colors.get(subject, "#ffffff")
            color_patch = f"<div style='background-color:{color};width:50px;height:20px;border:1px solid #ccc'></div>"
            summary_data.append((subject, name, count, color_patch))
        st.markdown(
            pd.DataFrame(summary_data, columns=["Code", "Subject", "No. of Classes", "Color"])
            .to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
    else:
        st.info("No subjects found in this timetable.")
