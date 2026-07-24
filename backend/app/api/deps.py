"""FastAPI dependencies.

The graph, session store, and document service are built once in the app
lifespan and stashed on `app.state`. These accessors expose them to endpoints
via `Depends(...)`, and tests can override them with `app.dependency_overrides`.
"""

from fastapi import Request
from langgraph.graph.state import CompiledStateGraph

from app.services.document_intelligence import DocumentIntelligenceService
from app.services.session_store import SessionDocumentStore


def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph


def get_session_store(request: Request) -> SessionDocumentStore:
    return request.app.state.session_store


def get_document_service(request: Request) -> DocumentIntelligenceService:
    return request.app.state.document_service
