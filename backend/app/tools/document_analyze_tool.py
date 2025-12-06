from langchain_core.tools import tool
from pathlib import Path
from typing import Dict, Any
from app.services.document_intelligence_service import DocumentIntelligenceService


document_intelligence_service = DocumentIntelligenceService()

@tool
async def analyze_financial_document(file_path: Path, document_type: str = "prebuilt-layout") -> Dict[str, Any]:
    """
    Analyze uploaded financial documents (e.g., bank statements, invoices, receipts, tax forms)

    Use this tool to extract key information from financial documents.
    
    Args:
        file_path: Absolute path to the document file
        document_type: Type of document to analyze - options are:
        - 'bank_statement': For bank statements
        - 'invoice': For invoices
        - 'receipt': For receipts
        - 'tax_w2': For tax forms
        - 'prebuilt-layout': For general document analysis
        
    Returns:
        DocumentAnalysisResponse with extracted content
    """
    try:
        result = await document_intelligence_service.analyze_document(
            file_path=file_path,
            document_type=document_type,
        )
        return result.model_dump()
    except Exception as e:
        return {
            "error": str(e)
        }