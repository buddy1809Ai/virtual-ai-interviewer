import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
import io
import json

# Mic recorder - safe import
try:
    from streamlit_mic_recorder import speech_to_text
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False
    def speech_to_text(**kwargs):
        return ""

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    st.error("❌ Set GROQ_API_KEY in Streamlit Cloud secrets or .env file")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="ShareGo Pro", layout="wide")
st.title("🤖 ShareGo Pro - AI Interview Pro")

# Sidebar
with st.sidebar:
    st.header("🎯 Setup")
    job_title = st.text_input("Job Title", "Software Engineer")
    company = st.text_input("Company", "Google")
    level = st.selectbox("Level", ["Entry", "Mid", "Senior"])
    
    resume_file = st.file_uploader("📄 Resume PDF", type="pdf")
    resume_text = ""
    if resume_file:
        try:
            reader = PdfReader(resume_file)
            resume_text = " ".join(page.extract_text() for page in reader.pages)
            st.success("✅ Resume OK")
        except:
            st.error("❌ Bad PDF")

# Tabs
tab1, tab2 = st.tabs(["🎤 Interview", "📊 Analysis"])

with tab1:
    prompt = f"""Professional {level} {job_title} interviewer at {company}.
Ask 1 question. Evaluate answers.
Resume: {resume_text[:1500] if resume_text else 'None'}"""
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": prompt}]
    
    # Input
    if MIC_AVAILABLE:
        text = speech_to_text(language='en', use_container_width=True)
    else:
        text = ""
    
    user_input = st.chat_input("Type/Speak answer...")
    if user_input or text:
        st.session_state.messages.append({"role": "user", "content": user_input or text})
        st.rerun()
    
    # Auto AI response
    if len(st.session_state.messages) % 2 == 0:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = ""
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=st.session_state.messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    response += chunk.choices[0].delta.content
                    placeholder.markdown(response)
            placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    # Show chat
    for m in st.session_state.messages[1:]:
        st.chat_message(m["role"]).markdown(m["content"])

with tab2:
    if resume_text and st.button("🔍 Analyze Resume"):
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Score resume 1-10 for {job_title}:\n{resume_text}"}]
        )
        st.markdown(resp.choices[0].message.content)
    
    if st.button("📊 Interview Report"):
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Score interview:\n{st.session_state.messages}"}]
        )
        st.markdown(resp.choices[0].message.content)

# Metrics
st.markdown("---")
col1, col2 = st.columns(2)
col1.metric("Questions", len(st.session_state.messages)//2)
col2.metric("Status", "✅ Live" if MIC_AVAILABLE else "Text Only")


