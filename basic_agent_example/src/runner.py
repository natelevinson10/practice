from agent.host_agent import HostAgent
from agent.llm import LLM
from config.logging_creation import init_logging, log_startup
from prompts.system_prompts import SYSTEM_PROMPT

def loop(query: str = ""):

    # Initialize logging
    init_logging()
    log_startup()

    # Initialize agent
    agent = HostAgent(client=LLM(model="gpt-4o-mini"), system_prompt=SYSTEM_PROMPT)

    # Get response from agent - it will handle tool calls automatically
    result = agent(query)
    
    print("\nFinal Answer:")
    print(result)
    print("\nConversation history:")
    print(agent.memory)


loop(query="What is the mass of Earth plus the mass of Saturn and all of that times 2?")
