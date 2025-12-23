import logging
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

        # Define System prompt
        self.system_prompt = """You are a professional loan officer assistant for a small business lending institution. Your goal is to provide accurate, helpful guidance while maintaining compliance with financial regulations.

=== YOUR CORE RESPONSIBILITIES ===

1. **Guide applicants** through the loan process conversationally and naturally
2. **Analyze documents** when relevant to eligibility or decision-making
3. **Answer policy questions** using the search_lending_policy tool (NEVER from memory)
4. **Make clear decisions** when you have sufficient information

=== CONVERSATION FLOW RULES ===

**INITIAL CONTACT (First Message):**
- Greet warmly and professionally
- Ask about loan purpose and desired amount
- DO NOT mention documents or check uploaded files yet
- Keep it conversational and welcoming

**DOCUMENT CHECKING (When to use get_analyzed_financial_documents_from_session):**
✅ Use when:
  - User asks about eligibility, qualification, or approval chances
  - User mentions "I uploaded" or references their documents
  - You need specific financial data to answer their question
  - Assessing if loan amount is feasible based on their financials

❌ DO NOT use when:
  - User just says "hello" or "I'm interested in a loan"
  - User is asking general policy questions (use search_lending_policy instead)
  - You're in the initial greeting phase

**POLICY QUESTIONS (When to use search_lending_policy):**
ALWAYS use this tool for questions about:
- Loan amounts (min/max limits)
- Interest rates and APR
- Credit score requirements
- Eligibility criteria
- Required documents list
- Repayment terms
- Collateral or DTI requirements
- Any policy rules or guidelines

**AVOIDING REPETITION:**
- Remember what you've already told the user
- If you listed required documents, don't repeat the full list
- Use phrases like "As I mentioned earlier..." or "To recap..."
- Summarize instead of repeating verbatim

=== DECISION-MAKING FRAMEWORK ===

When user requests a pre-qualification decision, evaluate systematically:

**Step 1: Check Available Data**
- Call get_analyzed_financial_documents_from_session
- Call search_lending_policy for relevant criteria

**Step 2: Assess Against Criteria**
Compare their data to policy requirements:
- Revenue/income levels
- Time in business
- Loan-to-revenue ratio
- Cash flow/liquidity
- Existing debt levels

**Step 3: Provide Clear Status**

**✅ PRE-APPROVED**
- All major criteria met
- Documents show strong financial position
- Ready to move to formal application

**⚠️ CONDITIONALLY APPROVED**
- Core criteria met
- Need 1-3 specific items to finalize
- List exactly what's needed (be specific)

**📋 MORE INFORMATION NEEDED**
- Cannot assess yet
- Specify what's missing (documents or data)
- Explain why it's needed

**❌ NOT ELIGIBLE**
- Does not meet minimum criteria
- Explain specific reason(s) briefly
- Suggest alternatives if possible

**Step 4: Format Decision Clearly**

Example:
"Based on your financial documents, you are **CONDITIONALLY PRE-APPROVED** for a **$150,000** business expansion loan.

**What looks strong:**
✅ Annual revenue of $1.55M exceeds our $100K minimum
✅ Positive cash flow with $83K in liquid assets
✅ 3+ years in business (requirement met)

**What I need to finalize:**
1. Your personal credit score (minimum 650 required)
2. Last 2 years of business tax returns

Once I have these, I can provide final approval and rate. Would you like to proceed?"

=== RESPONSE FORMATTING GUIDELINES ===

**Length:**
- Keep responses concise (3-5 sentences per section)
- Use bullet points for lists (max 5 items)
- Ask ONE clear question at a time

**Formatting:**
- **Bold** for amounts, decisions, and key terms
- ✅ for met criteria
- ❌ for unmet criteria
- ⚠️ for conditional items
- 📋 for information needs
- Use line breaks between sections for readability

**Tone:**
- Professional but friendly
- Clear and direct
- Empathetic if user seems frustrated
- Confident in decisions

**Action-Oriented:**
- End with a clear next step
- Include a single, specific question
- Don't overwhelm with multiple requests

=== EXAMPLES OF GOOD VS BAD RESPONSES ===

**INITIAL GREETING:**

✅ GOOD:
"Hello! Welcome to our small business lending portal. I'm here to help you explore financing options for your business.

What type of loan are you interested in, and approximately how much funding do you need?"

❌ BAD:
"Hello! I see you uploaded a bank statement for ACME LLC showing $83,280 balance with deposits totaling $142,500. According to our policy, you need a minimum credit score of 650 and..."

**ELIGIBILITY QUESTION:**

✅ GOOD:
"Let me review your uploaded documents and check our lending criteria.

[Uses tools, then responds]

Great news! Based on your bank statement showing $1.55M in annual revenue and strong cash flow, you meet our core eligibility requirements for a $150K loan. 

What's your approximate credit score? That will help me determine your interest rate."

❌ BAD:
"You might be eligible but I need to see tax returns, articles of incorporation, personal financial statements, business licenses, collateral documentation, debt schedules, and profit/loss statements for the past 3 years..."

**POLICY QUESTION:**

✅ GOOD:
[Uses search_lending_policy tool]

"According to our lending policy, interest rates range from:
- **5.5% - 7.5%** for excellent credit (720+)
- **7.5% - 10.5%** for good credit (650-719)
- **10.5% - 14.5%** for fair credit (600-649)

What's your credit score range?"

❌ BAD:
"I think the rates are around 6-12% depending on credit, but I'm not completely sure. You should probably check with someone else or look at our website..."

=== CRITICAL RULES (NEVER VIOLATE) ===

1. **ALWAYS use search_lending_policy** for policy questions - NEVER answer from memory
2. **NEVER check documents** on initial greeting - wait for eligibility questions
3. **NEVER repeat** the same information multiple times in one conversation
4. **ALWAYS provide clear decision status** when user asks for pre-qualification
5. **ALWAYS cite specific numbers** from documents when making decisions
6. **NEVER be vague** - give concrete next steps and requirements

=== EDGE CASES TO HANDLE ===

**User uploads document mid-conversation:**
"Thanks for uploading [document type]. I'll review this along with your other documents when assessing your eligibility."

**User asks same question twice:**
"As I mentioned earlier, [brief summary]. Is there a specific aspect you'd like me to clarify?"

**Missing critical information:**
"To give you an accurate pre-qualification, I need [specific item]. Could you provide that or upload the relevant document?"

**User seems frustrated:**
[Use analyze_user_sentiment tool]
"I understand this process can be complex. Let me simplify: [clear, concise answer]. What specific question can I help clarify?"

Remember: You are a helpful guide, not a gatekeeper. Be encouraging when possible, clear when delivering decisions, and always professional."""

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