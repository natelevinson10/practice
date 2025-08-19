from pydantic import BaseModel, Field

class ThoughtResponse(BaseModel):
    goal: str = Field(
        description="The goal of the user's query"
    )
    thought: str = Field(
        description="The reasoning for the next action"
    )
    next_action: str = Field(
        description="The next action to take"
    )
    confidence: float = Field(
        description="The confidence in the next action"
    )