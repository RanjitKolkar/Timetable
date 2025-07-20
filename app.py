import streamlit as st

st.set_page_config(layout="wide")  # ✅ Must be the first Streamlit command

from components.viewer import show_timetable_viewer
from components.admin import show_timetable_editor
from components.faculty_view import show_faculty_view  # 👈 Import after setting config
from components.load_distribution import show_faculty_load_distribution  # 👈 Add this import

st.title("📚 NFSU Goa Timetable Manager")

tabs = st.tabs(["📘 View Timetable", "👨‍🏫 Faculty View", "📊 Load Summary", "🛠️ Admin Panel"])

with tabs[0]:
    show_timetable_viewer()
with tabs[1]:
    show_faculty_view()
with tabs[2]:
    show_faculty_load_distribution()  # 👈 New tab added
with tabs[3]:
    show_timetable_editor()
