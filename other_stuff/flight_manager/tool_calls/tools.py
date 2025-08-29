import json
import os
from openai import OpenAI
from pydantic import BaseModel, Field
import dotenv
from models.models import Client, FlightDetails
from loguru import logger

def parse_booking_request(user_input: str) -> FlightDetails:
    """
    Tool function to extract flight information from the users request.
    """
    logger.info(f"Calling parse_booking_request with user_input: {user_input}")
    
    # Create a client instance for the tool call
    client = Client()

    completion = client.client.beta.chat.completions.parse(
        model=client.model,
        messages=[
            {
                "role": "system",
                "content": """You are a helpful flight assistant.
                              If the user asks to book a flight, extract the date, time, origin, and destination
                              Otherwise, just communicate with the user in a helpful way.
                            """
            },
            {   "role": "user",
                "content": user_input
            },
        ],
        response_format=FlightDetails
    )
    
    result = completion.choices[0].message.parsed
    logger.info(f"LLM call complete session ID {client.session_id}: Flight to {result.destination} from {result.origin} at {result.time} on {result.date}")

    # Return as dictionary for JSON serialization
    return {
        "date": result.date,
        "time": result.time,
        "origin": result.origin,
        "destination": result.destination
    }

def get_flights_data() -> dict:
    """
    Tool function to get flight data from the flights.json file.
    """
    logger.info("Calling get_flights_data")
    with open("flight_data.json", "r") as f:
        return json.load(f)
    
def edit_json_file(payload: dict) -> dict:
    """
    General-purpose JSON editing tool.
    Supports 'update', 'append', and 'delete' without rewriting the whole file.
    
    Args:
        payload (dict): Must include:
            - operation: "update" | "append" | "delete"
            - path: list of keys/indices to traverse (e.g. ["flights", 0, "origin"])
            - value: new value (for update/append)
    """
    logger.info(f"Calling edit_json_file with payload: {payload}")

    file_path = "flight_data.json"
    with open(file_path, "r") as f:
        data = json.load(f)
        
    op = payload.get("operation")
    path = payload.get("path", [])
    value = payload.get("value")

    # Traverse JSON
    target = data
    for key in path[:-1]:
        target = target[key]

    last_key = path[-1] if path else None

    if op == "update":
        target[last_key] = value

    elif op == "append":
        if not isinstance(target[last_key], list):
            return {"status": "error", "message": f"Target at {path} is not a list"}
        target[last_key].append(value)

    elif op == "delete":
        if isinstance(target, list):
            target.pop(last_key)
        else:
            target.pop(last_key, None)

    else:
        return {"status": "error", "message": f"Unknown operation {op}"}

    # Save updated JSON
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    return {"status": "success", "operation": op, "data": data}



tools = [
    {
        "type": "function",
        "function": {
            "name": "parse_booking_request",
            "description": "Extract info from users message for a flight with the provided details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {"type": "string", "description": "The user's flight request message"}
                },
                "required": ["user_input"],
                "additionalProperties": False,
            },
            "strict": False,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_flights_data",
            "description": "Get flight data from the flights.json file. This file contains the available flights a user can book and shows all booked flights.",
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_json_file",
            "description": "Edit the flights.json file to book/cancel/edit flights. Use 'delete' to remove from an array and 'append' to add to an array. Use 'update' to update a value in the json file. IMPORTANT: When appending a flight, use 'value' key for the flight object, NOT 'flight'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payload": {
                        "type": "object",
                        "description": "The edit operation details",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["update", "append", "delete"],
                                "description": "The operation to perform"
                            },
                            "path": {
                                "type": "array",
                                "items": {"type": ["string", "integer"]},
                                "description": "Path to the target in JSON (e.g., ['available_flights', 0] for first flight)"
                            },
                            "value": {
                                "type": "object",
                                "description": "The data to append or update. For appending flights, this should be the flight object. (Not needed for delete operation)"
                            }
                        },
                        "required": ["operation", "path"]
                    }
                },
                "required": ["payload"],
                "additionalProperties": False,
            },
            "strict": False,
        }
    }
]

# Function mapping for tool execution
available_functions = {
    "parse_booking_request": parse_booking_request,
    "get_flights_data": get_flights_data,
    "edit_json_file": edit_json_file
}

