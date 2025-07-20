import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from data.timetable import time_slots
from utils.image_exporter import generate_table_image

# Days
days = ["Time", "MON", "TUE", "WED", "THU", "FRI"]

# Light pastel colors for subjects
subject_colors = {
    "P1": "#d6eaf8", "P2": "#d1f2eb", "P3": "#f9e79f", "P4": "#f5cba7", "P5": "#f7dc6f",
    "L1": "#fadbd8", "L2": "#e8daef", "L3": "#d5f5e3", "L4": "#fcf3cf", "L5": "#f0b27a"
}


# === Utility Functions === #

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
                codes = cell.split("(")[-1].replace(")", "").strip().split(",")
                for code in codes:
                    faculty_involved.add(code.strip())
    return sorted(list(faculty_involved))


def get_subject_summary(timetable):
    subject_counts = defaultdict(int)
    for row in timetable:
        for cell in row[1:]:
            if cell.strip() and "Lunch" not in cell and "Library" not in cell:
                subject = cell.split()[0]
                subject_counts[subject] += 1
    return subject_counts


def parse_subject_faculty_map(data, subject_name_dict, faculties_dict):
    mapping = []
    for row in data:
        for cell in row[1:]:
            if "(" in cell and ")" in cell:
                parts = cell.split("(")
                subject_code = parts[0].strip()
                faculty_codes = parts[1].replace(")", "").strip().split(",")
                for faculty_code in faculty_codes:
                    faculty_code = faculty_code.strip()
                    if subject_code and faculty_code:
                        subject_name = subject_name_dict.get(subject_code, "Unknown Subject")
                        faculty_name = faculties_dict.get(faculty_code, "Unknown")
                        subject_entry = f"{subject_name} ({subject_code})"
                        faculty_entry = f"{faculty_name} ({faculty_code})"
                        mapping.append((subject_code, subject_entry, faculty_entry))
    return mapping


def sort_subject_map(subject_map):
    def sort_key(item):
        code = item[0]
        prefix = code[0]
        number = int(code[1:]) if code[1:].isdigit() else 0
        return (0 if prefix == 'P' else 1, number)

    return sorted(set(subject_map), key=sort_key)


def render_timetable_table(data):
    html = "<table border='1' style='border-collapse: collapse; width: 100%; text-align: center;'>"
    html += "<thead><tr>" + "".join(f"<th>{d}</th>" for d in days) + "</tr></thead><tbody>"

    skip_next = [False] * (len(days) - 1)

    for i in range(min(len(data), len(time_slots))):
        row = data[i]
        html += "<tr>"
        html += f"<td>{row[0]}</td>"

        for j in range(1, len(days)):
            if skip_next[j - 1]:
                skip_next[j - 1] = False
                continue

            cell = row[j]
            next_cell = data[i + 1][j] if i + 1 < len(data) else ""

            if cell and cell == next_cell and cell.startswith("L"):
                color = subject_colors.get(cell.split()[0], "#f0f0f0")
                html += f"<td rowspan='2' style='background-color:{color}; font-weight:bold'>{cell}</td>"
                skip_next[j - 1] = True
            else:
                style = highlight_cells(cell)
                html += f"<td style='{style}'>{cell}</td>"

        html += "</tr>"
    html += "</tbody></table>"
    return html


def show_timetable_viewer():
    # Load JSON data
    with open("data/timetable.json") as f:
        timetables = json.load(f)
    with open("data/faculties.json") as f:
        faculties = json.load(f)
    with open("data/subjects.json") as f:
        subjects = json.load(f)

    col1, col2 = st.columns(2)
    with col1:
        program = st.selectbox("Select Program", list(timetables.keys()), key="v_prog")
    with col2:
        available_sems = list(timetables[program].keys())
        semester = st.selectbox("Select Semester", available_sems, key="v_sem")


    data = timetables[program][semester]
    subject_name_dict = subjects.get(program, {}).get(semester, {})

    st.markdown("## 🗓️ Weekly Timetable")
    df_image = pd.DataFrame(data, columns=days)
    image_buf = generate_table_image(df_image, f"{program} - {semester} Timetable")

    st.download_button(
        label="📥 Download Timetable as PNG",
        data=image_buf,
        file_name=f"{program}_{semester}_timetable.png".replace(" ", "_"),
        mime="image/png"
    )

    st.markdown(render_timetable_table(data), unsafe_allow_html=True)

    # Faculty Mapping Table
    st.markdown("### 👨‍🏫 Subject-Faculty Mapping")
    subject_faculty_map = parse_subject_faculty_map(data, subject_name_dict, faculties)
    subject_faculty_map = sort_subject_map(subject_faculty_map)

    from collections import defaultdict

    # Group faculty names by subject
    grouped_map = defaultdict(list)
    for _, subject_display, faculty_display in subject_faculty_map:
        grouped_map[subject_display].append(faculty_display)

    # Convert to DataFrame
    grouped_data = [
        (subject, ", ".join(sorted(set(faculties)))) for subject, faculties in grouped_map.items()
    ]

    df_grouped = pd.DataFrame(grouped_data, columns=["Subject (Code)", "Faculty (Code)"])
    st.markdown(df_grouped.to_html(index=False), unsafe_allow_html=True)

    # Subject Summary
    st.markdown("### 📊 Subject-wise Class Distribution")
    subject_summary = get_subject_summary(data)

    if subject_summary:
        summary_data = []
        for subject in sorted(subject_summary):
            count = subject_summary[subject]
            name = subject_name_dict.get(subject, "Unknown Subject")
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
