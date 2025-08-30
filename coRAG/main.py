from src.agents.agent import ResearcherAgent
from src.prompts.system_prompts import RESEARCHER_PROMPT
from src.config.init_logging import init_logging, log_startup
from openai import OpenAI
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

load_dotenv()
console = Console()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def main():
  init_logging()
  log_startup()

  console.print("[bold green]coRAG tester[/bold green]\n")
  user_input = Prompt.ask("[bold green]Enter your query[/bold green]")
  
  agent = ResearcherAgent(client, RESEARCHER_PROMPT)

  response = agent(user_input)

  console.print(Markdown(response))

if __name__ == "__main__":
  main()