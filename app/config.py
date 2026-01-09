"""
Application Configuration
Manages environment variables and settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Info
    APP_NAME: str = "PortfoliAI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Supabase Settings (Optional - will use fallback if not provided)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None  # Anon key for client-side
    SUPABASE_SERVICE_KEY: Optional[str] = None  # Service role key for server-side admin operations
    
    # Database
    DATABASE_URL: Optional[str] = None  # Will be constructed from Supabase URL
    
    # API Keys
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    FMP_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: Optional[str] = "dev-secret-key-change-in-production"  # For JWT signing (generate a random string)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_database_url(self) -> str:
        """
        Construct PostgreSQL connection string from Supabase URL
        Format: postgresql://postgres:[password]@[host]:[port]/postgres
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Extract host from Supabase URL
        # Example: https://xxx.supabase.co -> xxx.supabase.co
        host = self.SUPABASE_URL.replace("https://", "").replace("http://", "")
        
        # Supabase direct database connection
        # You'll need to get the DB password from Supabase project settings
        return f"postgresql://postgres:your_db_password@db.{host}:5432/postgres"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance
    Only loads environment variables once
    """
    return Settings()


# For backward compatibility
settings = get_settings()


