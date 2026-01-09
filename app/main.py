"""
PortfoliAI FastAPI Application (Production Version)
Main application entry point with Supabase integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from pathlib import Path

from app.config import get_settings
from app.routers import auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="PortfoliAI",
    description="AI-Powered Investment Advisory Platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)

# TODO: Add other routers as we build them
# app.include_router(portfolio.router)
# app.include_router(chatbot.router)
# app.include_router(survey.router)


# Error Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PortfoliAI v2.0",
        "database": "Supabase",
        "auth": "Supabase Auth"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - serve landing page"""
    return {
        "message": "Welcome to PortfoliAI API v2.0",
        "docs": "/api/docs",
        "health": "/health",
        "auth": {
            "signup": "/api/auth/signup",
            "login": "/api/auth/login",
            "me": "/api/auth/me"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 PortfoliAI v2.0 starting...")
    logger.info(f"📊 Supabase URL: {settings.SUPABASE_URL}")
    logger.info(f"🔒 Email verification: Enabled (via Supabase)")
    logger.info(f"✅ Application started successfully!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 PortfoliAI shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )


