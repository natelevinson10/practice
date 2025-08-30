from agents import Runner
from .agent import create_researcher_agent, create_evaluator_agent
from ..prompts.system_prompts import RESEARCHER_PROMPT, EVALUATOR_PROMPT
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from loguru import logger
from rich.markdown import Markdown

console = Console()


class CoRAGOrchestratorSDK:
    def __init__(self, max_retries: int = 3):
        """
        Initialize the CoRAG Orchestrator for OpenAI Agents SDK
        
        Args:
            max_retries: Maximum number of retries if evaluation fails
        """
        self.max_retries = max_retries
    
    def run(self, query: str) -> dict:
        """
        Run the research-evaluate loop with the given query using OpenAI Agents SDK.
        
        Args:
            query: The user's initial query
            
        Returns:
            Dict with 'answer', 'attempts', and 'evaluation' keys
        """
        attempts = 0
        synthesized_response = None
        evaluation = None
        
        while attempts < self.max_retries:
            attempts += 1
            
            # Create a fresh researcher agent for each attempt (empty context)
            console.print(f"\n[bold cyan]Attempt {attempts}/{self.max_retries}[/bold cyan]")
            researcher = create_researcher_agent(RESEARCHER_PROMPT)
            
            # Get the synthesized response from the researcher
            logger.info(f"Research attempt {attempts} for query: {query}")
            
            try:
                # Run the researcher agent
                result = Runner.run_sync(researcher, query)
                logger.info(f"input to list (for context manager): {result.to_input_list()}")

                synthesized_response = result.final_output
                logger.info(f"SYNTHESIZED RESPONSE: {synthesized_response}")
                
                if synthesized_response:
                    # Display the response
                    console.print(Panel(
                        Markdown(synthesized_response),
                        title="[bold green]Research Result[/bold green]",
                        border_style="green"
                    ))
                    
                    # Evaluate the response
                    console.print("\n[bold yellow]Evaluating response...[/bold yellow]")
                    evaluator = create_evaluator_agent(EVALUATOR_PROMPT)
                    
                    # Prepare the user message for evaluation (EVALUATOR_PROMPT already tells it to return JSON)
                    evaluation_message = f"""
Initial Query: {query}

Synthesized Response: {synthesized_response}
"""
                    
                    # Run the evaluator - it returns RunResult with EvaluationResult in final_output
                    eval_result = Runner.run_sync(evaluator, evaluation_message)
                    logger.info(f"EVALUATION RESULT: {eval_result}")
                    # Access the final_output from RunResult which contains the EvaluationResult (Pydantic model)
                    # Convert to dict for compatibility with rest of code
                    evaluation = {
                        'fully_answered': eval_result.final_output.fully_answered,
                        'reason': eval_result.final_output.reason
                    }
                    
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
                    
            except Exception as e:
                logger.error(f"Error during attempt {attempts}: {str(e)}")
                console.print(f"[red]Error: {str(e)}[/red]")
        
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
            'evaluation': evaluation if evaluation else {'fully_answered': False, 'reason': 'No valid response'},
            'success': False
        }