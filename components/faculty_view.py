import streamlit as st
import pandas as pd
import json
from data.timetable import days

# Load JSON data
with open("data/timetable.json") as f:
    timetables = json.load(f)
with open("data/faculties.json") as f:
    faculties = json.load(f)

days = ["Time", "MON", "TUE", "WED", "THU", "FRI"]

def filter_faculty_timetable(faculty_code):
    results = []
    for program, semesters in timetables.items():
        for semester, timetable in semesters.items():
            filtered_rows = []
            for row in timetable:
                new_row = [row[0]]  # Time slot
                for cell in row[1:]:
                    if f"({faculty_code})" in cell:
                        new_row.append(cell)
                    else:
                        new_row.append("")
                filtered_rows.append(new_row)
            results.append((program, semester, pd.DataFrame(filtered_rows, columns=days)))
    return results

def show_faculty_view():
    st.title("👨‍🏫 Faculty Timetable Viewer")

    faculty_code = st.selectbox("Select Faculty Code", sorted(faculties.keys()))
    st.markdown(f"**Faculty Name:** {faculties.get(faculty_code, 'Unknown')}")

    views = filter_faculty_timetable(faculty_code)

    show_only_nonempty = st.checkbox("🔍 Show only assigned timetables", value=True)

    for program, semester, df in views:
        has_any_class = df.iloc[:, 1:].apply(lambda col: col.str.strip().any(), axis=None)

        if show_only_nonempty and not has_any_class:
            continue

        st.markdown(f"### 📘 {program} - {semester}")
        st.dataframe(df, use_container_width=True)

# Only used if run directly
if __name__ == "__main__":
    show_faculty_view()
