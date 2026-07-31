"""Index the lending policy into the configured vector store.

Run this once before using the chat agent, so `search_lending_policy` has
something to retrieve. The pipeline itself lives in app/rag/ingestion.py; this
file is just the command line around it.

Which backend gets written is decided by .env (see app/rag/README.md):
    VECTOR_STORE_PROVIDER=chroma   -> local ChromaDB directory
    VECTOR_STORE_PROVIDER=azure    -> Azure AI Search index

Usage:
    uv run python scripts/index_lending_policy.py
    uv run python scripts/index_lending_policy.py --reset
    uv run python scripts/index_lending_policy.py --pdf path/to/policy.pdf
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.rag.ingestion import ingest_policy, resolve_pdf_parser
from app.rag.vector_store import make_vector_store

BACKEND_DIR = Path(__file__).resolve().parent.parent
SAMPLE_POLICY_PDF = BACKEND_DIR / "tests/sample_data/policy/sample_lending_policy.pdf"
SMOKE_TEST_QUERY = "What is the minimum credit score required?"

setup_logging()
logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=SAMPLE_POLICY_PDF,
        help="Policy PDF to index (falls back to built-in sample text if missing)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing collection/index before indexing",
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip the search smoke test after indexing",
    )
    return parser.parse_args()


def smoke_test(settings) -> None:
    """Query the store we just wrote, to prove retrieval works end to end."""
    logger.info("Smoke test query: %s", SMOKE_TEST_QUERY)
    docs = make_vector_store(settings).similarity_search(SMOKE_TEST_QUERY, k=3)
    if not docs:
        logger.warning("No results returned — is the store empty?")
        return
    for rank, doc in enumerate(docs, start=1):
        snippet = doc.page_content[:120].replace("\n", " ")
        logger.info("  %d. [%s] %s...", rank, doc.metadata.get("title", ""), snippet)


def main() -> int:
    args = parse_args()
    settings = get_settings()

    logger.info(
        "Vector store: %s | embeddings: %s | PDF parser: %s",
        settings.VECTOR_STORE_PROVIDER,
        settings.EMBEDDING_PROVIDER,
        resolve_pdf_parser(settings),
    )

    try:
        count = ingest_policy(settings, pdf_path=args.pdf, reset=args.reset)
    except Exception as exc:
        logger.error("Indexing failed: %s", exc)
        return 1

    logger.info("Indexed %d chunks", count)

    if not args.skip_test:
        smoke_test(settings)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
