"""
Document Intelligence API router.

Provides endpoints for document upload and analysis using Azure Document Intelligence.
"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Query, HTTPException, status

from app.models.document_intelligence_models import (
    DocumentType,
    DocumentUploadResponse,
    DocumentAnalysisResponse,
)
from app.services.document_intelligence_service import DocumentIntelligenceService
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Document Intelligence"])

# Initialize service
document_service = DocumentIntelligenceService()

# Supported file extensions
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def validate_file_extension(filename: str) -> bool:
    """Validate that the file has an allowed extension."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload and analyze a document",
    description="Upload a document file and analyze it using Azure Document Intelligence.",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload and analyze"),
    document_type: DocumentType = Query(
        default=DocumentType.LAYOUT,
        description="Type of document to analyze",
    ),
) -> DocumentUploadResponse:
    """
    Upload a document and analyze it using Azure Document Intelligence.
    
    Args:
        file: The document file to upload (PDF, PNG, JPG, JPEG, TIFF, BMP)
        document_type: The type of document for specialized extraction
        
    Returns:
        DocumentUploadResponse with analysis results
    """
    logger.info(f"Document upload request received - File: {file.filename}, Type: {document_type.value}")
    
    # Validate file extension
    if not file.filename or not validate_file_extension(file.filename):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Create temporary file to store upload
    temp_file_path = None
    try:
        # Save uploaded file to temporary location
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        logger.debug(f"File saved to temporary location: {temp_file_path}")

        # Analyze the document
        logger.info(f"Starting document analysis for: {file.filename}")
        analysis_result = await document_service.analyze_document(
            file_path=temp_file_path,
            document_type=document_type.value,
        )

        logger.info(f"Document analysis completed successfully for: {file.filename}")
        return DocumentUploadResponse(
            success=True,
            message="Document analyzed successfully",
            filename=file.filename,
            document_type=document_type.value,
            analysis=analysis_result,
        )

    except Exception as e:
        logger.error(f"Document analysis failed for {file.filename}: {str(e)}", exc_info=True)
        return DocumentUploadResponse(
            success=False,
            message="Document analysis failed",
            filename=file.filename or "unknown",
            document_type=document_type.value,
            error=str(e),
        )

    finally:
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            os.unlink(temp_file_path)
            logger.debug(f"Cleaned up temporary file: {temp_file_path}")


@router.get(
    "/types",
    summary="Get supported document types",
    description="Returns the list of supported document types for analysis.",
)
async def get_document_types() -> dict:
    """Get list of supported document types."""
    return {
        "document_types": [
            {
                "value": dt.value,
                "name": dt.name,
                "description": _get_document_type_description(dt),
            }
            for dt in DocumentType
        ]
    }


def _get_document_type_description(doc_type: DocumentType) -> str:
    """Get description for a document type."""
    descriptions = {
        DocumentType.BANK_STATEMENT: "US bank statements with transaction details",
        DocumentType.INVOICE: "Invoices with line items and totals",
        DocumentType.RECEIPT: "Receipts with merchant and purchase details",
        DocumentType.TAX_W2: "US W-2 tax forms",
        DocumentType.LAYOUT: "General document layout extraction",
    }
    return descriptions.get(doc_type, "Document analysis")
