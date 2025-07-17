import json
from collections import defaultdict

# Load JSON files
with open("data/timetable.json") as f:
    timetables = json.load(f)

with open("data/subjects.json") as f:
    subjects = json.load(f)

# Function to extract subject codes from timetable
def extract_subject_codes(timetable):
    subject_codes = set()
    for row in timetable:
        for cell in row[1:]:
            cell = cell.strip()
            if cell and "Lunch" not in cell and "Library" not in cell:
                code = cell.split()[0]  # e.g., 'P1' from 'P1 (RJ)'
                subject_codes.add(code)
    return subject_codes

# Check all programs and semesters
for program, semesters in timetables.items():
    for sem, timetable in semesters.items():
        used_codes = extract_subject_codes(timetable)
        defined_codes = set(subjects.get(program, {}).get(sem, {}).keys())

        missing = used_codes - defined_codes
        extra = defined_codes - used_codes

        if missing:
            print(f"[❌] Missing in subjects.json for {program} - {sem}: {sorted(missing)}")
        else:
            print(f"[✅] All subject codes are defined for {program} - {sem}.")

        if extra:
            print(f"[⚠️] Extra subject codes in subjects.json for {program} - {sem} (not used in timetable): {sorted(extra)}")
