"""
API route definitions for the backend application.

This package contains FastAPI routers for:
- /documents - Document upload and processing with Azure Document Intelligence
- /chat - AI chat interactions
- /loan - Loan application management
"""

from app.routers.document_intelligence_router import router as document_intelligence_router

__all__ = ["document_intelligence_router"]
