import re
import streamlit as st
import pandas as pd
import json

# ------------------ Load JSON ------------------
with open("data/timetable.json") as f:
    timetables = json.load(f)

with open("data/subjects.json") as f:
    subjects = json.load(f)

with open("data/faculties.json") as f:
    faculties = json.load(f)

with open("data/subject_faculty_map.json") as f:
    subject_faculty_map = json.load(f)

try:
    with open("data/subject_metadata.json") as f:
        subject_metadata = json.load(f)
except FileNotFoundError:
    subject_metadata = {}

# ------------------ Helpers ------------------
def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


DEFAULT_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def save_updated_timetable(program, semester, df):
    timetables[program][semester] = df.values.tolist()
    save_json(timetables, "data/timetable.json")


def save_all_state():
    save_json(timetables, "data/timetable.json")
    save_json(subjects, "data/subjects.json")
    save_json(subject_faculty_map, "data/subject_faculty_map.json")
    save_json(subject_metadata, "data/subject_metadata.json")


def get_program_semesters(program):
    return sorted(
        set(timetables.get(program, {}))
        | set(subjects.get(program, {}))
        | set(subject_faculty_map.get(program, {}))
        | set(subject_metadata.get(program, {}))
    )


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


def parse_semester_number(semester_name):
    if not isinstance(semester_name, str):
        return None
    digits = re.findall(r"\d+", semester_name)
    if digits:
        return int(digits[0])
    roman_match = re.search(r"\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", semester_name.upper())
    if roman_match:
        return ROMAN_TO_INT.get(roman_match.group(1), None)
    return None


def semester_parity_matches(semester_name, parity):
    sem_number = parse_semester_number(semester_name)
    if sem_number is None:
        return True
    if parity == "Odd":
        return sem_number % 2 == 1
    return sem_number % 2 == 0


def delete_program(program):
    if program in timetables:
        del timetables[program]
    if program in subjects:
        del subjects[program]
    if program in subject_faculty_map:
        del subject_faculty_map[program]
    if program in subject_metadata:
        del subject_metadata[program]
    save_all_state()


def delete_semester(program, semester):
    if program in timetables and semester in timetables[program]:
        del timetables[program][semester]
    if program in subjects and semester in subjects[program]:
        del subjects[program][semester]
    if program in subject_faculty_map and semester in subject_faculty_map[program]:
        del subject_faculty_map[program][semester]
    if program in subject_metadata and semester in subject_metadata[program]:
        del subject_metadata[program][semester]
    save_all_state()


def delete_faculty(faculty_code):
    if faculty_code in faculties:
        del faculties[faculty_code]
    for prog, sems in subject_faculty_map.items():
        for sem, mapping in sems.items():
            for subject, faculty_list in mapping.items():
                subject_faculty_map[prog][sem][subject] = [f for f in faculty_list if f != faculty_code]
    save_all_state()


def delete_subject(program, semester, subject_code):
    if program in subjects and semester in subjects[program] and subject_code in subjects[program][semester]:
        del subjects[program][semester][subject_code]
    if program in subject_faculty_map and semester in subject_faculty_map[program] and subject_code in subject_faculty_map[program][semester]:
        del subject_faculty_map[program][semester][subject_code]
    if program in subject_metadata and semester in subject_metadata[program] and subject_code in subject_metadata[program][semester]:
        del subject_metadata[program][semester][subject_code]
    save_all_state()


def ensure_nested_dict(data, *keys):
    current = data
    for key in keys:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    return current


def normalize_faculty_codes(value):
    if isinstance(value, list):
        return [code.strip() for code in value if code]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def get_subject_metadata(program, semester, subject_code):
    return subject_metadata.get(program, {}).get(semester, {}).get(subject_code, {})


def update_timetable_subject_code(program, semester, old_code, new_code):
    table = timetables.get(program, {}).get(semester, [])
    for row_index, row in enumerate(table):
        for col_index, cell in enumerate(row):
            if not isinstance(cell, str) or not cell:
                continue
            parts = cell.split(" ", 1)
            if parts[0] == old_code:
                remainder = parts[1] if len(parts) > 1 else ""
                table[row_index][col_index] = new_code + (" " + remainder if remainder else "")
    save_json(timetables, "data/timetable.json")


def update_timetable_faculty_code(old_code, new_code):
    for program, semesters in timetables.items():
        for semester, table in semesters.items():
            for row_index, row in enumerate(table):
                for col_index, cell in enumerate(row):
                    if not isinstance(cell, str) or not cell or old_code not in cell:
                        continue
                    match = re.search(r"\(([^)]*)\)$", cell)
                    if not match:
                        continue
                    faculty_list = [part.strip() for part in match.group(1).split(",")]
                    if old_code not in faculty_list:
                        continue
                    updated_faculty = [new_code if part == old_code else part for part in faculty_list]
                    table[row_index][col_index] = cell[:match.start()] + "(" + ", ".join(updated_faculty) + ")"
    save_json(timetables, "data/timetable.json")


def rename_program(old_program, new_program):
    if old_program == new_program or not old_program:
        return
    if new_program in timetables:
        return
    if old_program in timetables:
        timetables[new_program] = timetables.pop(old_program)
    if old_program in subjects:
        subjects[new_program] = subjects.pop(old_program)
    if old_program in subject_faculty_map:
        subject_faculty_map[new_program] = subject_faculty_map.pop(old_program)
    if old_program in subject_metadata:
        subject_metadata[new_program] = subject_metadata.pop(old_program)
    save_json(timetables, "data/timetable.json")
    save_json(subjects, "data/subjects.json")
    save_json(subject_faculty_map, "data/subject_faculty_map.json")
    save_json(subject_metadata, "data/subject_metadata.json")


def rename_semester(program, old_semester, new_semester):
    if not program or old_semester == new_semester or not old_semester:
        return
    if new_semester in timetables.get(program, {}):
        return
    if old_semester in timetables.get(program, {}):
        timetables[program][new_semester] = timetables[program].pop(old_semester)
    if old_semester in subjects.get(program, {}):
        subjects[program][new_semester] = subjects[program].pop(old_semester)
    if old_semester in subject_faculty_map.get(program, {}):
        subject_faculty_map[program][new_semester] = subject_faculty_map[program].pop(old_semester)
    if old_semester in subject_metadata.get(program, {}):
        subject_metadata[program][new_semester] = subject_metadata[program].pop(old_semester)
    save_json(timetables, "data/timetable.json")
    save_json(subjects, "data/subjects.json")
    save_json(subject_faculty_map, "data/subject_faculty_map.json")
    save_json(subject_metadata, "data/subject_metadata.json")


def build_subject_table(program, semester):
    rows = []
    map_rows = subject_faculty_map.get(program, {}).get(semester, {})
    meta_rows = subject_metadata.get(program, {}).get(semester, {})
    for code, name in sorted(subjects.get(program, {}).get(semester, {}).items()):
        metadata = meta_rows.get(code, {})
        rows.append({
            "Code": code,
            "Subject Name": name,
            "Faculty Codes": ", ".join(map_rows.get(code, [])),
            "Hours/Week": metadata.get("hours_per_week", 0),
            "Common": "Yes" if metadata.get("is_common", False) else "No"
        })
    return pd.DataFrame(rows)


def is_common_subject(program, semester, subject_key):
    return bool(subject_metadata.get(program, {}).get(semester, {}).get(subject_key, {}).get("is_common", False))


def build_common_subject_summary():
    rows = []
    for program, sems in subject_metadata.items():
        for semester, metas in sems.items():
            for code, meta in metas.items():
                if not meta.get("is_common", False):
                    continue
                name = subjects.get(program, {}).get(semester, {}).get(code, "")
                rows.append({
                    "Program": program,
                    "Semester": semester,
                    "Code": code,
                    "Subject Name": name,
                    "Common": "Yes"
                })
    rows.sort(key=lambda r: (r["Program"], r["Semester"], r["Code"]))
    return pd.DataFrame(rows)


# ------------------ Clash Checker (NO REGEX) ------------------
def check_clashes(timetables, subject_faculty_map):
    faculty_schedule = {}
    clashes = []

    for program, semesters in timetables.items():
        for semester, table in semesters.items():
            for row in table:
                time_slot = row[0]
                for day_idx, subject_code in enumerate(row[1:], start=1):

                    if not subject_code or subject_code in ["Lunch break", "Library/Mentoring"]:
                        continue

                    subject_key = subject_code.split()[0].strip()
                    faculty_list = subject_faculty_map \
                        .get(program, {}) \
                        .get(semester, {}) \
                        .get(subject_key, [])
                    subject_common = is_common_subject(program, semester, subject_key)

                    for faculty in faculty_list:
                        key = (faculty, day_idx, time_slot)
                        if key in faculty_schedule:
                            prev = faculty_schedule[key]
                            prev_common = is_common_subject(prev["program"], prev["semester"], prev["subject"].split()[0].strip())
                            if prev_common and subject_common:
                                continue
                            clashes.append({
                                "faculty": faculty,
                                "time": time_slot,
                                "program1": prev["program"],
                                "semester1": prev["semester"],
                                "subject1": prev["subject"],
                                "program2": program,
                                "semester2": semester,
                                "subject2": subject_code
                            })
                        else:
                            faculty_schedule[key] = {
                                "program": program,
                                "semester": semester,
                                "subject": subject_code
                            }
    return clashes

# ------------------ Admin UI ------------------
def show_admin():
    st.title("📋 Timetable Admin Panel")

    st.markdown(
        "<div style='padding:18px; border-radius:14px; background:#f0f7ff; border-left:6px solid #0b69ff; margin-bottom:24px;'>"
        "<strong style='font-size:22px;'>Admin Editor</strong><br>"
        "<span style='color:#33475b;'>Only the three main sections are shown: faculties, subjects for the selected program/semester, timetable editing, and clash checker.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    all_programs = sorted(set(timetables) | set(subjects))
    if not all_programs:
        st.warning("No programs available. Please add programs in the data files.")
        return

    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        program = st.selectbox("Selected Program", all_programs, key="admin_program")
    with header_col2:
        semester_type = st.radio(
            "Semester type",
            ["Odd", "Even"],
            index=0,
            horizontal=True,
            key="semester_parity"
        )

    available_semesters = [
        sem for sem in get_program_semesters(program)
        if semester_parity_matches(sem, semester_type)
    ]
    if not available_semesters:
        st.warning(f"No {semester_type.lower()} semesters found for {program}.")
        return

    semester = st.selectbox("Selected Semester", available_semesters, key="admin_semester")

    table = timetables.get(program, {}).get(semester, [])
    if not table:
        table = [["", "", "", "", "", ""]]
    day_names = ["Time"] + [f"DAY {i+1}" for i in range(len(table[0]) - 1)]
    timetable_df = pd.DataFrame(table, columns=day_names)

    st.markdown(
        "<div style='padding:16px; border-radius:12px; background:#e8f5e9; border:1px solid #c8e6c9; margin-top:20px;'>"
        "<h3 style='margin:0; color:#256029;'>1. Edit Faculties</h3>"
        "<p style='margin:4px 0 0; color:#2f4f4f;'>Add or update faculty codes and names used across all programs.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    fac_col_left, fac_col_right = st.columns([2, 1])
    with fac_col_left:
        existing_faculty_codes = sorted(faculties.keys())
        faculty_selection = st.selectbox(
            "Faculty Code",
            ["NEW FACULTY"] + existing_faculty_codes,
            key="faculty_manager_selection"
        )
        faculty_code_default = "" if faculty_selection == "NEW FACULTY" else faculty_selection
        faculty_name_default = "" if faculty_selection == "NEW FACULTY" else faculties.get(faculty_selection, "")

        faculty_code = st.text_input(
            "Code",
            value=faculty_code_default,
            key="faculty_manager_code"
        ).strip()
        faculty_name = st.text_input(
            "Name",
            value=faculty_name_default,
            key="faculty_manager_name"
        ).strip()

        action_col1, action_col2 = st.columns([2, 1])
        with action_col1:
            if st.button("Save Faculty", key="save_faculty_btn"):
                if not faculty_code or not faculty_name:
                    st.warning("Provide both faculty code and faculty name.")
                elif faculty_selection != "NEW FACULTY" and faculty_code != faculty_selection and faculty_code in faculties:
                    st.error("This faculty code already exists.")
                else:
                    if faculty_selection != "NEW FACULTY" and faculty_code != faculty_selection:
                        faculties[faculty_code] = faculty_name
                        del faculties[faculty_selection]
                        for prog, sems in subject_faculty_map.items():
                            for sem, mapping in sems.items():
                                for subj, faculty_list in mapping.items():
                                    subject_faculty_map[prog][sem][subj] = [faculty_code if f == faculty_selection else f for f in faculty_list]
                        update_timetable_faculty_code(faculty_selection, faculty_code)
                    else:
                        faculties[faculty_code] = faculty_name
                    save_all_state()
                    st.success("✅ Faculty saved.")
        with action_col2:
            if faculty_selection != "NEW FACULTY" and st.button("Delete Faculty", key="delete_faculty_btn"):
                delete_faculty(faculty_selection)
                st.success("✅ Faculty deleted.")
                st.experimental_rerun()

    with fac_col_right:
        st.markdown("#### Faculty list")
        st.dataframe(
            pd.DataFrame(
                [{"Code": code, "Name": name} for code, name in sorted(faculties.items())]
            ),
            use_container_width=True,
        )

    st.markdown(
        "<div style='padding:16px; border-radius:12px; background:#fff8e1; border:1px solid #ffe082; margin-top:24px;'>"
        "<h3 style='margin:0; color:#8a6d3b;'>2. Edit Subjects for Selected Program/Semester</h3>"
        "<p style='margin:4px 0 0; color:#5f4d32;'>Update subject code, name, faculty mapping, hours per week, and mark if the subject is common.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        existing_codes = sorted(subjects.get(program, {}).get(semester, {}).keys())
        subject_selection = st.selectbox(
            "Subject",
            ["NEW SUBJECT"] + existing_codes,
            key="subject_editor_selection"
        )

        original_code = subject_selection if subject_selection != "NEW SUBJECT" else ""
        code_value = st.text_input(
            "Subject Code",
            value="" if original_code == "" else original_code,
            key="subject_editor_code"
        ).strip()
        subject_name_value = st.text_input(
            "Subject Name",
            value=subjects.get(program, {}).get(semester, {}).get(original_code, "") if original_code else "",
            key="subject_editor_name"
        ).strip()

        current_faculty = subject_faculty_map.get(program, {}).get(semester, {}).get(original_code, []) if original_code else []
        faculty_codes = st.multiselect(
            "Assigned Faculty",
            options=sorted(faculties.keys()),
            default=current_faculty,
            key="subject_editor_faculty"
        )

        metadata = get_subject_metadata(program, semester, original_code) if original_code else {}
        hours_per_week = st.number_input(
            "Hours per week",
            min_value=0,
            value=int(metadata.get("hours_per_week", 0)),
            step=1,
            key="subject_editor_hours"
        )

        is_common = st.checkbox(
            "Mark as common subject",
            value=bool(metadata.get("is_common", False)),
            key="subject_editor_is_common"
        )

        action_col1, action_col2 = st.columns([2, 1])
        with action_col1:
            if st.button("Save Subject", key="save_subject_detail_btn"):
                if not code_value:
                    st.warning("Enter a subject code.")
                elif not subject_name_value:
                    st.warning("Enter a subject name.")
                else:
                    ensure_nested_dict(subjects, program, semester)
                    ensure_nested_dict(subject_faculty_map, program, semester)
                    ensure_nested_dict(subject_metadata, program, semester)

                    if original_code and original_code != code_value:
                        if code_value in subjects[program][semester]:
                            st.error(f"Subject code {code_value} already exists.")
                        else:
                            subjects[program][semester][code_value] = subjects[program][semester].pop(original_code)
                            subject_faculty_map[program][semester][code_value] = subject_faculty_map[program][semester].pop(original_code, [])
                            subject_metadata[program][semester][code_value] = subject_metadata[program][semester].pop(original_code, {})
                            update_timetable_subject_code(program, semester, original_code, code_value)
                            subjects[program][semester][code_value] = subject_name_value
                            st.success(f"✅ Renamed {original_code} to {code_value} and updated timetable entries.")
                    else:
                        if code_value in subjects[program][semester] and not original_code:
                            st.error(f"Subject code {code_value} already exists.")
                        else:
                            subjects[program][semester][code_value] = subject_name_value

                    subject_faculty_map[program][semester][code_value] = normalize_faculty_codes(faculty_codes)
                    subject_metadata[program][semester][code_value] = {
                        "hours_per_week": int(hours_per_week),
                        "is_common": bool(is_common)
                    }

                    save_all_state()
                    st.success("✅ Subject saved.")

        with action_col2:
            if original_code and st.button("Delete Subject", key="delete_subject_btn"):
                delete_subject(program, semester, original_code)
                st.success("✅ Subject deleted.")
                st.experimental_rerun()

        st.markdown("#### Subject summary for selected semester")
        st.dataframe(
            build_subject_table(program, semester),
            use_container_width=True,
        )

        common_df = build_common_subject_summary()
        if not common_df.empty:
            st.markdown("#### Common subjects across programs")
            st.dataframe(common_df, use_container_width=True)

    st.markdown(
        "<div style='padding:16px; border-radius:12px; background:#f3e5f5; border:1px solid #e1bee7; margin-top:24px;'>"
        "<h3 style='margin:0; color:#6a1b9a;'>3. Edit Timetable</h3>"
        "<p style='margin:4px 0 0; color:#4a235a;'>Update the selected program and semester timetable directly in the grid.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("Use subject codes in the timetable cells, e.g. `P1 (RL)`. Leave breaks blank or use `Lunch break`.")
    edited_df = st.data_editor(
        timetable_df,
        num_rows="fixed",
        use_container_width=True,
        key="selected_timetable_editor"
    )
    if st.button("Save Timetable", key="save_timetable_btn"):
        save_updated_timetable(program, semester, edited_df)
        st.success("✅ Timetable saved successfully")

    st.markdown(
        "<div style='padding:16px; border-radius:12px; background:#fff3e0; border:1px solid #ffcc80; margin-top:24px;'>"
        "<h3 style='margin:0; color:#e65100;'>4. Clash Checker</h3>"
        "<p style='margin:4px 0 0; color:#5d4037;'>Validate faculty assignments across program/semester timetables.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if st.button("Check Clashes", key="admin_clash_btn"):
        clashes = check_clashes(timetables, subject_faculty_map)
        if clashes:
            st.error("❌ Faculty clashes found")
            for c in clashes:
                st.write(
                    f"👤 **{c['faculty']}** ⛔ {c['time']} | "
                    f"{c['program1']} {c['semester1']} ({c['subject1']}) "
                    f"vs {c['program2']} {c['semester2']} ({c['subject2']})"
                )
        else:
            st.success("✅ No clashes found")


if __name__ == "__main__":
    show_admin()
