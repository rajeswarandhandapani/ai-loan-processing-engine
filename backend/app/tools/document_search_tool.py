from azure.search.documents.models import VectorizedQuery
from langchain_core.tools import tool
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from app.config import settings
from typing import Dict, Any, List


def _generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text.

    Args:
        text: The text to generate an embedding for
    
    Returns:
        A list of floating-point numbers representing the embedding
    """
    openai_client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )
    
    response = openai_client.embeddings.create(
        input=text,
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
    )

    print(f"Embedding generated for text: {response.data[0].embedding}")

    return response.data[0].embedding


@tool
def search_lending_policy(query: str) -> Dict[str, Any]:
    """
    Search the company's lending policy documents for relevant information.

    Use this tool when you need to:
    - Check eligibility criteria
    - Find policy rules and limits (DTI rations, credit scores, loan amounts)
    - Verify compliance requirements
    - Answer questions about lending guidelines
    
    Args:
        query: Natural language question about the lending policy
        
    Returns:
        Search results as a dictionary
    """
    try:

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
        
        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["title, content, score"]
        )
        
        # Convert iterator to list and get count properly
        results_list = []
        for result in results:
            results_list.append({
                "content": result["content"],
                "title": result["title"],
                "score": result["score"]
            })
        
        print(f"Search results: {results_list}")

        return {
            "results": results_list,
            "total_count": len(results_list)
        }
    except Exception as e:
        return {
            "error": str(e)
        }