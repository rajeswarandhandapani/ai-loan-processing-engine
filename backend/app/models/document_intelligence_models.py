"""
============================================================================
Document Intelligence API Models
============================================================================
Pydantic models for Azure Document Intelligence integration.

Key Concepts:
- Enum: Restricts values to a predefined set
- Nested Models: Complex data structures with validation
- Optional Fields: Handle missing data gracefully

Azure Document Intelligence:
- Extracts text, tables, and key-value pairs from documents
- Supports pre-built models for common document types
- Returns confidence scores for extracted data

Supported Document Types:
- Bank statements: Transaction tables, account details
- Invoices: Line items, totals, vendor info
- Receipts: Merchant, items, totals
- W-2 forms: Tax information
- Layout: General document structure
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Document Type Enumeration
# ============================================================================
# Maps user-friendly names to Azure Document Intelligence model IDs.
# Using Enum ensures only valid document types are accepted.
class DocumentType(str, Enum):
    """Supported document types for analysis."""
    BANK_STATEMENT = "bank_statement"    # US bank statements
    INVOICE = "invoice"                  # Business invoices
    RECEIPT = "receipt"                  # Purchase receipts
    TAX_W2 = "tax_w2"                    # US W-2 tax forms
    LAYOUT = "prebuilt-layout"           # General document layout


# ============================================================================
# Document Field Model
# ============================================================================
# Represents a single extracted field (e.g., "InvoiceTotal", "AccountNumber")
# Includes confidence score from Azure Document Intelligence
class DocumentField(BaseModel):
    """Extracted field from a document."""
    name: str                            # Field name (e.g., "VendorName")
    value: Optional[Any] = None          # Extracted value (various types)
    confidence: Optional[float] = None   # Confidence score (0.0 to 1.0)
    value_type: Optional[str] = None     # Type hint (string, number, date, etc.)


# ============================================================================
# Document Table Model
# ============================================================================
# Represents tables extracted from documents (e.g., transaction lists)
# Critical for bank statements and invoices with line items
class DocumentTable(BaseModel):
    """Extracted table from a document."""
    row_count: int                       # Number of rows in table
    column_count: int                    # Number of columns
    cells: List[Dict[str, Any]] = Field(default_factory=list)  # Cell data


# ============================================================================
# Document Page Model
# ============================================================================
# Metadata about each page in the document
# Useful for multi-page documents
class DocumentPage(BaseModel):
    """Information about a document page."""
    page_number: int                     # 1-indexed page number
    width: Optional[float] = None        # Page width (in specified unit)
    height: Optional[float] = None       # Page height
    unit: Optional[str] = None           # Unit of measurement (inch, pixel)
    lines: List[str] = Field(default_factory=list)  # Text lines on page
    words_count: int = 0                 # Total words on page


# ============================================================================
# Document Analysis Response Model
# ============================================================================
# Complete response from document analysis containing all extracted data.
# This is what the agent uses to answer questions about documents.
class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis."""
    document_type: str                   # Type of document analyzed
    model_id: str                        # Azure model used for analysis
    content: Optional[str] = None        # Full text content (OCR result)
    pages: List[DocumentPage] = Field(default_factory=list)    # Page metadata
    tables: List[DocumentTable] = Field(default_factory=list)  # Extracted tables
    fields: Dict[str, DocumentField] = Field(default_factory=dict)  # Key-value pairs
    documents: List[Dict[str, Any]] = Field(default_factory=list)   # Sub-documents
    raw_response: Optional[Dict[str, Any]] = None  # Original Azure response


# ============================================================================
# Document Upload Response Model
# ============================================================================
# Response returned to the frontend after document upload and analysis.
# Includes success status, analysis results, and any errors.
class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""
    success: bool                        # Whether upload/analysis succeeded
    message: str                         # Human-readable status message
    filename: str                        # Original filename
    document_type: str                   # Document type used for analysis
    analysis: Optional[DocumentAnalysisResponse] = None  # Analysis results
    error: Optional[str] = None          # Error message if failed
