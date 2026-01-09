

# 🚀 Supabase Setup Guide - PortfoliAI

## Step-by-Step Setup (15 minutes)

### Step 1: Create Supabase Project (5 min)

1. **Go to** https://supabase.com
2. **Sign up** for free account
3. **Create new project:**
   - Name: `portfoliai-db`
   - Database Password: Choose a strong password (save it!)
   - Region: Choose closest to you
   - Click "Create new project"
   
4. **Wait 2-3 minutes** for project to provision

---

### Step 2: Get Your API Keys (2 min)

1. In your Supabase project dashboard, go to **Settings → API**

2. **Copy these values:**
   ```
   Project URL: https://xxxyyyzz.supabase.co
   anon/public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **⚠️ IMPORTANT:** 
   - `anon` key = Safe for frontend
   - `service_role` key = SECRET, never expose to frontend!

---

### Step 3: Enable Email Verification (3 min)

1. Go to **Authentication → Settings**

2. **Enable Email Confirmations:**
   - Toggle "Enable email confirmations" → **ON**
   
3. **Configure Email Templates** (optional but recommended):
   - Go to **Authentication → Email Templates**
   - Customize "Confirm signup" template if desired
   - Default template works fine!

4. **Set Site URL:**
   - In Auth settings, set:
     - Site URL: `http://localhost:8000`
     - Redirect URLs: `http://localhost:8000/*`

---

### Step 4: Run Database Schema (5 min)

1. Go to **SQL Editor** in your Supabase dashboard

2. **Click "New query"**

3. **Copy the entire contents** of `supabase_schema.sql`

4. **Paste into SQL editor**

5. **Click "Run"** (or press Cmd/Ctrl + Enter)

6. **Verify tables created:**
   - Go to **Table Editor**
   - You should see: users, investor_profiles, portfolios, positions, withdrawals, conversations, messages

---

### Step 5: Update .env File (2 min)

1. **Open** `.env` in your project root

2. **Add these lines:**

```env
# ============================================
# SUPABASE CONFIGURATION
# ============================================
SUPABASE_URL=https://xxxyyyzz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOi...  # anon key
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...  # service_role key

# ============================================
# SECURITY
# ============================================
SECRET_KEY=your-super-secret-jwt-signing-key-change-this-to-random-string

# (Keep your existing API keys below)
GROQ_API_KEY=gsk_...
FMP_API_KEY=ccg8o3...
FINNHUB_API_KEY=d2skh8hr...
```

3. **Generate a SECRET_KEY:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Copy the output and use it as SECRET_KEY

---

### Step 6: Install New Dependencies (2 min)

```bash
./venv/bin/pip install -r requirements.txt
```

This installs:
- `supabase` - Supabase Python client
- `sqlalchemy` - ORM for database
- `psycopg2-binary` - PostgreSQL driver
- `alembic` - Database migrations
- `passlib[bcrypt]` - Better password hashing
- `python-jose[cryptography]` - JWT tokens
- `pytest` & `httpx` - Testing tools

---

## ✅ Verification

### Test 1: Check Database Connection

Open Python:
```bash
./venv/bin/python3
```

Run:
```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

supabase = create_client(url, key)

# Test connection
result = supabase.table('users').select("*").limit(1).execute()
print("✅ Database connection successful!")
print(f"Users table exists: {result is not None}")
```

Should print: `✅ Database connection successful!`

---

### Test 2: Verify Email Auth is Enabled

1. Go to **Authentication** in Supabase dashboard
2. Check that "Enable email confirmations" is **ON**
3. Note the "Email Confirmations" section shows as enabled

---

## 🎯 What You've Set Up

### Database Tables
- ✅ `users` - User accounts
- ✅ `investor_profiles` - Risk profiles
- ✅ `portfolios` - User portfolios
- ✅ `positions` - Stock holdings
- ✅ `withdrawals` - Withdrawal history
- ✅ `conversations` - Chat conversations
- ✅ `messages` - Chat messages

### Security
- ✅ Row Level Security (RLS) enabled
- ✅ Users can only see their own data
- ✅ JWT-based authentication
- ✅ Email verification required

### Auth Features (Built-in!)
- ✅ Email/password signup
- ✅ Automatic email verification
- ✅ Password reset (automatic!)
- ✅ Session management
- ✅ Secure JWT tokens

---

## 🚀 Next Steps

1. **Start the new app:**
   ```bash
   ./venv/bin/python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Test signup:**
   - Go to http://localhost:8000
   - Create new account
   - Check your email for verification link
   - Click link to verify
   - Login!

3. **Everything should work:**
   - ✅ Email verification
   - ✅ Login/logout
   - ✅ Portfolio tracking
   - ✅ AI chatbot
   - ✅ Conversation history

---

## 🆘 Troubleshooting

### Issue: "Missing environment variable"
**Fix:** Make sure `.env` has all required fields:
- SUPABASE_URL
- SUPABASE_KEY
- SUPABASE_SERVICE_KEY
- SECRET_KEY

### Issue: "Failed to connect to database"
**Fix:** 
1. Check SUPABASE_URL is correct (should start with https://)
2. Verify project is fully provisioned (not still setting up)
3. Check internet connection

### Issue: "No email received"
**Fix:**
1. Check spam folder
2. Verify email confirmations are enabled in Supabase Auth settings
3. Check Supabase logs: Authentication → Logs

### Issue: "JWT expired" or "Invalid token"
**Fix:** Login again - tokens expire after 30 minutes by default

---

## 📊 Supabase Dashboard Overview

**Useful Sections:**
- **Table Editor** - View/edit data directly
- **SQL Editor** - Run custom queries
- **Authentication** - See all users, manage settings
- **Database** → **Roles** - View RLS policies
- **Logs** - Debug auth and database issues
- **API Docs** - Auto-generated API documentation

---

## 🎉 You're Ready!

Your PortfoliAI app now has:
- ✅ Professional cloud database (PostgreSQL)
- ✅ Built-in email verification
- ✅ Secure authentication
- ✅ Scalable to 1000s of users
- ✅ Free tier (500MB, 50K monthly users)

**No more JSON files! No more basic auth! Production-ready!** 🚀


