"""
Main FastAPI application entry point.

Provides the core API for the AI Loan Processing Engine.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import document_intelligence_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    description="AI-powered loan processing engine with Azure AI services",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],  # Angular dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to AI Loan Processing Engine", "version": "1.0.0"}


# Include routers
app.include_router(document_intelligence_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
