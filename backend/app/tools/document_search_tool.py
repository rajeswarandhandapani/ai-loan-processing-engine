from typing import Dict, Any, List
from azure.search.documents.models import VectorizedQuery
from langchain_core.tools import tool
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError, ServiceRequestError
from openai import AzureOpenAI
from openai import APITimeoutError, APIConnectionError, RateLimitError
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
        
    Raises:
        Exception: If embedding generation fails with descriptive error message
    """
    logger.debug(f"Generating embedding for text: {text[:100]}...")
    
    try:
        openai_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            timeout=30.0,  # 30 second timeout for embedding generation
            max_retries=2
        )
        
        response = openai_client.embeddings.create(
            input=text,
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
        )
        
        logger.debug(f"Embedding generated successfully (dimension: {len(response.data[0].embedding)})")
        return response.data[0].embedding
        
    except APITimeoutError as e:
        logger.error(f"Timeout generating embedding: {str(e)}")
        raise Exception("Embedding generation timed out. Please try again.")
        
    except RateLimitError as e:
        logger.warning(f"Rate limit hit for embeddings: {str(e)}")
        raise Exception("Service is currently busy. Please wait a moment and try again.")
        
    except APIConnectionError as e:
        logger.error(f"Connection error generating embedding: {str(e)}")
        raise Exception("Unable to connect to Azure OpenAI service. Please check your connection.")
        
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
        raise Exception(f"Failed to generate embedding: {str(e)}")


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
        
        # Generate embedding with timeout and retry
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
        
        if not results_list:
            logger.warning(f"No results found for query: {query}")
            return {
                "results": [],
                "total_count": 0,
                "message": "No matching policy information found. Please rephrase your question or contact support."
            }
        
        logger.debug(f"Top result score: {results_list[0]['score']:.4f}")

        return {
            "results": results_list,
            "total_count": len(results_list)
        }
        
    except HttpResponseError as e:
        logger.error(f"Azure Search HTTP error: {str(e)}", exc_info=True)
        return {
            "error": "Unable to search lending policies at this time. Please try again.",
            "results": [],
            "total_count": 0
        }
        
    except ServiceRequestError as e:
        logger.error(f"Azure Search service error: {str(e)}", exc_info=True)
        return {
            "error": "Search service is temporarily unavailable. Please try again in a moment.",
            "results": [],
            "total_count": 0
        }
        
    except Exception as e:
        logger.error(f"Error searching lending policy: {str(e)}", exc_info=True)
        return {
            "error": f"Search failed: {str(e)}",
            "results": [],
            "total_count": 0
        }