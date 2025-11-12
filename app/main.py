"""
GOP API Server - Main Application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import APILoggingMiddleware
from app.routers import auth, logs, controllers, sensors, cameras, detections, malfunctions, connections, actions
from app.utils.init_db import initialize_database
from app.schemas.common import ApiResponse


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
    description="General Outpost RESTful API Server",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    generate_unique_id_function=lambda route: f"{route.name}"
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTPException and return ApiResponse format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors and return ApiResponse format
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error: " + "; ".join(errors),
            "data": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions and return ApiResponse format
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"Internal server error: {str(exc)}",
            "data": None
        }
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
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(controllers.router, prefix="/api/devices/controllers", tags=["Controllers"])
app.include_router(sensors.router, prefix="/api/devices/sensors", tags=["Sensors"])
app.include_router(cameras.router, prefix="/api/devices/cameras", tags=["Cameras"])
app.include_router(detections.router, prefix="/api/events/detections", tags=["Detections"])
app.include_router(malfunctions.router, prefix="/api/events/malfunctions", tags=["Malfunctions"])
app.include_router(connections.router, prefix="/api/events/connections", tags=["Connections"])
app.include_router(actions.router, prefix="/api/events/actions", tags=["Actions"])

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