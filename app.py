import streamlit as st
import sqlite3
import re
import docx2txt
import pdfplumber
import os
import pandas as pd

st.set_page_config(layout="wide")

DB="ats.db"

# ================= DATABASE =================

conn=sqlite3.connect(DB,check_same_thread=False)
c=conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS candidates(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT,
phone TEXT,
skills TEXT,
experience TEXT,
location TEXT,
file_path TEXT UNIQUE,
content TEXT
)
""")

conn.commit()

# ================= PARSER =================

def extract_text(file):

    if file.name.endswith(".docx"):
        return docx2txt.process(file)

    if file.name.endswith(".pdf"):
        text=""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text+=page.extract_text() or ""
        return text

    return ""

def extract_email(text):
    match=re.search(r'\S+@\S+',text)
    return match.group() if match else ""

def extract_phone(text):
    match=re.search(r'(\+?\d[\d\s\-]{8,})',text)
    return match.group() if match else ""

def extract_name(text):
    lines=text.split("\n")
    for l in lines[:5]:
        if len(l.strip())>3:
            return l.strip()
    return "Unknown"

# ================= SIDEBAR FILTER =================

st.sidebar.title("🔎 Filters")

filter_name=st.sidebar.text_input("Candidate Name")
filter_email=st.sidebar.text_input("Email")
filter_skill=st.sidebar.text_input("Boolean Skill")

delete_mode=st.sidebar.checkbox("Enable Delete Mode")

# ================= UPLOAD =================

st.title("🔥 ATS PRO RECRUITER DASHBOARD")

uploaded=st.file_uploader("Upload Resume",accept_multiple_files=True,type=["pdf","docx"])

if uploaded:

    for file in uploaded:

        content=extract_text(file)

        name=extract_name(content)
        email=extract_email(content)
        phone=extract_phone(content)

        skills=",".join(set(re.findall(r'\b(python|sql|azure|aws|java|etl|data)\b',content.lower())))

        try:
            c.execute("""
            INSERT INTO candidates(name,email,phone,skills,experience,location,file_path,content)
            VALUES(?,?,?,?,?,?,?,?)
            """,(name,email,phone,skills,"","",file.name,content))
            conn.commit()
        except:
            pass

    st.success("Saved to ATS Database")

# ================= FETCH DATA =================

df=pd.read_sql("SELECT * FROM candidates",conn)

if filter_name:
    df=df[df["name"].str.contains(filter_name,case=False)]

if filter_email:
    df=df[df["email"].str.contains(filter_email,case=False)]

if filter_skill:
    df=df[df["skills"].str.contains(filter_skill,case=False)]

# ================= UI LAYOUT =================

col1,col2=st.columns([1,2])

selected_id=None

with col1:

    st.subheader("Candidates")

    for _,row in df.iterrows():

        with st.container():

            cols=st.columns([4,1])

            if cols[0].button(
                f"👉 {row['name']} | {row['email']} | {row['phone']}",
                key=f"cand_{row['id']}"):
                selected_id=row["id"]

            if delete_mode:
                if cols[1].button("❌",key=f"del_{row['id']}"):
                    c.execute("DELETE FROM candidates WHERE id=?",(row["id"],))
                    conn.commit()
                    st.rerun()

# ================= RIGHT PANEL =================

with col2:

    if selected_id:

        data=df[df["id"]==selected_id].iloc[0]

        st.subheader("Candidate Details")

        st.write("Name:",data["name"])
        st.write("Email:",data["email"])
        st.write("Phone:",data["phone"])
        st.write("Skills:",data["skills"])

        st.divider()

        st.subheader("Resume Preview")

        st.text_area("Full Resume",data["content"],height=600)
