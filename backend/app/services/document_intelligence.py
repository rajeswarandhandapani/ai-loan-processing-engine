"""Azure Document Intelligence wrapper.

Analyzes an uploaded file with the appropriate prebuilt model and flattens the
SDK result into our own `DocumentAnalysisResponse`. Results are cached by file
content so repeated uploads are cheap.
"""

import time
from pathlib import Path
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceResponseError

from app.core.config import Settings
from app.core.logging import get_logger
from app.models import (
    MODEL_MAP,
    DocumentAnalysisResponse,
    DocumentField,
    DocumentPage,
    DocumentTable,
)
from app.services.document_cache import DocumentCache

logger = get_logger(__name__)


class DocumentIntelligenceService:
    """Analyzes documents via Azure Document Intelligence, with caching."""

    def __init__(self, settings: Settings) -> None:
        self.client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
            retry_total=3,
            retry_backoff_factor=2,
            retry_mode="exponential",
        )
        self.cache = DocumentCache(settings)

    async def analyze_document(
        self,
        file_path: Path,
        document_type: str = "prebuilt-layout",
    ) -> DocumentAnalysisResponse:
        """Analyze a document and return its extracted content."""
        model_id = MODEL_MAP.get(document_type, document_type)
        cache_key = self.cache.get_cache_key(file_path, document_type)
        cached = self.cache.load(cache_key, DocumentAnalysisResponse)
        if cached:
            return cached

        logger.info("Analyzing %s with model %s", file_path.name, model_id)
        start = time.time()
        try:
            with open(file_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    model_id=model_id,
                    body=f,
                    content_type="application/octet-stream",
                )
            result = poller.result()
        except HttpResponseError as e:
            if e.status_code == 429:
                raise HttpResponseError(
                    "Service rate limit exceeded. Please try again later."
                ) from e
            raise HttpResponseError(f"Document Intelligence error: {e.message}") from e
        except ServiceResponseError as e:
            raise ServiceResponseError(
                "Unable to connect to Document Intelligence service."
            ) from e

        logger.info("Analysis of %s completed in %.2fs", file_path.name, time.time() - start)
        response = self._to_response(result, document_type, model_id)
        self.cache.save(cache_key, response)
        return response

    def _to_response(
        self, result: Any, document_type: str, model_id: str
    ) -> DocumentAnalysisResponse:
        fields, documents = self._extract_fields_and_documents(result)
        return DocumentAnalysisResponse(
            document_type=document_type,
            model_id=model_id,
            content=getattr(result, "content", None),
            pages=self._extract_pages(result),
            tables=self._extract_tables(result),
            fields=fields,
            documents=documents,
        )

    def _extract_pages(self, result: Any) -> list[DocumentPage]:
        pages = []
        for page in getattr(result, "pages", None) or []:
            lines = [line.content for line in getattr(page, "lines", None) or [] if line.content]
            pages.append(
                DocumentPage(
                    page_number=getattr(page, "page_number", 0),
                    width=getattr(page, "width", None),
                    height=getattr(page, "height", None),
                    unit=getattr(page, "unit", None),
                    lines=lines,
                    words_count=len(getattr(page, "words", None) or []),
                )
            )
        return pages

    def _extract_tables(self, result: Any) -> list[DocumentTable]:
        tables = []
        for table in getattr(result, "tables", None) or []:
            cells = [
                {
                    "row_index": getattr(cell, "row_index", 0),
                    "column_index": getattr(cell, "column_index", 0),
                    "content": getattr(cell, "content", ""),
                    "kind": getattr(cell, "kind", None),
                }
                for cell in getattr(table, "cells", None) or []
            ]
            tables.append(
                DocumentTable(
                    row_count=getattr(table, "row_count", 0),
                    column_count=getattr(table, "column_count", 0),
                    cells=cells,
                )
            )
        return tables

    def _extract_fields_and_documents(
        self, result: Any
    ) -> tuple[dict[str, DocumentField], list[dict[str, Any]]]:
        fields: dict[str, DocumentField] = {}
        documents: list[dict[str, Any]] = []
        for doc in getattr(result, "documents", None) or []:
            doc_info = {
                "doc_type": getattr(doc, "doc_type", None),
                "confidence": getattr(doc, "confidence", None),
                "fields": {},
            }
            for name, value in (getattr(doc, "fields", None) or {}).items():
                field = self._extract_field(name, value)
                fields[name] = field
                doc_info["fields"][name] = {
                    "value": field.value,
                    "confidence": field.confidence,
                    "value_type": field.value_type,
                }
            documents.append(doc_info)
        return fields, documents

    def _extract_field(self, name: str, value: Any) -> DocumentField:
        extracted: Any = None
        confidence = None
        value_type = None
        if value is not None:
            confidence = getattr(value, "confidence", None)
            value_type = getattr(value, "type", None)
            if hasattr(value, "value_string"):
                extracted = value.value_string
            elif hasattr(value, "value_number"):
                extracted = value.value_number
            elif hasattr(value, "value_date"):
                extracted = str(value.value_date) if value.value_date else None
            elif hasattr(value, "value_currency") and value.value_currency:
                currency = value.value_currency
                extracted = {
                    "amount": getattr(currency, "amount", None),
                    "currency_code": getattr(currency, "currency_code", None),
                }
            elif hasattr(value, "value_address") and value.value_address:
                addr = value.value_address
                extracted = {
                    "street": getattr(addr, "street_address", None),
                    "city": getattr(addr, "city", None),
                    "state": getattr(addr, "state", None),
                    "postal_code": getattr(addr, "postal_code", None),
                }
            elif hasattr(value, "content"):
                extracted = value.content
            elif hasattr(value, "value"):
                extracted = value.value
        return DocumentField(
            name=name, value=extracted, confidence=confidence, value_type=value_type
        )
