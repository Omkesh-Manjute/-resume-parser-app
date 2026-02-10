import streamlit as st
import pandas as pd
import re
import docx
import pdfplumber

st.title("🔥 AI Resume Parser Dashboard")

uploaded_files = st.file_uploader(
    "Upload resumes",
    accept_multiple_files=True,
    type=["pdf","docx"]
)

data = []

def extract_text_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_pdf(file):
    text=""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_info(text):

    email = re.findall(r'\S+@\S+', text)
    phone = re.findall(r'\+?\d[\d -]{8,12}\d', text)

    name = text.split("\n")[0]

    skills_keywords = ["python","java","sql","react","aws","testing","qa","developer"]
    skills = [s for s in skills_keywords if s.lower() in text.lower()]

    exp = re.findall(r'(\d+)\s+years', text.lower())

    return {
        "Name": name,
        "Email": email[0] if email else "",
        "Phone": phone[0] if phone else "",
        "Skills": ", ".join(skills),
        "Experience": exp[0] if exp else ""
    }

if uploaded_files:

    for file in uploaded_files:

        if file.name.endswith("docx"):
            text = extract_text_docx(file)

        elif file.name.endswith("pdf"):
            text = extract_text_pdf(file)

        else:
            continue

        info = extract_info(text)
        info["File"] = file.name

        data.append(info)

    df = pd.DataFrame(data)

    st.subheader("📊 Candidate Table")
    st.dataframe(df)

    st.subheader("🔎 Filter by Skill")

    skill_filter = st.text_input("Enter skill")

    if skill_filter:
        filtered = df[df["Skills"].str.contains(skill_filter, case=False)]
        st.dataframe(filtered)
