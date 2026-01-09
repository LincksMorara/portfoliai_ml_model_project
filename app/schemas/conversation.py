"""
Conversation and Chatbot Pydantic Schemas
Request/Response models for AI chatbot
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================
# CONVERSATION SCHEMAS
# ============================================

class ConversationCreate(BaseModel):
    """Create new conversation"""
    title: str = Field(default="New Chat", max_length=200)


class ConversationUpdate(BaseModel):
    """Update conversation (rename)"""
    title: str = Field(..., max_length=200)


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ============================================
# MESSAGE SCHEMAS
# ============================================

class MessageCreate(BaseModel):
    """Create message in conversation"""
    conversation_id: str
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# CHATBOT SCHEMAS
# ============================================

class ChatRequest(BaseModel):
    """Chat request to AI"""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response from AI"""
    response: str
    conversation_id: Optional[str]
    type: str  # 'analysis', 'general_research', 'portfolio_query', etc.
    query_style: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = []
    market_data_source: Optional[str] = None
    timestamp: datetime


# ============================================
# CONVERSATION LIST SCHEMAS
# ============================================

class ConversationListResponse(BaseModel):
    """List of conversations with summary"""
    conversations: List[ConversationResponse]


class ConversationDetailResponse(BaseModel):
    """Conversation with all messages"""
    conversation: ConversationResponse
    messages: List[MessageResponse]


