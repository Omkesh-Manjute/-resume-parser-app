import streamlit as st
import pandas as pd
import sqlite3
import os
import re

# ===============================
# PAGE CONFIG
# ===============================

st.set_page_config(layout="wide")

st.title("🔥 ATS PRO Resume Dashboard")

UPLOAD_FOLDER = "resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===============================
# DATABASE
# ===============================

conn = sqlite3.connect("candidates.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates(
name TEXT,
email TEXT,
phone TEXT,
skills TEXT,
file_path TEXT
)
""")

conn.commit()

# ===============================
# SIMPLE RESUME PARSER
# ===============================

def extract_email(text):
    match = re.findall(r'\S+@\S+', text)
    return match[0] if match else ""

def extract_phone(text):
    match = re.findall(r'\+?\d[\d -]{8,12}', text)
    return match[0] if match else ""

def extract_name(filename):
    return filename.split(".")[0]

def extract_skills(text):
    skills_list = ["python","sql","java","aws","azure","data","etl"]
    found = []
    for skill in skills_list:
        if skill.lower() in text.lower():
            found.append(skill)
    return ",".join(found)

# ===============================
# SIDEBAR FILTERS
# ===============================

with st.sidebar:

    st.header("🔎 Filters")

    name_filter = st.text_input("Candidate Name")

    email_filter = st.text_input("Email")

    skill_filter = st.text_input("Skills / Boolean")

    delete_mode = st.checkbox("Enable Delete Mode")

# ===============================
# UPLOAD SECTION
# ===============================

st.subheader("Upload Resumes")

uploaded_files = st.file_uploader(
    "Upload",
    accept_multiple_files=True,
    type=["pdf","docx","txt"]
)

if uploaded_files:

    for file in uploaded_files:

        path = os.path.join(UPLOAD_FOLDER,file.name)

        with open(path,"wb") as f:
            f.write(file.getbuffer())

        text = file.name  # demo parsing

        name = extract_name(file.name)
        email = extract_email(text)
        phone = extract_phone(text)
        skills = extract_skills(text)

        cursor.execute(
            "INSERT INTO candidates VALUES (?,?,?,?,?)",
            (name,email,phone,skills,path)
        )

        conn.commit()

    st.success("Uploaded & Saved")

# ===============================
# LOAD DATA
# ===============================

df = pd.read_sql_query("SELECT * FROM candidates", conn)

# FILTER APPLY

if name_filter:
    df = df[df["name"].str.contains(name_filter, case=False)]

if email_filter:
    df = df[df["email"].str.contains(email_filter, case=False)]

if skill_filter:
    df = df[df["skills"].str.contains(skill_filter, case=False)]

# ===============================
# SESSION STATE
# ===============================

if "selected_candidate" not in st.session_state:
    st.session_state.selected_candidate = None

# ===============================
# ATS LAYOUT
# ===============================

left, right = st.columns([1,2])

# LEFT PANEL (Candidate List)

with left:

    st.subheader("Candidates")

    for i,row in df.iterrows():

        colA,colB = st.columns([3,1])

        with colA:

            if st.button(row["name"], key=row["file_path"]):

                st.session_state.selected_candidate = row

        if delete_mode:

            with colB:

                if st.button("❌", key="del"+row["file_path"]):

                    cursor.execute(
                        "DELETE FROM candidates WHERE file_path=?",
                        (row["file_path"],)
                    )

                    conn.commit()
                    st.rerun()

# RIGHT PANEL (Preview)

with right:

    st.subheader("Candidate Preview")

    if st.session_state.selected_candidate is not None:

        candidate = st.session_state.selected_candidate

        st.write("Name:", candidate["name"])
        st.write("Email:", candidate["email"])
        st.write("Phone:", candidate["phone"])
        st.write("Skills:", candidate["skills"])

        if os.path.exists(candidate["file_path"]):

            with open(candidate["file_path"],"rb") as f:

                st.download_button(
                    "Preview Resume",
                    f,
                    disabled=True
                )

    else:

        st.info("Select candidate to preview")
