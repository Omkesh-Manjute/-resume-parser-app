import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(layout="wide")

# =============================
# DATABASE
# =============================

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT,
phone TEXT,
skills TEXT,
file_path TEXT
)
""")

conn.commit()

UPLOAD_FOLDER = "resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =============================
# SIDEBAR FILTER
# =============================

st.sidebar.title("🔎 Filters")

filter_name = st.sidebar.text_input("Candidate Name")
filter_email = st.sidebar.text_input("Email")
filter_skill = st.sidebar.text_input("Boolean Skill Search")

delete_mode = st.sidebar.checkbox("Enable Delete Mode")

# =============================
# FILE UPLOAD SECTION
# =============================

st.title("🔥 ATS PRO Recruiter Dashboard")

st.subheader("Upload Resume")

uploaded_file = st.file_uploader("", type=["pdf","docx"])

if uploaded_file:

    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

    with open(file_path,"wb") as f:
        f.write(uploaded_file.getbuffer())

    # Fake parser (replace later with AI)
    name = uploaded_file.name.replace(".pdf","").replace(".docx","")
    email = "demo@email.com"
    phone = "9999999999"
    skills = "python, sql, azure"

    cursor.execute("""
    INSERT INTO candidates(name,email,phone,skills,file_path)
    VALUES(?,?,?,?,?)
    """,(name,email,phone,skills,file_path))

    conn.commit()

    st.success("Uploaded & Saved")

# JD Upload Always Visible
st.subheader("Upload JD")

jd_file = st.file_uploader("", key="jd_upload")

# =============================
# LOAD DATA
# =============================

df = pd.read_sql("SELECT * FROM candidates", conn)

# FILTERS
if filter_name:
    df = df[df["name"].str.contains(filter_name, case=False)]

if filter_email:
    df = df[df["email"].str.contains(filter_email, case=False)]

if filter_skill:
    df = df[df["skills"].str.contains(filter_skill, case=False)]

# =============================
# MAIN UI (ATS STYLE)
# =============================

left, right = st.columns([2,3])

with left:

    st.subheader("Candidates")

    for index,row in df.iterrows():

        c1,c2 = st.columns([6,1])

        with c1:
            if st.button(row["name"], key=f"candidate_{row['id']}"):
                st.session_state["selected_resume"] = row["file_path"]

        with c2:
            if delete_mode:
                if st.button("❌", key=f"delete_{row['id']}"):
                    cursor.execute("DELETE FROM candidates WHERE id=?",(row["id"],))
                    conn.commit()
                    st.rerun()

with right:

    st.subheader("Resume Viewer")

    if "selected_resume" in st.session_state:

        file_path = st.session_state["selected_resume"]

        if file_path.endswith(".pdf"):

            with open(file_path,"rb") as f:
                pdf = f.read()

            st.download_button("Open Resume", pdf)

        else:
            st.info("DOCX preview coming soon")

    else:
        st.info("Click candidate to view resume")
