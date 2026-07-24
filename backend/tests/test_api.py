"""Contract tests for the HTTP endpoints, with dependencies stubbed.

TestClient is used WITHOUT its context manager so the app lifespan (which would
build real Azure clients) never runs; every endpoint dependency is overridden.
"""

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api.deps import get_document_service, get_graph, get_session_store
from app.main import create_app
from app.models import DocumentAnalysisResponse
from app.services.session_store import SessionDocumentStore


class StubGraph:
    async def ainvoke(self, inputs, config):
        return {"messages": [AIMessage(content="stub reply")]}


class StubDocService:
    def __init__(self, error: Exception | None = None):
        self.error = error

    async def analyze_document(self, file_path, document_type):
        if self.error:
            raise self.error
        return DocumentAnalysisResponse(
            document_type=document_type, model_id="prebuilt-layout", content="hello"
        )


def make_client(doc_service=None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_graph] = lambda: StubGraph()
    app.dependency_overrides[get_session_store] = lambda: SessionDocumentStore()
    app.dependency_overrides[get_document_service] = lambda: doc_service or StubDocService()
    return TestClient(app)


@pytest.fixture
def client():
    return make_client()


def test_chat_returns_reply(client):
    resp = client.post("/api/v1/chat/", json={"message": "hi", "session_id": "s1"})
    assert resp.status_code == 200
    assert resp.json() == {"message": "stub reply", "session_id": "s1"}


def test_chat_rejects_empty_message(client):
    resp = client.post("/api/v1/chat/", json={"message": "  ", "session_id": "s1"})
    assert resp.status_code == 400


def test_chat_health(client):
    resp = client.get("/api/v1/chat/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_document_types_lists_five(client):
    resp = client.get("/api/v1/documents/types")
    assert resp.status_code == 200
    assert len(resp.json()["document_types"]) == 5


def test_upload_success(client):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("statement.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["analysis"]["content"] == "hello"


def test_upload_reports_failure_in_body():
    client = make_client(doc_service=StubDocService(error=RuntimeError("azure down")))
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("statement.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    # Failure is reported in a 200 body (frontend contract), not an HTTP error.
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["error"] == "azure down"


def test_upload_rejects_bad_extension(client):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
