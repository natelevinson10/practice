import dotenv
import os
dotenv.load_dotenv()
from agents import Agent
from ..tools.tools import rag_search
from loguru import logger


def create_researcher_agent(system_prompt: str) -> Agent:
    """
    Create a researcher agent using OpenAI Agents SDK
    
    Args:
        system_prompt: The system prompt/instructions for the agent
        
    Returns:
        An Agent configured with the researcher prompt and RAG search tool
    """
    logger.info("Creating researcher agent with OpenAI Agents SDK")
    
    # Create the agent with instructions and tools
    agent = Agent(
        name="Researcher",
        model="gpt-4o-mini",
        instructions=system_prompt,
        tools=[rag_search]
    )
    
    return agent