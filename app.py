import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader  # ✅ Fixed: Use pypdf (modern, reliable)
import io
import json
try:
    from streamlit_mic_recorder import speech_to_text
except ImportError:
    speech_to_text = None  # Graceful fallback

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
        try:
            pdf_reader = PdfReader(io.BytesIO(resume_file.read()))
            resume_text = " ".join([page.extract_text() for page in pdf_reader.pages])
            st.success("✅ Resume loaded!")
        except Exception as e:
            st.error(f"❌ PDF parsing error: {str(e)}")

## Main Tabs
tab1, tab2, tab3 = st.tabs(["🎤 Interview", "📊 Feedback", "⚙️ Settings"])

with tab1:
    st.header("Live Interview")
    
    # Enhanced system prompt
    system_prompt = f"""You are a professional {experience_level} {job_title} interviewer at {company}.
Ask one question at a time. Wait for response.
Evaluate clarity, relevance, technical depth.
After 5-7 questions, give final assessment.
Resume context: {resume_text[:2000] if resume_text else 'No resume provided.'}"""  
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.interview_count = 0
    
    # Mic input (with fallback)
    st.subheader("🎤 Speak your answer")
    if speech_to_text:
        text = speech_to_text(
            language='en',
            start_prompt="🎤 Click to Speak",
            stop_prompt="⏹️ Transcribing...",
            use_container_width=True,
            key="stt"
        )
    else:
        st.warning("💡 Install `pip install streamlit-mic-recorder` for voice input")
        text = ""
    
    user_input = st.chat_input("💬 Or type your answer here...")
    final_input = text or (user_input if user_input else "")
    
    if final_input:
        st.session_state.messages.append({"role": "user", "content": final_input})
        st.session_state.interview_count += 1
        st.rerun()
    
    # AI Response - FIXED streaming logic
    if (len(st.session_state.messages) > 1 and 
        st.session_state.messages[-1]["role"] == "user"):
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
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
            except Exception as e:
                st.error(f"API Error: {str(e)}")
        st.rerun()
    
    # Chat History
    for msg in st.session_state.messages[1:]:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

with tab2:
    st.header("📊 Resume & Interview Feedback")
    
    if resume_text and st.button("🔍 Analyze Resume", type="primary"):
        analysis_prompt = f"""Analyze this resume for {job_title} role:
{resume_text[:4000]}
Format response:
**Score:** X/10
**Strengths:** ...
**Improvements:** ...
**Match:** XX%"""
        
        with st.spinner("🤖 Analyzing resume..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            st.markdown(response.choices[0].message.content)
    
    if len(st.session_state.messages) > 2 and st.button("🎯 Interview Scorecard", type="secondary"):
        feedback_prompt = f"""Score this interview for {job_title}:
{json.dumps(st.session_state.messages[-8:], indent=2)}
Give overall score, key strengths, areas to improve."""
        
        with st.spinner("📈 Generating scorecard..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": feedback_prompt}]
            )
            st.markdown("### 📋 Final Scorecard")
            st.markdown(response.choices[0].message.content)

with tab3:
    st.header("⚙️ Dashboard")
    
    # Progress - 100% SAFE
    total_questions = 7
    progress_value = min(max(st.session_state.interview_count / total_questions, 0.0), 1.0)
    st.progress(progress_value)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📝 Questions", st.session_state.interview_count)
    col2.metric("💬 Total Messages", len(st.session_state.messages))
    col3.metric("📄 Resume", "Loaded" if resume_text else "Upload")
    
    if st.button("🔄 Reset Interview", type="primary"):
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.interview_count = 0
        st.success("✅ Reset complete!")
        st.rerun()
    
    st.subheader("✅ Pro Features Active")
    st.info("""
    ✨ **Voice Input** (streamlit-mic-recorder)
    ✨ **PDF Resume Parser** (pypdf)
    ✨ **Groq Ultra-Fast Streaming** 
    ✨ **Smart Scorecards**
    ✨ **Job-Tailored Questions**
    ✨ **Progress Tracking**
    ✨ **Error-Resistant Code**
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("🎓 Built for", "Nagpur Students")
col2.metric("⚡ Powered by", "Groq Llama")
col3.metric("📱 Ready", "Streamlit Cloud")


