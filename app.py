import streamlit as st
import pandas as pd
import sqlite3
import pdfplumber
from docx import Document
import uuid

st.set_page_config(layout="wide")

# ================= DATABASE =================

conn = sqlite3.connect("database.db",check_same_thread=False)
c=conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS candidates(
id TEXT,
name TEXT,
email TEXT,
phone TEXT,
skills TEXT,
content TEXT
)
""")

conn.commit()

# ================= FUNCTIONS =================

def extract_text(file):

    if file.name.endswith(".pdf"):
        text=""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text+=page.extract_text() or ""
        return text

    if file.name.endswith(".docx"):
        doc=Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    return ""

def parse_resume(text):

    # basic demo parsing (can upgrade later)
    email="demo@email.com"
    phone="9999999999"

    name=text.split("\n")[0] if text else "Unknown"

    skills="python, sql, azure"

    return name,email,phone,skills

# ================= SESSION =================

if "selected_id" not in st.session_state:
    st.session_state.selected_id=None

# ================= SIDEBAR FILTER =================

st.sidebar.title("🔎 Filters")

name_filter=st.sidebar.text_input("Candidate Name")

email_filter=st.sidebar.text_input("Email")

boolean_filter=st.sidebar.text_input("Boolean Skill Search")

delete_mode=st.sidebar.checkbox("Enable Delete Mode")

# ================= UPLOAD AREA =================

st.title("🔥 ATS MONSTER RECRUITER MODE")

col_upload,col_jd=st.columns(2)

with col_upload:

    st.subheader("Upload Resume")

    file=st.file_uploader("",type=["pdf","docx"])

    if file:

        text=extract_text(file)

        name,email,phone,skills=parse_resume(text)

        uid=str(uuid.uuid4())

        c.execute("INSERT INTO candidates VALUES (?,?,?,?,?,?)",
                  (uid,name,email,phone,skills,text))

        conn.commit()

        st.success("Uploaded & Saved")

with col_jd:

    st.subheader("Upload JD (future matching)")
    st.file_uploader("",key="jd")

# ================= LOAD DATA =================

df=pd.read_sql("SELECT * FROM candidates",conn)

# ================= FILTER LOGIC =================

if name_filter:
    df=df[df["name"].str.contains(name_filter,case=False)]

if email_filter:
    df=df[df["email"].str.contains(email_filter,case=False)]

if boolean_filter:
    df=df[df["skills"].str.contains(boolean_filter,case=False)]

# ================= MAIN UI =================

left,right=st.columns([1.3,2])

# ===== LEFT TABLE (MONSTER STYLE) =====

with left:

    st.subheader("Candidates")

    if df.empty:
        st.info("No candidates")
    else:

        for i,row in df.iterrows():

            c1,c2=st.columns([6,1])

            with c1:

                if st.button(
                    f"👉 {row['name']} | {row['email']} | {row['phone']}",
                    key=row["id"]
                ):
                    st.session_state.selected_id=row["id"]

            with c2:

                if delete_mode:
                    if st.button("❌",key="del"+row["id"]):

                        c.execute("DELETE FROM candidates WHERE id=?",(row["id"],))
                        conn.commit()
                        st.rerun()

# ===== RIGHT PANEL =====

with right:

    if st.session_state.selected_id:

        selected=df[df["id"]==st.session_state.selected_id]

        if not selected.empty:

            data=selected.iloc[0]

            st.subheader("Candidate Details")

            st.write("Name:",data["name"])
            st.write("Email:",data["email"])
            st.write("Phone:",data["phone"])
            st.write("Skills:",data["skills"])

            st.divider()

            st.subheader("Resume Preview")

            st.text_area("Full Resume",
                         data["content"],
                         height=600)
