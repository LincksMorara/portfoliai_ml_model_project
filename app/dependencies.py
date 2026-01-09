"""
FastAPI Dependencies
Dependency injection for routes (auth, database access, etc.)
"""

from typing import Optional
from fastapi import Depends, HTTPException, Header, Cookie
from supabase import Client

from app.database import get_supabase
from app.services.auth_service import get_auth_service, AuthService
from app.schemas.user import UserResponse


async def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Get current authenticated user from JWT token
    
    Checks in order:
    1. Authorization header (Bearer token)
    2. access_token cookie
    
    Raises:
        HTTPException: 401 if not authenticated or invalid token
    """
    token = None
    
    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    # Fall back to cookie
    elif access_token:
        token = access_token
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please login.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[UserResponse]:
    """
    Get current user if authenticated, None otherwise
    Use for endpoints that work with or without auth
    """
    try:
        return await get_current_user(authorization, access_token, auth_service)
    except HTTPException:
        return None


