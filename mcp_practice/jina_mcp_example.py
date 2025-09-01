from openai import OpenAI
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
import dotenv
import os
import asyncio

dotenv.load_dotenv()

async def main():
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Connect to Jina MCP server
    async with MCPServerStdio(
        params={
            "command": "npx",
            "args": ["-y", "mcp-remote", "https://mcp.jina.ai/sse", "--header", f"Authorization: Bearer jina_b8a0a98855ca42879121ab492de564faY-6xevSudQMs6bm4x5aNtyqpxC2Z"],
        }
    ) as jina_server:
        # If you have a Jina API key, use this configuration instead:
        # async with MCPServerStdio(
        #     params={
        #         "command": "npx",
        #         "args": ["-y", "mcp-remote", "https://mcp.jina.ai/sse", "--header", f"Authorization: Bearer {os.getenv('JINA_API_KEY')}"],
        #     }
        # ) as jina_server:
        
        # Create an agent with the Jina MCP server
        agent = Agent(
            name="Assistant",
            instructions="You are a helpful assistant that can search the web and read URLs using Jina's tools.",
            model="gpt-4o-mini",
            mcp_servers=[jina_server]
        )
        
        #print all the tools available to the agent
        print(f"Manual tools: {agent.tools}")
        
        # Get MCP tools directly from the server
        mcp_tools = await jina_server.list_tools()
        print(f"MCP tools from Jina server:")
        for tool in mcp_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # # Create a response
        # result = await Runner.run(
        #     agent,
        #     "Search for an image of a hamster and return its URL"
        # )
        
        # print("Agent response:")
        # # Handle the RunResult object
        
        # #print full memory including system message
        # print(f"agent instructions: {agent.instructions}")
        # for message in result.to_input_list():
        #     #print the first 100 characters of the message
        #     print(message)
        # print()

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())