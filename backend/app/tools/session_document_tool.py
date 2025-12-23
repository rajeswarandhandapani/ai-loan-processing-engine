"""
Agent tool for retrieving uploaded documents from the current session.

This tool allows the agent to access documents that were uploaded during
the current conversation, enabling it to answer questions about them.
"""

from langchain_core.tools import tool
from typing import Dict, Any
import contextvars
from app.services.session_document_store import get_session_document_store
from app.logging_config import get_logger

logger = get_logger(__name__)

# Context variable to store the current session ID
current_session_id: contextvars.ContextVar[str] = contextvars.ContextVar('current_session_id', default='')


@tool
async def get_analyzed_financial_documents_from_session() -> Dict[str, Any]:
    """
    Retrieve all analyzed financial documents from the current session.
    
    Use this tool when the user asks about documents they uploaded, mentions their
    bank statement, invoice, receipt, tax form, or any financial document.
    
    This tool returns the COMPLETE extracted data from documents that were already
    analyzed during upload - including all fields, tables, and full content.
    
    No parameters needed - automatically accesses the current conversation session.
        
    Returns:
        Dictionary containing:
        - count: Number of documents in session
        - summary: Human-readable summary
        - documents: List with FULL extracted data (fields, tables, content)
    """
    # Get session_id from context variable
    session_id = current_session_id.get()
    logger.info(f"Agent requesting analyzed documents for session: {session_id}")
    
    try:
        store = get_session_document_store()
        docs = store.get_documents(session_id)
        
        if not docs:
            logger.debug(f"No documents found for session {session_id}")
            return {
                "count": 0,
                "summary": "No documents have been uploaded in this session yet. Ask the user to upload their financial documents first.",
                "documents": []
            }
        
        # Build detailed document list with FULL data (no truncation)
        document_list = []
        for doc in docs:
            doc_info = {
                "filename": doc.filename,
                "document_type": doc.document_type,
                "upload_time": doc.upload_timestamp.isoformat(),
            }
            
            # Include ALL extracted fields from analysis
            if doc.analysis and 'fields' in doc.analysis:
                fields = doc.analysis['fields']
                extracted_fields = {}
                
                for field_name, field_data in fields.items():
                    if isinstance(field_data, dict):
                        # Include value if available
                        value = field_data.get('value')
                        if value is not None:
                            extracted_fields[field_name] = value
                    elif field_data is not None:
                        # Direct value (not wrapped in dict)
                        extracted_fields[field_name] = field_data
                
                if extracted_fields:
                    doc_info['extracted_fields'] = extracted_fields
            
            # Include tables if available (important for bank statement transactions)
            if doc.analysis and 'tables' in doc.analysis:
                tables = doc.analysis['tables']
                if tables:
                    doc_info['tables'] = tables
            
            # Include FULL content (no truncation - agent needs complete data)
            if doc.analysis and 'content' in doc.analysis:
                doc_info['full_content'] = doc.analysis['content']
            
            # Include page count
            if doc.analysis and 'pages' in doc.analysis:
                doc_info['page_count'] = len(doc.analysis['pages'])
            
            document_list.append(doc_info)
        
        summary = store.get_document_summary(session_id)
        
        logger.info(f"Returning {len(docs)} analyzed documents for session {session_id}")
        return {
            "count": len(docs),
            "summary": summary,
            "documents": document_list
        }
        
    except Exception as e:
        logger.error(f"Error retrieving documents for session {session_id}: {str(e)}", exc_info=True)
        return {
            "count": 0,
            "summary": f"Error retrieving documents: {str(e)}",
            "documents": [],
            "error": str(e)
        }
