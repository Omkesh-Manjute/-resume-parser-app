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
        st.error(f"Error extracting text from {file.name}: {str(e)}")
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
                  "tensorflow", "pytorch", "excel", "tableau", "powerbi", "databricks",
                  "snowflake", "airflow", "kafka", "redis", "mongodb", "postgresql",
                  "machine learning", "ml", "ai", "data science", "analytics", "bi",
                  "power bi", "looker", "quicksight", "redshift", "bigquery", "gcp",
                  "devops", "ci/cd", "jenkins", "git", "linux", "bash", "shell"]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_list:
        if skill in text_lower:
            found_skills.append(skill)
    
    skills = ", ".join(found_skills) if found_skills else "Not specified"
    
    return name, email, phone, skills, experience

# ================= JD MATCHING =================

def calculate_match_percentage(candidate_text, candidate_skills, jd_text):
    """Calculate match percentage between candidate and JD"""
    
    if not jd_text:
        return 0
    
    candidate_text_lower = candidate_text.lower()
    jd_text_lower = jd_text.lower()
    
    # Extract keywords from JD (simple approach)
    jd_words = set(re.findall(r'\b\w+\b', jd_text_lower))
    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has',
                  'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may',
                  'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
                  'he', 'she', 'it', 'we', 'they', 'them', 'their', 'what', 'which',
                  'who', 'when', 'where', 'why', 'how'}
    jd_keywords = jd_words - stop_words
    
    # Count matching keywords
    matches = 0
    total_keywords = len(jd_keywords)
    
    if total_keywords == 0:
        return 0
    
    for keyword in jd_keywords:
        if len(keyword) > 2 and keyword in candidate_text_lower:
            matches += 1
    
    # Calculate percentage
    match_percentage = int((matches / total_keywords) * 100)
    
    return min(match_percentage, 100)

# ================= SESSION STATE =================

if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""

# ================= SIDEBAR =================

st.sidebar.title("🔍 Filters")

name_filter = st.sidebar.text_input("Candidate Name")
email_filter = st.sidebar.text_input("Email")
skill_filter = st.sidebar.text_input("Skills (contains)")
min_match = st.sidebar.slider("Minimum Match %", 0, 100, 0)

delete_mode = st.sidebar.checkbox("🗑️ Enable Delete Mode")

if st.sidebar.button("Clear All Filters"):
    st.rerun()

st.sidebar.divider()

# JD Section in Sidebar
st.sidebar.subheader("📋 Job Description")

jd_input = st.sidebar.text_area(
    "Paste JD Here",
    value=st.session_state.jd_text,
    height=300,
    placeholder="Paste the job description here to match candidates..."
)

if st.sidebar.button("Apply JD"):
    st.session_state.jd_text = jd_input
    st.rerun()

if st.sidebar.button("Clear JD"):
    st.session_state.jd_text = ""
    st.rerun()

# ================= MAIN UI =================

st.title("🔥 ATS MONSTER RECRUITER UI")

# ================= BULK UPLOAD =================

st.subheader("📤 Upload Resumes")

files = st.file_uploader(
    "Upload Multiple Resumes (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if files:
    if st.button("🚀 Process All Resumes", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        uploaded_count = 0
        error_count = 0
        
        for idx, file in enumerate(files):
            status_text.text(f"Processing {file.name}...")
            
            try:
                text = extract_text(file)
                
                if text:
                    name, email, phone, skills, experience = parse_resume(text)
                    uid = str(uuid.uuid4())
                    
                    c.execute("INSERT INTO candidates VALUES (?,?,?,?,?,?,?)",
                             (uid, name, email, phone, skills, experience, text))
                    conn.commit()
                    uploaded_count += 1
                else:
                    error_count += 1
            
            except sqlite3.IntegrityError:
                error_count += 1
            except Exception as e:
                st.warning(f"Error processing {file.name}: {str(e)}")
                error_count += 1
            
            progress_bar.progress((idx + 1) / len(files))
        
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✅ Uploaded {uploaded_count} resumes successfully!")
        if error_count > 0:
            st.warning(f"⚠️ {error_count} files failed to upload")
        
        st.rerun()

st.divider()

# ================= LOAD DATA =================

try:
    df = pd.read_sql("SELECT * FROM candidates", conn)
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    df = pd.DataFrame()

# Calculate match percentage if JD is provided
if not df.empty and st.session_state.jd_text:
    df['match_percentage'] = df.apply(
        lambda row: calculate_match_percentage(
            row['content'], 
            row['skills'], 
            st.session_state.jd_text
        ), 
        axis=1
    )
    # Sort by match percentage
    df = df.sort_values('match_percentage', ascending=False)
else:
    df['match_percentage'] = 0

# APPLY FILTERS

if not df.empty:
    if name_filter:
        df = df[df["name"].str.contains(name_filter, case=False, na=False)]
    
    if email_filter:
        df = df[df["email"].str.contains(email_filter, case=False, na=False)]
    
    if skill_filter:
        df = df[df["skills"].str.contains(skill_filter, case=False, na=False)]
    
    if min_match > 0:
        df = df[df["match_percentage"] >= min_match]

# ================= DISPLAY =================

left, right = st.columns([1.3, 2])

# ===== LEFT TABLE =====

with left:
    st.subheader(f"👥 Candidates ({len(df)})")
    
    if st.session_state.jd_text:
        st.caption("🎯 Sorted by JD Match")
    
    if df.empty:
        st.info("No candidates found. Upload resumes to get started!")
    else:
        for i, row in df.iterrows():
            col1, col2, col3 = st.columns([4, 1, 0.7])
            
            with col1:
                button_label = f"{row['name']}"
                if row['email']:
                    button_label += f" | {row['email'][:20]}"
                
                if st.button(button_label, key=row["id"], use_container_width=True):
                    st.session_state.selected_id = row["id"]
            
            with col2:
                # Show match percentage badge
                if st.session_state.jd_text:
                    match = row['match_percentage']
                    if match >= 70:
                        st.success(f"✅ {match}%")
                    elif match >= 50:
                        st.warning(f"⚠️ {match}%")
                    else:
                        st.error(f"❌ {match}%")
                else:
                    st.text("")
            
            with col3:
                if delete_mode:
                    if st.button("🗑️", key="del" + row["id"]):
                        try:
                            c.execute("DELETE FROM candidates WHERE id=?", (row["id"],))
                            conn.commit()
                            
                            if st.session_state.selected_id == row["id"]:
                                st.session_state.selected_id = None
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {str(e)}")

# ===== RIGHT PANEL =====

with right:
    if st.session_state.selected_id:
        selected = df[df["id"] == st.session_state.selected_id]
        
        if not selected.empty:
            data = selected.iloc[0]
            
            st.subheader("📋 Candidate Details")
            
            # Show match percentage prominently if JD exists
            if st.session_state.jd_text:
                match = data['match_percentage']
                if match >= 70:
                    st.success(f"🎯 JD Match Score: {match}% - Strong Match!")
                elif match >= 50:
                    st.warning(f"🎯 JD Match Score: {match}% - Moderate Match")
                else:
                    st.error(f"🎯 JD Match Score: {match}% - Weak Match")
                st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Name:**", data["name"])
                st.write("**Email:**", data["email"] if data["email"] else "Not found")
                st.write("**Phone:**", data["phone"] if data["phone"] else "Not found")
            
            with col2:
                st.write("**Experience:**", data["experience"] if data["experience"] else "Not specified")
                st.write("**Skills:**", data["skills"])
            
            st.divider()
            
            # Tabs for better organization
            tab1, tab2 = st.tabs(["📄 Resume Preview", "🎯 Skills Breakdown"])
            
            with tab1:
                st.text_area(
                    "Full Resume Content",
                    value=data["content"],
                    height=500,
                    disabled=True
                )
            
            with tab2:
                st.write("**Detected Skills:**")
                skills_list = data["skills"].split(", ")
                
                # Create skill badges
                cols = st.columns(3)
                for idx, skill in enumerate(skills_list):
                    with cols[idx % 3]:
                        st.info(f"🔹 {skill}")
        else:
            st.info("Selected candidate not found.")
    else:
        st.info("👈 Select a candidate from the list to view details")
        
        if st.session_state.jd_text:
            st.divider()
            st.subheader("📋 Current Job Description")
            st.text_area(
                "JD Preview",
                value=st.session_state.jd_text,
                height=300,
                disabled=True
            )
