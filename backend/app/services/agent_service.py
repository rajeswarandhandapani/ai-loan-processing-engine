import logging
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from app.config import settings
from app.logging_config import get_logger
from app.tools import (
    analyze_financial_document,
    search_lending_policy,
    analyze_user_sentiment,
    extract_entities,
    analyze_text_comprehensive
)

logger = get_logger(__name__)


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

        # Initialize the LLM
        logger.debug(f"Initializing Azure OpenAI LLM with deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        logger.debug("Azure OpenAI LLM initialized successfully")

        # Define tools
        self.tools = [
            analyze_financial_document,
            search_lending_policy,
            analyze_user_sentiment,
            extract_entities,
            analyze_text_comprehensive
        ]

        # Define System prompt
        self.system_prompt = """You are a helpful loan processing assistant. Always be accurate and follow financial regulations.

Your role is to:
1. Interview loan applicants and gather all required information.
2. Analyze uploaded financial documents (income statements, balance sheets, etc.) when the user provides a file path.
3. Check eligibility and answer policy questions using the lending policy search tool.
4. Understand user sentiment and extract key information from their messages.
5. Provide clear, professional, and empathetic guidance throughout the loan application process.

IMPORTANT - Tool Usage Rules:

DOCUMENT ANALYSIS:
- Use analyze_financial_document tool when the user provides a document file path.

POLICY LOOKUP:
- ALWAYS use search_lending_policy tool for ANY question about:
  * Loan amounts, limits, or how much can be borrowed
  * Interest rates or APR
  * Credit score requirements
  * Eligibility criteria or requirements
  * Required documents
  * Repayment terms
  * Collateral requirements
  * DTI (debt-to-income) ratios
  * Any policy rules or guidelines
- Do NOT answer policy questions from memory - always search the lending policy first.

TEXT ANALYSIS (Azure AI Language):
- Use analyze_user_sentiment when you detect the user may be frustrated, confused, or emotional.
  * If sentiment is negative, respond with extra empathy and reassurance.
  * If sentiment is positive, maintain enthusiasm and momentum.
- Use extract_entities to identify key information like:
  * Loan amounts mentioned
  * Business types or names
  * Dates and timeframes
  * Locations
- Use analyze_text_comprehensive for important messages that need full analysis (both sentiment and entities).

RESPONSE GUIDELINES:
- Be empathetic - acknowledge user frustrations and concerns.
- Be precise - use extracted entities to personalize responses.
- Be helpful - proactively guide users through the loan process.
- Be professional - maintain a friendly but business-appropriate tone.
"""

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
        """Process a chat message using the AI agent."""
        logger.info(f"Processing chat message for session: {session_id}")
        logger.debug(f"Message content: {message[:100]}...")
        
        try:
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": message}]},
                {"configurable": {"thread_id": session_id}}
            )
            
            agent_response = response["messages"][-1].content
            logger.debug(f"Agent response generated (length: {len(agent_response)} chars)")
            logger.info(f"Chat message processed successfully for session: {session_id}")
            return agent_response
        except Exception as e:
            logger.error(f"Error processing chat message for session {session_id}: {str(e)}", exc_info=True)
            raise