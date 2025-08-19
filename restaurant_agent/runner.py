from src.agent.host_agent import HostAgent
from src.agent.llm import LLM
from src.config.logging_init import init_logging, log_startup
from src.prompts.system_prompt import SYSTEM_PROMPT

def loop():

    # Initialize logging
    init_logging()
    log_startup()

    # Initialize agent
    client = LLM(model="gpt-5-mini")
    host_agent = HostAgent(client, system_prompt=SYSTEM_PROMPT)

    # Continuous loop
    while True:
        query = input("\n> ")
        if query.lower() == 'quit':
            break
        
        result = host_agent(query)
        print(f"\nAnswer: {result}")

if __name__ == "__main__":
    loop()