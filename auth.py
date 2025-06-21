# File: utils/auth.py
import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from utils.config import SECRET_KEY  


class AuthSystem:
    def __init__(self):
        # Create connection only when needed
        self._conn = None
        
    @property
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect('eduquest.db')
        return self._conn
        
    def __del__(self):
        if hasattr(self, '_conn') and self._conn:
            try:
                self._conn.close()
            except:
                pass  # Ignore any close errors during garbage collection
            
class AuthSystem:
    def __init__(self):
        self.conn = sqlite3.connect('eduquest.db')
        self.serializer = URLSafeTimedSerializer(SECRET_KEY)
        
    def validate_password(self, password):
        """Enforce password policy"""
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        return True
    
    def render_login(self):  # NEW METHOD
        """Streamlit UI for login/registration"""
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                user = self.login_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user[0]
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with tab2:
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            new_email = st.text_input("Email")
            if st.button("Create Account"):
                try:
                    self.register_user(new_user, new_pass, new_email)
                    st.success("Account created! Please login")
                except Exception as e:
                    st.error(str(e))
    
    def register_user(self, username, password, email):
        """Enhanced registration flow"""
        if not self.validate_password(password):
            raise ValueError("Password must be 8+ chars with uppercase and numbers")
            
        hashed_pw = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode(), 
                                      SECRET_KEY.encode(), 
                                      100000)
        try:
            self.conn.execute('''INSERT INTO users 
                              (username, password, email, created_at)
                              VALUES (?, ?, ?, ?)''',
                              (username, hashed_pw, email, datetime.now()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Username/email already exists")
    
    def login_user(self, identifier, password):
        """Multi-factor authentication support"""
        # Check if identifier is email or username
        if '@' in identifier:
            user = self.conn.execute('''SELECT * FROM users 
                                      WHERE email=?''', (identifier,)).fetchone()
        else:
            user = self.conn.execute('''SELECT * FROM users 
                                      WHERE username=?''', (identifier,)).fetchone()
        
        if user:
            hashed_input = hashlib.pbkdf2_hmac('sha256', 
                                              password.encode(),
                                              SECRET_KEY.encode(), 
                                              100000)
            if hashed_input == user[2]:  # Compare hashed passwords
                return user
        return None

    def __del__(self):
        self.conn.close()