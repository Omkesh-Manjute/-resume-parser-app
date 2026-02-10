import streamlit as st
import pandas as pd
import sqlite3
import os
import docx2txt

st.set_page_config(layout="wide")

# =====================
# DATABASE
# =====================

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

UPLOAD_FOLDER="resumes"
os.makedirs(UPLOAD_FOLDER,exist_ok=True)

# =====================
# SIDEBAR FILTER
# =====================

st.sidebar.title("🔎 Filters")

filter_name=st.sidebar.text_input("Candidate Name")
filter_email=st.sidebar.text_input("Email")
filter_skill=st.sidebar.text_input("Skills Boolean")

delete_mode=st.sidebar.checkbox("Enable Delete Mode")

# =====================
# UPLOAD SECTION
# =====================

st.title("🔥 ATS PRO Recruiter Dashboard")

uploaded_file=st.file_uploader("Upload Resume",type=["pdf","docx"])

if uploaded_file:

    file_path=os.path.join(UPLOAD_FOLDER,uploaded_file.name)

    # prevent duplicate insert
    cursor.execute("SELECT * FROM candidates WHERE file_path=?",(file_path,))
    exist=cursor.fetchone()

    if not exist:

        with open(file_path,"wb") as f:
            f.write(uploaded_file.getbuffer())

        name=uploaded_file.name.replace(".pdf","").replace(".docx","")
        email="demo@email.com"
        phone="9999999999"
        skills="python, sql, azure"

        cursor.execute("""
        INSERT INTO candidates(name,email,phone,skills,file_path)
        VALUES(?,?,?,?,?)
        """,(name,email,phone,skills,file_path))

        conn.commit()

        st.success("Uploaded & Saved")

# =====================
# LOAD DATA
# =====================

df=pd.read_sql("SELECT * FROM candidates",conn)

if filter_name:
    df=df[df["name"].str.contains(filter_name,case=False)]

if filter_email:
    df=df[df["email"].str.contains(filter_email,case=False)]

if filter_skill:
    df=df[df["skills"].str.contains(filter_skill,case=False)]

# =====================
# ATS LAYOUT
# =====================

left,right=st.columns([2,3])

with left:

    st.subheader("Candidates")

    for _,row in df.iterrows():

        container=st.container()

        with container:

            c1,c2=st.columns([6,1])

            # UNIQUE KEY FIX
            if c1.button(
                f"{row['name']} | {row['email']} | {row['phone']}",
                key=f"candidate_{row['id']}"
            ):
                st.session_state["selected_candidate"]=row.to_dict()

            if delete_mode:
                if c2.button("❌",key=f"delete_{row['id']}"):
                    cursor.execute("DELETE FROM candidates WHERE id=?",(row["id"],))
                    conn.commit()
                    st.rerun()

# =====================
# RIGHT PANEL
# =====================

with right:

    st.subheader("Candidate Details")

    if "selected_candidate" in st.session_state:

        data=st.session_state["selected_candidate"]

        st.write("### Name:",data["name"])
        st.write("Email:",data["email"])
        st.write("Phone:",data["phone"])
        st.write("Skills:",data["skills"])

        st.divider()

        st.subheader("Resume Preview")

        file_path=data["file_path"]

        if file_path.endswith(".docx"):

            text=docx2txt.process(file_path)
            st.text(text[:2000])

        elif file_path.endswith(".pdf"):

            with open(file_path,"rb") as f:
                st.download_button("Open PDF",f,"resume.pdf")

    else:
        st.info("Select candidate from left panel")
