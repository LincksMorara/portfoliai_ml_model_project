"""
Portfolio Pydantic Schemas
Request/Response models for portfolio management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ============================================
# PORTFOLIO SCHEMAS
# ============================================

class PortfolioCreate(BaseModel):
    """Create portfolio"""
    name: str = Field(default="My Portfolio", max_length=100)
    currency: str = Field(default="USD", max_length=3)


class PortfolioResponse(BaseModel):
    """Portfolio response"""
    id: str
    user_id: str
    name: str
    currency: str
    total_invested: Decimal
    current_value: Decimal
    total_profit_loss: Decimal
    last_calculated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# POSITION SCHEMAS
# ============================================

class PositionEntry(BaseModel):
    """Single purchase entry in a position"""
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    date: date
    notes: Optional[str] = None


class PositionCreate(BaseModel):
    """Create position (add new holding)"""
    symbol: str = Field(..., max_length=20)
    company_name: Optional[str] = None
    asset_type: str = Field(default="stock", pattern="^(stock|etf|crypto|bond|other)$")
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    date: date
    notes: Optional[str] = None


class PositionAddEntry(BaseModel):
    """Add entry to existing position (buy more)"""
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    date: date
    notes: Optional[str] = None


class PositionUpdatePrice(BaseModel):
    """Update current price (for manual tracking)"""
    current_price: Decimal = Field(..., gt=0)
    manual: bool = True


class PositionResponse(BaseModel):
    """Position response"""
    id: str
    portfolio_id: str
    symbol: str
    company_name: Optional[str]
    asset_type: str
    entries: List[dict]  # List of PositionEntry as dicts
    current_price: Optional[Decimal]
    price_updated_at: Optional[datetime]
    manual_price: bool
    total_quantity: Decimal
    average_cost: Decimal
    total_invested: Decimal
    current_value: Decimal
    profit_loss: Decimal
    profit_loss_percent: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# WITHDRAWAL SCHEMAS
# ============================================

class WithdrawalCreate(BaseModel):
    """Record a withdrawal"""
    amount: Decimal = Field(..., gt=0)
    withdrawal_date: date
    withdrawal_type: str = Field(default="general", pattern="^(general|rebalance|emergency|planned)$")
    notes: Optional[str] = None


class WithdrawalResponse(BaseModel):
    """Withdrawal response"""
    id: str
    portfolio_id: str
    amount: Decimal
    withdrawal_date: date
    withdrawal_type: str
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# PORTFOLIO SUMMARY SCHEMAS
# ============================================

class PortfolioSummary(BaseModel):
    """Complete portfolio summary with all holdings"""
    portfolio: PortfolioResponse
    positions: List[PositionResponse]
    withdrawals: List[WithdrawalResponse]
    health_score: Optional[float] = None
    safe_withdrawal_rate: Optional[float] = None
    needs_price_update: List[str] = []  # List of symbols needing price update


