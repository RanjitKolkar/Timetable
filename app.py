import streamlit as st
from components.viewer import show_timetable_viewer
from components.admin import show_timetable_editor
from components.faculty_view import show_faculty_view  # 👈 Import this

st.set_page_config(layout="wide")
st.title("📚 NFSU Goa Timetable Manager")

tabs = st.tabs(["📘 View Timetable", "🛠️ Admin Panel", "👨‍🏫 Faculty View"])  # 👈 Added new tab
with tabs[0]:
    show_timetable_viewer()
with tabs[1]:
    show_timetable_editor()
with tabs[2]:  # 👈 Faculty View logic
    show_faculty_view()
