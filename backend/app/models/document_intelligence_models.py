"""
Pydantic models for Document Intelligence API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types for analysis."""
    BANK_STATEMENT = "bank_statement"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    TAX_W2 = "tax_w2"
    LAYOUT = "prebuilt-layout"


class DocumentField(BaseModel):
    """Extracted field from a document."""
    name: str
    value: Optional[Any] = None
    confidence: Optional[float] = None
    value_type: Optional[str] = None


class DocumentTable(BaseModel):
    """Extracted table from a document."""
    row_count: int
    column_count: int
    cells: List[Dict[str, Any]] = Field(default_factory=list)


class DocumentPage(BaseModel):
    """Information about a document page."""
    page_number: int
    width: Optional[float] = None
    height: Optional[float] = None
    unit: Optional[str] = None
    lines: List[str] = Field(default_factory=list)
    words_count: int = 0


class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis."""
    document_type: str
    model_id: str
    content: Optional[str] = None
    pages: List[DocumentPage] = Field(default_factory=list)
    tables: List[DocumentTable] = Field(default_factory=list)
    fields: Dict[str, DocumentField] = Field(default_factory=dict)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""
    success: bool
    message: str
    filename: str
    document_type: str
    analysis: Optional[DocumentAnalysisResponse] = None
    error: Optional[str] = None
