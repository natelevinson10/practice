from openai import OpenAI
from loguru import logger
import os
import dotenv
import datetime
from models.models import Client, FlightDetails
from tool_calls.tools import parse_booking_request

# Load environment variables
dotenv.load_dotenv()

# Configure logger to write to file (overwrite on each run)
log_file_path = "/Users/natelevinson/Desktop/practice/logs/workflow.log"
logger.add(log_file_path, rotation="1 day", retention="7 days", level="DEBUG", mode="w")

# Log script startup
logger.info("=" * 80)
logger.info(f"⏰ Start time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)

def run_workflow():
    client = Client()
    user_input = "I want to book a flight from San Francisco to Boston on December 15th at 2pm"
    
    # Test basic flight details extraction
    flight_details = parse_booking_request(client, user_input)
    logger.info(f"Extracted flight details: {flight_details}")

if __name__ == "__main__":
    run_workflow()