import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schema import GetPlanetMassParams, CalculateParams, GetPlanetMassResponse, CalculateResponse

def calculate(operation: str) -> dict:
    # Validate input
    params = CalculateParams(operation=operation)
    result = eval(params.operation)
    
    # Return structured response
    response = CalculateResponse(result=result, fav_animal="dog")
    return response.model_dump()


def get_planet_mass(planet: str) -> dict:
    # Validate input using Pydantic
    params = GetPlanetMassParams(planet=planet)
    
    # Get mass based on validated planet name
    mass = 0.0
    match params.planet.lower():
        case "earth":
            mass = 5.972e24
        case "jupiter":
            mass = 1.898e27
        case "mars":
            mass = 6.39e23
        case "mercury":
            mass = 3.285e23
        case "neptune":
            mass = 1.024e26
        case "saturn":
            mass = 5.683e26
        case "uranus":
            mass = 8.681e25
        case "venus":
            mass = 4.867e24
    
    # Return structured response
    response = GetPlanetMassResponse(mass=mass)
    return response.model_dump()
        
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate the result of an arithmetic operation",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The arithmetic operation to perform (e.g., '1 + 1', '2 * 3', '5 / 2')"
                    }
                },
                "required": ["operation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_planet_mass",
            "description": "Get the mass of a planet in kg",
            "parameters": {
                "type": "object",
                "properties": {
                    "planet": {
                        "type": "string",
                        "description": "Name of the planet (Earth, Mars, Jupiter, Saturn, etc.)"
                    }
                }
            },
            "required": ["planet"]
        }
    }
]   

available_tools = {
    "calculate": calculate,
    "get_planet_mass": get_planet_mass
}