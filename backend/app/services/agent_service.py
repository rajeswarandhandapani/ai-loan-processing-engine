from langchain_azure import AzureChatOpenAI
from langchain.memory import InMemorySaver
from langchain.agents import create_agent
from app.config import settings

class AgentService:
    """Service class for managing AI agent interactions and loan processing."""
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version="2024-06-01",
            api_key=settings.AZURE_OPENAI_API_KEY
        )
        self.checkpointer = InMemorySaver()
        self.agent = create_agent(
            llm=self.llm,
            checkpointer=self.checkpointer,
            tools=[],
            verbose=True
        )


    async def chat(self, message: str, session_id: str):
        """Process a chat message using the AI agent."""
        response = await self.agent.ainvoke({
            "input": message,
            "thread_id": session_id
        })
        return response["messages"][-1].content