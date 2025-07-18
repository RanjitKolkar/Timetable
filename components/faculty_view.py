import streamlit as st
import pandas as pd
import json
from collections import defaultdict
from data.timetable import days, time_slots  # Ensure these are defined

# --- Load JSON data ---
with open("data/timetable.json") as f:
    timetables = json.load(f)
with open("data/faculties.json") as f:
    faculties = json.load(f)

# --- Main UI ---
def show_faculty_view():
    st.title("👨‍🏫 Faculty Timetable & Load Viewer")

    faculty_code = st.selectbox("Select Faculty Code", sorted(faculties.keys()))
    st.markdown(f"**Faculty Name:** {faculties.get(faculty_code, 'Unknown')}")

    detailed_load = []
    consolidated = [[slot] + [""] * (len(days) - 1) for slot in time_slots]

    # Go through all programs & semesters
    for program, semesters in timetables.items():
        for semester, timetable in semesters.items():
            filtered_rows = []

            for i, row in enumerate(timetable):
                new_row = [row[0]]
                for j in range(1, len(row)):
                    cell = row[j]
                    if f"({faculty_code})" in cell:
                        subject_code = cell.split()[0]
                        new_row.append(cell)
                        consolidated[i][j] = cell
                        detailed_load.append({
                            "Program": program,
                            "Semester": semester,
                            "Subject Code": subject_code,
                            "Hour Slot": row[0]
                        })
                    else:
                        new_row.append("")
                filtered_rows.append(new_row)

            df = pd.DataFrame(filtered_rows, columns=days)
            if df.iloc[:, 1:].replace("", pd.NA).dropna(how='all').shape[0] > 0:
                st.markdown(f"### 📘 {program} - {semester}")
                st.dataframe(df, use_container_width=True)

    # --- Consolidated View ---
    st.markdown("## 📅 Consolidated Timetable")
    df_consolidated = pd.DataFrame(consolidated, columns=days)
    st.dataframe(df_consolidated, use_container_width=True)
    import matplotlib.pyplot as plt
    from io import BytesIO

   
    # --- Generate downloadable PNG ---
    def create_timetable_image(df, faculty_code):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.axis('tight')
        ax.axis('off')
        table_data = [df.columns.tolist()] + df.values.tolist()
        table = ax.table(cellText=table_data, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        plt.title(f"Consolidated Timetable for {faculty_code}", fontsize=14, weight='bold')

        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf

    image_buf = create_timetable_image(df_consolidated, faculty_code)

    # --- Download Button ---
    st.download_button(
        label="📥 Download PNG",
        data=image_buf,
        file_name=f"{faculty_code}_timetable.png",
        mime="image/png"
    )

    # --- Load Summary ---
    st.markdown("## ⏱️ Load Distribution")
    if detailed_load:
        df_load = pd.DataFrame(detailed_load)
        summary = df_load.groupby(["Program", "Semester", "Subject Code"]).size().reset_index(name="Hours")
        st.table(summary)
        total_hours = summary["Hours"].sum()
        st.markdown(f"**Total Teaching Load: `{total_hours}` hours/week**")
    else:
        st.info("No teaching assignments found for this faculty.")


# For direct run
if __name__ == "__main__":
    show_faculty_view()
