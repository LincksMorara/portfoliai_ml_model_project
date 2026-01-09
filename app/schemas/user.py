"""
User and Auth Pydantic Schemas
Request/Response models for API endpoints
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============================================
# AUTH SCHEMAS
# ============================================

class UserSignup(BaseModel):
    """Sign up request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenData(BaseModel):
    """Data encoded in JWT token"""
    user_id: str
    email: str


# ============================================
# USER SCHEMAS
# ============================================

class UserBase(BaseModel):
    """Base user fields"""
    email: EmailStr
    full_name: Optional[str] = None


class UserResponse(UserBase):
    """User response (public safe)"""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# INVESTOR PROFILE SCHEMAS
# ============================================

class InvestorProfileCreate(BaseModel):
    """Create investor profile"""
    # Core ML-generated fields from survey
    risk_score: Optional[Decimal] = Field(None, ge=0, le=1)
    risk_category: Optional[str] = None
    persona: Optional[str] = None
    
    # Legacy/optional fields for backward compatibility
    risk_tolerance: Optional[Decimal] = Field(None, ge=0, le=1)
    investment_goals: Optional[List[str]] = None
    time_horizon: Optional[str] = None
    expected_return_min: Optional[int] = Field(None, ge=0)
    expected_return_max: Optional[int] = Field(None, ge=0)
    
    # Survey data
    category: Optional[str] = None  # Alternative field name for risk_category
    survey_responses: Optional[dict] = None
    timestamp: Optional[str] = None  # When survey was completed


class InvestorProfileUpdate(BaseModel):
    """Update investor profile (all fields optional)"""
    risk_tolerance: Optional[Decimal] = Field(None, ge=0, le=1)
    investment_goals: Optional[List[str]] = None
    time_horizon: Optional[str] = Field(None, pattern="^(short|medium|long)$")
    expected_return_min: Optional[int] = Field(None, ge=0)
    expected_return_max: Optional[int] = Field(None, ge=0)
    risk_category: Optional[str] = Field(None, pattern="^(conservative|moderate|aggressive)$")
    survey_responses: Optional[dict] = None


class InvestorProfileResponse(BaseModel):
    """Investor profile response"""
    id: str
    user_id: str
    
    # Core fields
    risk_score: Optional[Decimal]
    risk_category: Optional[str]
    persona: Optional[str]
    
    # Legacy fields
    risk_tolerance: Optional[Decimal]
    investment_goals: Optional[List[str]]
    time_horizon: Optional[str]
    expected_return_min: Optional[int]
    expected_return_max: Optional[int]
    
    survey_responses: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


