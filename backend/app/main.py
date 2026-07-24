"""FastAPI application entry point.

`create_app()` wires everything together. All heavy objects (LLM, vector store,
Azure clients, the compiled graph) are built once in the lifespan handler and
stored on `app.state`, from where `app/api/deps.py` hands them to endpoints.
Nothing connects to Azure at import time.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import build_graph
from app.agent.tools import make_tools
from app.api import chat, documents
from app.core.clients import (
    make_chat_model,
    make_language_client,
    make_vector_store,
)
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.services.document_intelligence import DocumentIntelligenceService
from app.services.session_store import SessionDocumentStore

CORS_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def _configure_langsmith(settings: Settings) -> None:
    """Enable LangSmith tracing via environment variables, if configured."""
    if not settings.LANGSMITH_TRACING:
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY or ""
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or ""
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT or ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the graph and services on startup; tear down on shutdown."""
    logger = get_logger(__name__)
    settings = get_settings()
    _configure_langsmith(settings)

    logger.info("Starting %s", settings.app_name)
    session_store = SessionDocumentStore()
    tools = make_tools(
        vector_store_factory=lambda: make_vector_store(settings),
        language_client=make_language_client(settings),
        session_store=session_store,
    )
    app.state.graph = build_graph(make_chat_model(settings), tools)
    app.state.session_store = session_store
    app.state.document_service = DocumentIntelligenceService(settings)
    logger.info("Startup complete")

    yield

    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered loan processing engine with Azure AI services",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "healthy", "service": settings.app_name}

    @app.get("/")
    async def root() -> dict:
        return {"message": "Welcome to AI Loan Processing Engine", "version": "1.0.0"}

    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=get_settings().debug,
        log_level="info",
    )
