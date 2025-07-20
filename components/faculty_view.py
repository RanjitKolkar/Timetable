import streamlit as st
import pandas as pd
import json
import re
from collections import defaultdict
from data.timetable import days, time_slots
from utils.image_exporter import generate_table_image


# --- Load JSON data ---
def load_data():
    with open("data/timetable.json") as f:
        timetables = json.load(f)
    with open("data/faculties.json") as f:
        faculties = json.load(f)
    return timetables, faculties


# --- Filter cells for faculty ---
def extract_faculty_cells(timetable, faculty_code):
    detailed_load = []
    filtered_by_program = {}

    # Consolidated table: initialize with time slots
    consolidated = [[slot] + [""] * (len(days) - 1) for slot in time_slots]

    # Short labels for known programs
    program_abbr = {
        "MSc CS": "CS",
        "MSc DFIS": "DF",
        "MTech Cyber Security": "MT",
        "MSc FS": "FS"
    }

    for program, semesters in timetable.items():
        short_prog = program_abbr.get(program, program.replace(" ", "")[:2])

        for semester, table in semesters.items():
            sem_short = "".join(filter(str.isdigit, semester)) or "1"
            short_label = f"{short_prog}{sem_short}"

            filtered_rows = []
            include = False

            for i, row in enumerate(table):
                new_row = [row[0]]
                for j in range(1, len(row)):
                    cell = row[j]
                    if f"({faculty_code})" in cell:
                        subject_code = cell.split()[0]
                        # Annotate with short label (e.g., P1 (RJ) [CS1])
                        cell_with_info = f"{subject_code} ({faculty_code}) [{short_label}]"
                        new_row.append(cell_with_info)
                        consolidated[i][j] = cell_with_info
                        detailed_load.append({
                            "Program": program,
                            "Semester": semester,
                            "Subject Code": subject_code,
                            "Hour Slot": row[0],
                            "Day": days[j]
                        })
                        include = True
                    else:
                        new_row.append("")
                filtered_rows.append(new_row)

            if include:
                filtered_by_program[f"{program} - {semester}"] = pd.DataFrame(filtered_rows, columns=days)

    return consolidated, filtered_by_program, detailed_load

# --- Main UI ---
def show_faculty_view():
    st.title("👨‍🏫 Faculty Timetable & Load Viewer")

    timetables, faculties = load_data()
    faculty_code = st.selectbox("Select Faculty Code", sorted(faculties.keys()))
    st.markdown(f"**Faculty Name:** {faculties.get(faculty_code, 'Unknown')}")

    consolidated, program_tables, detailed_load = extract_faculty_cells(timetables, faculty_code)

    # --- Consolidated View ---
    # --- Consolidated View with Color ---
    st.markdown("## 📅 Consolidated Timetable")

    # Color mapping for tags
    color_map = {
        "CS": "#d0ebff",  # light blue
        "DF": "#ffd6a5",  # light orange
        "MT": "#caffbf",  # light green
        "FS": "#ffadad",  # light red
    }

    # Helper to extract tag and wrap in color
    def colorize_cell(cell):
        match = re.search(r"\[(\w+)\]", cell)
        if match:
            tag = match.group(1)
            prog = ''.join(filter(str.isalpha, tag))
            color = color_map.get(prog, "#e0e0e0")  # fallback gray
            return f'<td style="background-color:{color}; padding:4px;">{cell}</td>'
        return f"<td>{cell}</td>"

    # Construct HTML table
    html = "<table style='border-collapse: collapse; width: 100%;'>"
    # Header row
    html += "<tr>" + "".join([f"<th style='background:#333;color:#fff;padding:6px;'>{day}</th>" for day in days]) + "</tr>"

    # Data rows
    for row in consolidated:
        html += "<tr>"
        for i, cell in enumerate(row):
            if i == 0:
                html += f"<td style='background:#f1f1f1;font-weight:bold;padding:4px;'>{cell}</td>"
            else:
                html += colorize_cell(cell)
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

    # Create df_consolidated for image generation (without colors)
    df_consolidated = pd.DataFrame(consolidated, columns=days)
    # Downloadable image
    image_buf = generate_table_image(df_consolidated, f"Consolidated Timetable for {faculty_code}")
    st.download_button(
        label="📥 Download PNG",
        data=image_buf,
        file_name=f"{faculty_code}_timetable.png",
        mime="image/png"
    )

    # --- Program-wise Detail View ---
    if program_tables:
        st.markdown("## 📘 Timetable by Program & Semester")
        for key, df in program_tables.items():
            st.markdown(f"### {key}")
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No teaching assignments found for this faculty.")

    # --- Load Summary ---
    st.markdown("## ⏱️ Load Distribution")
    if detailed_load:
        df_load = pd.DataFrame(detailed_load)
        summary = df_load.groupby(["Program", "Semester", "Subject Code"]).size().reset_index(name="Hours")
        st.table(summary)
        total_hours = summary["Hours"].sum()
        st.markdown(f"**Total Teaching Load: `{total_hours}` hours/week**")
    else:
        st.info("No teaching load found.")


# For direct run
if __name__ == "__main__":
    show_faculty_view()
