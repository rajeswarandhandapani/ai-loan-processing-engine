"""
============================================================================
Main FastAPI Application Entry Point
============================================================================
This is the main entry point for the AI Loan Processing Engine backend.

Key Concepts:
- FastAPI: Modern, high-performance Python web framework
- ASGI: Asynchronous Server Gateway Interface (async version of WSGI)
- Lifespan: Application startup/shutdown lifecycle management
- CORS: Cross-Origin Resource Sharing for frontend communication

Architecture Overview:
- main.py: Application entry point and configuration
- routers/: API endpoint definitions (chat, documents)
- services/: Business logic layer (agent, document processing)
- models/: Pydantic data models for request/response validation
- tools/: LangChain tools for AI agent capabilities
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.routers import document_intelligence_router, chat_router

# ============================================================================
# Logging Initialization
# ============================================================================
# Set up structured logging before anything else runs.
# This ensures all subsequent log messages are properly formatted.
setup_logging()
logger = get_logger(__name__)


# ============================================================================
# Application Lifespan Management
# ============================================================================
# The lifespan context manager handles application startup and shutdown.
# 
# Why use lifespan instead of @app.on_event()?
# - @app.on_event() is deprecated in FastAPI
# - Lifespan provides cleaner resource management
# - Allows for async initialization/cleanup
# 
# Common use cases:
# - Initialize database connections
# - Load ML models into memory
# - Set up connection pools
# - Clean up resources on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # === Startup Phase ===
    logger.info("🚀 Starting AI Loan Processing Engine")
    logger.info(f"Debug mode: {settings.debug}")
    
    yield  # Application runs here
    
    # === Shutdown Phase ===
    logger.info("🛑 Shutting down AI Loan Processing Engine")


# ============================================================================
# FastAPI Application Instance
# ============================================================================
# Create the main FastAPI application with metadata for API documentation.
# 
# FastAPI automatically generates:
# - OpenAPI schema at /openapi.json
# - Swagger UI at /docs
# - ReDoc at /redoc
app = FastAPI(
    title=settings.app_name,
    description="AI-powered loan processing engine with Azure AI services",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================================
# CORS Middleware Configuration
# ============================================================================
# CORS (Cross-Origin Resource Sharing) is essential for frontend-backend
# communication when they run on different ports.
# 
# Without CORS:
# - Browser blocks requests from http://localhost:4200 to http://localhost:8000
# - This is a security feature to prevent malicious cross-site requests
# 
# Our configuration:
# - allow_origins: Which domains can make requests (Angular dev server)
# - allow_credentials: Allow cookies and auth headers
# - allow_methods: HTTP methods permitted (GET, POST, etc.)
# - allow_headers: Which headers are allowed in requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",      # Angular dev server
        "http://127.0.0.1:4200",      # Angular dev server (IP address)
        "http://localhost:3000",      # Alternative frontend port
        "http://127.0.0.1:3000"       # Alternative frontend port (IP)
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)


# ============================================================================
# Health Check & Root Endpoints
# ============================================================================
# These endpoints are essential for:
# - Load balancers to verify service availability
# - Kubernetes liveness/readiness probes
# - Monitoring systems to check service health

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "healthy", "service": settings.app_name}


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {"message": "Welcome to AI Loan Processing Engine", "version": "1.0.0"}


# ============================================================================
# Router Registration
# ============================================================================
# Routers are modular collections of related endpoints.
# 
# Benefits of using routers:
# - Organize endpoints by feature (chat, documents)
# - Each router can have its own prefix and tags
# - Easier to maintain and test individual features
# 
# URL structure:
# - /api/v1/chat/* - Chat and AI agent endpoints
# - /api/v1/documents/* - Document upload and analysis
app.include_router(document_intelligence_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


# ============================================================================
# Development Server
# ============================================================================
# This block runs only when executing the file directly (python -m app.main).
# 
# Uvicorn is an ASGI server that:
# - Handles HTTP requests asynchronously
# - Supports WebSockets
# - Hot-reloads code changes in debug mode
# 
# In production, use: uvicorn app.main:app --workers 4
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",            # Listen on all network interfaces
        port=8000,                  # Default API port
        reload=settings.debug,      # Auto-reload on code changes
        log_level="info",
    )
