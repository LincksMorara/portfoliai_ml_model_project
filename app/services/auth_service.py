"""
Authentication Service
Handles user signup, login, and session management with Supabase Auth
"""

import logging
from typing import Optional, Dict, Any
from gotrue.errors import AuthApiError
from supabase import Client

from app.database import supabase, supabase_admin
from app.schemas.user import UserSignup, UserLogin, UserResponse, InvestorProfileCreate
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Authentication service using Supabase Auth"""
    
    def __init__(self, db: Client = supabase):
        self.db = db
    
    async def signup(
        self, 
        signup_data: UserSignup,
        investor_profile: Optional[InvestorProfileCreate] = None
    ) -> Dict[str, Any]:
        """
        Sign up new user with Supabase Auth
        Automatically sends verification email
        
        Args:
            signup_data: User signup information
            investor_profile: Optional investor profile data
            
        Returns:
            Dict with user info and message about email verification
            
        Raises:
            ValueError: If signup fails
        """
        try:
            # Use admin API to create user (bypasses email validation issues)
            auth_response = supabase_admin.auth.admin.create_user({
                "email": signup_data.email,
                "password": signup_data.password,
                "email_confirm": True,  # Auto-confirm for development
                "user_metadata": {
                    "full_name": signup_data.full_name
                }
            })
            
            if not auth_response.user:
                raise ValueError("Signup failed - no user returned")
            
            user = auth_response.user
            logger.info(f"✅ New user signed up: {signup_data.email} (ID: {user.id})")
            
            # Create user record in public.users table (use admin client to bypass RLS)
            user_record = {
                "id": str(user.id),
                "email": signup_data.email,
                "full_name": signup_data.full_name
            }
            
            supabase_admin.table("users").insert(user_record).execute()
            logger.info(f"✅ User record created for {signup_data.email}")
            
            # Create investor profile if provided
            if investor_profile:
                profile_data = investor_profile.dict(exclude_none=True)
                profile_data["user_id"] = str(user.id)
                
                # Convert Decimal to float for JSON serialization
                for key, value in list(profile_data.items()):
                    if hasattr(value, '__float__'):  # Check if it's a Decimal or similar
                        profile_data[key] = float(value)
                
                # Handle alternative field names from frontend
                # Map 'category' to 'risk_category' if needed
                if "category" in profile_data:
                    if not profile_data.get("risk_category"):
                        profile_data["risk_category"] = profile_data["category"]
                    # Always remove 'category' as it's not in DB schema
                    del profile_data["category"]
                
                # Map risk_category values to database-allowed values
                # Database allows: 'Conservative', 'Comfortable', 'Enthusiastic', 'conservative', 'moderate', 'aggressive'
                risk_category_mapping = {
                    'Balanced': 'Comfortable',
                    'balanced': 'moderate',
                    'Low': 'Conservative',
                    'low': 'conservative',
                    'High': 'Enthusiastic',
                    'high': 'aggressive',
                    'Moderate': 'Comfortable',
                    'moderate': 'moderate',
                    'Conservative': 'Conservative',
                    'conservative': 'conservative',
                    'Enthusiastic': 'Enthusiastic',
                    'enthusiastic': 'aggressive',
                    'Aggressive': 'Enthusiastic',
                    'aggressive': 'aggressive'
                }
                if profile_data.get("risk_category"):
                    mapped = risk_category_mapping.get(profile_data["risk_category"])
                    if mapped:
                        profile_data["risk_category"] = mapped
                    # If not in mapping and not already valid, default to 'moderate'
                    elif profile_data["risk_category"] not in ['Conservative', 'Comfortable', 'Enthusiastic', 'conservative', 'moderate', 'aggressive']:
                        profile_data["risk_category"] = 'moderate'
                
                # Set risk_tolerance from risk_score if not provided
                if profile_data.get("risk_score") and not profile_data.get("risk_tolerance"):
                    profile_data["risk_tolerance"] = float(profile_data["risk_score"])
                
                # Remove timestamp if present (not in DB schema)
                profile_data.pop("timestamp", None)
                
                logger.info(f"Profile data to insert: {profile_data.keys()}")
                
                supabase_admin.table("investor_profiles").insert(profile_data).execute()
                logger.info(f"✅ Investor profile created for {signup_data.email}: {profile_data.get('persona', 'N/A')}")
            
            # Create default portfolio
            portfolio_data = {
                "user_id": str(user.id),
                "name": "My Portfolio",
                "currency": "USD"
            }
            supabase_admin.table("portfolios").insert(portfolio_data).execute()
            logger.info(f"✅ Default portfolio created for {signup_data.email}")
            
            user_response = UserResponse(
                id=str(user.id),
                email=signup_data.email,
                full_name=signup_data.full_name,
                created_at=user.created_at
            )
            
            return {
                "user": user_response.dict(),
                "message": "Signup successful! Your account is ready. You can now login.",
                "email_confirmation_required": False
            }
            
        except AuthApiError as e:
            logger.error(f"❌ Supabase auth error during signup: {e}")
            raise ValueError(f"Signup failed: {e.message}")
        except Exception as e:
            logger.error(f"❌ Signup error: {e}")
            raise ValueError(f"Signup failed: {str(e)}")
    
    async def login(self, login_data: UserLogin) -> Dict[str, Any]:
        """
        Login user with Supabase Auth
        
        Args:
            login_data: Login credentials
            
        Returns:
            Dict with access token and user info
            
        Raises:
            ValueError: If login fails
        """
        try:
            # Sign in with Supabase Auth
            auth_response = self.db.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if not auth_response.user or not auth_response.session:
                raise ValueError("Login failed - invalid credentials")
            
            user = auth_response.user
            session = auth_response.session
            
            # Note: email_confirmed_at might be None even for auto-confirmed users
            # We'll allow login if we got a valid session
            if not session:
                raise ValueError("Login failed - no session created")
            
            logger.info(f"✅ User logged in: {login_data.email}")
            
            # Get user data from database
            user_data = self.db.table("users")\
                .select("*")\
                .eq("id", str(user.id))\
                .execute()
            
            if not user_data.data:
                raise ValueError("User data not found")
            
            user_record = user_data.data[0]
            
            return {
                "access_token": session.access_token,
                "token_type": "bearer",
                "user": UserResponse(
                    id=user_record["id"],
                    email=user_record["email"],
                    full_name=user_record.get("full_name"),
                    created_at=user_record["created_at"]
                )
            }
            
        except AuthApiError as e:
            logger.error(f"❌ Supabase auth error during login: {e}")
            if "Invalid login credentials" in str(e):
                raise ValueError("Invalid email or password")
            elif "Email not confirmed" in str(e):
                raise ValueError("Please verify your email before logging in")
            raise ValueError(f"Login failed: {e.message}")
        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            raise ValueError(f"Login failed: {str(e)}")
    
    async def get_current_user(self, access_token: str) -> Optional[UserResponse]:
        """
        Get current user from access token
        
        Args:
            access_token: JWT access token from login
            
        Returns:
            UserResponse or None if invalid token
        """
        try:
            # Get user from token
            user = self.db.auth.get_user(access_token)
            
            if not user or not user.user:
                return None
            
            # Get full user data
            user_data = self.db.table("users")\
                .select("*")\
                .eq("id", str(user.user.id))\
                .execute()
            
            if not user_data.data:
                return None
            
            user_record = user_data.data[0]
            
            return UserResponse(
                id=user_record["id"],
                email=user_record["email"],
                full_name=user_record.get("full_name"),
                created_at=user_record["created_at"]
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting current user: {e}")
            return None
    
    async def logout(self, access_token: str) -> bool:
        """
        Logout user (invalidate session)
        
        Args:
            access_token: JWT access token
            
        Returns:
            True if successful
        """
        try:
            self.db.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"❌ Logout error: {e}")
            return False
    
    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token from login
            
        Returns:
            New access token and user info
        """
        try:
            session = self.db.auth.refresh_session(refresh_token)
            
            if not session or not session.session:
                raise ValueError("Failed to refresh session")
            
            return {
                "access_token": session.session.access_token,
                "refresh_token": session.session.refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"❌ Session refresh error: {e}")
            raise ValueError("Failed to refresh session")


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create AuthService instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(supabase)
    return _auth_service


