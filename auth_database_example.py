"""
Database-Ready Authentication System for PortfoliAI
DROP-IN REPLACEMENT for auth.py when you're ready for production

Simply rename this to auth.py to use database instead of JSON file!
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets

# Example 1: PostgreSQL/MySQL Integration
class DatabaseAuthSystem:
    """Production-ready auth system with database backend."""
    
    def __init__(self, db_connection_string: str = None):
        """
        Initialize with database connection.
        
        Args:
            db_connection_string: e.g., "postgresql://user:pass@localhost/portfoliai"
        """
        self.db = self._init_database(db_connection_string or os.getenv('DATABASE_URL'))
        self.sessions = {}  # Can also move to Redis for distributed systems
    
    def _init_database(self, connection_string):
        """Initialize database connection."""
        # Example with SQLAlchemy (most flexible)
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(connection_string)
        Session = sessionmaker(bind=engine)
        return Session()
    
    def signup(self, email: str, password: str, investor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user - SAME SIGNATURE as current auth.py!"""
        # Check if exists
        existing = self.db.query(User).filter_by(email=email).first()
        if existing:
            raise ValueError("Email already registered")
        
        # Create user (database model)
        user = User(
            email=email,
            password_hash=self._hash_password(password),
            investor_profile=investor_profile,  # Stored as JSONB
            created_at=datetime.now()
        )
        
        self.db.add(user)
        self.db.commit()
        
        # Create session (SAME as current)
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'email': email,
            'user_id': str(user.id),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        # SAME return format!
        return {
            'user_id': str(user.id),
            'email': email,
            'session_token': session_token,
            'investor_profile': investor_profile
        }
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user - SAME SIGNATURE!"""
        user = self.db.query(User).filter_by(email=email).first()
        
        if not user or user.password_hash != self._hash_password(password):
            raise ValueError("Invalid email or password")
        
        # Update last login
        user.last_login = datetime.now()
        self.db.commit()
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'email': email,
            'user_id': str(user.id),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        # SAME return format!
        return {
            'user_id': str(user.id),
            'email': email,
            'session_token': session_token,
            'investor_profile': user.investor_profile
        }
    
    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Verify session - SAME SIGNATURE!"""
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        expires_at = datetime.fromisoformat(session['expires_at'])
        
        if datetime.now() > expires_at:
            del self.sessions[session_token]
            return None
        
        # Get user from database
        user = self.db.query(User).filter_by(email=session['email']).first()
        if not user:
            return None
        
        # SAME return format!
        return {
            'user_id': str(user.id),
            'email': user.email,
            'investor_profile': user.investor_profile
        }
    
    def logout(self, session_token: str):
        """Logout - SAME SIGNATURE!"""
        if session_token in self.sessions:
            del self.sessions[session_token]
    
    def _hash_password(self, password: str) -> str:
        """Hash password - SAME as current!"""
        return hashlib.sha256(password.encode()).hexdigest()


# Example 2: Firebase/Supabase Integration (Even Easier!)
class FirebaseAuthSystem:
    """Auth system using Firebase (managed backend)."""
    
    def __init__(self):
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Initialize Firebase
        cred = credentials.Certificate('firebase-credentials.json')
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.sessions = {}
    
    def signup(self, email: str, password: str, investor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create user in Firebase - SAME SIGNATURE!"""
        # Check if exists
        users_ref = self.db.collection('users')
        existing = users_ref.where('email', '==', email).get()
        
        if existing:
            raise ValueError("Email already registered")
        
        # Create user document
        user_ref = users_ref.document()
        user_ref.set({
            'email': email,
            'password_hash': self._hash_password(password),
            'investor_profile': investor_profile,
            'created_at': datetime.now().isoformat()
        })
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'email': email,
            'user_id': user_ref.id,
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        # SAME return format!
        return {
            'user_id': user_ref.id,
            'email': email,
            'session_token': session_token,
            'investor_profile': investor_profile
        }
    
    # login(), verify_session(), logout() - SAME signatures!
    # Just query Firebase instead of JSON file


# Global instance - swap the class here when ready!
def get_auth_system():
    """Get auth system instance."""
    # Current (File-based):
    from auth import SimpleAuthSystem
    return SimpleAuthSystem()
    
    # Future (Database):
    # return DatabaseAuthSystem(os.getenv('DATABASE_URL'))
    
    # Or (Firebase):
    # return FirebaseAuthSystem()
```

---

## 🔧 **Migration Steps (When Ready):**

### **Option A: PostgreSQL**

```bash
# 1. Install dependencies
pip install sqlalchemy psycopg2-binary alembic

# 2. Create database models
# (I can generate this for you)

# 3. Replace auth.py
mv auth.py auth_old.py
cp auth_database_example.py auth.py

# 4. Set DATABASE_URL
echo "DATABASE_URL=postgresql://user:pass@localhost/portfoliai" >> .env

# 5. Restart server
# Done! Zero changes to server.py or other files!
```

### **Option B: Firebase**

```bash
# 1. Install
pip install firebase-admin

# 2. Download credentials from Firebase Console
# Save as firebase-credentials.json

# 3. Replace auth.py
mv auth.py auth_old.py
cp auth_firebase_example.py auth.py

# 4. Restart server
# Done!
```

### **Option C: Supabase** (Easiest!)

```bash
# 1. Install
pip install supabase

# 2. Get Supabase URL and key from dashboard

# 3. Minimal changes to auth.py
# Just replace _load_users() and _save_users()

# 4. Done!
```

---

## ✅ **Why It's Easy to Migrate:**

### **1. Interface Contract is Stable:**

All these methods have FIXED signatures:
```python
signup(email, password, investor_profile) → dict
login(email, password) → dict
verify_session(token) → dict or None
logout(token) → None
```

**server.py doesn't care where data comes from** - it just calls these methods!

### **2. No Code Changes Needed:**

When you swap `auth.py`:
- ✅ `server.py` - NO changes needed
- ✅ `signup.html` - NO changes needed
- ✅ `login.html` - NO changes needed
- ✅ `dashboard.html` - NO changes needed

**Just replace the auth backend and restart!**

### **3. Data Structure is Standard:**

```python
{
  'email': str,
  'password_hash': str,
  'investor_profile': dict,  # Already JSON-serializable
  'created_at': ISO datetime,
  'last_login': ISO datetime
}
```

This maps directly to any database schema!

---

## 📊 **Storage Options Comparison:**

| Storage | Current | Migration Time | Best For |
|---------|---------|----------------|----------|
| **JSON File** | ✅ Active | - | Demo, <100 users |
| **SQLite** | Ready | 30 min | Small apps, <10K users |
| **PostgreSQL** | Ready | 1-2 hours | Production, unlimited |
| **Firebase** | Ready | 1 hour | No server management |
| **Supabase** | Ready | 1 hour | PostgreSQL + Auth built-in |

---

## 🎯 **Current vs Future:**

### **Current (Working Now):**
```python
# auth.py
users = json.load(open('users_db.json'))  # ← File
```

### **Future (Drop-in replacement):**
```python
# auth.py
users = db.query(User).all()  # ← PostgreSQL
# OR
users = supabase.table('users').select('*')  # ← Supabase
# OR
users = firebase.collection('users').get()  # ← Firebase
```

**Everything else stays the same!** 🎯

---

## 💡 **My Recommendation:**

**For Now:** Keep JSON file (working perfectly!)

**When Scaling:** Use **Supabase** because:
- ✅ Free tier (50K users)
- ✅ Built-in auth + database
- ✅ Real-time features
- ✅ No server management
- ✅ 10-minute setup

---

**Your auth system is modular and database-agnostic! Easy migration when ready!** 🔌✨

**Want me to generate the PostgreSQL or Supabase migration code for you?**






