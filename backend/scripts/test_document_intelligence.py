import sys
from pathlib import Path
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BACKEND_DIR / "tests/tests-output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(BACKEND_DIR))
from app.config import settings

document_intelligence_client = DocumentIntelligenceClient(
    endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
    credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
)

def analyze_document():
    sample_file = BACKEND_DIR / "tests/sample_data/bank_statements/dummy_statement.pdf"
    if not sample_file.exists():
        print(f"Error: Sample file not found at {sample_file}")
        return

    with open(sample_file, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=f,
            content_type="application/pdf"
        )
    result = poller.result()

    output_path = OUTPUT_DIR / "layout_result.json"
    with open(output_path, "w") as f:
        json.dump(result.as_dict(), f, indent=2, default=str)
    
    print(f"Document analysis result: {result}")

if __name__ == "__main__":
    analyze_document()