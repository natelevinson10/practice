from agent.llm import LLM
from tools.tools import available_tools, tools
import json
from loguru import logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schema import ThoughtResponse

class HostAgent:
    def __init__(self, client : LLM, system_prompt : str):
        self.client = client
        self.system_prompt = system_prompt
        self.memory = []  # Full memory for debugging
        self.agent_memory = []  # Clean memory for agent
        self.tools = available_tools
        self.tool_schemas = tools
        self.goal = None
        if self.system_prompt is not None:
            self.memory.append({"role": "system", "content": self.system_prompt})
            self.agent_memory.append({"role": "system", "content": self.system_prompt})
    
    def trace(self, tool_call):
        """Convert tool call to plaintext description"""
        function_name = tool_call.function.name
        function_args = tool_call.function.arguments
        return f"Called tool {function_name} with args {function_args}"
    
    def __call__(self, message=None):
        if message:
            logger.info(f"User message: {message}")
            self.memory.append({"role": "user", "content": message})
            self.agent_memory.append({"role": "user", "content": message})
            # Extract and set goal from user's query
            self.goal = self.extract_goal(message)
            print(f"Goal: {self.goal}")
        result = self.execute()
        return result

    def _planner_messages(self):
        """
        Tool-free, text-only view:
        - keep system/user/assistant messages (drop tool_calls),
        - convert tool observations into assistant text.
        """
        msgs = []
        for m in self.memory:
            role = m.get("role")
            if role in ("system", "user", "assistant"):
                content = m.get("content") or ""
                msgs.append({"role": role, "content": content})
            elif role == "tool":
                obs = m.get("content") or ""
                msgs.append({"role": "assistant", "content": f"Observation: {obs}"})
        return msgs
    
    def extract_goal(self, user_query):
        """Extract a clear, actionable goal from the user's query"""
        goal_completion = self.client.chat.completions.create(
            model=self.client.model,
            messages=[
                {"role": "system", "content": "Convert the user's query into a clear, specific goal statement. Be concise and action-oriented."},
                {"role": "user", "content": user_query}
            ],
        )
        return goal_completion.choices[0].message.content

    def think(self):
        """Plan next step with structured output; no tool calls allowed."""
        planner_guard = (
            "You are the planning module. Do NOT call tools. "
            "Reply ONLY with JSON that matches the ThoughtResponse schema. "
            "Fields: reasoning (string), next_action (string), confidence (number 0-1)."
        )
        think_prompt = (
            f"Current goal: {self.goal}\n"
            "Have you completed the goal? If not, what's the single next step?\n"
            "Respond as JSON only."
        )

        messages = self.agent_memory + [
            {"role": "system", "content": planner_guard},
            {"role": "user", "content": think_prompt},
        ]

        # Build JSON schema from ThoughtResponse (Pydantic v2 or v1)
        try:
            schema_fn = getattr(ThoughtResponse, "model_json_schema", None) or ThoughtResponse.schema
            json_schema = schema_fn()
        except Exception:
            json_schema = ThoughtResponse.schema()

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
                reasoning=f"Failed to parse strict JSON: {e}. Raw: {raw}",
                next_action="re-evaluate-goal",
                confidence=0.3,
            )

        # Save a plain-text summary (no tool_calls)
        thought_content = (
            f"Thought: {reasoning_obj.reasoning}\n"
            f"Next Action: {reasoning_obj.next_action}\n"
            f"Confidence: {reasoning_obj.confidence}"
        )
        self.memory.append({"role": "assistant", "content": thought_content})
        self.agent_memory.append({"role": "assistant", "content": thought_content})
        return reasoning_obj.reasoning
    
    def act(self):
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
                
                print(f"Action: {function_name}({function_args})")
                
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
                
                print(f"Observation: {result_str}")
                
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
                
                # Create plaintext description for agent memory
                tool_desc = f"Called tool {function_name} with args {function_args} and got {content} as the output"
                logger.info(f"Converted tool call {tool_call.id} to plaintext")
                tool_descriptions.append(tool_desc)
            
            # Add combined tool descriptions to agent memory as assistant message
            if tool_descriptions:
                combined_desc = "\n".join(tool_descriptions)
                self.agent_memory.append({"role": "assistant", "content": combined_desc})
            
            return True  # Tool was used
        
        # Final answer (no tool calls) - add to both memories
        self.memory.append(response_message.model_dump())  # Full message to debug memory
        if response_message.content:
            self.agent_memory.append({"role": "assistant", "content": response_message.content})
        
        return response_message.content  # Final answer
    
    def execute(self):
        """Execute the ReAct loop: Thought -> Action -> Observation"""
        # Generate reasoning
        self.think()
        
        # Take action (may involve tools)
        result = self.act()
        
        # If tools were used, continue the loop
        if result == True:
            return self.execute()
        
        # Otherwise return the final answer
        # Log both memories for debugging
        logger.info("=== DEBUG MEMORY ===")
        for msg in self.memory:
            logger.info(f"Debug memory: {msg}")
        
        logger.info("=== AGENT MEMORY ===")
        for msg in self.agent_memory:
            logger.info(f"Agent memory: {msg}")

        return result