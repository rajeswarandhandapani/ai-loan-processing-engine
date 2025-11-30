import sys
from pathlib import Path
from openai import AzureOpenAI

# Add backend directory to path to import app.config
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from app.config import settings

def create_openai_client():
    """
    Create and return an Azure OpenAI client, validating credentials first.
    """
    if not all([settings.AZURE_OPENAI_ENDPOINT, settings.AZURE_OPENAI_API_KEY]):
        raise ValueError("Azure OpenAI credentials (ENDPOINT, API_KEY) not found in .env file.")
    
    return AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version="2024-06-01"
    )

def run_hello_world_test():
    """
    Runs a simple 'Hello World' test against the Azure OpenAI service.
    This is the core requirement for Day 6.
    """
    if not settings.AZURE_OPENAI_DEPLOYMENT_NAME:
        print("❌ Error: AZURE_OPENAI_DEPLOYMENT_NAME not found in your .env file.")
        return

    print("🚀 Testing Azure OpenAI 'Hello World'...")
    print(f"   - Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    print(f"   - Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
    print("-" * 50)

    try:
        client = create_openai_client()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Can you respond with 'Hello World' and tell me what you are?"}
        ]
        
        print("📤 Sending message...")
        print(f"> User: {messages[1]['content']}")
        
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages
        )
        
        assistant_message = response.choices[0].message.content
        
        print("\n📥 Response received!")
        print(f"> Assistant: {assistant_message}")
        print("\n✅ Azure OpenAI test completed successfully!")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error calling Azure OpenAI: {str(e)}")


if __name__ == "__main__":
    print("🧪 Azure OpenAI Chat Client - Day 6 Implementation")
    print("=" * 60)
    print("This script tests Azure OpenAI connectivity and basic chat functionality.")
    print("Make sure your .env file contains the required Azure OpenAI settings.")
    print("=" * 60)
    
    # Run the basic hello world test
    run_hello_world_test()