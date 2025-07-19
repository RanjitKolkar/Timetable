import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from data.timetable import days, time_slots  # Ensure these are defined
from utils.image_exporter import generate_table_image

# --- Load JSON data ---
with open("data/timetable.json") as f:
    timetables = json.load(f)
with open("data/faculties.json") as f:
    faculties = json.load(f)

# --- Main UI ---
def show_faculty_view():
    st.title("👨‍🏫 Faculty Timetable & Load Viewer")

    faculty_code = st.selectbox("Select Faculty Code", sorted(faculties.keys()))
    st.markdown(f"**Faculty Name:** {faculties.get(faculty_code, 'Unknown')}")

    detailed_load = []
    consolidated = [[slot] + [""] * (len(days) - 1) for slot in time_slots]

    # Go through all programs & semesters
    for program, semesters in timetables.items():
        for semester, timetable in semesters.items():
            filtered_rows = []

            for i, row in enumerate(timetable):
                new_row = [row[0]]
                for j in range(1, len(row)):
                    cell = row[j]
                    if f"({faculty_code})" in cell:
                        subject_code = cell.split()[0]
                        new_row.append(cell)
                        consolidated[i][j] = cell
                        detailed_load.append({
                            "Program": program,
                            "Semester": semester,
                            "Subject Code": subject_code,
                            "Hour Slot": row[0]
                        })
                    else:
                        new_row.append("")
                filtered_rows.append(new_row)

            df = pd.DataFrame(filtered_rows, columns=days)
            if df.iloc[:, 1:].replace("", pd.NA).dropna(how='all').shape[0] > 0:
                st.markdown(f"### 📘 {program} - {semester}")
                st.dataframe(df, use_container_width=True)

    # --- Consolidated View ---
    st.markdown("## 📅 Consolidated Timetable")
    df_consolidated = pd.DataFrame(consolidated, columns=days)
    st.dataframe(df_consolidated, use_container_width=True)
    # Generate image from consolidated table

    image_buf = generate_table_image(df_consolidated, f"Consolidated Timetable for {faculty_code}")

    # Download button
    st.download_button(
        label="📥 Download PNG",
        data=image_buf,
        file_name=f"{faculty_code}_timetable.png",
        mime="image/png"
    )
    # --- Load Summary ---
    st.markdown("## ⏱️ Load Distribution")
    if detailed_load:
        df_load = pd.DataFrame(detailed_load)
        summary = df_load.groupby(["Program", "Semester", "Subject Code"]).size().reset_index(name="Hours")
        st.table(summary)
        total_hours = summary["Hours"].sum()
        st.markdown(f"**Total Teaching Load: `{total_hours}` hours/week**")
    else:
        st.info("No teaching assignments found for this faculty.")


# For direct run
if __name__ == "__main__":
    show_faculty_view()
