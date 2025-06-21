# app.py

import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"
os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

import asyncio
import sys
import torch  
from pathlib import Path

# Torch patch
import torch._classes
if not hasattr(torch._classes, '__path__'):
    torch._classes.__path__ = [os.path.dirname(torch._classes.__file__)]
    
project_root = Path(__file__).parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "utils"))

# Windows-specific event loop policy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import pandas as pd
from utils.auth import AuthSystem
from utils.database import init_db
from utils.processors import ContentProcessor 
from utils.questions import QuestionGenerator  

# Initialize core components
init_db()
auth = AuthSystem()
processor = ContentProcessor()
qgen = QuestionGenerator()

# Session management
if 'authenticated' not in st.session_state:
    st.session_state.update({
        'authenticated': False,
        'user_id': None,
        'processed_content': None,
        'questions': []
    })

# Authentication flow
if not st.session_state.authenticated:
    st.title("EduQuest AI -- Login")
    auth.render_login()
    st.stop()

# Main application
st.set_page_config(page_title="EduQuest AI PRO Question/Answer Gen", layout="wide")
st.sidebar.title("Navigation")

def main():
    menu = ["📤 Upload", "❓ Questions", "📊 Progress"]
    choice = st.sidebar.radio("Menu", menu)

    if choice == "📤 Upload":
        handle_upload()
    elif choice == "❓ Questions":
        handle_questions()
    elif choice == "📊 Progress":
        show_progress()

def handle_upload():
    st.header("EduQuest AI PRO Question/Answer Generator")
    file = st.file_uploader("Upload PDF/Text/Image", type=["pdf", "txt", "png", "jpg", "jpeg"])
    
    if file:
        try:
            processed = processor.process_input(file.read(), file.type)
            
            # Check processing status
            if processed['metadata']['status'] != 'processed':
                st.error(f"Processing failed: {processed['metadata']['status']}")
                return
            
            st.session_state.processed_content = processed
            char_count = len(processed['text'])
            page_count = len(processed['pages'])
            
            st.success(f"Processed {page_count} page(s) with {char_count} characters!")
            st.session_state.questions = []  # Clear previous questions
            
            # Optional: Show preview
            with st.expander("View extracted text"):
                st.text(processed['text'][:2000] + "...")  # First 2000 chars
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            if 'processed' in locals():
                st.json(processed)  # Debug output

def handle_questions():
    if not st.session_state.processed_content:
        st.warning("Upload content first!")
        return
        
    # Add content validation
    content = st.session_state.processed_content
    if not content.get('text'):
        st.error("No text content available for generation")
        return

    st.header("Generate Questions")
    col1, col2 = st.columns(2)
    
    with col1:
        q_type = st.selectbox("Question Type", ["MCQ", "Short Answer", "True/False"])
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"])
    
    with col2:
        num_q = st.slider("Number of Questions", 1, 20, 5)
        focus_area = st.text_input("Focus Area (optional)")

    if st.button("Generate Questions"):
        with st.spinner("Generating questions..."):
            try:
                questions = qgen.generate(
                    text=content['text'],
                    q_type=q_type,
                    num_q=num_q,
                    difficulty=difficulty,
                    focus=focus_area
                )
                st.session_state.questions = questions
                st.success(f"Generated {len(questions)} {q_type} questions!")
                st.balloons()
                
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
                st.error("Please try with different content or parameters")


def show_progress():
    st.header("Learning Progress")
    if st.session_state.questions:
        df = pd.DataFrame([{
            "Type": q['type'],
            "Question": q['question'],
            "Difficulty": q.get('difficulty', 'Medium')
        } for q in st.session_state.questions])
        
        st.dataframe(df)
        st.download_button("Export Progress", df.to_csv(), "progress.csv")
    else:
        st.info("No questions generated yet")

if __name__ == "__main__":
    main()