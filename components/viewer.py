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

    st.markdown("### 🗓️ Weekly Timetable (with Lab Merging)")

    # Build HTML table with merged lab rows
    html = "<table border='1' style='border-collapse: collapse; width: 100%; text-align: center;'>"
    html += "<thead><tr>" + "".join(f"<th>{d}</th>" for d in days) + "</tr></thead><tbody>"

    skip_next = [False] * (len(days) - 1)  # skip_next[i] tells us to skip the cell below due to rowspan

    for i in range(min(len(data), len(time_slots))):
        row = data[i]
        html += "<tr>"
        html += f"<td>{row[0]}</td>"  # Time column

        for j in range(1, len(days)):
            if skip_next[j - 1]:
                skip_next[j - 1] = False
                continue

            cell = row[j]
            next_cell = data[i + 1][j] if i + 1 < len(data) else ""

            if cell and cell == next_cell and cell.startswith("L"):  # Lab spanning 2 rows
                color = subject_colors.get(cell.split()[0], "#f0f0f0")
                html += f"<td rowspan='2' style='background-color:{color}; font-weight:bold'>{cell}</td>"
                skip_next[j - 1] = True
            else:
                style = highlight_cells(cell)
                html += f"<td style='{style}'>{cell}</td>"

        html += "</tr>"
    html += "</tbody></table>"

    st.markdown(html, unsafe_allow_html=True)

    # Faculty involved
    st.markdown("### 👨‍🏫 Faculty Involved")
    faculty_codes = extract_faculty_codes(data)
    filtered_faculty = {code: faculties.get(code, "Unknown") for code in faculty_codes}
    st.table(pd.DataFrame(list(filtered_faculty.items()), columns=["Code", "Faculty"]))

    # Optional: Filter by faculty
    st.markdown("### 🔍 Filter Timetable by Faculty (Optional)")
    if st.checkbox("Show Faculty wise Timetable"):
        selected_faculty = st.selectbox("Select Faculty Code", faculty_codes)
        filtered = []
        for row in data:
            new_row = [row[0]]
            for cell in row[1:]:
                new_row.append(cell if f"({selected_faculty})" in cell else "")
            filtered.append(new_row)

        # Show filtered as DataFrame
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
