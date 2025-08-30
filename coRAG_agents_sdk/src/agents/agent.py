import dotenv
import os
dotenv.load_dotenv()
from agents import Agent
from ..tools.tools import rag_search
from loguru import logger
from ..models.models import EvaluationResult

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


def create_evaluator_agent(system_prompt: str) -> Agent:
    """
    Create an evaluator agent using OpenAI Agents SDK
    
    Args:
        system_prompt: The system prompt/instructions for the evaluator
        
    Returns:
        An Agent configured with the evaluator prompt
    """
    logger.info("Creating evaluator agent with OpenAI Agents SDK")
    
    # Create the agent with instructions (no tools needed for evaluation)
    agent = Agent(
        name="Evaluator",
        model="gpt-4o-mini",
        instructions=system_prompt,
        tools=[],  # No tools needed for evaluation
        output_type=EvaluationResult
    )
    
    return agent