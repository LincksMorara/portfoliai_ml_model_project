-- ================================================
-- ADD TRADE HISTORY TABLE
-- ================================================
-- Tracks all buy/sell transactions with profit/loss
-- ================================================

CREATE TABLE IF NOT EXISTS public.trade_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
  
  symbol TEXT NOT NULL,
  trade_type TEXT NOT NULL CHECK (trade_type IN ('buy', 'sell', 'deposit', 'withdrawal')),
  
  -- Trade details
  quantity DECIMAL(15,6),
  price_per_share DECIMAL(12,2),
  total_amount DECIMAL(15,2) NOT NULL,
  
  -- For sells: profit/loss tracking
  cost_basis DECIMAL(15,2),  -- What you paid for these shares
  realized_pl DECIMAL(15,2),  -- Actual profit/loss (sell_proceeds - cost_basis)
  realized_pl_percent DECIMAL(8,2),
  
  -- Metadata
  trade_date DATE NOT NULL,
  notes TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for performance
CREATE INDEX idx_trade_history_portfolio ON public.trade_history(portfolio_id);
CREATE INDEX idx_trade_history_date ON public.trade_history(trade_date DESC);
CREATE INDEX idx_trade_history_symbol ON public.trade_history(symbol);

-- RLS Policy
ALTER TABLE public.trade_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own trade history" ON public.trade_history
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

CREATE POLICY "Users can insert own trades" ON public.trade_history
  FOR INSERT WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM public.portfolios WHERE id = portfolio_id
    )
  );

-- ================================================
-- SUCCESS! ✅
-- ================================================
-- Now you can track:
-- - Every buy transaction
-- - Every sell transaction with realized profit/loss
-- - Deposit/withdrawal history
-- - Complete trading history
-- ================================================




