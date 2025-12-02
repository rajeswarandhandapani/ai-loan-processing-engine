from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from app.config import settings

class AgentService:
    """Service class for managing AI agent interactions and loan processing."""
    
    def __init__(self):

        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        self.checkpointer = InMemorySaver()

        self.agent = create_agent(
            model=self.llm,
            system_prompt="You are a helpful loan processing assistant. Always be accurate and follow financial regulations.",
            tools=[],
            checkpointer=self.checkpointer
        )


    async def chat(self, message: str, session_id: str) -> str:
        """Process a chat message using the AI agent."""
        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            {"configurable": {"thread_id": session_id}}
        )
        return response["messages"][-1].content