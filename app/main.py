"""
GOP API Server - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import APILoggingMiddleware
from app.routers import auth
from app.utils.init_db import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    print("=" * 60)
    print("GOP API Server Starting...")
    print("=" * 60)

    # Initialize database
    initialize_database()

    print(f"Server running on http://{settings.HOST}:{settings.PORT}")
    print(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Authentication Mode: {settings.AUTH_MODE}")
    print("=" * 60)

    yield

    # Shutdown
    print("GOP API Server Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="GOP RESTful API Server",
    description="Guarding Operation Platform RESTful API Server",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middlewares (order matters - applied in reverse)
app.add_middleware(APILoggingMiddleware)  # Applied second
app.add_middleware(RequestIDMiddleware)   # Applied first

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "GOP RESTful API Server",
        "version": "1.0.0",
        "status": "running",
        "auth_mode": settings.AUTH_MODE,
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "auth_mode": settings.AUTH_MODE
    }