"""
Session-based document storage service.

Maintains an in-memory store of uploaded documents linked to chat sessions.
This allows the agent to access documents uploaded during a conversation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SessionDocument:
    """Represents a document uploaded in a session."""
    filename: str
    document_type: str
    upload_timestamp: datetime
    analysis: Dict[str, Any]
    file_path: Optional[str] = None  # Optional: if we keep the file


class SessionDocumentStore:
    """In-memory store for session documents."""
    
    def __init__(self):
        # session_id -> list of SessionDocument
        self._store: Dict[str, List[SessionDocument]] = {}
        logger.info("SessionDocumentStore initialized")
    
    def add_document(
        self,
        session_id: str,
        filename: str,
        document_type: str,
        analysis: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> None:
        """Add a document to a session."""
        if session_id not in self._store:
            self._store[session_id] = []
        
        doc = SessionDocument(
            filename=filename,
            document_type=document_type,
            upload_timestamp=datetime.now(),
            analysis=analysis,
            file_path=file_path
        )
        
        self._store[session_id].append(doc)
        logger.info(f"Added document '{filename}' to session '{session_id}' (total: {len(self._store[session_id])})")
    
    def get_documents(self, session_id: str) -> List[SessionDocument]:
        """Get all documents for a session."""
        docs = self._store.get(session_id, [])
        logger.debug(f"Retrieved {len(docs)} documents for session '{session_id}'")
        return docs
    
    def get_latest_document(self, session_id: str) -> Optional[SessionDocument]:
        """Get the most recently uploaded document for a session."""
        docs = self.get_documents(session_id)
        if docs:
            return docs[-1]
        return None
    
    def clear_session(self, session_id: str) -> None:
        """Clear all documents for a session."""
        if session_id in self._store:
            count = len(self._store[session_id])
            del self._store[session_id]
            logger.info(f"Cleared {count} documents from session '{session_id}'")
    
    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self._store)
    
    def get_document_summary(self, session_id: str) -> str:
        """Get a human-readable summary of documents in a session."""
        docs = self.get_documents(session_id)
        if not docs:
            return "No documents uploaded in this session."
        
        summary_parts = [f"Documents uploaded in this session ({len(docs)} total):"]
        for i, doc in enumerate(docs, 1):
            doc_type_label = doc.document_type.replace('_', ' ').title()
            summary_parts.append(f"{i}. {doc.filename} ({doc_type_label})")
            
            # Add key extracted fields if available
            if doc.analysis and 'fields' in doc.analysis:
                fields = doc.analysis['fields']
                key_info = []
                
                # Extract important fields based on document type
                if 'AccountHolderName' in fields and fields['AccountHolderName'].get('value'):
                    key_info.append(f"Account Holder: {fields['AccountHolderName']['value']}")
                if 'BankName' in fields and fields['BankName'].get('value'):
                    key_info.append(f"Bank: {fields['BankName']['value']}")
                if 'InvoiceTotal' in fields and fields['InvoiceTotal'].get('value'):
                    key_info.append(f"Total: {fields['InvoiceTotal']['value']}")
                if 'VendorName' in fields and fields['VendorName'].get('value'):
                    key_info.append(f"Vendor: {fields['VendorName']['value']}")
                
                if key_info:
                    summary_parts.append(f"   - {', '.join(key_info)}")
        
        return "\n".join(summary_parts)


# Global singleton instance
_session_store: Optional[SessionDocumentStore] = None


def get_session_document_store() -> SessionDocumentStore:
    """Get the global session document store instance."""
    global _session_store
    if _session_store is None:
        _session_store = SessionDocumentStore()
    return _session_store
