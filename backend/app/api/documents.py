"""Document endpoints — upload/analyze files and list supported types."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.deps import get_document_service, get_session_store
from app.core.logging import get_logger
from app.models import DocumentType, DocumentUploadResponse
from app.services.document_intelligence import DocumentIntelligenceService
from app.services.session_store import SessionDocumentStore

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Document Intelligence"])

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PDF_SIZE = 15 * 1024 * 1024  # 15MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

_DESCRIPTIONS = {
    DocumentType.BANK_STATEMENT: "US bank statements with transaction details",
    DocumentType.INVOICE: "Invoices with line items and totals",
    DocumentType.RECEIPT: "Receipts with merchant and purchase details",
    DocumentType.TAX_W2: "US W-2 tax forms",
    DocumentType.LAYOUT: "General document layout extraction",
}


def _validate_size(filename: str, size: int) -> str | None:
    """Return an error message if the file is too large, else None."""
    ext = Path(filename).suffix.lower()
    mb = size / 1024 / 1024
    if ext == ".pdf" and size > MAX_PDF_SIZE:
        return f"PDF file size ({mb:.1f}MB) exceeds {MAX_PDF_SIZE // 1024 // 1024}MB"
    if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"} and size > MAX_IMAGE_SIZE:
        return f"Image file size ({mb:.1f}MB) exceeds {MAX_IMAGE_SIZE // 1024 // 1024}MB"
    if size > MAX_FILE_SIZE:
        return f"File size ({mb:.1f}MB) exceeds {MAX_FILE_SIZE // 1024 // 1024}MB"
    return None


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload and analyze"),
    document_type: DocumentType = Query(default=DocumentType.LAYOUT),
    session_id: str | None = Query(default=None),
    service: DocumentIntelligenceService = Depends(get_document_service),
    session_store: SessionDocumentStore = Depends(get_session_store),
) -> DocumentUploadResponse:
    """Upload a document, analyze it, and (optionally) attach it to a session."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")
    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    size_error = _validate_size(file.filename, len(content))
    if size_error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=size_error
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        analysis = await service.analyze_document(temp_path, document_type.value)

        if session_id:
            try:
                session_store.add_document(
                    session_id=session_id,
                    filename=file.filename,
                    document_type=document_type.value,
                    analysis=analysis.model_dump(),
                )
            except Exception:  # noqa: BLE001 — session storage is best-effort
                logger.exception("Failed to store document in session %s", session_id)

        return DocumentUploadResponse(
            success=True,
            message="Document analyzed successfully",
            filename=file.filename,
            document_type=document_type.value,
            analysis=analysis,
        )
    except Exception as exc:  # noqa: BLE001 — report failure in the 200 body (frontend contract)
        logger.exception("Document analysis failed for %s", file.filename)
        return DocumentUploadResponse(
            success=False,
            message="Document analysis failed",
            filename=file.filename,
            document_type=document_type.value,
            error=str(exc),
        )
    finally:
        if temp_path and temp_path.exists():
            os.unlink(temp_path)


@router.get("/types")
async def get_document_types() -> dict:
    """List the supported document types and their descriptions."""
    return {
        "document_types": [
            {"value": dt.value, "name": dt.name, "description": _DESCRIPTIONS.get(dt, "")}
            for dt in DocumentType
        ]
    }
