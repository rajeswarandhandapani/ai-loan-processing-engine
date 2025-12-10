import sys
import logging
from pathlib import Path
from openai import AzureOpenAI

# Add backend directory to path to import app.config
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from app.config import settings
from app.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

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
        logger.error("AZURE_OPENAI_DEPLOYMENT_NAME not found in your .env file.")
        return

    logger.info("Testing Azure OpenAI 'Hello World'...")
    logger.info(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")

    try:
        client = create_openai_client()
        logger.debug("Azure OpenAI client created successfully")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Can you respond with 'Hello World' and tell me what you are?"}
        ]
        
        logger.info("Sending message to Azure OpenAI...")
        logger.debug(f"User message: {messages[1]['content']}")
        
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages
        )
        
        assistant_message = response.choices[0].message.content
        
        logger.info("Response received from Azure OpenAI")
        logger.info(f"Assistant response: {assistant_message}")
        logger.info("Azure OpenAI test completed successfully!")
        
    except ValueError as e:
        logger.error(f"Configuration Error: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error calling Azure OpenAI: {str(e)}", exc_info=True)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Azure OpenAI Chat Client - Day 6 Implementation")
    logger.info("=" * 60)
    logger.info("This script tests Azure OpenAI connectivity and basic chat functionality.")
    logger.info("Make sure your .env file contains the required Azure OpenAI settings.")
    logger.info("=" * 60)
    
    # Run the basic hello world test
    run_hello_world_test()