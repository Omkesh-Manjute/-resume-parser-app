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

# -----------------------------
# Extract text functions
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

# -----------------------------
# BOOLEAN SEARCH FUNCTION
# -----------------------------

def boolean_filter(df, query):

    if not query:
        return df

    query = query.lower()

    filtered = []

    for _, row in df.iterrows():

        text = " ".join(row.astype(str)).lower()

        # AND logic
        if " and " in query:
            terms = query.split(" and ")
            if all(t in text for t in terms):
                filtered.append(row)

        # OR logic
        elif " or " in query:
            terms = query.split(" or ")
            if any(t in text for t in terms):
                filtered.append(row)

        # NOT logic
        elif " not " in query:
            term = query.replace(" not ","")
            if term not in text:
                filtered.append(row)

        else:
            if query in text:
                filtered.append(row)

    return pd.DataFrame(filtered)


# -----------------------------
# MAIN
# -----------------------------

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

    # 🔥 FILTER TOP (as you wanted)
    st.subheader("🔎 Advanced Search")

    search_query = st.text_input(
        "Search (Name / Email / Skills / Boolean search)",
        placeholder="Example: python AND aws OR java NOT testing"
    )

    filtered_df = boolean_filter(df, search_query)

    # TABLE
    st.subheader("📊 Candidate Table")
    st.dataframe(filtered_df)
