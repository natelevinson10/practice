from src.agents.agent import create_researcher_agent
from src.prompts.system_prompts import RESEARCHER_PROMPT
from src.config.init_logging import init_logging, log_startup
from agents import Runner
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from loguru import logger

load_dotenv()
console = Console()


def main():
    init_logging()
    log_startup()

    console.print("[bold green]coRAG tester (OpenAI Agents SDK)[/bold green]\n")
    user_input = Prompt.ask("[bold green]Enter your query[/bold green]")
    
    # Create the agent with the researcher prompt
    agent = create_researcher_agent(RESEARCHER_PROMPT)

    # Run the agent synchronously
    result = Runner.run_sync(agent, user_input)

    # Display the result
    console.print(Markdown(result.final_output))

    # Log full conversation memory with structured details
    logger.info("Conversation Memory:")
    for i, message in enumerate(result.new_items, 1):
        
        # Log to file with structured details
        if hasattr(message, 'role'):
            if message.role == 'user':
                logger.info(f"User ({i}): {message.content}")
            elif message.role == 'assistant':
                logger.info(f"Assistant ({i}): {message.content[:200]}...")
            elif message.role == 'tool':
                logger.info(f"Tool Call ({i}): {getattr(message, 'name', 'unknown')}")
        else:
            logger.info(f"Message {i}: {str(message)[:100]}...")

if __name__ == "__main__":
    main()