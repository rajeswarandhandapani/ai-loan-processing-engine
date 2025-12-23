import logging
from pathlib import Path
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from app.config import settings
from app.logging_config import get_logger
from app.tools import (
    search_lending_policy,
    analyze_user_sentiment,
    extract_entities,
    analyze_text_comprehensive,
    get_analyzed_financial_documents_from_session
)
from app.tools.session_document_tool import current_session_id

logger = get_logger(__name__)


def _load_system_prompt() -> str:
    """Load the system prompt from the markdown file."""
    prompt_file = Path(__file__).parent.parent / "prompts" / "loan_officer_system_prompt.md"
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        logger.debug(f"Loaded system prompt from {prompt_file} ({len(prompt)} chars)")
        return prompt
    except FileNotFoundError:
        logger.error(f"System prompt file not found: {prompt_file}")
        raise FileNotFoundError(
            f"System prompt file not found at {prompt_file}. "
            "Please ensure the file exists in backend/app/prompts/"
        )
    except Exception as e:
        logger.error(f"Error loading system prompt: {str(e)}")
        raise


def _create_llm() -> BaseChatModel:
    """Create the LLM based on configured provider with timeout and retry settings."""
    provider = settings.LLM_PROVIDER
    
    if provider == "anthropic":
        logger.info(f"Initializing Anthropic Claude with model: {settings.ANTHROPIC_MODEL}")
        return ChatAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            timeout=60.0,  # 60 second timeout
            max_retries=2
        )
    else:
        logger.info(f"Initializing Azure OpenAI LLM with deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
        return AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            max_tokens=2048,
            timeout=60.0,  # 60 second timeout
            max_retries=2
        )


class AgentService:
    """Service class for managing AI agent interactions and loan processing."""
    
    def __init__(self):
        logger.info("Initializing AgentService...")
        
        # Set up LangSmith tracing environment variables
        import os
        if settings.LANGSMITH_TRACING:
            logger.debug("LangSmith tracing enabled")
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or ""
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT or ""
        else:
            logger.debug("LangSmith tracing disabled")

        
        # Create LLM
        self.llm = _create_llm()

        # Define tools
        self.tools = [
            search_lending_policy,
            analyze_user_sentiment,
            extract_entities,
            analyze_text_comprehensive,
            get_analyzed_financial_documents_from_session
        ]

        # Load system prompt from file
        logger.debug("Loading system prompt from file...")
        self.system_prompt = _load_system_prompt()
        logger.info(f"System prompt loaded successfully ({len(self.system_prompt)} characters)")

        # Initialize the checkpointer
        logger.debug("Initializing in-memory checkpointer for session state")
        self.checkpointer = InMemorySaver()

        # Create the agent
        logger.debug(f"Creating agent with {len(self.tools)} tools")
        self.agent = create_agent(
            model=self.llm,
            system_prompt=self.system_prompt,
            tools=self.tools,
            checkpointer=self.checkpointer
        )
        logger.info("AgentService initialized successfully")


    async def chat(self, message: str, session_id: str) -> str:
        """
        Process a chat message using the AI agent.
        
        Args:
            message: User's chat message
            session_id: Session identifier for conversation context
            
        Returns:
            Agent's response message
            
        Raises:
            Exception: If chat processing fails with user-friendly error message
        """
        import time
        import asyncio
        start_time = time.time()
        
        logger.info(f"Processing chat message for session: {session_id}")
        logger.debug(f"Message content: {message[:100]}...")
        
        # Log agent decision context
        logger.info(f"Agent decision flow - Session: {session_id}")
        logger.debug(f"Available tools: {[tool.name for tool in self.tools]}")
        
        # Analyze message to predict likely tool usage
        message_lower = message.lower()
        likely_tools = []
        
        if any(keyword in message_lower for keyword in ["document", "file", "upload", "pdf", "statement", "invoice", "receipt", "balance", "transaction"]):
            likely_tools.append("get_analyzed_financial_documents_from_session")
        if any(keyword in message_lower for keyword in ["policy", "requirement", "credit score", "interest rate", "loan amount", "eligible"]):
            likely_tools.append("search_lending_policy")
        if any(keyword in message_lower for keyword in ["frustrated", "confused", "worried", "happy", "excited"]):
            likely_tools.append("analyze_user_sentiment")
        if any(keyword in message_lower for keyword in ["amount", "business", "date", "location"]):
            likely_tools.append("extract_entities")
            
        if likely_tools:
            logger.info(f"Predicted tool usage for session {session_id}: {', '.join(likely_tools)}")
        
        try:
            # Set session context for tools that need it
            current_session_id.set(session_id)
            
            # Track agent invocation
            invoke_start = time.time()
            logger.debug(f"Invoking agent for session {session_id}")
            
            # Add timeout for agent invocation (90 seconds max)
            try:
                response = await asyncio.wait_for(
                    self.agent.ainvoke(
                        {"messages": [{"role": "user", "content": message}]},
                        {"configurable": {"thread_id": session_id}}
                    ),
                    timeout=90.0
                )
            except asyncio.TimeoutError:
                logger.error(f"Agent invocation timed out after 90s for session {session_id}")
                raise Exception(
                    "I apologize, but processing your request is taking longer than expected. "
                    "This might be due to high service load. Please try again in a moment."
                )
            
            invoke_time = time.time() - invoke_start
            logger.info(f"Agent invocation completed in {invoke_time:.2f}s for session {session_id}")
            
            # Extract and analyze the response
            agent_response = response["messages"][-1].content
            
            # Check which tools were actually used by analyzing the response
            tools_used = []
            if any(kw in agent_response.lower() for kw in ["document", "statement", "uploaded", "bank", "invoice"]):
                tools_used.append("get_analyzed_financial_documents_from_session")
            if "policy" in agent_response.lower() or "according to" in agent_response.lower():
                tools_used.append("search_lending_policy")
            if "sentiment" in agent_response.lower() or "feeling" in agent_response.lower():
                tools_used.append("analyze_user_sentiment")
            if "entities" in agent_response.lower() or "extracted" in agent_response.lower():
                tools_used.append("extract_entities")
                
            if tools_used:
                logger.info(f"Tools actually used for session {session_id}: {', '.join(tools_used)}")
            else:
                logger.debug(f"No specific tool usage detected in response for session {session_id}")
            
            total_time = time.time() - start_time
            logger.info(f"Chat message processed successfully for session {session_id} "
                       f"(Response length: {len(agent_response)} chars, Total time: {total_time:.2f}s)")
            
            return agent_response
            
        except Exception as e:
            total_time = time.time() - start_time
            error_msg = str(e)
            
            # Provide user-friendly error messages
            if "timeout" in error_msg.lower():
                logger.error(f"Timeout processing chat for session {session_id} after {total_time:.2f}s")
                raise Exception(
                    "The request took too long to process. Please try again with a simpler question "
                    "or contact support if the issue persists."
                )
            elif "rate limit" in error_msg.lower() or "429" in error_msg:
                logger.warning(f"Rate limit hit for session {session_id}")
                raise Exception(
                    "Our service is currently experiencing high demand. "
                    "Please wait a moment and try again."
                )
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                logger.error(f"Connection error for session {session_id}: {error_msg}")
                raise Exception(
                    "Unable to connect to AI services. Please check your internet connection "
                    "and try again."
                )
            else:
                logger.error(f"Error processing chat message for session {session_id} after {total_time:.2f}s: {error_msg}", exc_info=True)
                raise Exception(
                    f"I encountered an error processing your message. Please try rephrasing your question "
                    f"or contact support if the issue continues."
                )