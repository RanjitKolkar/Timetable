# data/master.py
import json
from pathlib import Path

def load_json(filename):
    path = Path(__file__).parent / filename
    with open(path, "r") as f:
        return json.load(f)

def save_json(filename, data):
    path = Path(__file__).parent / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

faculties = load_json("faculties.json")
subjects = load_json("subjects.json")
timetables = load_json("timetable.json")
