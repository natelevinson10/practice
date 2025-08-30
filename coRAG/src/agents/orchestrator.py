from openai import OpenAI
from .agent import ResearcherAgent, EvaluatorAgent
from ..prompts.system_prompts import RESEARCHER_PROMPT, EVALUATOR_PROMPT
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from loguru import logger

console = Console()

class CoRAGOrchestrator:
    def __init__(self, client: OpenAI, max_retries: int = 3):
        """
        Initialize the CoRAG Orchestrator that manages the research-evaluate loop.
        
        Args:
            client: OpenAI client instance
            max_retries: Maximum number of retries if evaluation fails
        """
        self.client = client
        self.max_retries = max_retries
        self.evaluator = EvaluatorAgent(client, EVALUATOR_PROMPT)
    
    def run(self, query: str) -> dict:
        """
        Run the research-evaluate loop with the given query.
        
        Args:
            query: The user's initial query
            
        Returns:
            Dict with 'answer', 'attempts', and 'evaluation' keys
        """
        attempts = 0
        
        while attempts < self.max_retries:
            attempts += 1
            
            # Create a fresh researcher agent for each attempt (empty context)
            console.print(f"\n[bold cyan]Attempt {attempts}/{self.max_retries}[/bold cyan]")
            researcher = ResearcherAgent(self.client, RESEARCHER_PROMPT)
            
            # Get the synthesized response from the researcher
            logger.info(f"Research attempt {attempts} for query: {query}")
            synthesized_response = researcher(query)
            
            if synthesized_response:
                # Display the response
                console.print(Panel(
                    Markdown(synthesized_response),
                    title="[bold green]Research Result[/bold green]",
                    border_style="green"
                ))
                
                # Evaluate the response
                console.print("\n[bold yellow]Evaluating response...[/bold yellow]")
                evaluation = self.evaluator.evaluate(query, synthesized_response)
                
                logger.info(f"Evaluation result: {evaluation}")
                
                # Display evaluation result
                if evaluation['fully_answered']:
                    console.print(Panel(
                        Text(f"✓ {evaluation['reason']}", style="bold green"),
                        title="[bold green]Evaluation: PASSED[/bold green]",
                        border_style="green"
                    ))
                    
                    return {
                        'answer': synthesized_response,
                        'attempts': attempts,
                        'evaluation': evaluation,
                        'success': True
                    }
                else:
                    console.print(Panel(
                        Text(f"✗ {evaluation['reason']}", style="bold red"),
                        title="[bold red]Evaluation: FAILED[/bold red]",
                        border_style="red"
                    ))
                    
                    if attempts < self.max_retries:
                        console.print(f"\n[yellow]Response incomplete. Retrying with fresh context...[/yellow]")
            else:
                logger.error(f"No response from researcher on attempt {attempts}")
                console.print("[red]No response received from researcher.[/red]")
        
        # Max retries reached
        console.print(Panel(
            Text(f"Maximum retries ({self.max_retries}) reached without satisfactory answer.", 
                 style="bold red"),
            title="[bold red]Final Status: FAILED[/bold red]",
            border_style="red"
        ))
        
        return {
            'answer': synthesized_response if synthesized_response else None,
            'attempts': attempts,
            'evaluation': evaluation if 'evaluation' in locals() else {'fully_answered': False, 'reason': 'No valid response'},
            'success': False
        }