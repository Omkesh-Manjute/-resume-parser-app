import streamlit as st
import sqlite3
import pandas as pd
import os
import base64

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("ats.db", check_same_thread=False)
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS jobs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
description TEXT
)
""")

conn.commit()

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(layout="wide")

st.title("🔥 ATS PRO Recruiter Dashboard")

# =========================
# SIDEBAR FILTERS
# =========================

st.sidebar.header("🔎 Filters")

name_filter = st.sidebar.text_input("Candidate Name")
email_filter = st.sidebar.text_input("Email")
boolean_filter = st.sidebar.text_input("Boolean Skill Search")

delete_mode = st.sidebar.checkbox("Enable Delete Mode")

# =========================
# UPLOAD RESUME
# =========================

st.subheader("Upload Resume")

upload = st.file_uploader("Upload Resume", type=["pdf","docx"], key="resume")

if upload:

    save_path = os.path.join("uploads", upload.name)

    os.makedirs("uploads", exist_ok=True)

    with open(save_path,"wb") as f:
        f.write(upload.read())

    # Dummy parsing (replace later AI parsing)
    name = upload.name.split(".")[0]

    cursor.execute("""
    INSERT INTO candidates(name,email,phone,skills,file_path)
    VALUES(?,?,?,?,?)
    """,(name,"demo@email.com","0000000000","python, sql",save_path))

    conn.commit()

    st.success("Uploaded & Saved")


# =========================
# JOB DESCRIPTION UPLOAD
# =========================

st.subheader("Upload JD")

jd = st.file_uploader("Upload Job Description", key="jd")

if jd:

    jd_text = jd.read().decode(errors="ignore")

    cursor.execute("INSERT INTO jobs(title,description) VALUES (?,?)",
                   ("JD Upload", jd_text))

    conn.commit()

    st.success("JD Saved")


# =========================
# LOAD DATA
# =========================

df = pd.read_sql_query("SELECT * FROM candidates", conn)

# =========================
# FILTER LOGIC
# =========================

filtered = df.copy()

if name_filter:
    filtered = filtered[filtered["name"].str.contains(name_filter, case=False)]

if email_filter:
    filtered = filtered[filtered["email"].str.contains(email_filter, case=False)]

if boolean_filter:

    # simple AND boolean logic
    words = boolean_filter.split()

    for w in words:
        filtered = filtered[filtered["skills"].str.contains(w, case=False)]

# =========================
# LAYOUT
# =========================

col1, col2 = st.columns([2,3])

# LEFT = Candidate list
with col1:

    st.subheader("Candidates")

    for index,row in filtered.iterrows():

        c1,c2 = st.columns([4,1])

        with c1:

            if st.button(row["name"], key=f"name_{row['id']}"):
                st.session_state["selected_resume"] = row["file_path"]

        with c2:

            if delete_mode:
                if st.button("❌", key=f"delete_{row['id']}"):
                    cursor.execute("DELETE FROM candidates WHERE id=?",(row["id"],))
                    conn.commit()
                    st.rerun()

# RIGHT = Resume Viewer
with col2:

    st.subheader("Resume Viewer")

    if "selected_resume" in st.session_state:

        file_path = st.session_state["selected_resume"]

        if os.path.exists(file_path):

            with open(file_path,"rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode()

            pdf_display = f'''
            <iframe src="data:application/pdf;base64,{base64_pdf}"
            width="100%" height="700"></iframe>
            '''

            st.markdown(pdf_display, unsafe_allow_html=True)

        else:
            st.info("Resume not found")
