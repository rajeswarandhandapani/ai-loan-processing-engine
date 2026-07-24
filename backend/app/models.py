"""Pydantic request/response models for the API and document analysis.

Kept in one module because the schemas are small and closely related. The
`document_type` string values and MODEL_MAP feed Azure Document Intelligence.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# --- Chat ---------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for POST /chat/."""

    message: str
    session_id: str


class ChatResponse(BaseModel):
    """Response body from POST /chat/."""

    message: str
    session_id: str


# --- Documents ----------------------------------------------------------------


class DocumentType(StrEnum):
    """Supported document types (values are the API/Azure identifiers)."""

    BANK_STATEMENT = "bank_statement"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    TAX_W2 = "tax_w2"
    LAYOUT = "prebuilt-layout"


# Maps document types to Azure Document Intelligence prebuilt model IDs.
MODEL_MAP = {
    DocumentType.BANK_STATEMENT.value: "prebuilt-bankStatement.us",
    DocumentType.INVOICE.value: "prebuilt-invoice",
    DocumentType.RECEIPT.value: "prebuilt-receipt",
    DocumentType.TAX_W2.value: "prebuilt-tax.us.w2",
    DocumentType.LAYOUT.value: "prebuilt-layout",
}


class DocumentField(BaseModel):
    """A single extracted field (e.g. VendorName, InvoiceTotal)."""

    name: str
    value: Any | None = None
    confidence: float | None = None
    value_type: str | None = None


class DocumentTable(BaseModel):
    """An extracted table (e.g. bank-statement transactions)."""

    row_count: int
    column_count: int
    cells: list[dict[str, Any]] = Field(default_factory=list)


class DocumentPage(BaseModel):
    """Metadata about a single document page."""

    page_number: int
    width: float | None = None
    height: float | None = None
    unit: str | None = None
    lines: list[str] = Field(default_factory=list)
    words_count: int = 0


class DocumentAnalysisResponse(BaseModel):
    """Full extracted content from a document analysis."""

    document_type: str
    model_id: str
    content: str | None = None
    pages: list[DocumentPage] = Field(default_factory=list)
    tables: list[DocumentTable] = Field(default_factory=list)
    fields: dict[str, DocumentField] = Field(default_factory=dict)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    raw_response: dict[str, Any] | None = None


class DocumentUploadResponse(BaseModel):
    """Response from POST /documents/upload."""

    success: bool
    message: str
    filename: str
    document_type: str
    analysis: DocumentAnalysisResponse | None = None
    error: str | None = None
