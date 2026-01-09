"""
Authentication API Router
Handles signup, login, logout with Supabase Auth
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from app.services.auth_service import get_auth_service, AuthService
from app.schemas.user import UserSignup, UserLogin, Token, UserResponse, InvestorProfileCreate
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class SignupRequest(BaseModel):
    """Combined signup and investor profile request"""
    email: str
    password: str
    full_name: Optional[str] = None
    investor_profile: Optional[InvestorProfileCreate] = None


@router.post("/signup")
async def signup(
    request: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Sign up new user with Supabase Auth
    
    - Creates user account
    - Sends verification email automatically
    - Creates default portfolio
    - Creates investor profile if provided
    
    Returns:
        Message about email verification
    """
    try:
        # Create UserSignup from request
        signup_data = UserSignup(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        result = await auth_service.signup(signup_data, request.investor_profile)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again.")


@router.post("/login")
async def login(
    login_data: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login user with email and password
    
    - Validates credentials
    - Checks email verification
    - Returns JWT token
    - Sets httpOnly cookie
    
    Returns:
        access_token, user info
    """
    try:
        result = await auth_service.login(login_data)
        
        # Set httpOnly cookie for web clients
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=1800  # 30 minutes
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


@router.post("/logout")
async def logout(
    response: Response,
    access_token: Optional[str] = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current user
    
    - Invalidates session
    - Clears cookies
    
    Returns:
        Success message
    """
    if access_token:
        await auth_service.logout(access_token)
    
    # Clear cookie
    response.delete_cookie(key="access_token")
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user info
    
    Requires:
        Valid JWT token in Authorization header or cookie
    
    Returns:
        Current user information
    """
    return current_user


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_token: Refresh token from login
    
    Returns:
        New access token
    """
    try:
        result = await auth_service.refresh_session(refresh_token)
        
        # Update cookie
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=1800
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


