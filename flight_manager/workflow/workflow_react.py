from openai import OpenAI
from loguru import logger
import os
import dotenv
import json
import sys
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.models import Client
from tool_calls.tools import tools, available_functions
from prompts.system_prompts import SYSTEM_PROMPT
from config.logging import init_logging, log_startup

# Load environment variables
dotenv.load_dotenv()


def extract_status(response_text: str) -> str:
    """Extract status indicator from agent response"""
    if not response_text:
        return "UNKNOWN"
    
    # Look for [STATUS: X] pattern
    status_match = re.search(r'\[STATUS:\s*(CONTINUE|COMPLETE)\]', response_text, re.IGNORECASE)
    if status_match:
        return status_match.group(1).upper()
    
    # Fallback: check if response seems final
    completion_phrases = ["successfully booked", "has been booked", "booking confirmed", "all set"]
    if any(phrase in response_text.lower() for phrase in completion_phrases):
        return "COMPLETE"
    
    return "CONTINUE"

def process_message_with_react(openai_client: Client, user_input: str, conversation_history: list = None, max_iterations: int = 10) -> str:
    """
    Process a message using ReAct pattern with agent self-assessment.
    Returns only when the agent declares [STATUS: COMPLETE].
    """
    logger.info(f"Starting ReAct processing for: {user_input}")
    
    # Enhanced system prompt with self-assessment instruction
    enhanced_prompt = SYSTEM_PROMPT + """

## CRITICAL: Task Status Self-Assessment
You MUST end EVERY response with one of these status indicators:
- [STATUS: CONTINUE] - if you need to perform more actions to complete the user's request
- [STATUS: COMPLETE] - if the task is fully done and no more actions are needed

Examples:
- After getting flight data: "I found 3 available flights. Now I need to book the one you requested. [STATUS: CONTINUE]"
- After booking: "Successfully booked flight AA123 from SFO to NYC. Your booking is confirmed. [STATUS: COMPLETE]"
- After just showing info: "Here are the available flights for your review. [STATUS: COMPLETE]"
- When mid-task: "I've removed the flight from available list, now adding to booked. [STATUS: CONTINUE]"

ALWAYS include [STATUS: X] at the end of your message!
"""
    
    # Build initial messages with conversation history
    messages = [{"role": "system", "content": enhanced_prompt}]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user input
    messages.append({"role": "user", "content": user_input})
    
    iterations = 0
    final_response = None
    
    while iterations < max_iterations:
        iterations += 1
        
        # Get LLM response with potential tool calls
        response = openai_client.client.chat.completions.create(
            model=openai_client.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            # Agent decided to use tools - add to message history
            messages.append(response_message)
            
            # Execute all tool calls
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)                
                logger.info(f"Executing tool: {function_name} with args: {function_args}")
                
                # Execute the tool
                try:
                    function_to_call = available_functions[function_name]
                    function_response = function_to_call(**function_args)
                    logger.info(f"Tool {function_name} completed successfully")
                except Exception as e:
                    logger.error(f"Tool {function_name} failed: {str(e)}")
                    function_response = {"error": str(e)}
                
                # Add tool result to messages
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
            
            # Continue the loop - let the agent decide if more work is needed
            continue
            
        else:
            # No tool calls - agent is providing a response
            final_response = response_message.content
            logger.info(f"Agent response: {final_response[:100]}...")
            
            # Extract status from response
            status = extract_status(final_response)
            logger.info(f"Agent self-assessment: {status}")
            
            if status == "COMPLETE":
                logger.info(f"Task completed after {iterations} iterations")
                # Remove the status indicator from the final response for cleaner output
                final_response = re.sub(r'\[STATUS:\s*(CONTINUE|COMPLETE)\]', '', final_response).strip()
                return final_response
            
            elif status == "CONTINUE" or iterations < max_iterations - 1:
                # Agent wants to continue - add response and let it continue
                messages.append(response_message)
                logger.info("Agent indicated more work needed, continuing...")
                
                # Add a gentle reminder if status was missing
                if status == "CONTINUE" and "[STATUS:" not in final_response:
                    messages.append({
                        "role": "system",
                        "content": "Please continue with the task. Remember to end your response with [STATUS: CONTINUE] or [STATUS: COMPLETE]."
                    })
            else:
                # Max iterations reached
                logger.info(f"Max iterations reached ({max_iterations})")
                final_response = re.sub(r'\[STATUS:\s*(CONTINUE|COMPLETE)\]', '', final_response).strip()
                return final_response
    
    logger.warning(f"Exited loop unexpectedly after {iterations} iterations")
    return final_response or "I've completed the available steps for your request."

def run_react_workflow():
    """Main workflow with ReAct pattern and self-assessment"""
    openai_client = Client()
    
    print("\n🛫 Flight Booking Assistant (ReAct with Self-Assessment)")
    print("=" * 60)
    print("The agent will complete your entire request autonomously.")
    print("It self-assesses after each step to determine when done.")
    print("Type 'exit', 'quit', or 'bye' to end the conversation")
    print("=" * 60 + "\n")
    
    conversation_history = []
    MAX_HISTORY_LENGTH = 10

    # Initialize logging
    init_logging()
    log_startup()
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                print("\n✈️ Thank you for using Flight Booking Assistant! Goodbye!")
                logger.info("User exited the chat")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            # Process with ReAct - this will complete the entire task
            logger.info(f"User input: {user_input}\n")
            print("\n🤖 Assistant: Working on your request...\n")
            
            final_response = process_message_with_react(
                openai_client, 
                user_input, 
                conversation_history
            )
            
            # Display the final response
            print(f"🤖 Assistant: {final_response}")
            
            # Log the interaction
            logger.info(f"User: {user_input}")
            logger.info(f"Final Assistant Response: {final_response}")
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": final_response})
            
            # Trim history
            if len(conversation_history) > MAX_HISTORY_LENGTH * 2:
                conversation_history = conversation_history[-(MAX_HISTORY_LENGTH * 2):]
            
        except KeyboardInterrupt:
            print("\n\n✈️ Chat interrupted. Goodbye!")
            logger.info("Chat interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            logger.error(f"Error in chat loop: {str(e)}")
            print("Please try again or type 'exit' to quit.")

if __name__ == "__main__":
    run_react_workflow()