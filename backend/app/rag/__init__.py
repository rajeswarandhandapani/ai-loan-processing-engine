"""RAG (Retrieval-Augmented Generation) for lending policy documents.

The agent cannot answer policy questions from the LLM's own knowledge — the
policy is private and changes. RAG fixes that by retrieving the handful of policy
chunks most relevant to the question and putting them in the prompt.

Two halves, each with its own module:

* **Ingestion** (offline, ingestion.py) — parse the policy PDF, chunk it, embed
  the chunks, store the vectors. Run via scripts/index_lending_policy.py.
* **Retrieval** (per request) — the ``search_lending_policy`` tool in
  app/agent/tools.py calls ``similarity_search`` on the store built here.

Both halves run against LangChain's ``VectorStore`` interface, so the backend is
a configuration choice: Azure AI Search (hosted) or ChromaDB (local). See
README.md in this package for the provider matrix and setup.
"""

from app.rag.embeddings import make_embeddings
from app.rag.ingestion import ingest_policy, split_policy_text
from app.rag.vector_store import make_vector_store

__all__ = [
    "make_embeddings",
    "make_vector_store",
    "ingest_policy",
    "split_policy_text",
]
