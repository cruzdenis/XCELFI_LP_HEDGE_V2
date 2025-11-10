"""
Authentication module for XCELFI LP Hedge application.
Handles user authentication with bcrypt password hashing.
"""
import bcrypt
import streamlit as st
from typing import Optional, Dict
from datetime import datetime, timedelta


class AuthManager:
    """Manages user authentication and session."""
    
    def __init__(self, users: Dict[str, str], session_timeout_hours: int = 24):
        """
        Initialize authentication manager.
        
        Args:
            users: Dictionary of username -> hashed_password
            session_timeout_hours: Session timeout in hours
        """
        self.users = users
        self.session_timeout = timedelta(hours=session_timeout_hours)
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        Verify username and password.
        
        Args:
            username: Username to verify
            password: Plain text password
            
        Returns:
            True if credentials are valid, False otherwise
        """
        if username not in self.users:
            return False
        
        hashed = self.users[username]
        
        # Handle both string and bytes
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        try:
            return bcrypt.checkpw(password, hashed)
        except Exception:
            return False
    
    def login(self, username: str, password: str) -> bool:
        """
        Attempt to log in user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if login successful, False otherwise
        """
        if self.verify_password(username, password):
            st.session_state['authenticated'] = True
            st.session_state['username'] = username
            st.session_state['login_time'] = datetime.now()
            return True
        return False
    
    def logout(self):
        """Log out current user."""
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.session_state['login_time'] = None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated and session is valid.
        
        Returns:
            True if authenticated and session valid, False otherwise
        """
        if not st.session_state.get('authenticated', False):
            return False
        
        login_time = st.session_state.get('login_time')
        if login_time is None:
            return False
        
        # Check session timeout
        if datetime.now() - login_time > self.session_timeout:
            self.logout()
            return False
        
        return True
    
    def get_current_user(self) -> Optional[str]:
        """
        Get current authenticated username.
        
        Returns:
            Username if authenticated, None otherwise
        """
        if self.is_authenticated():
            return st.session_state.get('username')
        return None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password for storage.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password as string
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        return hashed.decode('utf-8')


def render_login_page(auth_manager: AuthManager):
    """
    Render login page.
    
    Args:
        auth_manager: AuthManager instance
    """
    st.title("🔐 XCELFI LP Hedge - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if auth_manager.login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
