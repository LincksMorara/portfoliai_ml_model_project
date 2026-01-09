# 🚀 Production Migration Plan - PortfoliAI

## Current State (What Needs Improvement)

### ❌ Current Issues:
1. **JSON File Storage** - Not scalable, no concurrency control
   - `users_db.json` - User profiles and portfolios
   - `conversations.json` - Chat history
   - Risk of data corruption with multiple users

2. **Basic Auth System** - No email verification, insecure password storage
   - Passwords stored with basic hashing
   - No forgot password
   - No email verification
   - Session tokens in cookies (basic)

3. **Unstructured Code** - Everything in a few large files
   - `server.py` (500+ lines, all routes mixed)
   - No separation of concerns
   - Hard to test
   - Difficult to maintain

4. **No Database** - Can't scale, no relationships, no queries
   - Linear search through JSON
   - No indexes
   - No transactions

---

## ✅ Target State (Production-Ready)

### What We'll Build:

**1. Supabase Cloud Database**
```
PostgreSQL Database (Free Tier)
├── users table (with RLS)
├── investor_profiles table
├── portfolios table
├── positions table (multi-entry cost basis)
├── withdrawals table
├── conversations table
└── messages table
```

**2. Supabase Auth (Built-in)**
```
✅ Email/password authentication
✅ Email verification (automatic!)
✅ Password reset (automatic!)
✅ JWT tokens (secure)
✅ Session management
✅ No coding needed - it's built-in!
```

**3. Clean Architecture**
```
portfoliai_ml_model_project/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization
│   ├── config.py                  # Settings management
│   ├── dependencies.py            # Dependency injection
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   ├── conversation.py
│   │   └── base.py
│   │
│   ├── schemas/                   # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   └── conversation.py
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── portfolio_service.py
│   │   ├── chatbot_service.py
│   │   └── market_data_service.py
│   │
│   ├── routers/                   # API routes (separated)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── portfolio.py
│   │   ├── chatbot.py
│   │   └── survey.py
│   │
│   └── utils/                     # Helper functions
│       ├── __init__.py
│       ├── security.py
│       └── email.py
│
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
│
├── static/                        # Frontend files
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                     # HTML templates
│   ├── auth/
│   ├── dashboard/
│   └── chatbot/
│
├── tests/                         # Unit tests
│   ├── test_auth.py
│   ├── test_portfolio.py
│   └── test_chatbot.py
│
├── ml_models/                     # Keep ML models separate
│   ├── survey_regressor.pkl
│   └── ...
│
├── requirements.txt
├── alembic.ini
├── .env
└── README.md
```

---

## 📋 Migration Steps

### Phase 1: Setup Supabase (30 minutes)

**Step 1.1: Create Supabase Project**
1. Go to https://supabase.com
2. Sign up (free)
3. Create new project: "portfoliai-db"
4. Copy these credentials:
   - Project URL: `https://xxx.supabase.co`
   - Anon Key: `eyJhbGc...` (public, safe for frontend)
   - Service Role Key: `eyJhbGc...` (secret, server-only)

**Step 1.2: Enable Email Auth**
1. Go to Authentication → Settings
2. Enable "Confirm Email" ✅
3. Set up email templates (or use default)
4. Add your site URL: `http://localhost:8000`

**Step 1.3: Create Database Schema**
```sql
-- Run in Supabase SQL Editor

-- Users table (synced with auth.users automatically by Supabase)
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Investor profiles
CREATE TABLE public.investor_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  risk_tolerance DECIMAL(3,2),
  investment_goals TEXT[],
  time_horizon TEXT,
  expected_return_min INTEGER,
  expected_return_max INTEGER,
  survey_responses JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Portfolios
CREATE TABLE public.portfolios (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  name TEXT DEFAULT 'My Portfolio',
  currency TEXT DEFAULT 'USD',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id) -- One portfolio per user for now
);

-- Positions (holdings)
CREATE TABLE public.positions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  portfolio_id UUID REFERENCES public.portfolios(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  company_name TEXT,
  asset_type TEXT DEFAULT 'stock',
  entries JSONB NOT NULL, -- Array of {quantity, price, date}
  current_price DECIMAL(12,2),
  price_updated_at TIMESTAMPTZ,
  manual_price BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Withdrawals
CREATE TABLE public.withdrawals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  portfolio_id UUID REFERENCES public.portfolios(id) ON DELETE CASCADE,
  amount DECIMAL(12,2) NOT NULL,
  withdrawal_date DATE NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations
CREATE TABLE public.conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages
CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_positions_portfolio ON public.positions(portfolio_id);
CREATE INDEX idx_positions_symbol ON public.positions(symbol);
CREATE INDEX idx_withdrawals_portfolio ON public.withdrawals(portfolio_id);
CREATE INDEX idx_conversations_user ON public.conversations(user_id);
CREATE INDEX idx_messages_conversation ON public.messages(conversation_id);

-- Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investor_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.withdrawals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only see their own data)
CREATE POLICY "Users can view own data" ON public.users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view own profile" ON public.investor_profiles
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own portfolio" ON public.portfolios
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own positions" ON public.positions
  FOR ALL USING (auth.uid() IN (
    SELECT user_id FROM public.portfolios WHERE id = portfolio_id
  ));

CREATE POLICY "Users can view own withdrawals" ON public.withdrawals
  FOR ALL USING (auth.uid() IN (
    SELECT user_id FROM public.portfolios WHERE id = portfolio_id
  ));

CREATE POLICY "Users can view own conversations" ON public.conversations
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own messages" ON public.messages
  FOR ALL USING (auth.uid() IN (
    SELECT user_id FROM public.conversations WHERE id = conversation_id
  ));
```

---

### Phase 2: Install Dependencies (5 minutes)

**Update requirements.txt:**
```txt
# Existing dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pandas>=1.5.0
numpy>=1.24.0
scikit-learn==1.6.1
joblib>=1.3.0
xgboost>=1.7.0
groq>=0.30.0
openai>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0

# NEW: Database & ORM
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.9        # PostgreSQL driver

# NEW: Supabase
supabase>=2.0.0               # Official Supabase client
postgrest-py>=0.10.0          # REST client for Supabase

# NEW: Security
passlib[bcrypt]>=1.7.4        # Better password hashing
python-jose[cryptography]>=3.3.0  # JWT tokens
python-multipart>=0.0.6       # Form data

# NEW: Email (optional - Supabase handles this)
# emails>=0.6.0               # If you want custom emails

# Testing (optional but recommended)
pytest>=7.4.0
httpx>=0.25.0                 # For async testing
```

**Install:**
```bash
./venv/bin/pip install -r requirements.txt
```

---

### Phase 3: Create New Project Structure (1 hour)

**I'll create all the files with proper architecture:**
- SQLAlchemy models
- Pydantic schemas
- Service layer for business logic
- Separated routers
- Configuration management
- Dependency injection

---

### Phase 4: Migrate Existing Data (30 minutes)

**Create migration script to transfer:**
- `users_db.json` → Supabase `users` + `investor_profiles` + `portfolios`
- `conversations.json` → Supabase `conversations` + `messages`

**Script will:**
1. Read existing JSON files
2. Create users in Supabase Auth (mark as verified)
3. Insert profiles, portfolios, conversations
4. Preserve all data

---

### Phase 5: Update Frontend (30 minutes)

**Changes needed:**
- Auth flow now uses Supabase (sign up, login, email verification)
- Show "Check your email" message after signup
- Handle email verification callback
- Update API calls (mostly same, but better error handling)

---

### Phase 6: Testing & Deployment (30 minutes)

**Test:**
- New user signup → Email verification
- Login → Dashboard
- Portfolio tracking
- Chatbot with conversation history
- Data persistence

**Deploy Options:**
- Railway.app (free tier, easiest)
- Render.com (free tier)
- Fly.io (free tier)
- Heroku (paid now)

---

## 🎯 Benefits After Migration

**Before (Current):**
```
❌ JSON files (risky, not scalable)
❌ No email verification
❌ No password reset
❌ Messy code structure
❌ Hard to test
❌ Hard to deploy
```

**After (Production):**
```
✅ PostgreSQL cloud database
✅ Email verification (automatic!)
✅ Password reset (automatic!)
✅ Clean architecture (easy to understand)
✅ Easy to test
✅ Easy to deploy
✅ Scalable to 1000s of users
✅ Professional-grade security
```

---

## 📊 Effort Estimate

**Total Time: ~3-4 hours**
- Supabase setup: 30 min
- Install dependencies: 5 min
- Create new structure: 1 hour
- Migrate data: 30 min
- Update frontend: 30 min
- Testing: 30 min
- Documentation: 30 min

**I can do this for you step by step!**

---

## 🚀 Ready to Start?

**Option A: Full Migration (Recommended)**
- I'll create the entire new structure
- Migrate your data
- Update all code
- Test everything

**Option B: Incremental Migration**
- First: Set up Supabase + Auth
- Second: Migrate users/profiles
- Third: Migrate portfolios
- Fourth: Migrate conversations
- Fifth: Clean up old code

**Which approach do you prefer?**

Tell me to proceed and I'll:
1. Create the Supabase schema SQL file
2. Set up the new project structure
3. Create all the models, schemas, and services
4. Write the data migration script
5. Update the frontend

**Ready to go? Say the word!** 🚀


