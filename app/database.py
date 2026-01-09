"""
Database Connection and Session Management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional
from supabase import create_client, Client
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

try:
    settings = get_settings()
    
    # Supabase Client (Primary database interface)
    supabase: Optional[Client] = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    
    # Admin Supabase Client (with service role key for admin operations)
    supabase_admin: Optional[Client] = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )
    
    logger.info("✅ Supabase clients initialized successfully")
    
except Exception as e:
    logger.warning(f"⚠️ Supabase not configured: {e}")
    logger.warning("Running in fallback mode - Supabase features disabled")
    supabase = None
    supabase_admin = None

# SQLAlchemy Base for models
Base = declarative_base()


def get_supabase() -> Client:
    """
    Dependency for getting Supabase client
    Use this in route dependencies
    """
    return supabase


def get_supabase_admin() -> Client:
    """
    Dependency for getting admin Supabase client
    Use sparingly - only for admin operations
    """
    return supabase_admin


