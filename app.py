import streamlit as st
import pandas as pd
import sqlite3
import re
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
experience TEXT,
content TEXT
)
""")

conn.commit()

# ================= TEXT EXTRACTION =================

def extract_text(file):

    text=""

    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                text+=p.extract_text() or ""

    elif file.name.endswith(".docx"):
        doc=Document(file)
        text="\n".join([p.text for p in doc.paragraphs])

    return text

# ================= SMART PARSER =================

def parse_resume(text):

    # NAME
    name=text.split("\n")[0][:60]

    # EMAIL
    email_match=re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',text)
    email=email_match[0] if email_match else ""

    # PHONE
    phone_match=re.findall(r'\+?\d[\d\s-]{8,}',text)
    phone=phone_match[0] if phone_match else ""

    # EXPERIENCE
    exp_match=re.findall(r'(\d+\+?\s?years?)',text.lower())
    experience=exp_match[0] if exp_match else ""

    # SKILLS keyword scan
    skill_list=["python","sql","azure","aws","java","react","etl","data","spark"]
    skills=[s for s in skill_list if s.lower() in text.lower()]
    skills=", ".join(skills)

    return name,email,phone,skills,experience

# ================= SESSION =================

if "selected_id" not in st.session_state:
    st.session_state.selected_id=None

# ================= SIDEBAR =================

st.sidebar.title("Filters")

name_filter=st.sidebar.text_input("Candidate Name")
email_filter=st.sidebar.text_input("Email")
skill_filter=st.sidebar.text_input("Skills Boolean")

delete_mode=st.sidebar.checkbox("Enable Delete Mode")

# ================= UPLOAD =================

st.title("🔥 ATS MONSTER RECRUITER UI")

file=st.file_uploader("Upload Resume",type=["pdf","docx"])

if file:

    text=extract_text(file)

    name,email,phone,skills,experience=parse_resume(text)

    uid=str(uuid.uuid4())

    c.execute("INSERT INTO candidates VALUES (?,?,?,?,?,?,?)",
              (uid,name,email,phone,skills,experience,text))
    conn.commit()

    st.success("Uploaded & Saved")

# ================= LOAD DATA =================

df=pd.read_sql("SELECT * FROM candidates",conn)

# FILTERS

if name_filter:
    df=df[df["name"].str.contains(name_filter,case=False)]

if email_filter:
    df=df[df["email"].str.contains(email_filter,case=False)]

if skill_filter:
    df=df[df["skills"].str.contains(skill_filter,case=False)]

# ================= UI =================

left,right=st.columns([1.3,2])

# ===== LEFT TABLE =====

with left:

    st.subheader("Candidates")

    for i,row in df.iterrows():

        col1,col2=st.columns([5,1])

        with col1:
            if st.button(
                f"{row['name']} | {row['email']} | {row['experience']}",
                key=row["id"]
            ):
                st.session_state.selected_id=row["id"]

        with col2:
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
            st.write("Experience:",data["experience"])
            st.write("Skills:",data["skills"])

            st.divider()

            st.subheader("Resume Preview")

            st.text_area(
                "Full Resume",
                value=data["content"],
                height=600
            )
