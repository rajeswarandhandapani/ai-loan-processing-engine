import logging
from typing import Dict, Any, List
from azure.search.documents.models import VectorizedQuery
from langchain_core.tools import tool
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def _generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text.

    Args:
        text: The text to generate an embedding for
    
    Returns:
        A list of floating-point numbers representing the embedding
    """
    logger.debug(f"Generating embedding for text: {text[:100]}...")
    
    try:
        openai_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        
        response = openai_client.embeddings.create(
            input=text,
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
        )
        
        logger.debug(f"Embedding generated successfully (dimension: {len(response.data[0].embedding)})")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
        raise


@tool
def search_lending_policy(query: str) -> Dict[str, Any]:
    """
    Search the company's lending policy documents for relevant information.

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
        query: Natural language question about the lending policy (e.g., "maximum loan amount", "credit score requirement")
        
    Returns:
        Search results containing relevant policy sections
    """
    try:
        logger.info(f"Searching lending policy for query: {query}")
        
        query_embedding = _generate_embedding(query)

        search_credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name="lending-policies",
            credential=search_credential
        )

        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=5,
            fields="content_vector"
        )
        
        logger.debug("Executing vector search...")
        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["title", "content"]
        )
        
        # Convert iterator to list and get count properly
        results_list = []
        for result in results:
            results_list.append({
                "content": result["content"],
                "title": result["title"],
                "score": result.get("@search.score", 0.0)
            })
        
        logger.info(f"Found {len(results_list)} search results for query: {query}")
        logger.debug(f"Search results: {results_list}")

        return {
            "results": results_list,
            "total_count": len(results_list)
        }
    except Exception as e:
        logger.error(f"Error searching lending policy: {str(e)}", exc_info=True)
        return {
            "error": str(e)
        }