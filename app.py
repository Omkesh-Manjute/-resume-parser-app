import streamlit as st
import pandas as pd
import re
import docx
import pdfplumber

st.set_page_config(layout="wide")

st.title("🔥 ATS PRO MODE — Ultra Recruiter Dashboard")

# -----------------------
# TEXT EXTRACTION
# -----------------------

def extract_docx(file):
    doc=docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_pdf(file):
    text=""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() or ""
    return text

# -----------------------
# JD MATCH SCORING
# -----------------------

def calculate_match(resume_text,jd):

    resume_words=set(resume_text.lower().split())
    jd_words=set(jd.lower().split())

    if len(jd_words)==0:
        return 0

    match=len(resume_words & jd_words)/len(jd_words)

    return round(match*100,2)

# -----------------------
# BOOLEAN SEARCH
# -----------------------

def boolean_filter(df,query):

    if not query:
        return df

    result=[]

    for _,row in df.iterrows():

        text=" ".join(row.astype(str)).lower()

        if " and " in query:
            terms=query.split(" and ")
            if all(t in text for t in terms):
                result.append(row)

        elif " or " in query:
            terms=query.split(" or ")
            if any(t in text for t in terms):
                result.append(row)

        else:
            if query in text:
                result.append(row)

    return pd.DataFrame(result)

# -----------------------
# PARSE RESUME
# -----------------------

def parse_resume(text,file,jd):

    email=re.findall(r'\S+@\S+',text)
    phone=re.findall(r'\+?\d[\d -]{8,12}\d',text)

    skills_keywords=["python","java","aws","azure","sql","react","qa"]

    skills=[s for s in skills_keywords if s in text.lower()]

    match_score=calculate_match(text,jd)

    return{
        "Name":text.split("\n")[0],
        "Email":email[0] if email else "",
        "Phone":phone[0] if phone else "",
        "Skills":", ".join(skills),
        "Match Score":match_score,
        "FullText":text.lower(),
        "Resume":file
    }

# -----------------------
# JD INPUT
# -----------------------

jd=st.text_area("📄 Paste Job Description for AI Matching")

# -----------------------
# UPLOAD
# -----------------------

files=st.file_uploader(
    "Upload resumes",
    accept_multiple_files=True,
    type=["pdf","docx"]
)

if files:

    data=[]

    for file in files:

        if file.name.endswith("docx"):
            text=extract_docx(file)
        else:
            text=extract_pdf(file)

        data.append(parse_resume(text,file,jd))

    df=pd.DataFrame(data)

    # SORT BY MATCH SCORE
    df=df.sort_values(by="Match Score",ascending=False)

    # -----------------------
    # FILTER PANEL
    # -----------------------

    st.subheader("🔎 Recruiter Filters")

    col1,col2,col3,col4=st.columns(4)

    name_filter=col1.text_input("Name")
    email_filter=col2.text_input("Email")
    skill_filter=col3.text_input("Skill")
    boolean_input=col4.text_input("Boolean (python AND aws)")

    filtered=df.copy()

    if name_filter:
        filtered=filtered[filtered["Name"].str.contains(name_filter,case=False)]

    if email_filter:
        filtered=filtered[filtered["Email"].str.contains(email_filter,case=False)]

    if skill_filter:
        filtered=filtered["Skills"].str.contains(skill_filter,case=False)]

    filtered=boolean_filter(filtered,boolean_input.lower())

    # -----------------------
    # ATS UI
    # -----------------------

    st.subheader("📋 Candidates")

    for i,row in filtered.iterrows():

        with st.container():

            colA,colB,colC,colD=st.columns([3,3,3,2])

            with colA:
                st.markdown(f"### 🔹 {row['Name']}")
                st.download_button("Open Resume",row["Resume"],file_name=row["Resume"].name)

            with colB:
                st.write("📧",row["Email"])
                st.write("📞",row["Phone"])

            with colC:
                st.write("💻",row["Skills"])

            with colD:
                st.metric("Match %",row["Match Score"])

            with st.expander("Details"):
                st.write(row["FullText"][:500])
