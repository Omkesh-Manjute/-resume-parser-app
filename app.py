import streamlit as st
import pandas as pd
import re
import docx
import pdfplumber

st.set_page_config(layout="wide")

st.title("🔥 Ultra Recruiter ATS Dashboard")

# --------------------------
# TEXT EXTRACTION
# --------------------------

def extract_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_pdf(file):
    text=""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() or ""
    return text

# --------------------------
# SKILLS LIST
# --------------------------

skills_keywords=[
    "python","java","sql","aws","react","node","azure",
    "qa","testing","data engineer"
]

# --------------------------
# PARSE RESUME
# --------------------------

def parse_resume(text,file):

    email=re.findall(r'\S+@\S+',text)
    phone=re.findall(r'\+?\d[\d -]{8,12}\d',text)

    skills=[s for s in skills_keywords if s in text.lower()]

    name=text.split("\n")[0]

    return{
        "Name":name,
        "Email":email[0] if email else "",
        "Phone":phone[0] if phone else "",
        "Skills":", ".join(skills),
        "FullText":text.lower(),
        "Resume":file
    }

# --------------------------
# BOOLEAN FILTER
# --------------------------

def boolean_search(df,query):

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

# --------------------------
# UPLOAD FILES
# --------------------------

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

        data.append(parse_resume(text,file))

    df=pd.DataFrame(data)

    # --------------------------
    # FILTER PANEL
    # --------------------------

    st.subheader("🔎 Recruiter Filters")

    col1,col2,col3=st.columns(3)

    name_filter=col1.text_input("Search Name")
    email_filter=col2.text_input("Search Email")
    boolean_filter_input=col3.text_input(
        "Boolean Search (python AND aws)"
    )

    filtered=df.copy()

    if name_filter:
        filtered=filtered[
            filtered["Name"].str.contains(name_filter,case=False)
        ]

    if email_filter:
        filtered=filtered[
            filtered["Email"].str.contains(email_filter,case=False)
        ]

    filtered=boolean_search(filtered,boolean_filter_input.lower())

    # --------------------------
    # ATS STYLE TABLE
    # --------------------------

    st.subheader("📋 Candidate List")

    for i,row in filtered.iterrows():

        with st.container():

            colA,colB,colC=st.columns([3,3,4])

            # CLICKABLE NAME
            with colA:
                st.markdown(
                    f"### 🔹 {row['Name']}"
                )

                st.download_button(
                    "Open Resume",
                    row["Resume"],
                    file_name=row["Resume"].name
                )

            with colB:
                st.write("📧",row["Email"])
                st.write("📞",row["Phone"])

            with colC:
                st.write("💻 Skills:",row["Skills"])

            # EXPANDABLE DETAILS
            with st.expander("More Details"):
                st.write("Full Resume Text Preview:")
                st.write(row["FullText"][:500])

