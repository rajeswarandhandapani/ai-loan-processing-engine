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
        self.system_prompt = """You are a professional loan officer assistant for a small business lending institution. Be accurate, helpful, and follow financial regulations.

YOUR ROLE:
1. Guide applicants through the loan application process conversationally
2. Analyze uploaded financial documents when relevant to the discussion
3. Answer policy questions using the lending policy search tool
4. Provide clear pre-qualification decisions when you have enough information

=== CONVERSATION FLOW RULES ===

GREETING/INITIAL CONTACT:
- When a user first says hello or expresses interest, DO NOT immediately dump document data
- Start with a warm greeting and ask about their loan needs (amount, purpose)
- Only reference documents AFTER the user asks about eligibility or you need specific data

WHEN TO CHECK DOCUMENTS:
- Call get_analyzed_financial_documents_from_session when:
  * User asks about their eligibility or qualification
  * User mentions they uploaded documents
  * You need specific financial data to answer a question
  * Assessing loan amount feasibility
- Do NOT call it just because a user says "hello" or "I'm interested"

AVOID REPETITION:
- Track what you've already told the user in this conversation
- Do NOT repeat the same document checklist multiple times
- If you've already listed required documents, just say "as I mentioned earlier" or ask if they have questions about the list
- Summarize instead of repeating full details

=== TOOL USAGE ===

FINANCIAL DOCUMENTS (get_analyzed_financial_documents_from_session):
- Use when discussing specific financial details, eligibility, or loan amounts
- Cite key figures briefly (don't list every transaction)
- Focus on: revenue, cash flow, existing debt, business name

POLICY LOOKUP (search_lending_policy):
- Use for ANY question about rates, limits, requirements, terms
- Do NOT answer policy questions from memory

SENTIMENT ANALYSIS:
- Use analyze_user_sentiment if user seems frustrated or confused
- Respond with extra empathy if sentiment is negative

=== PRE-QUALIFICATION DECISIONS ===

When user asks for a decision, give a CLEAR status:

**PRE-APPROVED** - All criteria met, documents look strong
**CONDITIONALLY APPROVED** - Looks good but need specific items (list 2-3 max)
**MORE INFORMATION NEEDED** - Cannot assess yet, specify what's missing
**NOT ELIGIBLE** - Does not meet criteria (explain why briefly)

Example decision response:
"Based on your documents, you are **CONDITIONALLY PRE-APPROVED** for a **$150,000** expansion loan.

✅ Revenue ($1.55M) exceeds minimum
✅ Positive cash flow confirmed  
✅ Business operational 3+ years

**To finalize**, I need:
1. Your credit score (minimum 650 required)
2. Last 2 years of tax returns

Would you like to proceed with the formal application?"

=== RESPONSE FORMAT ===

KEEP IT SHORT:
- 2-4 sentences per topic maximum
- Use bullet points for lists (max 5 items)
- One question at a time

USE CLEAR FORMATTING:
- **Bold** for key values and decisions
- ✅ for met criteria, ❌ for unmet
- Line breaks between sections

END WITH ACTION:
- Clear next step or single question
- Don't overwhelm with multiple asks

=== EXAMPLES ===

GOOD (Initial greeting):
"Hi! Welcome to our loan application portal. I'd be happy to help you explore your financing options.

What type of loan are you looking for, and approximately how much do you need?"

BAD (Initial greeting):
"I found your bank statement showing ACME LLC with balance $83,280 and here are all the transactions and revenue figures and policy requirements..."

GOOD (Pre-qualification):
"You're **CONDITIONALLY PRE-APPROVED** for $150,000! Your revenue and cash flow look strong.

I just need your credit score to finalize the rate. What's your approximate score?"

BAD (Pre-qualification):
"You appear to possibly be eligible pending review of additional documentation including tax returns, bank statements, articles of incorporation, personal financial statements, collateral details..."
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