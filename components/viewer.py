import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from utils.image_exporter import generate_table_image

# ------------------ Load JSON ------------------
with open("data/timetable.json") as f:
    timetables = json.load(f)

with open("data/subjects.json") as f:
    subjects = json.load(f)

with open("data/faculties.json") as f:
    faculties = json.load(f)

with open("data/subject_faculty_map.json") as f:
    subject_faculty_map = json.load(f)

# ------------------ Subject Colors ------------------
subject_colors = {
    "P1": "#d6eaf8", "P2": "#d1f2eb", "P3": "#f9e79f",
    "P4": "#f5cba7", "P5": "#f7dc6f",
    "L1": "#fadbd8", "L2": "#e8daef",
    "L3": "#d5f5e3", "L4": "#fcf3cf", "L5": "#f0b27a",
    "CDC": "#d7bde2"
}

# ------------------ Subject Summary ------------------
def subject_summary(data):
    counts = defaultdict(int)
    for row in data:
        for cell in row[1:]:
            cell = str(cell).strip()
            if cell and cell not in ["Lunch break", "Library/Mentoring"]:
                counts[cell] += 1
    return counts

# ------------------ Viewer UI ------------------
def show_viewer():
    st.title("🗓️ Timetable Viewer")

    # -------- Program & Semester --------
    program = st.selectbox(
    "Select Program",
    sorted(timetables.keys()),
    key="viewer_program"
    )

    semester = st.selectbox(
        "Select Semester",
        sorted(timetables[program].keys()),
        key="viewer_semester"
    )


    data = timetables[program][semester]
    subject_names = subjects.get(program, {}).get(semester, {})

    days = ["Time"] + [f"DAY {i+1}" for i in range(len(data[0]) - 1)]

    # -------- HTML Timetable (WITH FACULTY DISPLAY) --------
    st.markdown("## 🗓️ Weekly Timetable")

    html = "<table style='border-collapse:collapse;width:100%;text-align:center;'>"

    # Header
    html += "<tr>" + "".join(
        f"<th style='background:#333;color:#fff;padding:6px;border:1px solid #999;'>{d}</th>"
        for d in days
    ) + "</tr>"

    # Body
    for row in data:
        html += "<tr>"
        for i, cell in enumerate(row):
            cell = str(cell).strip()

            # Time column
            if i == 0:
                html += (
                    "<td style='background:#f1f1f1;"
                    "font-weight:bold;padding:4px;border:1px solid #999;'>"
                    f"{cell}</td>"
                )

            # Lunch / Library
            elif cell in ["Lunch break", "Library/Mentoring"]:
                html += (
                    "<td style='background:#d9d9d9;"
                    "font-weight:bold;border:1px solid #999;'>"
                    f"{cell}</td>"
                )

            # Subject cells
            elif cell:
                color = subject_colors.get(cell, "#eef")

                faculty_list = (
                    subject_faculty_map
                    .get(program, {})
                    .get(semester, {})
                    .get(cell, [])
                )

                faculty_suffix = ""
                if faculty_list:
                    faculty_suffix = " (" + ",".join(faculty_list) + ")"

                display_text = f"{cell}{faculty_suffix}"

                html += (
                    "<td style='background:"
                    f"{color};font-weight:bold;border:1px solid #999;'>"
                    f"{display_text}</td>"
                )
            else:
                html += "<td style='border:1px solid #999;'></td>"

        html += "</tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

    # -------- Download Image --------
    df_image = pd.DataFrame(data, columns=days)
    img = generate_table_image(df_image, f"{program} - {semester}")
    st.download_button(
        label="📥 Download Timetable as PNG",
        data=img,
        file_name=f"{program}_{semester}_timetable.png".replace(" ", "_"),
        mime="image/png"
    )

    # -------- Subject–Faculty Mapping --------
    st.markdown("## 👨‍🏫 Subject–Faculty Mapping")

    rows = []
    sf_map = subject_faculty_map.get(program, {}).get(semester, {})

    for code, faculty_list in sf_map.items():
        subject_name = subject_names.get(code, "Unknown Subject")
        faculty_display = ", ".join(
            f"{faculties.get(f, 'Unknown')} ({f})"
            for f in faculty_list
        )
        rows.append((f"{subject_name} ({code})", faculty_display))

    if rows:
        st.dataframe(
            pd.DataFrame(rows, columns=["Subject", "Faculty"]),
            use_container_width=True
        )
    else:
        st.info("No subject–faculty mapping available.")

    # -------- Subject-wise Load --------
    st.markdown("## 📊 Subject-wise Class Count")

    summary = subject_summary(data)
    if summary:
        st.dataframe(
            pd.DataFrame(
                [(k, subject_names.get(k, "Unknown Subject"), v)
                 for k, v in summary.items()],
                columns=["Code", "Subject", "Classes / Week"]
            ),
            use_container_width=True
        )
    else:
        st.info("No classes found.")

# ------------------ Run ------------------
if __name__ == "__main__":
    show_viewer()
