-- ================================================
-- ADD CASH ACCOUNT FEATURE TO PORTFOLIOS
-- ================================================
-- Run this in Supabase SQL Editor to add cash tracking
-- ================================================

-- Add cash_balance column to portfolios table
ALTER TABLE public.portfolios 
ADD COLUMN IF NOT EXISTS cash_balance DECIMAL(15,2) DEFAULT 0;

-- Set existing portfolios to have $0 cash (if any exist)
UPDATE public.portfolios 
SET cash_balance = 0 
WHERE cash_balance IS NULL;

-- ================================================
-- VERIFICATION
-- ================================================
-- Check that cash_balance was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'portfolios' 
  AND column_name = 'cash_balance';

-- ================================================
-- SUCCESS! ✅
-- ================================================
-- Your portfolios table now has:
-- - cash_balance: Tracks available cash for buying/withdrawing
-- 
-- New Flow:
-- 1. Deposit cash → increases cash_balance
-- 2. Buy stocks → decreases cash_balance, adds to positions
-- 3. Sell stocks → increases cash_balance, removes from positions
-- 4. Withdraw → decreases cash_balance (only if sufficient cash)
-- ================================================




