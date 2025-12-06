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
1. Interview the loan applicants and gather all the required information.
2. Analyze uploaded financial documents (income statements, balance sheets, etc.) when the user provides a file path.
3. Check the eligibility of the loan applicant based on the lending policy using the search tool.
4. Provide clear, professional guidance throughout the loan application process.

When a user uploads a document, use the analyze_financial_document tool to extract information.
When you need to check lending policies or eligibility criteria, use the search_lending_policy tool.
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