-- ================================================
-- PortfoliAI Supabase Database Schema (WITH DROP)
-- ================================================
-- This script will DROP existing tables and recreate them
-- Run this SQL in your Supabase SQL Editor
-- Project: portfoliai-db
-- ================================================

-- ================================================
-- DROP EXISTING TABLES (in reverse dependency order)
-- ================================================
-- Drop triggers first
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users CASCADE;
DROP TRIGGER IF EXISTS update_investor_profiles_updated_at ON public.investor_profiles CASCADE;
DROP TRIGGER IF EXISTS update_portfolios_updated_at ON public.portfolios CASCADE;
DROP TRIGGER IF EXISTS update_positions_updated_at ON public.positions CASCADE;
DROP TRIGGER IF EXISTS update_conversations_updated_at ON public.conversations CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Drop tables (children first, then parents)
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.conversations CASCADE;
DROP TABLE IF EXISTS public.withdrawals CASCADE;
DROP TABLE IF EXISTS public.positions CASCADE;
DROP TABLE IF EXISTS public.portfolios CASCADE;
DROP TABLE IF EXISTS public.investor_profiles CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- ================================================
-- CREATE TABLES
-- ================================================

-- Enable UUID extension (usually already enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================
-- USERS TABLE
-- ================================================
-- Synced with auth.users (Supabase Auth)
-- This extends the auth.users table with profile information
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- INVESTOR PROFILES TABLE
-- ================================================
-- Stores ML-generated investor profiles from survey
CREATE TABLE public.investor_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  
  -- Core ML-generated profile data (from survey localStorage)
  risk_score DECIMAL(4,3) CHECK (risk_score BETWEEN 0 AND 1),
  risk_category TEXT CHECK (risk_category IN ('Conservative', 'Comfortable', 'Enthusiastic', 'conservative', 'moderate', 'aggressive')),
  persona TEXT, -- e.g., "Strategic Balancer", "Conservative Guardian", "Risk Seeker"
  
  -- Legacy/optional fields for backward compatibility
  risk_tolerance DECIMAL(3,2) CHECK (risk_tolerance BETWEEN 0 AND 1),
  investment_goals TEXT[],
  time_horizon TEXT CHECK (time_horizon IN ('short', 'medium', 'long')),
  expected_return_min INTEGER CHECK (expected_return_min >= 0),
  expected_return_max INTEGER CHECK (expected_return_max >= expected_return_min),
  
  -- Survey data (complete survey responses from frontend - all 13 Q&A)
  survey_responses JSONB,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- PORTFOLIOS TABLE
-- ================================================
CREATE TABLE public.portfolios (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL DEFAULT 'My Portfolio',
  currency TEXT NOT NULL DEFAULT 'USD',
  
  -- Cash account (liquid funds available)
  cash_balance DECIMAL(15,2) DEFAULT 0,
  
  -- Invested values (in stocks/assets)
  total_invested DECIMAL(15,2) DEFAULT 0,
  current_value DECIMAL(15,2) DEFAULT 0,
  total_profit_loss DECIMAL(15,2) DEFAULT 0,
  
  last_calculated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- POSITIONS TABLE (Portfolio Holdings)
-- ================================================
CREATE TABLE public.positions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  company_name TEXT,
  asset_type TEXT DEFAULT 'stock' CHECK (asset_type IN ('stock', 'etf', 'crypto', 'bond', 'other')),
  
  -- Multi-entry cost basis stored as JSONB array
  -- Format: [{"quantity": 10, "price": 150.00, "date": "2024-01-15", "notes": "Initial purchase"}]
  entries JSONB NOT NULL DEFAULT '[]'::jsonb,
  
  -- Current price tracking
  current_price DECIMAL(12,2),
  price_updated_at TIMESTAMPTZ,
  manual_price BOOLEAN DEFAULT FALSE,
  
  -- Aggregated values (calculated)
  total_quantity DECIMAL(15,6) DEFAULT 0,
  average_cost DECIMAL(12,2) DEFAULT 0,
  total_invested DECIMAL(15,2) DEFAULT 0,
  current_value DECIMAL(15,2) DEFAULT 0,
  profit_loss DECIMAL(15,2) DEFAULT 0,
  profit_loss_percent DECIMAL(8,2) DEFAULT 0,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  CONSTRAINT unique_position_per_portfolio UNIQUE(portfolio_id, symbol)
);

-- ================================================
-- WITHDRAWALS TABLE
-- ================================================
CREATE TABLE public.withdrawals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
  amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
  withdrawal_date DATE NOT NULL,
  withdrawal_type TEXT DEFAULT 'general' CHECK (withdrawal_type IN ('general', 'rebalance', 'emergency', 'planned')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- CONVERSATIONS TABLE (for chatbot)
-- ================================================
CREATE TABLE public.conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- MESSAGES TABLE (chatbot messages)
-- ================================================
CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  metadata JSONB,  -- For storing query style, symbols, etc.
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- INDEXES FOR PERFORMANCE
-- ================================================
CREATE INDEX idx_investor_profiles_user ON public.investor_profiles(user_id);
CREATE INDEX idx_portfolios_user ON public.portfolios(user_id);
CREATE INDEX idx_positions_portfolio ON public.positions(portfolio_id);
CREATE INDEX idx_positions_symbol ON public.positions(symbol);
CREATE INDEX idx_withdrawals_portfolio ON public.withdrawals(portfolio_id);
CREATE INDEX idx_withdrawals_date ON public.withdrawals(withdrawal_date DESC);
CREATE INDEX idx_conversations_user ON public.conversations(user_id);
CREATE INDEX idx_conversations_updated ON public.conversations(updated_at DESC);
CREATE INDEX idx_messages_conversation ON public.messages(conversation_id);
CREATE INDEX idx_messages_created ON public.messages(created_at DESC);

-- ================================================
-- ROW LEVEL SECURITY (RLS)
-- ================================================
-- Enable RLS on all tables (security: users can only see their own data)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investor_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.withdrawals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- ================================================
-- RLS POLICIES
-- ================================================

-- Users can only view/edit their own data
CREATE POLICY "Users can view own data" ON public.users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON public.users
  FOR UPDATE USING (auth.uid() = id);

-- Investor Profiles
CREATE POLICY "Users can view own profile" ON public.investor_profiles
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON public.investor_profiles
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON public.investor_profiles
  FOR UPDATE USING (auth.uid() = user_id);

-- Portfolios
CREATE POLICY "Users can view own portfolio" ON public.portfolios
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own portfolio" ON public.portfolios
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own portfolio" ON public.portfolios
  FOR UPDATE USING (auth.uid() = user_id);

-- Positions
CREATE POLICY "Users can view own positions" ON public.positions
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

CREATE POLICY "Users can insert own positions" ON public.positions
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

CREATE POLICY "Users can update own positions" ON public.positions
  FOR UPDATE USING (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

CREATE POLICY "Users can delete own positions" ON public.positions
  FOR DELETE USING (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

-- Withdrawals
CREATE POLICY "Users can view own withdrawals" ON public.withdrawals
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

CREATE POLICY "Users can insert own withdrawals" ON public.withdrawals
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

-- Conversations
CREATE POLICY "Users can view own conversations" ON public.conversations
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations" ON public.conversations
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations" ON public.conversations
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations" ON public.conversations
  FOR DELETE USING (auth.uid() = user_id);

-- Messages
CREATE POLICY "Users can view own messages" ON public.messages
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM public.conversations WHERE id = conversation_id
    )
  );

CREATE POLICY "Users can insert own messages" ON public.messages
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM public.conversations WHERE id = conversation_id
    )
  );

-- ================================================
-- FUNCTIONS & TRIGGERS
-- ================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_investor_profiles_updated_at BEFORE UPDATE ON public.investor_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON public.portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON public.positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- SETUP COMPLETE! ✅
-- ================================================
-- You should see "Success. No rows returned" message
-- 
-- Your database now has:
-- ✅ users - User accounts
-- ✅ investor_profiles - ML risk profiles (risk_score, persona, etc.)
-- ✅ portfolios - User portfolios
-- ✅ positions - Stock/asset holdings
-- ✅ withdrawals - Withdrawal tracking
-- ✅ conversations - Chatbot conversations
-- ✅ messages - Chat messages
-- 
-- Next: Tell the AI assistant "Done!" and they'll restart the server
-- ================================================

