import streamlit as st

st.title("Resume Parser Dashboard")

files = st.file_uploader("Upload resumes", accept_multiple_files=True)

if files:
    for file in files:
        st.write("Uploaded:", file.name)
