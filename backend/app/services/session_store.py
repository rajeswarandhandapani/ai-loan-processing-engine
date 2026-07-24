"""In-memory store for documents uploaded during a chat session.

Documents are scoped by session_id so the agent can answer questions about
what the user uploaded. This is process-local and non-persistent — swap in
Redis or a database for multi-worker or production use.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_DOCUMENTS_PER_SESSION = 20


@dataclass
class SessionDocument:
    """A single document analyzed and stored for a session."""

    filename: str
    document_type: str
    upload_timestamp: datetime
    analysis: dict[str, Any]


class SessionDocumentStore:
    """Session-scoped, in-memory document storage."""

    def __init__(self) -> None:
        self._store: dict[str, list[SessionDocument]] = {}

    def add_document(
        self,
        session_id: str,
        filename: str,
        document_type: str,
        analysis: dict[str, Any],
    ) -> None:
        """Store an analyzed document under a session (oldest evicted at limit)."""
        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")

        docs = self._store.setdefault(session_id, [])
        if len(docs) >= MAX_DOCUMENTS_PER_SESSION:
            removed = docs.pop(0)
            logger.info("Evicted oldest document '%s' from %s", removed.filename, session_id)

        docs.append(
            SessionDocument(
                filename=filename,
                document_type=document_type,
                upload_timestamp=datetime.now(),
                analysis=analysis,
            )
        )
        logger.info("Stored '%s' in session %s (total: %d)", filename, session_id, len(docs))

    def get_documents(self, session_id: str) -> list[SessionDocument]:
        """Return all documents stored for a session."""
        return self._store.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """Remove all documents for a session."""
        self._store.pop(session_id, None)

    def get_document_summary(self, session_id: str) -> str:
        """Return a short human-readable summary of a session's documents."""
        docs = self.get_documents(session_id)
        if not docs:
            return "No documents uploaded in this session."

        parts = [f"Documents uploaded in this session ({len(docs)} total):"]
        for i, doc in enumerate(docs, 1):
            label = doc.document_type.replace("_", " ").title()
            parts.append(f"{i}. {doc.filename} ({label})")
            fields = (doc.analysis or {}).get("fields") or {}
            key_info = []
            for field_name, display in (
                ("AccountHolderName", "Account Holder"),
                ("BankName", "Bank"),
                ("InvoiceTotal", "Total"),
                ("VendorName", "Vendor"),
            ):
                value = fields.get(field_name, {})
                if isinstance(value, dict) and value.get("value"):
                    key_info.append(f"{display}: {value['value']}")
            if key_info:
                parts.append(f"   - {', '.join(key_info)}")
        return "\n".join(parts)
