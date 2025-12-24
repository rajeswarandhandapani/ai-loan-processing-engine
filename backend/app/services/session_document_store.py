"""
============================================================================
Session Document Storage Service
============================================================================
In-memory storage for documents uploaded during chat sessions.

Key Concepts:
- Session Isolation: Documents are scoped to individual conversations
- In-Memory Storage: Fast access, but data lost on restart
- Document Limit: Prevents memory exhaustion from large uploads

How it works:
1. User uploads document during chat
2. Document analyzed and stored with session_id
3. Agent tool retrieves documents for that session
4. Agent can answer questions about uploaded docs

Data Flow:
  Upload -> Document Intelligence -> Session Store -> Agent Tool -> Response

Production Considerations:
- Use Redis or database for persistence
- Implement TTL (time-to-live) for automatic cleanup
- Add distributed storage for multi-server deployments
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from app.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Session Document Data Class
# ============================================================================
# Represents a single document stored in a session.
# Uses @dataclass for automatic __init__, __repr__, etc.

@dataclass
class SessionDocument:
    """Represents a document uploaded in a session."""
    filename: str                    # Original filename
    document_type: str               # Type used for analysis
    upload_timestamp: datetime       # When document was uploaded
    analysis: Dict[str, Any]         # Extracted data from Document Intelligence
    file_path: Optional[str] = None  # Physical file path (if retained)
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if document has expired based on upload time."""
        age = datetime.now() - self.upload_timestamp
        return age > timedelta(hours=max_age_hours)


# ============================================================================
# Session Document Store Class
# ============================================================================
# In-memory storage with automatic cleanup and limits.
# 
# Thread Safety Note:
# This implementation is NOT thread-safe. For production with multiple
# workers, use Redis or a database with proper locking.

class SessionDocumentStore:
    """In-memory store for session documents with automatic cleanup."""
    
    # === Configuration ===
    SESSION_MAX_AGE_HOURS = None   # Sessions never expire (None = disabled)
    MAX_DOCUMENTS_PER_SESSION = 20  # Prevent memory exhaustion
    
    def __init__(self):
        # Main storage: session_id -> list of documents
        self._store: Dict[str, List[SessionDocument]] = {}
        
        # Track activity for cleanup: session_id -> last access time
        self._last_access: Dict[str, datetime] = {}
        
        logger.info("SessionDocumentStore initialized with automatic cleanup")
    
    def add_document(
        self,
        session_id: str,
        filename: str,
        document_type: str,
        analysis: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> None:
        """Add a document to a session with validation."""
        # Validate session_id
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")
        
        # Clean up expired sessions before adding
        self._cleanup_expired_sessions()
        
        if session_id not in self._store:
            self._store[session_id] = []
            logger.debug(f"Created new session: {session_id}")
        
        # Check document limit per session
        if len(self._store[session_id]) >= self.MAX_DOCUMENTS_PER_SESSION:
            logger.warning(f"Session {session_id} has reached max documents ({self.MAX_DOCUMENTS_PER_SESSION})")
            # Remove oldest document to make room
            removed = self._store[session_id].pop(0)
            logger.info(f"Removed oldest document '{removed.filename}' from session {session_id}")
        
        doc = SessionDocument(
            filename=filename,
            document_type=document_type,
            upload_timestamp=datetime.now(),
            analysis=analysis,
            file_path=file_path
        )
        
        self._store[session_id].append(doc)
        self._last_access[session_id] = datetime.now()
        logger.info(f"Added document '{filename}' to session '{session_id}' (total: {len(self._store[session_id])})")
    
    def get_documents(self, session_id: str) -> List[SessionDocument]:
        """Get all documents for a session."""
        # Update last access time
        if session_id in self._store:
            self._last_access[session_id] = datetime.now()
        
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
    
    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions from the store."""
        # Skip cleanup if expiration is disabled
        if self.SESSION_MAX_AGE_HOURS is None:
            return
        
        now = datetime.now()
        expired_sessions = []
        
        for session_id, last_access in list(self._last_access.items()):
            age = now - last_access
            if age > timedelta(hours=self.SESSION_MAX_AGE_HOURS):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            doc_count = len(self._store.get(session_id, []))
            if session_id in self._store:
                del self._store[session_id]
            if session_id in self._last_access:
                del self._last_access[session_id]
            logger.info(f"Cleaned up expired session '{session_id}' ({doc_count} documents)")
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def cleanup_all_expired(self) -> int:
        """Manually trigger cleanup of all expired sessions. Returns count of cleaned sessions."""
        initial_count = len(self._store)
        self._cleanup_expired_sessions()
        cleaned_count = initial_count - len(self._store)
        return cleaned_count
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        if session_id not in self._store:
            return None
        
        docs = self._store[session_id]
        last_access = self._last_access.get(session_id)
        
        return {
            "session_id": session_id,
            "document_count": len(docs),
            "last_access": last_access.isoformat() if last_access else None,
            "age_hours": (datetime.now() - last_access).total_seconds() / 3600 if last_access else None,
            "documents": [{
                "filename": doc.filename,
                "type": doc.document_type,
                "uploaded": doc.upload_timestamp.isoformat()
            } for doc in docs]
        }
    
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
        
        # Add session age info
        if session_id in self._last_access:
            age = datetime.now() - self._last_access[session_id]
            hours = age.total_seconds() / 3600
            if hours < 1:
                summary_parts.append(f"\nSession active for {int(age.total_seconds() / 60)} minutes")
            else:
                summary_parts.append(f"\nSession active for {hours:.1f} hours")
        
        return "\n".join(summary_parts)


# Global singleton instance
_session_store: Optional[SessionDocumentStore] = None


def get_session_document_store() -> SessionDocumentStore:
    """Get the global session document store instance."""
    global _session_store
    if _session_store is None:
        _session_store = SessionDocumentStore()
    return _session_store
