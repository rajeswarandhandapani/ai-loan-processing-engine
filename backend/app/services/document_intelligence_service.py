import logging
import time
import pathlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, ServiceResponseError, HttpResponseError

from app.config import settings
from app.logging_config import get_logger
from app.models.document_intelligence_models import (
    DocumentAnalysisResponse,
    DocumentPage,
    DocumentTable,
    DocumentField,
)
from app.utils.document_cache import DocumentCache

logger = get_logger(__name__)


class DocumentIntelligenceService:
    """Service for document intelligent processing using Azure Document Intelligence."""

    MODEL_MAP = {
        "bank_statement": "prebuilt-bankStatement.us",
        "invoice": "prebuilt-invoice",
        "receipt": "prebuilt-receipt",
        "tax_w2": "prebuilt-tax.us.w2",
        "prebuilt-layout": "prebuilt-layout",
    }

    def __init__(self):
        # Configure retry policy for Azure Document Intelligence
        # Retry up to 3 times with exponential backoff starting at 2 seconds
        # Total timeout of 120 seconds for document analysis (OCR is slow)
        self.client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
            retry_total=3,
            retry_backoff_factor=2,
            retry_mode="exponential",
        )
        
        # Initialize cache
        self.cache = DocumentCache()

    async def analyze_document(
        self,
        file_path: Path,
        document_type: str = "prebuilt-layout",
    ) -> DocumentAnalysisResponse:
        """
        Analyze a document using Azure Document Intelligence.
        
        Args:
            file_path: Path to the document file
            document_type: Type of document to analyze
            
        Returns:
            DocumentAnalysisResponse with extracted content
            
        Raises:
            AzureError: For Azure service-specific errors including rate limits
            ServiceResponseError: For network/service connectivity issues
            Exception: For other unexpected errors
        """
        model_id = self.MODEL_MAP.get(document_type, document_type)
        start_time = time.time()

        logger.info(f"Analyzing document: {file_path}")
        logger.debug(f"Using model: {model_id}")
        
        # Check cache first
        cache_key = self.cache.get_cache_key(file_path, document_type)
        cached_result = self.cache.load(cache_key, DocumentAnalysisResponse)
        if cached_result:
            return cached_result
        
        logger.info(f"Cache MISS: Calling Azure Document Intelligence API...")

        try:
            with open(file_path, "rb") as f:
                logger.debug(f"Opened file: {file_path}")
                
                # Track the Azure API call with timing
                api_start = time.time()
                poller = self.client.begin_analyze_document(
                    model_id=model_id,
                    body=f,
                    content_type="application/octet-stream",
                )
                api_call_time = time.time() - api_start
                logger.info(f"Azure Document Intelligence API call initiated in {api_call_time:.2f}s")

            logger.debug("Waiting for document analysis to complete...")
            wait_start = time.time()
            result = poller.result()
            wait_time = time.time() - wait_start
            
            total_time = time.time() - start_time
            logger.info(f"Document analysis completed successfully for {pathlib.Path(file_path).name} "
                       f"(API: {api_call_time:.2f}s, Processing: {wait_time:.2f}s, Total: {total_time:.2f}s)")
            
            response = self._extract_result(result, document_type, model_id)
            
            # Save to cache
            self.cache.save(cache_key, response)
            
            return response
            
        except HttpResponseError as e:
            if e.status_code == 429:
                logger.warning(f"Rate limit exceeded for Document Intelligence: {e.message}")
                raise AzureError(f"Service rate limit exceeded. Please try again later. {e.message}")
            elif e.status_code == 408:
                logger.warning(f"Request timeout for Document Intelligence: {e.message}")
                raise AzureError(f"Request timed out. The document may be too large or complex. {e.message}")
            else:
                logger.error(f"HTTP error {e.status_code} from Document Intelligence: {e.message}")
                raise AzureError(f"Document Intelligence service error: {e.message}")
                
        except ServiceResponseError as e:
            logger.error(f"Network/service connectivity error: {str(e)}")
            raise ServiceResponseError(f"Unable to connect to Document Intelligence service: {str(e)}")
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Unexpected error analyzing document {file_path} after {total_time:.2f}s: {str(e)}", exc_info=True)
            raise

    def _extract_result(
        self,
        result: Any,
        document_type: str,
        model_id: str,
    ) -> DocumentAnalysisResponse:
        """
        Extract and structure the analysis result from Azure Document Intelligence.
        
        Args:
            result: Raw result from Azure Document Intelligence
            document_type: Original document type requested
            model_id: Model ID used for analysis
            
        Returns:
            Structured DocumentAnalysisResponse
        """
        # Extract pages
        pages = self._extract_pages(result)
        
        # Extract tables
        tables = self._extract_tables(result)
        
        # Extract fields from documents
        fields, documents = self._extract_fields_and_documents(result)
        
        return DocumentAnalysisResponse(
            document_type=document_type,
            model_id=model_id,
            content=result.content if hasattr(result, "content") else None,
            pages=pages,
            tables=tables,
            fields=fields,
            documents=documents,
        )

    def _extract_pages(self, result: Any) -> List[DocumentPage]:
        """Extract page information from the result."""
        pages = []
        if hasattr(result, "pages") and result.pages:
            for page in result.pages:
                lines = []
                words_count = 0
                
                if hasattr(page, "lines") and page.lines:
                    lines = [line.content for line in page.lines if hasattr(line, "content")]
                
                if hasattr(page, "words") and page.words:
                    words_count = len(page.words)
                
                pages.append(
                    DocumentPage(
                        page_number=page.page_number if hasattr(page, "page_number") else 0,
                        width=page.width if hasattr(page, "width") else None,
                        height=page.height if hasattr(page, "height") else None,
                        unit=page.unit if hasattr(page, "unit") else None,
                        lines=lines,
                        words_count=words_count,
                    )
                )
        return pages

    def _extract_tables(self, result: Any) -> List[DocumentTable]:
        """Extract table information from the result."""
        tables = []
        if hasattr(result, "tables") and result.tables:
            for table in result.tables:
                cells = []
                if hasattr(table, "cells") and table.cells:
                    for cell in table.cells:
                        cells.append({
                            "row_index": cell.row_index if hasattr(cell, "row_index") else 0,
                            "column_index": cell.column_index if hasattr(cell, "column_index") else 0,
                            "content": cell.content if hasattr(cell, "content") else "",
                            "kind": cell.kind if hasattr(cell, "kind") else None,
                        })
                
                tables.append(
                    DocumentTable(
                        row_count=table.row_count if hasattr(table, "row_count") else 0,
                        column_count=table.column_count if hasattr(table, "column_count") else 0,
                        cells=cells,
                    )
                )
        return tables

    def _extract_fields_and_documents(
        self,
        result: Any,
    ) -> tuple[Dict[str, DocumentField], List[Dict[str, Any]]]:
        """Extract fields and document information from the result."""
        fields: Dict[str, DocumentField] = {}
        documents: List[Dict[str, Any]] = []
        
        if hasattr(result, "documents") and result.documents:
            for doc in result.documents:
                doc_info = {
                    "doc_type": doc.doc_type if hasattr(doc, "doc_type") else None,
                    "confidence": doc.confidence if hasattr(doc, "confidence") else None,
                    "fields": {},
                }
                
                if hasattr(doc, "fields") and doc.fields:
                    for field_name, field_value in doc.fields.items():
                        extracted_field = self._extract_field(field_name, field_value)
                        fields[field_name] = extracted_field
                        doc_info["fields"][field_name] = {
                            "value": extracted_field.value,
                            "confidence": extracted_field.confidence,
                            "value_type": extracted_field.value_type,
                        }
                
                documents.append(doc_info)
        
        return fields, documents

    def _extract_field(self, field_name: str, field_value: Any) -> DocumentField:
        """Extract a single field value."""
        value = None
        confidence = None
        value_type = None
        
        if field_value is not None:
            confidence = field_value.confidence if hasattr(field_value, "confidence") else None
            value_type = field_value.type if hasattr(field_value, "type") else None
            
            # Extract value based on type
            if hasattr(field_value, "value_string"):
                value = field_value.value_string
            elif hasattr(field_value, "value_number"):
                value = field_value.value_number
            elif hasattr(field_value, "value_date"):
                value = str(field_value.value_date) if field_value.value_date else None
            elif hasattr(field_value, "value_currency"):
                currency = field_value.value_currency
                if currency:
                    value = {
                        "amount": currency.amount if hasattr(currency, "amount") else None,
                        "currency_code": currency.currency_code if hasattr(currency, "currency_code") else None,
                    }
            elif hasattr(field_value, "value_address"):
                addr = field_value.value_address
                if addr:
                    value = {
                        "street": addr.street_address if hasattr(addr, "street_address") else None,
                        "city": addr.city if hasattr(addr, "city") else None,
                        "state": addr.state if hasattr(addr, "state") else None,
                        "postal_code": addr.postal_code if hasattr(addr, "postal_code") else None,
                    }
            elif hasattr(field_value, "content"):
                value = field_value.content
            elif hasattr(field_value, "value"):
                value = field_value.value
        
        return DocumentField(
            name=field_name,
            value=value,
            confidence=confidence,
            value_type=value_type,
        )

