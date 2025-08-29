from .llm import LLM
from loguru import logger
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from models.schemas import ThoughtResponse
from ..tools.tools import available_tools, tools
import time

class HostAgent:
    def __init__(self, client: LLM, system_prompt: str):
        self.client = client
        self.system_prompt = system_prompt
        self.memory = []  # Full memory for debugging
        self.agent_memory = []  # Clean memory for agent
        self.tools = available_tools
        self.tool_schemas = tools
        self.user_query = None
        if self.system_prompt is not None:
            self.append_to_both_memories("system", self.system_prompt)
    
    def append_to_both_memories(self, role: str, content: str):
        """Append a message to both memory and agent_memory"""
        message = {"role": role, "content": content}
        self.memory.append(message)
        self.agent_memory.append(message)
    
    def trace(self, tool_call_id, function_name, function_args, content):
        """Convert tool call and result to plaintext description"""
        description = f"Called {function_name} with args {function_args} and got {content} as the output"
        logger.info(f"Converted tool call {tool_call_id} to plaintext: {description}")
        return description
    
    def __call__(self, message=None):
        if message:
            logger.info(f"User message: {message}")
            self.append_to_both_memories("user", message)
            self.user_query = message
        result = self.execute()
        return result
    
    def think(self):
        start_time = time.time()
        logger.info("=== THINKING ===")
        """Plan next step with structured output; no tool calls allowed."""
        planner_guard = (
            "You are the planning module. Do NOT call tools."
            "Reply ONLY with JSON that matches the ThoughtResponse schema."
            "Keep your 'thought' short and concise"
            "Fields: user_query (string), thought (string), next_action (string), answer (optional string), confidence (number 0-1).\n"
            "If you can answer WITHOUT tools, set next_action='provide_answer' and include the answer field.\n"
            "If you need tools, set next_action to the tool name (e.g., 'get_restaurant_info').\n"
            "IMPORTANT: Check if information is already available in the conversation history "
            "before deciding to call tools. If you recently called get_restaurant_info, "
            "that data contains ALL restaurant information - reuse it instead of calling again."
        )
        think_prompt = (
            f"User's query: {self.user_query}\n"
            "Can I answer with available info? If yes, provide the answer. If not, what tool is needed?\n"
            "Respond as JSON only."
        )

        messages = self.agent_memory + [
            {"role": "system", "content": planner_guard},
            {"role": "assistant", "content": think_prompt},
        ]

        # Build JSON schema from ThoughtResponse (Pydantic v2 or v1)
        try:
            schema_fn = getattr(ThoughtResponse, "model_json_schema", None) or ThoughtResponse
            json_schema = schema_fn()
        except Exception:
            json_schema = ThoughtResponse
        
        # Hardcode the user_query to always be self.user_query
        json_schema["properties"]["user_query"]["const"] = self.user_query

        # IMPORTANT: do NOT pass tool_choice or tools here
        completion = self.client.chat.completions.create(
            model=self.client.model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ThoughtResponse",
                    "schema": json_schema,
                },
            },
        )

        raw = completion.choices[0].message.content
        try:
            data = json.loads(raw)
            reasoning_obj = ThoughtResponse.model_validate(data)
        except Exception as e:
            reasoning_obj = ThoughtResponse(
                user_query=self.user_query or "No user_query set",
                thought=f"Failed to parse strict JSON: {e}. Raw: {raw}",
                next_action="re-evaluate-user_query",
                answer=None,
                confidence=0.3,
            )

        # Save a plain-text summary (no tool_calls)
        thought_content = (
            f"User's query: {self.user_query}\n"
            f"Thought: {reasoning_obj.thought}\n"
            f"Next Action: {reasoning_obj.next_action}\n"
            f"Answer: {reasoning_obj.answer}\n"
            f"Confidence: {reasoning_obj.confidence}"
        )
        print(f"\n \033[90mThought: {reasoning_obj.thought}\033[0m")
        if reasoning_obj.answer:
            print(f"\n \033[90mAnswer Identified. Returning... \033[0m")
            thought_content += f"\nAnswer: {reasoning_obj.answer}"
        logger.info(f"Thought for {time.time() - start_time} seconds: \n User's query: {self.user_query} \n Thought: {reasoning_obj.thought} \n Next Action: {reasoning_obj.next_action} \n Answer: {reasoning_obj.answer} \n Confidence: {reasoning_obj.confidence}")
        self.append_to_both_memories("assistant", "THOUGHT: " + thought_content)
        return reasoning_obj
    
    def act(self):
        start_time = time.time()
        logger.info("=== ACTING ===")
        """Decide on and execute an action using tools"""
        completion = self.client.chat.completions.create(
            model=self.client.model,
            messages=self.agent_memory,
            tools=self.tool_schemas,
            tool_choice="auto",
        )
        
        response_message = completion.choices[0].message
        logger.info(f"Response message: {response_message}")
        
        # Handle tool calls
        if response_message.tool_calls:
            # Add raw tool call message to debug memory only
            self.memory.append(response_message.model_dump())
            # Build plaintext description of all tool calls and results
            tool_descriptions = []
            for tool_call in response_message.tool_calls:
                logger.info(f"Tool call: {tool_call}")
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"\n \033[90mCalling {function_name}...\033[0m")
                
                # Execute the tool
                if function_name in self.tools:
                    try:
                        result = self.tools[function_name](**function_args)
                        # Convert dict result to string for display
                        if isinstance(result, dict):
                            result_str = str(result)
                        else:
                            result_str = str(result)
                    except Exception as e:
                        result = f"Error: {str(e)}"
                        result_str = result
                else:
                    result = "Tool not found"
                    result_str = result
                
                # Add tool response to debug memory
                if isinstance(result, dict):
                    content = json.dumps(result)
                else:
                    content = str(result)
                
                self.memory.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": content
                })
                
                # Create plaintext description for agent memory using trace method
                tool_desc = self.trace(tool_call.id, function_name, function_args, content)
                tool_descriptions.append(tool_desc)
            
            # Add combined tool descriptions to agent memory as assistant message
            if tool_descriptions:
                combined_desc = "\n".join(tool_descriptions)
                self.agent_memory.append({"role": "assistant", "content": "ACTION: I used the following tools- " + combined_desc})
            logger.info(f"Action for {time.time() - start_time} seconds: {combined_desc}")
            return True  # Tool was used
        
        # Final answer (no tool calls)
        self.memory.append(response_message.model_dump())  # Full message to debug memory
        if response_message.content:
            logger.info(f"Action for {time.time() - start_time} seconds: {response_message.content}")
            self.agent_memory.append({"role": "assistant", "content": response_message.content})
        
        return response_message.content  # Final answer

    def observe(self):
        """Observe the previous thought and action and the result of the action ti """
        pass
    
    def execute(self):
        """Execute the ReAct loop: Thought -> Action -> Observation"""
        while True:
            # Generate reasoning
            reasoning = self.think()
            
            # If thinking provided a direct answer, return it without calling act()
            if reasoning.next_action == "provide_answer" and reasoning.answer:
                logger.info(f"Direct answer provided: {reasoning.answer}")
                self.append_to_both_memories("assistant", reasoning.answer)
                
                # Log both memories for debugging
                logger.info("=== DEBUG MEMORY ===")
                for msg in self.memory:
                    logger.info(f"Debug memory: {msg}")
                
                logger.info("=== AGENT MEMORY ===")
                for msg in self.agent_memory:
                    logger.info(f"Agent memory: {msg}")
                
                return reasoning.answer
            
            # Take action (may involve tools)
            result = self.act()
            
            # If tools were used, continue the loop
            if result == True:
                continue  # Keep looping
            
            # Otherwise we have the final answer
            # Log both memories for debugging
            logger.info("=== DEBUG MEMORY ===")
            for msg in self.memory:
                logger.info(f"Debug memory: {msg}")
            
            logger.info("=== AGENT MEMORY ===")
            for msg in self.agent_memory:
                logger.info(f"Agent memory: {msg}")

            return result  # Return final answer and exit loop

        