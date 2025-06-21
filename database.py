# File: utils/database.py
import sqlite3
from datetime import datetime, timedelta
import json

def init_db():
    """Initialize database with advanced schema"""
    conn = sqlite3.connect('eduquest.db')
    c = conn.cursor()
    
    # User Table with Preferences
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  username TEXT UNIQUE,
                  password TEXT,
                  email TEXT UNIQUE,
                  preferences TEXT,
                  created_at DATETIME,
                  last_login DATETIME)''')
    
    # Content Table for PDF/text storage
    c.execute('''CREATE TABLE IF NOT EXISTS content
                 (content_id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  raw_text TEXT,
                  processed_text TEXT,
                  file_hash TEXT UNIQUE,
                  upload_date DATETIME,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Question Repository with Spaced Repetition
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (question_id INTEGER PRIMARY KEY,
                  content_id INTEGER,
                  question_type TEXT CHECK(question_type IN 
                    ('MCQ', 'SHORT', 'LONG', 'TRUE_FALSE')),
                  question_text TEXT,
                  correct_answer TEXT,
                  options TEXT,
                  difficulty INTEGER,
                  next_review DATETIME,
                  interval INTEGER,
                  creation_date DATETIME,
                  FOREIGN KEY(content_id) REFERENCES content(content_id))''')
    
    # Progress Tracking
    c.execute('''CREATE TABLE IF NOT EXISTS progress
                 (progress_id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  question_id INTEGER,
                  attempts INTEGER,
                  last_attempt DATETIME,
                  success_rate REAL,
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  FOREIGN KEY(question_id) REFERENCES questions(question_id))''')
    
    # Social Sharing
    c.execute('''CREATE TABLE IF NOT EXISTS shared_content
                 (share_id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  question_id INTEGER,
                  share_date DATETIME,
                  platform TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  FOREIGN KEY(question_id) REFERENCES questions(question_id))''')
    
    conn.commit()
    conn.close()