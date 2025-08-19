from openai import OpenAI
import os
import dotenv

dotenv.load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class LLM:
    def __init__(self, model: str):
        self.client = openai_client
        self.model = model
        self.chat = self.client.chat

        