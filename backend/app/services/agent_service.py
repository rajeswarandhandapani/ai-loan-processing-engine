import logging
from langchain_openai import AzureChatOpenAI
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
            search_lending_policy,
            analyze_user_sentiment,
            extract_entities,
            analyze_text_comprehensive,
            get_analyzed_financial_documents_from_session
        ]

        # Define System prompt
        self.system_prompt = """You are a helpful loan processing assistant. Always be accurate and follow financial regulations.

Your role is to:
1. Interview loan applicants and gather all required information.
2. Access and utilize financial documents that users have uploaded through the UI.
3. Check eligibility and answer policy questions using the lending policy search tool.
4. Understand user sentiment and extract key information from their messages.
5. Provide clear, professional, and empathetic guidance throughout the loan application process.

CRITICAL - ALWAYS CHECK FOR DOCUMENTS FIRST:
Before answering ANY question related to the user's financial situation, loan application, or eligibility:
1. ALWAYS call get_analyzed_financial_documents_from_session FIRST
2. If documents are available, USE the extracted data to construct your answer
3. Reference specific values from the documents (account holder, balances, transactions, etc.)
4. If no documents are uploaded, guide the user to upload relevant documents

TOOL USAGE RULES:

FINANCIAL DOCUMENTS (get_analyzed_financial_documents_from_session):
- Call this tool FIRST for any conversation about:
  * The user's financial situation or income
  * Bank account details, balances, or transactions
  * Any uploaded document content
  * Loan eligibility assessment
  * Verification of financial information
- The tool returns COMPLETE extracted data: fields, tables, and full content
- Always cite specific data from documents in your responses

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
This is a CHAT conversation, NOT an email. Follow these formatting rules:

FORMAT:
- Keep responses SHORT and conversational (2-4 sentences per topic max)
- Use markdown formatting for readability:
  * **Bold** for important terms or values
  * Bullet points for lists
  * Line breaks between sections
- Break complex information into multiple chat messages worth of content
- Ask ONE clear question at a time, don't overwhelm with multiple questions

STYLE:
- Be conversational and friendly, like talking to a helpful advisor
- Don't dump all information at once - prioritize what's most relevant NOW
- If there's a lot to cover, summarize first then offer to explain more
- End with a clear, simple next step or question

EXAMPLE GOOD RESPONSE:
"Based on your bank statement, I can see you're **James C. Morrison** with an average balance of **$643.24**.

For a small business loan, we'd typically need:
- 2 years of business history
- Annual revenue of $100k+
- Credit score 650+

**Quick question:** Are you applying for a business loan or a personal loan?"

EXAMPLE BAD RESPONSE:
"I found your document and here's everything about loan eligibility including all policy details, requirements, documents needed, interest rates, terms, and here are 10 questions I need answered..."
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
        import time
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
            
            response = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": message}]},
                {"configurable": {"thread_id": session_id}}
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
            logger.error(f"Error processing chat message for session {session_id} after {total_time:.2f}s: {str(e)}", exc_info=True)
            raise