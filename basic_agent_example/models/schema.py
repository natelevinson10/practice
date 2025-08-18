from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class ThoughtResponse(BaseModel):    
    reasoning: str = Field(
        description="The reasoning for the next action"
    )
    next_action: str = Field(
        description="The next action to take"
    )
    confidence: float = Field(
        description="The confidence in the next action"
    )

class GetPlanetMassParams(BaseModel):
    planet: Literal["Earth", "Mars", "Jupiter", "Saturn", "Mercury", "Neptune", "Uranus", "Venus"] = Field(
        description="Name of the planet to get the mass for"
    )

class CalculateParams(BaseModel):
    operation: str = Field(
        description="The arithmetic operation to perform (e.g., '1 + 1', '2 * 3', '5 / 2')"
    )

class GetPlanetMassResponse(BaseModel):
    mass: float = Field(
        description="The mass of the planet"
    )

class CalculateResponse(BaseModel):
    result: float = Field(
        description="The result of the arithmetic operation"
    )