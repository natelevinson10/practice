from openai import OpenAI
import os
import dotenv
import uuid
from pydantic import BaseModel, Field

# Load environment variables
dotenv.load_dotenv()

# Create OpenAI client instance with API key from environment
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Client:
    def __init__(self):
        self.client = openai_client
        self.model = "gpt-4o-2024-08-06"
        self.session_id = str(uuid.uuid4())

class FlightDetails(BaseModel):
    date: str = Field(description="The date of the flight")
    time: str = Field(description="The time of the flight")
    origin: str = Field(description="The origin (take off point) of the flight")
    destination: str = Field(description="The destination of the flight")

