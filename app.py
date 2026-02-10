import streamlit as st
import pandas as pd
import re
import docx
import pdfplumber

st.title("🔥 ULTRA Recruiter AI Dashboard")

uploaded_files = st.file_uploader(
    "Upload resumes",
    accept_multiple_files=True,
    type=["pdf","docx"]
)

# -----------------------------
# Extract text
# -----------------------------

def extract_text_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_pdf(file):
    text=""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# -----------------------------
# Resume parsing
# -----------------------------

skills_keywords = [
    "python","java","sql","aws","react","node","azure",
    "testing","qa","developer","data engineer"
]

def extract_info(text):

    email = re.findall(r'\S+@\S+', text)
    phone = re.findall(r'\+?\d[\d -]{8,12}\d', text)

    name = text.split("\n")[0]

    skills = [s for s in skills_keywords if s in text.lower()]

    exp = re.findall(r'(\d+)\s+years', text.lower())

    return {
        "Name": name,
        "Email": email[0] if email else "",
        "Phone": phone[0] if phone else "",
        "Skills": ", ".join(skills),
        "Experience": exp[0] if exp else "",
        "FullText": text.lower()
    }

# -----------------------------
# BOOLEAN SEARCH
# -----------------------------

def boolean_filter(df, query):

    if not query:
        return df

    query = query.lower()

    filtered=[]

    for _,row in df.iterrows():

        text=" ".join(row.astype(str)).lower()

        if " and " in query:
            terms=query.split(" and ")
            if all(t in text for t in terms):
                filtered.append(row)

        elif " or " in query:
            terms=query.split(" or ")
            if any(t in text for t in terms):
                filtered.append(row)

        elif " not " in query:
            term=query.replace(" not ","")
            if term not in text:
                filtered.append(row)

        else:
            if query in text:
                filtered.append(row)

    return pd.DataFrame(filtered)

# -----------------------------
# JD MATCH SCORE
# -----------------------------

def match_score(resume_text, jd):

    jd_words = jd.lower().split()

    score=0

    for word in jd_words:
        if word in resume_text:
            score+=1

    return score

# -----------------------------
# MAIN
# -----------------------------

data=[]

if uploaded_files:

    for file in uploaded_files:

        if file.name.endswith("docx"):
            text = extract_text_docx(file)

        elif file.name.endswith("pdf"):
            text = extract_text_pdf(file)

        else:
            continue

        info=extract_info(text)
        info["File"]=file.name
        data.append(info)

    df=pd.DataFrame(data)

    # -----------------------------
    # JD Input
    # -----------------------------

    st.subheader("📄 Paste Job Description")

    jd_text = st.text_area("Paste JD here for AI matching")

    if jd_text:

        df["MatchScore"]=df["FullText"].apply(lambda x: match_score(x,jd_text))

        df=df.sort_values(by="MatchScore",ascending=False)

    # -----------------------------
    # ADVANCED FILTER
    # -----------------------------

    st.subheader("🔎 Recruiter Search")

    search_query = st.text_input(
        "Boolean search (python AND aws OR java)"
    )

    filtered_df=boolean_filter(df,search_query)

    # -----------------------------
    # SHORTLIST FILTER
    # -----------------------------

    min_score=st.slider("Minimum Match Score",0,50,0)

    if "MatchScore" in filtered_df.columns:
        filtered_df=filtered_df[filtered_df["MatchScore"]>=min_score]

    # -----------------------------
    # TABLE
    # -----------------------------

    st.subheader("📊 Candidate Ranking")

    st.dataframe(filtered_df.drop(columns=["FullText"]))

    # -----------------------------
    # DOWNLOAD EXCEL
    # -----------------------------

    csv=filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Shortlist",
        csv,
        "shortlist.csv",
        "text/csv"
    )
