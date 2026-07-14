import streamlit as st
import pandas as pd
import json
import re
from collections import defaultdict
from data.timetable import days, time_slots
from utils.image_exporter import generate_table_image, get_cell_color


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
        "MTech AI & DS": "MT",
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
    st.markdown("## 📅 Consolidated Timetable")

    def render_colored_table(rows, columns):
        html = "<table style='border-collapse: collapse; width: 100%; text-align:center;'>"
        html += "<tr>" + "".join(
            [f"<th style='background:#333;color:#fff;padding:8px;border:1px solid #999;'>{col}</th>" for col in columns]
        ) + "</tr>"
        for row in rows:
            html += "<tr>"
            for i, cell in enumerate(row):
                cell_str = str(cell).strip()
                if i == 0:
                    html += (
                        "<td style='background:#f1f1f1;font-weight:bold;padding:8px;border:1px solid #999;'>"
                        f"{cell_str}</td>"
                    )
                else:
                    bg_color = get_cell_color(cell_str)
                    html += (
                        "<td style='background:"
                        f"{bg_color};padding:8px;border:1px solid #999;font-weight:bold;'>{cell_str}</td>"
                    )
            html += "</tr>"
        html += "</table>"
        return html

    st.markdown(render_colored_table(consolidated, days), unsafe_allow_html=True)

    # Create df_consolidated for image generation
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
            st.markdown(render_colored_table(df.values.tolist(), df.columns), unsafe_allow_html=True)
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
