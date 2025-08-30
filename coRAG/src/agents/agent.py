import dotenv
import os
import json
dotenv.load_dotenv()
from openai import OpenAI
from ..tools.tools import rag_search_tool_schema, AVAILABLE_TOOLS
from rich.console import Console
from rich.markdown import Markdown
from loguru import logger

console = Console()

class ResearcherAgent:
    def __init__(self, client: OpenAI, system_prompt: str):
        self.client = client
        self.system_prompt = system_prompt
        self.memory = []
        self.tools = [rag_search_tool_schema]
        if self.system_prompt is not None:
            self.memory.append({"role": "system", "content": self.system_prompt})
    
    def __call__(self, message=None):

        logger.info(f"NEW QUERY: {message}")

        if message:
            self.memory.append({"role": "user", "content": message})
        
        response_message = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.memory,
            stream=False,
            tools=self.tools
        ).choices[0].message

        logger.info(f"RESPONSE MESSAGE: {response_message}")
        self.memory.append(response_message)

        if response_message.tool_calls:

            #print all queries (args for search)
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "rag_search":
                    function_args = json.loads(tool_call.function.arguments)
                    console.print(f"[bright_black]Running query: {function_args['query']}[/bright_black]")

            logger.info(f"TOOL CALLS: {response_message.tool_calls}")

            # Execute tool calls
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name in AVAILABLE_TOOLS:
                    tool_result = AVAILABLE_TOOLS[function_name](**function_args)
                    
                    # Add tool result to memory
                    self.memory.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })

                    logger.info(f"TOOL RESULT: {tool_result}")

            # Get final response after tool execution
            final_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.memory,
                stream=False,
                tools=self.tools
            ).choices[0].message

            logger.info(f"FINAL RESPONSE: {final_response}")
            self.memory.append(final_response)
            return final_response.content
        
        logger.info(f"RESPONSE MESSAGE: {response_message}")
        return response_message.content
    


    