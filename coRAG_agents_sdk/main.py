from src.agents.orchestrator import CoRAGOrchestratorSDK
from src.config.init_logging import init_logging, log_startup
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

load_dotenv()
console = Console()


def main():
    init_logging()
    log_startup()

    console.print(Panel(
        "[bold green]coRAG (OpenAI Agents SDK)[/bold green]\n" +
        "Research → Evaluate → Retry if needed",
        expand=False
    ))
    
    user_input = Prompt.ask("\n[bold green]Enter your query[/bold green]")
    
    # Initialize the orchestrator with max 3 retries
    orchestrator = CoRAGOrchestratorSDK(max_retries=3)
    
    # Run the research-evaluate loop
    result = orchestrator.run(user_input)
    
    # Display final result
    console.print("\n" + "="*60)
    if result['success']:
        # Extract just the final synthesis for the final answer
        final_answer = result['answer']
        if "Final Synthesis" in final_answer:
            parts = final_answer.split("Final Synthesis")
        if len(parts) > 1:
            synthesis = parts[1].strip()
            # Clean up markdown formatting
            if synthesis.startswith("**"):
                synthesis = synthesis[2:].strip()
            if synthesis.startswith("-"):
                synthesis = synthesis[1:].strip()
            final_answer = synthesis
    
        console.print(Panel(
        Markdown(final_answer),
        title=f"[bold green]✓ Final Answer (Attempt {result['attempts']})[/bold green]",
        border_style="green"
        ))
    else:
        console.print(Panel(
        Text("Failed to get a satisfactory answer after maximum retries.", style="bold red"),
        title="[bold red]✗ Failed[/bold red]",
        border_style="red"
        ))
        if result['answer']:
            console.print("\n[yellow]Last response:[/yellow]")
            console.print(Markdown(result['answer']))

if __name__ == "__main__":
  main()