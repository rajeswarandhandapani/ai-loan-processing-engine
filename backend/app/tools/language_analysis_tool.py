"""
Azure AI Language tool for sentiment analysis and entity extraction.

This tool analyzes user messages to detect:
- Sentiment (positive, negative, neutral, mixed)
- Named entities (loan amounts, business types, dates, etc.)
"""

from langchain_core.tools import tool
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


def get_language_client() -> TextAnalyticsClient:
    """Create and return an Azure Text Analytics client."""
    if not settings.AZURE_LANGUAGE_ENDPOINT or not settings.AZURE_LANGUAGE_KEY:
        raise ValueError("Azure AI Language credentials not configured")
    
    credential = AzureKeyCredential(settings.AZURE_LANGUAGE_KEY)
    return TextAnalyticsClient(
        endpoint=settings.AZURE_LANGUAGE_ENDPOINT,
        credential=credential
    )


@tool
def analyze_user_sentiment(text: str) -> dict:
    """
    Analyze the sentiment of user text to understand their emotional state.
    
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
    logger.info(f"Analyzing sentiment for text: {text[:100]}...")
    try:
        client = get_language_client()
        logger.debug("Azure Language client initialized")
        
        # Analyze sentiment
        response = client.analyze_sentiment(documents=[text])[0]
        logger.debug(f"Sentiment analysis completed")
        
        if response.is_error:
            logger.error(f"Sentiment analysis error: {response.error.message}")
            return {"error": f"Analysis failed: {response.error.message}"}
        
        # Extract confidence scores
        confidence = response.confidence_scores
        
        result = {
            "sentiment": response.sentiment,
            "confidence_scores": {
                "positive": round(confidence.positive, 2),
                "neutral": round(confidence.neutral, 2),
                "negative": round(confidence.negative, 2)
            },
            "sentences": []
        }
        
        # Analyze each sentence
        for sentence in response.sentences:
            result["sentences"].append({
                "text": sentence.text,
                "sentiment": sentence.sentiment
            })
        
        logger.info(f"Sentiment analysis successful: {response.sentiment}")
        return result
        
    except ValueError as e:
        logger.error(f"Configuration error in sentiment analysis: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}", exc_info=True)
        return {"error": f"Sentiment analysis failed: {str(e)}"}


@tool
def extract_entities(text: str) -> dict:
    """
    Extract named entities from user text to identify key information.
    
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
    logger.info(f"Extracting entities from text: {text[:100]}...")
    try:
        client = get_language_client()
        logger.debug("Azure Language client initialized")
        
        # Recognize entities
        response = client.recognize_entities(documents=[text])[0]
        logger.debug("Entity extraction completed")
        
        if response.is_error:
            logger.error(f"Entity extraction error: {response.error.message}")
            return {"error": f"Entity extraction failed: {response.error.message}"}
        
        # Group entities by category
        entities_by_category = {}
        
        for entity in response.entities:
            category = entity.category
            if category not in entities_by_category:
                entities_by_category[category] = []
            
            entities_by_category[category].append({
                "text": entity.text,
                "subcategory": entity.subcategory,
                "confidence": round(entity.confidence_score, 2)
            })
        
        logger.info(f"Entity extraction successful: found {len(response.entities)} entities")
        return {
            "entities": entities_by_category,
            "entity_count": len(response.entities)
        }
        
    except ValueError as e:
        logger.error(f"Configuration error in entity extraction: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Entity extraction failed: {str(e)}", exc_info=True)
        return {"error": f"Entity extraction failed: {str(e)}"}


@tool
def analyze_text_comprehensive(text: str) -> dict:
    """
    Perform comprehensive text analysis including sentiment and entity extraction.
    
    Use this tool for a complete analysis of user messages when you need both:
    - Emotional state (sentiment)
    - Key information (entities)
    
    This is useful at the start of a conversation or when processing important messages.
    
    Args:
        text: The user's message to analyze
        
    Returns:
        A dictionary containing both sentiment and entity analysis
    """
    logger.info(f"Performing comprehensive text analysis: {text[:100]}...")
    try:
        client = get_language_client()
        logger.debug("Azure Language client initialized")
        
        # Analyze sentiment
        sentiment_response = client.analyze_sentiment(documents=[text])[0]
        
        # Extract entities
        entities_response = client.recognize_entities(documents=[text])[0]
        
        result = {
            "text_analyzed": text[:100] + "..." if len(text) > 100 else text
        }
        
        # Add sentiment results
        if not sentiment_response.is_error:
            confidence = sentiment_response.confidence_scores
            result["sentiment"] = {
                "overall": sentiment_response.sentiment,
                "confidence": {
                    "positive": round(confidence.positive, 2),
                    "neutral": round(confidence.neutral, 2),
                    "negative": round(confidence.negative, 2)
                }
            }
        else:
            result["sentiment"] = {"error": sentiment_response.error.message}
        
        # Add entity results
        if not entities_response.is_error:
            entities_by_category = {}
            for entity in entities_response.entities:
                category = entity.category
                if category not in entities_by_category:
                    entities_by_category[category] = []
                entities_by_category[category].append({
                    "text": entity.text,
                    "subcategory": entity.subcategory,
                    "confidence": round(entity.confidence_score, 2)
                })
            result["entities"] = entities_by_category
            result["entity_count"] = len(entities_response.entities)
        else:
            result["entities"] = {"error": entities_response.error.message}
        
        # Add a summary for the agent
        summary_parts = []
        if "sentiment" in result and "overall" in result["sentiment"]:
            summary_parts.append(f"User sentiment: {result['sentiment']['overall']}")
        if "entities" in result and isinstance(result["entities"], dict):
            for category, entities in result["entities"].items():
                entity_texts = [e["text"] for e in entities]
                summary_parts.append(f"{category}: {', '.join(entity_texts)}")
        
        result["summary"] = "; ".join(summary_parts) if summary_parts else "No significant findings"
        
        logger.info(f"Comprehensive analysis successful - Sentiment: {result.get('sentiment', {}).get('overall', 'N/A')}, Entities: {result.get('entity_count', 0)}")
        return result
        
    except ValueError as e:
        logger.error(f"Configuration error in comprehensive analysis: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}", exc_info=True)
        return {"error": f"Comprehensive analysis failed: {str(e)}"}
