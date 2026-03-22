import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
import io
import json
from streamlit_mic_recorder import speech_to_text

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="ShareGo Pro", layout="wide")
st.title("🤖 ShareGo Pro - AI Virtual Interviewer Pro")

## Sidebar: Job & Resume Setup
with st.sidebar:
    st.header("🎯 Job Settings")
    job_title = st.text_input("Job Title", "Software Engineer")
    company = st.text_input("Company", "Tech Corp")
    experience_level = st.selectbox("Experience Level", ["Entry", "Mid", "Senior"])
    
    st.header("📄 Resume Upload")
    resume_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    resume_text = ""
    if resume_file:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(resume_file.read()))
        resume_text = " ".join([page.extract_text() for page in pdf_reader.pages])
        st.success("Resume loaded!")

## Main Tabs
tab1, tab2, tab3 = st.tabs(["🎤 Interview", "📊 Feedback", "⚙️ Settings"])

with tab1:
    st.header("Live Interview")
    
    # Enhanced system prompt
    system_prompt = f"""You are a professional {experience_level} {job_title} interviewer at {company}.
Ask behavioral and technical questions one at a time.
Evaluate answers on clarity, relevance, depth.
After 5-7 questions, provide overall assessment.
Resume context: {resume_text[:2000] if resume_text else 'No resume provided.'}"""  
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.interview_count = 0
    
    # Mic input with streamlit-mic-recorder
    st.subheader("🎤 Speak your answer (or type below)")
    text = speech_to_text(
        language='en',
        start_prompt="🎤 Start Speaking",
        stop_prompt="⏹️ Stop & Transcribe",
        use_container_width=True,
        key="stt"
    )
    
    user_input = st.text_input("💬 Or type here:", key="manual_input")
    final_input = text or user_input
    
    col1, col2 = st.columns([3,1])
    with col1:
        if st.button("🚀 Send Answer", type="primary", disabled=not final_input):
            st.session_state.messages.append({"role": "user", "content": final_input})
            st.session_state.interview_count += 1
            st.rerun()
    
    # Streamed AI response - FIXED
    if (len(st.session_state.messages) > 1 and 
        st.session_state.messages[-1]["role"] == "user"):
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=st.session_state.messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()
    
    # Chat display
    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

with tab2:
    st.header("📊 Resume & Interview Feedback")
    
    if resume_text and st.button("🔍 Analyze Resume", type="primary"):
        analysis_prompt = f"""Analyze this resume for {job_title} at {company}:
{resume_text}
Provide:
1. Score 1-10
2. Strengths
3. Areas to improve
4. Match percentage"""
        
        with st.spinner("Analyzing..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            st.markdown(response.choices[0].message.content)
    
    if len(st.session_state.messages) > 2 and st.button("🎯 Full Interview Score"):
        feedback_prompt = f"Summarize interview performance for {job_title}. Last 10 exchanges: {json.dumps(st.session_state.messages[-10:])}"
        with st.spinner("Generating feedback..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": feedback_prompt}]
            )
            st.markdown(response.choices[0].message.content)

with tab3:
    st.header("⚙️ Advanced Features")
    
    # FIXED Progress - clamped between 0-1
    progress = min(max(st.session_state.interview_count / 7, 0.0), 1.0)
    st.progress(progress)
    st.metric("Questions Answered", st.session_state.interview_count, delta=None)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Interview", type="secondary"):
            st.session_state.messages = [{"role": "system", "content": system_prompt}]
            st.session_state.interview_count = 0
            st.rerun()
    
    st.subheader("🚀 Pro Features")
    st.markdown("""
    - 🎤 **Real-time Speech-to-Text** (Client-side)
    - 📄 **PDF Resume Parser** + AI Analysis  
    - ⚡ **Groq Streaming** (Instant responses)
    - 📊 **Interview Scorecard**
    - 🎯 **Job-Specific Questions**
    - 📈 **Live Progress Tracking**
    - 🔄 **Session Management**
    - 💾 **Persistent Chat Memory**
    """)

# Footer
st.markdown("---")
st.markdown("**ShareGo Pro v2.0** - Fixed & Production Ready | Nagpur Student Edition 🚀")

