from langchain_core.tools import tool
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings
from typing import Dict, Any


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
        search_credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name="lending-policies",
            credential=search_credential
        )
        
        results = search_client.search(
            search_text=query,
            top=5,
            include_total_count=True
        )
        
        return {
            "results": [result for result in results],
            "total_count": results.get("@odata.count", 0)
        }
    except Exception as e:
        return {
            "error": str(e)
        }