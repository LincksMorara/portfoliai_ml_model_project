"""
Simple Authentication System for PortfoliAI
Handles user signup, login, and session management
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib
import secrets

class SimpleAuthSystem:
    """Simple file-based auth system for demo purposes."""
    
    def __init__(self, users_file: str = "users_db.json"):
        """Initialize auth system with user database file."""
        self.users_file = Path(users_file)
        self.sessions = {}  # In-memory sessions {token: user_data}
        
        # Create users file if doesn't exist
        if not self.users_file.exists():
            self._save_users({})
    
    def _load_users(self) -> Dict:
        """Load users from JSON file."""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users: Dict):
        """Save users to JSON file."""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def signup(self, email: str, password: str, investor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new user account.
        
        Args:
            email: User email
            password: User password
            investor_profile: Profile data from survey
            
        Returns:
            Dict with user data and session token
        """
        users = self._load_users()
        
        # Check if user exists
        if email in users:
            raise ValueError("Email already registered")
        
        # Create user
        user_id = hashlib.md5(email.encode()).hexdigest()
        users[email] = {
            'user_id': user_id,
            'email': email,
            'password_hash': self._hash_password(password),
            'investor_profile': investor_profile,
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat()
        }
        
        self._save_users(users)
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'email': email,
            'user_id': user_id,
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return {
            'user_id': user_id,
            'email': email,
            'session_token': session_token,
            'investor_profile': investor_profile
        }
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login existing user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict with user data and session token
        """
        users = self._load_users()
        
        if email not in users:
            raise ValueError("Invalid email or password")
        
        user = users[email]
        
        # Verify password
        if user['password_hash'] != self._hash_password(password):
            raise ValueError("Invalid email or password")
        
        # Update last login
        user['last_login'] = datetime.now().isoformat()
        users[email] = user
        self._save_users(users)
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'email': email,
            'user_id': user['user_id'],
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return {
            'user_id': user['user_id'],
            'email': email,
            'session_token': session_token,
            'investor_profile': user.get('investor_profile', {})
        }
    
    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify session token and return user data.
        
        Args:
            session_token: Session token from cookie
            
        Returns:
            User data if valid, None otherwise
        """
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        
        # Check expiration
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires_at:
            del self.sessions[session_token]
            return None
        
        # Get user data
        users = self._load_users()
        email = session['email']
        
        if email not in users:
            return None
        
        user = users[email]
        return {
            'user_id': user['user_id'],
            'email': email,
            'investor_profile': user.get('investor_profile', {})
        }
    
    def logout(self, session_token: str):
        """Logout user by invalidating session."""
        if session_token in self.sessions:
            del self.sessions[session_token]


# Global instance
auth_system = None

def get_auth_system() -> SimpleAuthSystem:
    """Get global auth system instance."""
    global auth_system
    if auth_system is None:
        auth_system = SimpleAuthSystem()
    return auth_system







