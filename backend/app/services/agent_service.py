from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from app.config import settings
from app.tools import (
    analyze_financial_document,
    search_lending_policy
)

class AgentService:
    """Service class for managing AI agent interactions and loan processing."""
    
    def __init__(self):
        # Set up LangSmith tracing environment variables
        import os
        if settings.LANGSMITH_TRACING:
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or ""
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT or ""

        # Initialize the LLM
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        # Define tools
        self.tools = [
            analyze_financial_document,
            search_lending_policy
        ]

        # Define System prompt
        self.system_prompt = """You are a helpful loan processing assistant. Always be accurate and follow financial regulations.

Your role is to:
1. Interview loan applicants and gather all required information.
2. Analyze uploaded financial documents (income statements, balance sheets, etc.) when the user provides a file path.
3. Check eligibility and answer policy questions using the lending policy search tool.
4. Provide clear, professional guidance throughout the loan application process.

IMPORTANT - Tool Usage Rules:
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
- Use analyze_financial_document tool when the user provides a document file path.
- Do NOT answer policy questions from memory - always search the lending policy first.
"""

        # Initialize the checkpointer
        self.checkpointer = InMemorySaver()

        # Create the agent
        self.agent = create_agent(
            model=self.llm,
            system_prompt=self.system_prompt,
            tools=self.tools,
            checkpointer=self.checkpointer
        )


    async def chat(self, message: str, session_id: str) -> str:
        """Process a chat message using the AI agent."""
        
        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            {"configurable": {"thread_id": session_id}}
        )
        
        return response["messages"][-1].content