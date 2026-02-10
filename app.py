import streamlit as st
import pandas as pd
import sqlite3
import re
import pdfplumber
from docx import Document
import uuid

st.set_page_config(layout="wide")

# ================= DATABASE =================

conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS candidates(
id TEXT PRIMARY KEY,
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
    """Extract text from PDF or DOCX files with error handling"""
    text = ""
    
    try:
        if file.name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                for p in pdf.pages:
                    page_text = p.extract_text()
                    if page_text:
                        text += page_text + "\n"
        
        elif file.name.endswith(".docx"):
            doc = Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
    
    except Exception as e:
        st.error(f"Error extracting text: {str(e)}")
        return ""
    
    return text.strip()

# ================= SMART PARSER =================

def parse_resume(text):
    """Parse resume with improved regex and validation"""
    
    if not text:
        return "Unknown", "", "", "", ""
    
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # NAME - first non-empty line
    name = lines[0][:60] if lines else "Unknown"
    
    # EMAIL - improved pattern
    email_match = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    email = email_match[0] if email_match else ""
    
    # PHONE - improved pattern for various formats
    phone_match = re.findall(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    phone = phone_match[0] if phone_match else ""
    
    # EXPERIENCE - improved pattern
    exp_match = re.findall(r'(\d+\+?\s*(?:years?|yrs?))', text.lower())
    experience = exp_match[0] if exp_match else ""
    
    # SKILLS - expanded keyword scan
    skill_list = ["python", "sql", "azure", "aws", "java", "react", "etl", "data", 
                  "spark", "javascript", "typescript", "node", "docker", "kubernetes",
                  "tensorflow", "pytorch", "excel", "tableau", "powerbi"]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_list:
        if skill in text_lower:
            found_skills.append(skill)
    
    skills = ", ".join(found_skills) if found_skills else "Not specified"
    
    return name, email, phone, skills, experience

# ================= SESSION STATE =================

if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()

# ================= SIDEBAR =================

st.sidebar.title("Filters")

name_filter = st.sidebar.text_input("Candidate Name")
email_filter = st.sidebar.text_input("Email")
skill_filter = st.sidebar.text_input("Skills (contains)")

delete_mode = st.sidebar.checkbox("Enable Delete Mode")

if st.sidebar.button("Clear All Filters"):
    st.rerun()

# ================= MAIN UI =================

st.title("🔥 ATS MONSTER RECRUITER UI")

# ================= UPLOAD =================

file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if file:
    # Create a unique identifier for this specific file upload
    file_id = f"{file.name}_{file.size}"
    
    # Only process if this exact file hasn't been uploaded this session
    if file_id not in st.session_state.uploaded_files:
        
        with st.spinner("Processing resume..."):
            text = extract_text(file)
            
            if text:
                name, email, phone, skills, experience = parse_resume(text)
                
                uid = str(uuid.uuid4())
                
                try:
                    c.execute("INSERT INTO candidates VALUES (?,?,?,?,?,?,?)",
                             (uid, name, email, phone, skills, experience, text))
                    conn.commit()
                    
                    st.session_state.uploaded_files.add(file_id)
                    st.success(f"✅ Resume uploaded successfully: {name}")
                    st.rerun()
                
                except sqlite3.IntegrityError:
                    st.warning("This candidate may already exist in the database.")
                except Exception as e:
                    st.error(f"Database error: {str(e)}")
            else:
                st.error("Could not extract text from the file. Please check the file format.")

# ================= LOAD DATA =================

try:
    df = pd.read_sql("SELECT * FROM candidates", conn)
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    df = pd.DataFrame()

# APPLY FILTERS

if not df.empty:
    if name_filter:
        df = df[df["name"].str.contains(name_filter, case=False, na=False)]
    
    if email_filter:
        df = df[df["email"].str.contains(email_filter, case=False, na=False)]
    
    if skill_filter:
        df = df[df["skills"].str.contains(skill_filter, case=False, na=False)]

# ================= DISPLAY =================

left, right = st.columns([1.3, 2])

# ===== LEFT TABLE =====

with left:
    st.subheader(f"Candidates ({len(df)})")
    
    if df.empty:
        st.info("No candidates found. Upload a resume to get started!")
    else:
        for i, row in df.iterrows():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                button_label = f"{row['name']}"
                if row['email']:
                    button_label += f" | {row['email']}"
                if row['experience']:
                    button_label += f" | {row['experience']}"
                
                if st.button(button_label, key=row["id"], use_container_width=True):
                    st.session_state.selected_id = row["id"]
            
            with col2:
                if delete_mode:
                    if st.button("❌", key="del" + row["id"]):
                        try:
                            c.execute("DELETE FROM candidates WHERE id=?", (row["id"],))
                            conn.commit()
                            
                            # Clear selection if deleted candidate was selected
                            if st.session_state.selected_id == row["id"]:
                                st.session_state.selected_id = None
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting candidate: {str(e)}")

# ===== RIGHT PANEL =====

with right:
    if st.session_state.selected_id:
        selected = df[df["id"] == st.session_state.selected_id]
        
        if not selected.empty:
            data = selected.iloc[0]
            
            st.subheader("📋 Candidate Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Name:**", data["name"])
                st.write("**Email:**", data["email"] if data["email"] else "Not found")
                st.write("**Phone:**", data["phone"] if data["phone"] else "Not found")
            
            with col2:
                st.write("**Experience:**", data["experience"] if data["experience"] else "Not specified")
                st.write("**Skills:**", data["skills"])
            
            st.divider()
            
            st.subheader("📄 Resume Preview")
            
            st.text_area(
                "Full Resume Content",
                value=data["content"],
                height=500,
                disabled=True
            )
        else:
            st.info("Selected candidate not found. They may have been deleted.")
    else:
        st.info("👈 Select a candidate from the list to view details")
