import streamlit as st
import pandas as pd
import json
import re
from collections import defaultdict

# Load timetable and faculty data
with open("data/timetable.json") as f:
    timetables = json.load(f)
with open("data/faculties.json") as f:
    faculties = json.load(f)

def show_faculty_load_distribution():
    st.title("📊 Faculty Load Distribution")

    faculty_hours = defaultdict(int)

    # Loop through all timetable entries
    for program, semesters in timetables.items():
        for semester, timetable in semesters.items():
            for row in timetable:
                for cell in row[1:]:  # skip time slot
                    matches = re.findall(r"\((.*?)\)", cell)
                    for faculty_code in matches:
                        faculty_hours[faculty_code] += 1

    # Prepare dataframe
    data = [{"Faculty": f, "Name": faculties.get(f, "Unknown"), "Total Hours": h} for f, h in faculty_hours.items()]
    df = pd.DataFrame(data).sort_values(by="Total Hours", ascending=False)

    st.dataframe(df, use_container_width=True)

    # Optional CSV download
    csv = df.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, "faculty_load_distribution.csv", "text/csv")

    # Optional bar chart
    st.markdown("### 📊 Bar Chart of Teaching Load")
    st.bar_chart(df.set_index("Faculty")["Total Hours"])
