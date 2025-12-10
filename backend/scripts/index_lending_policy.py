"""
Script to index a sample Lending Policy PDF into Azure AI Search.

This script demonstrates:
1. Reading and extracting text from a PDF
2. Chunking text into manageable pieces
3. Generating embeddings using Azure OpenAI
4. Creating a vector search index
5. Uploading documents to Azure AI Search

Usage:
    python scripts/index_lending_policy.py
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.ai.documentintelligence import DocumentIntelligenceClient
from openai import AzureOpenAI

from app.config import settings
from app.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Constants
BACKEND_DIR = Path(__file__).resolve().parent.parent
SAMPLE_POLICY_PDF = BACKEND_DIR / "tests/sample_data/policy/sample_lending_policy.pdf"


class LendingPolicyIndexer:
    """Handles indexing of lending policy documents into Azure AI Search."""
    
    def __init__(self):
        """Initialize the indexer with Azure credentials."""
        # Validate required settings
        if not settings.AZURE_SEARCH_ENDPOINT or not settings.AZURE_SEARCH_KEY:
            raise ValueError("Azure Search credentials not found in .env file")
        
        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("Azure OpenAI credentials not found in .env file")
        
        # Initialize Azure Search clients
        self.search_endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.search_credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        self.index_name = "lending-policies"
        
        # Initialize Azure OpenAI client for embeddings
        self.openai_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2024-06-01",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        # Embedding model (text-embedding-ada-002 is common)
        self.embedding_model = "text-embedding-ada-002"
        
        # Initialize Document Intelligence client (optional, for PDF extraction)
        self.doc_intelligence_client = None
        if settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY:
            self.doc_intelligence_client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
            )
        
        logger.info("Indexer initialized successfully")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from a PDF file using Azure Document Intelligence.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        if not self.doc_intelligence_client:
            logger.warning("Document Intelligence not configured, using fallback sample text")
            return self.create_sample_policy_text()
        
        if not pdf_path.exists():
            logger.warning(f"PDF file not found at {pdf_path}, using fallback sample text")
            return self.create_sample_policy_text()
        
        logger.info(f"Extracting text from PDF: {pdf_path.name}")
        
        with open(pdf_path, "rb") as f:
            poller = self.doc_intelligence_client.begin_analyze_document(
                model_id="prebuilt-layout",
                body=f,
                content_type="application/pdf"
            )
        result = poller.result()
        
        # Extract all text content
        extracted_text = []
        for page in result.pages:
            if page.lines:
                for line in page.lines:
                    extracted_text.append(line.content)
        
        full_text = "\n".join(extracted_text)
        logger.info(f"Extracted {len(full_text)} characters from {len(result.pages)} pages")
        
        return full_text
    
    def create_index(self) -> None:
        """Create the Azure AI Search index with vector search capabilities."""
        logger.info(f"Creating index: {self.index_name}")
        
        # Define the index schema
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True
            ),
            SimpleField(
                name="chunk_id",
                type=SearchFieldDataType.Int32,
                filterable=True
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,  # text-embedding-ada-002 dimension
                vector_search_profile_name="default-vector-profile"
            ),
        ]
        
        # Configure vector search
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="default-vector-profile",
                    algorithm_configuration_name="hnsw-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config"
                )
            ]
        )
        
        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        # Create or update the index
        index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.search_credential
        )
        
        result = index_client.create_or_update_index(index)
        logger.info(f"Index '{result.name}' created successfully")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings for text using Azure OpenAI.
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Error generating embedding: {e}")
            # Return a zero vector as fallback
            return [0.0] * 1536
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def create_sample_policy_text(self) -> str:
        """Create a sample lending policy document."""
        return """
        SMALL BUSINESS LENDING POLICY
        
        1. ELIGIBILITY CRITERIA
        
        1.1 Business Requirements
        - Business must be operational for at least 2 years
        - Must have a valid business license and tax identification number
        - Annual revenue must be at least $100,000
        - Business must be registered in the United States
        
        1.2 Financial Requirements
        - Minimum credit score of 650 for primary business owner
        - Debt-to-income ratio must not exceed 40%
        - Business must show positive cash flow for the last 12 months
        - No bankruptcies in the last 7 years
        - No outstanding tax liens or judgments
        
        2. LOAN AMOUNTS AND TERMS
        
        2.1 Loan Amounts
        - Minimum loan amount: $10,000
        - Maximum loan amount: $500,000
        - Loan amount cannot exceed 3x annual revenue
        
        2.2 Interest Rates
        - Base rate: Prime + 2% to Prime + 8%
        - Rate determined by credit score, revenue, and time in business
        - Excellent credit (750+): Prime + 2% to 3%
        - Good credit (700-749): Prime + 3% to 5%
        - Fair credit (650-699): Prime + 5% to 8%
        
        2.3 Repayment Terms
        - Minimum term: 12 months
        - Maximum term: 60 months
        - Monthly payments required
        - No prepayment penalties
        
        3. REQUIRED DOCUMENTATION
        
        3.1 Business Documents
        - Business license and registration
        - Articles of incorporation or partnership agreement
        - Last 2 years of business tax returns
        - Last 12 months of bank statements
        - Profit and loss statements for last 2 years
        - Balance sheet (current)
        
        3.2 Personal Documents
        - Personal identification (driver's license or passport)
        - Personal tax returns for last 2 years
        - Personal credit report authorization
        - Resume or business experience summary
        
        4. APPROVAL PROCESS
        
        4.1 Initial Review
        - Application completeness check
        - Credit score verification
        - Revenue verification
        - Time in business verification
        
        4.2 Financial Analysis
        - Cash flow analysis
        - Debt service coverage ratio calculation (must be > 1.25)
        - Working capital assessment
        - Collateral evaluation (if applicable)
        
        4.3 Decision Timeline
        - Initial review: 1-2 business days
        - Full underwriting: 3-5 business days
        - Final decision: 7-10 business days from complete application
        
        5. SPECIAL CONSIDERATIONS
        
        5.1 Startups
        - Businesses under 2 years may qualify with:
          * Strong personal credit (720+)
          * Significant industry experience
          * Substantial down payment (20%+)
          * Personal guarantee
        
        5.2 Seasonal Businesses
        - Must demonstrate 2 full seasonal cycles
        - Cash reserves required equal to 6 months of payments
        - May require flexible payment schedule
        
        5.3 Franchise Businesses
        - Franchise must be from approved franchise list
        - Franchise agreement review required
        - May receive preferential rates
        
        6. COLLATERAL REQUIREMENTS
        
        6.1 Secured Loans
        - Loans over $100,000 typically require collateral
        - Acceptable collateral: real estate, equipment, inventory, accounts receivable
        - Loan-to-value ratios:
          * Real estate: up to 80%
          * Equipment: up to 70%
          * Inventory: up to 50%
          * Accounts receivable: up to 80%
        
        6.2 Unsecured Loans
        - Available for loans under $100,000
        - Requires excellent credit and strong financials
        - Higher interest rates apply
        - Personal guarantee required
        
        7. PROHIBITED USES
        
        Loan funds may NOT be used for:
        - Speculative investments
        - Illegal activities
        - Gambling operations
        - Multi-level marketing businesses
        - Cryptocurrency trading
        - Personal expenses unrelated to business
        
        8. DEFAULT AND REMEDIES
        
        8.1 Default Conditions
        - Failure to make payment within 15 days of due date
        - Bankruptcy filing
        - Material misrepresentation on application
        - Business closure without notification
        
        8.2 Remedies
        - Late fees: 5% of payment amount
        - Default interest rate: additional 3% APR
        - Acceleration of full loan balance
        - Collection activities
        - Legal action if necessary
        
        9. POLICY UPDATES
        
        This policy is subject to change. Current version: 2024.1
        Last updated: January 2024
        Next review: January 2025
        """
    
    def index_document(self, policy_text: str) -> None:
        """Index the lending policy document.
        
        Args:
            policy_text: The full text of the lending policy
        """
        logger.info("Processing lending policy document...")
        
        # Chunk the text
        chunks = self.chunk_text(policy_text)
        logger.info(f"Created {len(chunks)} chunks from policy document")
        
        # Prepare documents for indexing
        documents = []
        
        logger.info("Generating embeddings for each chunk...")
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}...")
            
            # Generate embedding
            embedding = self.generate_embedding(chunk)
            
            # Create document
            doc = {
                "id": f"policy-chunk-{i}",
                "title": "Small Business Lending Policy",
                "content": chunk,
                "chunk_id": i,
                "content_vector": embedding
            }
            documents.append(doc)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        logger.info(f"Generated embeddings for all {len(chunks)} chunks")
        
        # Upload documents to index
        logger.info(f"Uploading documents to index '{self.index_name}'...")
        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.search_credential
        )
        
        result = search_client.upload_documents(documents=documents)
        
        # Check results
        succeeded = sum(1 for r in result if r.succeeded)
        logger.info(f"Successfully uploaded {succeeded}/{len(documents)} documents")
    
    def test_search(self, query: str = "What is the minimum credit score required?") -> None:
        """Test the search functionality.
        
        Args:
            query: Search query to test
        """
        logger.info(f"Testing search with query: '{query}'")
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Perform vector search
        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=self.search_credential
        )
        
        from azure.search.documents.models import VectorizedQuery
        
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=3,
            fields="content_vector"
        )
        
        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["title", "content", "chunk_id"]
        )
        
        logger.info("Search Results:")
        for i, result in enumerate(results, 1):
            logger.info(f"Result {i} (Chunk {result['chunk_id']}): {result['content'][:200]}...")


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Azure AI Search - Lending Policy Indexer")
    logger.info("=" * 80)
    
    try:
        # Initialize indexer
        indexer = LendingPolicyIndexer()
        
        # Create the index
        indexer.create_index()
        
        # Try to extract text from PDF, fall back to sample text if unavailable
        if SAMPLE_POLICY_PDF.exists():
            policy_text = indexer.extract_text_from_pdf(SAMPLE_POLICY_PDF)
        else:
            logger.warning(f"PDF not found at {SAMPLE_POLICY_PDF}, using sample text")
            policy_text = indexer.create_sample_policy_text()
        
        # Index the document
        indexer.index_document(policy_text)
        
        # Test the search
        indexer.test_search("What is the minimum credit score required?")
        indexer.test_search("What documents are needed for a loan application?")
        
        logger.info("=" * 80)
        logger.info("Indexing completed successfully!")
        logger.info("=" * 80)
        logger.info(f"Index name: {indexer.index_name}")
        logger.info(f"Search endpoint: {indexer.search_endpoint}")
        logger.info("You can now use this index for RAG-based queries in your application.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
