"""Ingestion — turning a policy PDF into searchable vectors.

This is the "write" half of RAG, and it runs offline (see
scripts/index_lending_policy.py). Four steps:

1. **Parse**  — PDF bytes to plain text, via pypdf locally or Azure Document
   Intelligence. Controlled by ``POLICY_PDF_PARSER``.
2. **Chunk**  — split the text into ~1000-character pieces with 200 characters of
   overlap. Chunks must be small enough that a retrieved hit is mostly relevant
   text, and the overlap keeps a sentence that straddles a boundary intact in at
   least one chunk.
3. **Embed**  — done for us by the vector store, which calls the embedding model
   from ``add_documents``.
4. **Store**  — write chunks + vectors to whichever backend is configured.

Because steps 3 and 4 go through LangChain's ``VectorStore`` interface, this one
pipeline feeds both Azure AI Search and local ChromaDB.

Chunks get stable ids (``policy-chunk-0``, ``policy-chunk-1``, ...), so re-running
ingestion overwrites the previous run rather than piling up duplicates. Pass
``reset=True`` to wipe the collection first — needed when the chunking changes
and produces fewer chunks than last time.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings, is_configured
from app.core.logging import get_logger
from app.rag.vector_store import make_vector_store

logger = get_logger(__name__)

# Every chunk is tagged with this title; the search tool returns it alongside the
# text so the agent can cite where an answer came from.
POLICY_TITLE = "Small Business Lending Policy"

# Chunking parameters. Bigger chunks give the LLM more context per hit but dilute
# the embedding (a vector averaging four topics matches none of them well).
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Below this many characters we assume extraction failed rather than that the
# policy is genuinely tiny. Scanned PDFs have no text layer, so pypdf returns
# almost nothing from them — see load_policy_text.
MIN_USABLE_TEXT_CHARS = 200


def resolve_pdf_parser(settings: Settings) -> str:
    """Decide which PDF parser to use: ``"pypdf"`` or ``"azure_di"``.

    ``auto`` prefers Azure Document Intelligence when its credentials are present
    (better at tables and scanned pages) and falls back to pypdf otherwise, so a
    local-only setup works with no configuration at all.
    """
    configured = (settings.POLICY_PDF_PARSER or "auto").lower()
    has_di = is_configured(settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT) and is_configured(
        settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
    )

    if configured == "auto":
        return "azure_di" if has_di else "pypdf"
    if configured == "azure_di":
        if not has_di:
            raise ValueError(
                "POLICY_PDF_PARSER=azure_di requires AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT "
                "and AZURE_DOCUMENT_INTELLIGENCE_KEY. Use POLICY_PDF_PARSER=pypdf to parse locally."
            )
        return "azure_di"
    if configured == "pypdf":
        return "pypdf"

    raise ValueError(
        f"Unknown POLICY_PDF_PARSER: {settings.POLICY_PDF_PARSER!r}. "
        'Expected "auto", "pypdf", or "azure_di".'
    )


def extract_pdf_text(pdf_path: Path, settings: Settings) -> str:
    """Extract plain text from a PDF using the configured parser."""
    parser = resolve_pdf_parser(settings)
    logger.info("Extracting text from %s using %s", pdf_path.name, parser)

    if parser == "azure_di":
        text = _extract_with_document_intelligence(pdf_path, settings)
    else:
        text = _extract_with_pypdf(pdf_path)

    logger.info("Extracted %d characters", len(text))
    return text


def _extract_with_pypdf(pdf_path: Path) -> str:
    """Local, dependency-light extraction. Works on text-based (not scanned) PDFs."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    logger.info("Read %d pages with pypdf", len(pages))
    return "\n".join(pages)


def _extract_with_document_intelligence(pdf_path: Path, settings: Settings) -> str:
    """Azure Document Intelligence ``prebuilt-layout`` — handles scans and tables."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    client = DocumentIntelligenceClient(
        endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
    )
    with open(pdf_path, "rb") as handle:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout", body=handle, content_type="application/pdf"
        )
    result = poller.result()

    lines = [line.content for page in result.pages if page.lines for line in page.lines]
    logger.info("Read %d pages with Document Intelligence", len(result.pages))
    return "\n".join(lines)


def split_policy_text(text: str) -> list[Document]:
    """Split policy text into overlapping chunks, ready to embed.

    ``RecursiveCharacterTextSplitter`` tries paragraph breaks first, then lines,
    then words, so it splits at the most natural boundary that fits the size
    limit instead of cutting mid-sentence.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_text(text)
    return [
        Document(
            page_content=chunk,
            metadata={"title": POLICY_TITLE, "chunk_id": index},
        )
        for index, chunk in enumerate(chunks)
    ]


def chunk_ids(documents: list[Document]) -> list[str]:
    """Stable ids so re-ingesting updates chunks in place instead of duplicating them."""
    return [f"policy-chunk-{doc.metadata['chunk_id']}" for doc in documents]


def load_policy_text(pdf_path: Path | None, settings: Settings) -> str:
    """Get the policy text, falling back to the built-in sample when extraction fails.

    pypdf can only read a PDF's text layer. The bundled sample policy is a scanned
    document with no text layer, so parsing it locally yields nothing — that needs
    OCR (``POLICY_PDF_PARSER=azure_di``). Rather than index an empty document, fall
    back to the sample text so the local demo still works.
    """
    if not (pdf_path and pdf_path.exists()):
        logger.warning("No PDF at %s — using the built-in sample policy text", pdf_path)
        return SAMPLE_POLICY_TEXT

    text = extract_pdf_text(pdf_path, settings)
    if len(text.strip()) < MIN_USABLE_TEXT_CHARS:
        logger.warning(
            "Only %d characters extracted from %s — it likely has no text layer "
            "(a scan). Using the built-in sample policy text instead; set "
            "POLICY_PDF_PARSER=azure_di to OCR it with Azure Document Intelligence.",
            len(text.strip()),
            pdf_path.name,
        )
        return SAMPLE_POLICY_TEXT
    return text


def reset_store(settings: Settings) -> None:
    """Delete the existing collection/index so ingestion starts from empty.

    Needed when re-chunking produces *fewer* chunks than the previous run: stable
    ids overwrite chunks 0..n, but anything beyond n would otherwise linger.
    """
    provider = (settings.VECTOR_STORE_PROVIDER or "chroma").lower()

    if provider == "chroma":
        from app.rag.chroma import make_chroma_store

        make_chroma_store(settings).delete_collection()
        logger.info("Deleted local Chroma collection")
    elif provider == "azure":
        from app.rag.azure_search import delete_azure_search_index

        delete_azure_search_index(settings)
    else:
        raise ValueError(
            f"Unknown VECTOR_STORE_PROVIDER: {settings.VECTOR_STORE_PROVIDER!r}. "
            'Expected "azure" or "chroma".'
        )


def ingest_policy(
    settings: Settings,
    pdf_path: Path | None = None,
    reset: bool = False,
) -> int:
    """Run the full ingest pipeline and return the number of chunks written.

    Args:
        settings: App settings; decides parser, embeddings, and vector store.
        pdf_path: Policy PDF. Falls back to ``SAMPLE_POLICY_TEXT`` if missing.
        reset: Drop the existing collection/index before writing.
    """
    text = load_policy_text(pdf_path, settings)
    documents = split_policy_text(text)
    logger.info("Split policy into %d chunks", len(documents))

    if not documents:
        raise ValueError("No text to index — the policy source produced zero chunks.")

    if reset:
        reset_store(settings)

    # Built after the reset so the store points at the freshly recreated collection.
    store: VectorStore = make_vector_store(settings)
    store.add_documents(documents, ids=chunk_ids(documents))
    logger.info("Indexed %d chunks", len(documents))
    return len(documents)


# Fallback policy text, used when no PDF is available. Keeps the demo runnable
# with zero external files or cloud services.
SAMPLE_POLICY_TEXT = """SMALL BUSINESS LENDING POLICY

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
