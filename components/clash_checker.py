import re
from difflib import SequenceMatcher


def extract_faculties_from_cell(cell):
    return re.findall(r"\((.*?)\)", cell)


def extract_subject_from_cell(cell):
    return cell.split(" ")[0] if cell else ""


def is_similar_subject(subj1, subj2, threshold=0.85):
    return SequenceMatcher(None, subj1.lower(), subj2.lower()).ratio() >= threshold


def find_all_clashes_and_common_subjects(timetables):
    clashes = []
    common_subjects = []

    for prog1, sems1 in timetables.items():
        for sem1, table1 in sems1.items():
            for prog2, sems2 in timetables.items():
                for sem2, table2 in sems2.items():
                    # Avoid duplicate checks
                    if (prog1, sem1) > (prog2, sem2):
                        continue

                    for row1, row2 in zip(table1, table2):
                        time1, *cells1 = row1
                        time2, *cells2 = row2
                        if time1 != time2:
                            continue

                        for day_index, (cell1, cell2) in enumerate(zip(cells1, cells2)):
                            faculties1 = extract_faculties_from_cell(cell1)
                            faculties2 = extract_faculties_from_cell(cell2)
                            common = set(faculties1).intersection(faculties2)

                            if common:
                                subj1 = extract_subject_from_cell(cell1)
                                subj2 = extract_subject_from_cell(cell2)

                                if is_similar_subject(subj1, subj2):
                                    common_subjects.append(f"{subj1} ≈ {subj2} at {time1} ({prog1}-{sem1} & {prog2}-{sem2})")
                                else:
                                    for f in common:
                                        clashes.append(f"Faculty {f} assigned in both {prog1}-{sem1} and {prog2}-{sem2} at {time1}")

    return clashes, common_subjects
