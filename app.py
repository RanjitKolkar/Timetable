import streamlit as st

# ✅ Must be the very first Streamlit command
st.set_page_config(
    layout="wide",
    page_title="NFSU Goa Timetable Manager 2026-27",
    page_icon="📚"
)

# ------------------ Import Components ------------------
from components.viewer import show_viewer            # UPDATED name
from components.admin import show_admin               # UPDATED name
from components.faculty_view import show_faculty_view
from components.load_distribution import show_faculty_load_distribution

# ------------------ App Header ------------------
st.title("📚 NFSU Goa Timetable Manager 2026-27")

st.markdown(
    "<div style='font-size: 0.8em; color: gray;'>"
    "Version 1.0.0 • Academic Year 2026-27"
    "</div>",
    unsafe_allow_html=True
)

# ------------------ Tabs ------------------
tabs = st.tabs([
    "📘 View Timetable",
    "👨‍🏫 Faculty View",
    "📊 Load Summary",
    "🛠️ Admin Panel"
])

# ------------------ Tab Routing ------------------
with tabs[0]:
    show_viewer()                     # ⬅ updated viewer (subject-code based)

with tabs[1]:
    show_faculty_view()               # ⬅ faculty timetable (mapping-based)

with tabs[2]:
    show_faculty_load_distribution()  # ⬅ load from subject_faculty_map + timetable

with tabs[3]:
    show_admin()                      # ⬅ updated admin (no regex, no hardcoding)
