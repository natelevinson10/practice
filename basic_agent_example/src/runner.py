from agent.host_agent import HostAgent
from agent.llm import LLM
from config.logging_creation import init_logging, log_startup
from prompts.system_prompts import SYSTEM_PROMPT

def loop():
    # Initialize logging
    init_logging()
    log_startup()

    # Initialize agent
    agent = HostAgent(client=LLM(model="gpt-4o-mini"), system_prompt=SYSTEM_PROMPT)

    # Continuous loop
    while True:
        query = input("\n> ")
        if query.lower() == 'quit':
            break
        
        result = agent(query)
        print(f"\nAnswer: {result}")


loop()
