"""Agent tools, built by a factory so their dependencies are injected.

`make_tools(...)` closes over the clients each tool needs and returns the list
to bind to the graph. This keeps the tools free of module-level globals and
import-time Azure connections, which makes them easy to test and ready to be
exposed over MCP later.

Tool names are part of the contract with the system prompt — do not rename
`search_lending_policy`, `analyze_user_sentiment`, or
`get_analyzed_financial_documents_from_session`.
"""

from collections.abc import Callable

from azure.ai.textanalytics import TextAnalyticsClient
from langchain.tools import ToolRuntime
from langchain_core.tools import BaseTool, tool
from langchain_core.vectorstores import VectorStore

from app.core.errors import tool_errors
from app.core.logging import get_logger
from app.services.session_store import SessionDocumentStore

logger = get_logger(__name__)

# Number of policy chunks to retrieve per RAG query.
POLICY_SEARCH_K = 5


def make_tools(
    vector_store_factory: Callable[[], VectorStore],
    language_client: TextAnalyticsClient,
    session_store: SessionDocumentStore,
) -> list[BaseTool]:
    """Build the agent's tools with their dependencies bound in.

    The vector store is created lazily on first search (via
    `vector_store_factory`) so app startup does not require a live connection to
    the search backend — only actually using the RAG tool does. Any LangChain
    `VectorStore` works here; which one is live is a config choice (see app/rag/).
    """
    cached: dict[str, VectorStore] = {}

    def vector_store() -> VectorStore:
        if "store" not in cached:
            cached["store"] = vector_store_factory()
        return cached["store"]

    @tool
    @tool_errors
    def search_lending_policy(query: str) -> dict:
        """Search the company's lending policy documents for relevant information.

        ALWAYS use this tool when the user asks about:
        - Loan amounts: minimum, maximum, or how much they can borrow
        - Interest rates or APR
        - Credit score requirements
        - Eligibility criteria or requirements
        - Required documents for loan application
        - Repayment terms and loan duration
        - Collateral requirements
        - DTI (debt-to-income) ratio limits
        - Any lending policy rules or guidelines

        Args:
            query: Natural language question about the lending policy
                (e.g., "maximum loan amount", "credit score requirement")

        Returns:
            Search results containing relevant policy sections
        """
        logger.info("Searching lending policy: %s", query)
        docs = vector_store().similarity_search(query, k=POLICY_SEARCH_K)
        if not docs:
            return {
                "results": [],
                "total_count": 0,
                "message": "No matching policy information found. Please rephrase your question.",
            }
        results = [
            {"title": doc.metadata.get("title", ""), "content": doc.page_content} for doc in docs
        ]
        return {"results": results, "total_count": len(results)}

    @tool
    @tool_errors
    def analyze_user_sentiment(text: str) -> dict:
        """Analyze the sentiment of user text to understand their emotional state.

        Use this tool when you want to understand if the user is:
        - Frustrated or upset (negative sentiment)
        - Happy or satisfied (positive sentiment)
        - Neutral or mixed

        This helps provide more empathetic responses.

        Args:
            text: The user's message to analyze for sentiment

        Returns:
            A dictionary containing sentiment analysis results
        """
        logger.info("Analyzing sentiment")
        result = language_client.analyze_sentiment(documents=[text])[0]
        if result.is_error:
            return {"error": result.error.message}
        scores = result.confidence_scores
        return {
            "sentiment": result.sentiment,
            "confidence_scores": {
                "positive": round(scores.positive, 2),
                "neutral": round(scores.neutral, 2),
                "negative": round(scores.negative, 2),
            },
            "sentences": [{"text": s.text, "sentiment": s.sentiment} for s in result.sentences],
        }

    @tool
    @tool_errors
    def extract_entities(text: str) -> dict:
        """Extract named entities from user text to identify key information.

        Use this tool to extract important details like:
        - Money amounts (loan amounts, revenue, etc.)
        - Organizations (business names)
        - Dates and times
        - Locations
        - Person names
        - Quantities and percentages

        Args:
            text: The user's message to extract entities from

        Returns:
            A dictionary containing extracted entities grouped by category
        """
        logger.info("Extracting entities")
        result = language_client.recognize_entities(documents=[text])[0]
        if result.is_error:
            return {"error": result.error.message}
        by_category: dict[str, list] = {}
        for entity in result.entities:
            by_category.setdefault(entity.category, []).append(
                {
                    "text": entity.text,
                    "subcategory": entity.subcategory,
                    "confidence": round(entity.confidence_score, 2),
                }
            )
        return {"entities": by_category, "entity_count": len(result.entities)}

    @tool
    @tool_errors
    def get_analyzed_financial_documents_from_session(runtime: ToolRuntime) -> dict:
        """Retrieve all analyzed financial documents from the current session.

        Use this tool when the user asks about documents they uploaded, mentions
        their bank statement, invoice, receipt, tax form, or any financial
        document.

        This tool returns the COMPLETE extracted data from documents that were
        already analyzed during upload - including all fields, tables, and full
        content.

        No parameters needed - automatically accesses the current conversation
        session.

        Returns:
            Dictionary with count, a human-readable summary, and the documents
            with their full extracted data (fields, tables, content).
        """
        session_id = runtime.config["configurable"]["thread_id"]
        logger.info("Retrieving session documents for %s", session_id)
        docs = session_store.get_documents(session_id)
        if not docs:
            return {
                "count": 0,
                "summary": (
                    "No documents have been uploaded in this session yet. "
                    "Ask the user to upload their financial documents first."
                ),
                "documents": [],
            }

        document_list = []
        for doc in docs:
            info = {
                "filename": doc.filename,
                "document_type": doc.document_type,
                "upload_time": doc.upload_timestamp.isoformat(),
            }
            analysis = doc.analysis or {}
            fields = analysis.get("fields") or {}
            extracted = {}
            for name, data in fields.items():
                if isinstance(data, dict):
                    if data.get("value") is not None:
                        extracted[name] = data["value"]
                elif data is not None:
                    extracted[name] = data
            if extracted:
                info["extracted_fields"] = extracted
            if analysis.get("tables"):
                info["tables"] = analysis["tables"]
            if analysis.get("content"):
                info["full_content"] = analysis["content"]
            if analysis.get("pages"):
                info["page_count"] = len(analysis["pages"])
            document_list.append(info)

        return {
            "count": len(docs),
            "summary": session_store.get_document_summary(session_id),
            "documents": document_list,
        }

    return [
        search_lending_policy,
        analyze_user_sentiment,
        extract_entities,
        get_analyzed_financial_documents_from_session,
    ]
