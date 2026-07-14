import copy
import re
import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from utils.image_exporter import generate_table_image, subject_colors

# ------------------ Load JSON ------------------
with open("data/timetable.json") as f:
    timetables = json.load(f)


ROMAN_TO_INT = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10
}


def sort_semesters(semesters):
    return sorted(
        semesters,
        key=lambda sem: (
            parse_semester_number(sem) if parse_semester_number(sem) is not None else 999,
            sem
        )
    )


def parse_semester_number(semester_name):
    if not isinstance(semester_name, str):
        return None
    digits = [int(d) for d in re.findall(r"\d+", semester_name)]
    if digits:
        return digits[0]
    roman_match = re.search(r"\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", semester_name.upper())
    if roman_match:
        return ROMAN_TO_INT.get(roman_match.group(1))
    return None


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def clone_semester_data(program, source_semester, target_semester):
    timetables.setdefault(program, {})
    subjects.setdefault(program, {})
    subject_metadata.setdefault(program, {})
    subject_faculty_map.setdefault(program, {})
    semester_metadata.setdefault(program, {})
    if source_semester in timetables.get(program, {}):
        timetables[program][target_semester] = copy.deepcopy(timetables[program][source_semester])
    if source_semester in subjects.get(program, {}):
        subjects[program][target_semester] = copy.deepcopy(subjects[program][source_semester])
    if source_semester in subject_metadata.get(program, {}):
        subject_metadata[program][target_semester] = copy.deepcopy(subject_metadata[program][source_semester])
    if source_semester in subject_faculty_map.get(program, {}):
        subject_faculty_map[program][target_semester] = copy.deepcopy(subject_faculty_map[program][source_semester])
    if source_semester in semester_metadata.get(program, {}):
        semester_metadata[program][target_semester] = copy.deepcopy(semester_metadata[program][source_semester])


def create_blank_semester(program, target_semester, template_semester=None):
    timetables.setdefault(program, {})
    subjects.setdefault(program, {})
    subject_faculty_map.setdefault(program, {})
    if template_semester in timetables.get(program, {}):
        template = timetables[program][template_semester]
        rows = len(template)
        cols = len(template[0]) if template else 6
    else:
        rows = 10
        cols = 6
    timetables[program][target_semester] = [["" for _ in range(cols)] for _ in range(rows)]
    subjects[program][target_semester] = {}
    subject_faculty_map[program][target_semester] = {}


def is_bsc_program(program):
    if not isinstance(program, str):
        return False
    identifier = program.lower().replace(".", "").replace(" ", "")
    return "bsc" in identifier or "baccalaure" in identifier


def ensure_bsc_semesters(program, total_semesters=10):
    if not is_bsc_program(program):
        return False

    existing = set(sort_semesters(timetables.get(program, {}).keys()))
    base_odd = "Semester I"
    base_even = "Semester II"
    changed = False

    for sem_number in range(1, total_semesters + 1):
        sem_name = f"Semester {sem_number}" if sem_number > 10 else ["", "Semester I", "Semester II", "Semester III", "Semester IV", "Semester V", "Semester VI", "Semester VII", "Semester VIII", "Semester IX", "Semester X"][sem_number]
        if sem_name in existing:
            continue

        if sem_number % 2 == 1:
            if base_odd in existing:
                clone_semester_data(program, base_odd, sem_name)
            elif base_even in existing:
                clone_semester_data(program, base_even, sem_name)
            else:
                create_blank_semester(program, sem_name, template_semester=base_odd)
        else:
            if base_even in existing:
                clone_semester_data(program, base_even, sem_name)
            elif base_odd in existing:
                clone_semester_data(program, base_odd, sem_name)
            else:
                create_blank_semester(program, sem_name, template_semester=base_even)

        changed = True
        existing.add(sem_name)

    if changed:
        save_json(timetables, "data/timetable.json")
        save_json(subjects, "data/subjects.json")
        save_json(subject_metadata, "data/subject_metadata.json")
        save_json(subject_faculty_map, "data/subject_faculty_map.json")
        save_json(semester_metadata, "data/semester_metadata.json")
    return changed


def semester_parity_matches(semester_name, parity):
    sem_number = parse_semester_number(semester_name)
    if sem_number is None:
        return True
    return (sem_number % 2 == 1) if parity == "Odd" else (sem_number % 2 == 0)


def extract_subject_code(cell):
    if not isinstance(cell, str):
        return ""
    cell = cell.strip()
    return cell.split()[0] if cell else ""

with open("data/subjects.json") as f:
    subjects = json.load(f)

try:
    with open("data/subject_metadata.json") as f:
        subject_metadata = json.load(f)
except FileNotFoundError:
    subject_metadata = {}

with open("data/faculties.json") as f:
    faculties = json.load(f)

with open("data/subject_faculty_map.json") as f:
    subject_faculty_map = json.load(f)

try:
    with open("data/semester_metadata.json") as f:
        semester_metadata = json.load(f)
except FileNotFoundError:
    semester_metadata = {}

# ------------------ Subject Summary ------------------
def subject_summary(data):
    counts = defaultdict(int)
    for row in data:
        for cell in row[1:]:
            cell = str(cell).strip()
            if cell and cell not in ["Lunch break", "Library/Mentoring"]:
                code = extract_subject_code(cell)
                if code:
                    counts[code] += 1
    return counts


DEFAULT_SUBJECT_COLOR = "#eef"

def render_subject_summary(summary, subject_names):
    if not summary:
        return

    html = (
        "<table style='border-collapse:collapse;width:100%;font-family:Arial,sans-serif;'>"
        "<tr>"
        "<th style='background:#333;color:#fff;padding:10px;border:1px solid #999;text-align:left;'>Code</th>"
        "<th style='background:#333;color:#fff;padding:10px;border:1px solid #999;text-align:left;'>Subject</th>"
        "<th style='background:#333;color:#fff;padding:10px;border:1px solid #999;text-align:right;'>Classes / Week</th>"
        "</tr>"
    )

    for code, count in sorted(summary.items(), key=lambda item: (-item[1], item[0])):
        color = subject_colors.get(code, DEFAULT_SUBJECT_COLOR)
        subject_name = subject_names.get(code, "Unknown Subject")
        html += (
            "<tr>"
            f"<td style='background:{color};padding:10px;border:1px solid #999;font-weight:bold;'>{code}</td>"
            f"<td style='background:{color};padding:10px;border:1px solid #999;'>{subject_name}</td>"
            f"<td style='background:{color};padding:10px;border:1px solid #999;text-align:right;'>{count}</td>"
            "</tr>"
        )

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)


# ------------------ Viewer UI ------------------
def show_viewer():
    st.title("🗓️ Timetable Viewer")

    semester_type = st.radio(
        "Semester type",
        ["Odd", "Even"],
        index=0,
        horizontal=True,
        key="viewer_semester_parity"
    )

    # -------- Program & Semester --------
    program = st.selectbox(
        "Select Program",
        sorted(timetables.keys()),
        key="viewer_program"
    )

    ensure_bsc_semesters(program, total_semesters=10)

    filtered_semesters = [
        sem for sem in sort_semesters(timetables[program].keys())
        if semester_parity_matches(sem, semester_type)
    ]
    if not filtered_semesters:
        st.warning(f"No {semester_type.lower()} semesters found for {program}. Showing all semesters instead.")
        filtered_semesters = sorted(timetables[program].keys())

    semester = st.selectbox(
        "Select Semester",
        filtered_semesters,
        key="viewer_semester"
    )


    data = timetables[program][semester]
    subject_names = subjects.get(program, {}).get(semester, {})
    room_number = semester_metadata.get(program, {}).get(semester, {}).get("room_number", "")

    days = ["Time"] + [f"DAY {i+1}" for i in range(len(data[0]) - 1)]

    # -------- HTML Timetable (WITH FACULTY DISPLAY) --------
    timetable_heading = f"## 🗓️ {program} — {semester}"
    if room_number:
        timetable_heading += f" — Room {room_number}"
    st.markdown(timetable_heading)

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
                code = extract_subject_code(cell)
                color = subject_colors.get(code, DEFAULT_SUBJECT_COLOR)

                faculty_list = (
                    subject_faculty_map
                    .get(program, {})
                    .get(semester, {})
                    .get(code, [])
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

    if room_number:
        st.markdown(f"**Room:** {room_number}")

    # -------- Download Image --------
    df_image = pd.DataFrame(data, columns=days)
    title_text = f"{program} - {semester}"
    if room_number:
        title_text += f"\nRoom {room_number}"
    img = generate_table_image(df_image, title_text)
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
        render_subject_summary(summary, subject_names)
    else:
        st.info("No classes found.")

# ------------------ Run ------------------
if __name__ == "__main__":
    show_viewer()
