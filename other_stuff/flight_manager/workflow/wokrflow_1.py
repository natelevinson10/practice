from openai import OpenAI
from loguru import logger
import os
import dotenv
import datetime
import json
from pydantic import BaseModel, Field
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.models import Client
from tool_calls.tools import tools, available_functions
from prompts.system_prompts import SYSTEM_PROMPT

# Load environment variables
dotenv.load_dotenv()

# Configure logger to write to file (overwrite on each run)
log_file_path = "/Users/natelevinson/Desktop/practice/logs/workflow.log"
logger.add(log_file_path, rotation="1 day", retention="7 days", level="DEBUG", mode="w")

# Log script startup
logger.info("=" * 80)
logger.info(f"⏰ Start time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)

def process_message(openai_client: Client, user_input: str, conversation_history: list = None) -> tuple[dict, str]:
    """
    Process a flight booking request using tool calling workflow with conversation history
    """
    logger.info(f"Processing flight booking request: {user_input}")
    
    # Build messages with conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history if provided (last N messages)
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user input
    messages.append({"role": "user", "content": user_input})
    
    response = openai_client.client.chat.completions.create(
        model=openai_client.model,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    if tool_calls:
        # Process tool calls
        messages.append(response_message)
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"Calling tool: {function_name} with args: {function_args}")
            
            function_response = function_to_call(**function_args)
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_response)
            })
        
        # Get final response after tool execution
        second_response = openai_client.client.chat.completions.create(
            model=openai_client.model,
            messages=messages
        )
        
        final_message = second_response.choices[0].message.content
        logger.info(f"DONE PROCESSING")
        return function_response, final_message
    else:
        logger.info("No tool calls were made")
        return None, response_message.content

def run_workflow():
    # Properly instantiate the client
    openai_client = Client()
    
    print("\n🛫 Flight Booking Assistant")
    print("=" * 50)
    print("Type 'exit', 'quit', or 'bye' to end the conversation")
    print("=" * 50 + "\n")
    
    # Maintain conversation history in OpenAI format
    conversation_history = []
    MAX_HISTORY_LENGTH = 10  # Keep last N message pairs
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
                print("\nThank you for using Flight Booking Assistant! Goodbye!")
                logger.info("User exited the chat")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            # Process the message with conversation history
            print("\n🤖 Assistant: ", end="", flush=True)
            tool_call_result, response = process_message(openai_client, user_input, conversation_history)
            
            # Display the response
            print(response)
            
            # Log the interaction
            logger.info(f"User: {user_input}")
            logger.info(f"Assistant: {response}")
            # if tool_call_result:
            #     logger.info(f"Tool call response: {tool_call_result}")
            
            # Update conversation history in OpenAI format
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
            
            # Trim history to maintain last N message pairs
            if len(conversation_history) > MAX_HISTORY_LENGTH * 2:
                conversation_history = conversation_history[-(MAX_HISTORY_LENGTH * 2):]
            
        except KeyboardInterrupt:
            print("\n\n✈️  Chat interrupted. Goodbye!")
            logger.info("Chat interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            logger.error(f"Error in chat loop: {str(e)}")
            print("Please try again or type 'exit' to quit.")

if __name__ == "__main__":
    run_workflow()