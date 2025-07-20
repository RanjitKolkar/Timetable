import streamlit as st
import pandas as pd
import json
import re
from collections import defaultdict


# --- Load Data ---
def load_data():
    with open("data/timetable.json") as f:
        timetables = json.load(f)
    with open("data/faculties.json") as f:
        faculties = json.load(f)
    return timetables, faculties


# --- Calculate Load Distribution ---
def calculate_faculty_load(timetables):
    faculty_hours = defaultdict(int)

    for program, semesters in timetables.items():
        for semester, timetable_data in semesters.items():
            if isinstance(timetable_data, dict) and "Semester I" in timetable_data:
                timetable = timetable_data["Semester I"]
            elif isinstance(timetable_data, list):  # fallback for direct list structure
                timetable = timetable_data
            else:
                continue

            for row in timetable:
                for cell in row[1:]:  # skip time column
                    if not isinstance(cell, str) or not cell.strip():
                        continue
                    # Extract all (...) groups
                    matches = re.findall(r"\(([^)]+)\)", cell)
                    for match in matches:
                        # Handle comma-separated faculty codes inside the same parenthesis
                        faculty_codes = [code.strip() for code in match.split(',')]
                        for code in faculty_codes:
                            if code:  # skip empty strings
                                faculty_hours[code] += 1
    return faculty_hours

# --- Display UI ---
def show_faculty_load_distribution():
    st.title("📊 Faculty Load Distribution")

    timetables, faculties = load_data()
    faculty_hours = calculate_faculty_load(timetables)

    # Convert to DataFrame
    data = [
        {
            "Faculty Code": f,
            "Name": faculties.get(f, "Unknown"),
            "Total Hours/Week": h
        }
        for f, h in faculty_hours.items()
    ]

    df = pd.DataFrame(data).sort_values(by="Total Hours/Week", ascending=False)

    if df.empty:
        st.warning("No faculty assignments found in the timetable.")
        return

    # --- Table View ---
    st.markdown("### 📋 Teaching Load Table")
    st.dataframe(df, use_container_width=True)

    # --- CSV Download ---
    csv = df.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, "faculty_load_distribution.csv", "text/csv")

    # --- Bar Chart ---
    st.markdown("### 📊 Bar Chart of Teaching Load")
    st.bar_chart(df.set_index("Faculty Code")["Total Hours/Week"])


# For direct execution
if __name__ == "__main__":
    show_faculty_load_distribution()
