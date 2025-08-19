from pydantic import BaseModel, Field
from typing import Optional

class ThoughtResponse(BaseModel):
    user_query: str = Field(
        description="The user's query"
    )
    thought: str = Field(
        description="The reasoning for the next action"
    )
    next_action: str = Field(
        description="The next action to take (use 'provide_answer' if no tools needed)"
    )
    answer: Optional[str] = Field(
        default=None,
        description="Direct answer if next_action is 'provide_answer'"
    )
    confidence: float = Field(
        description="The confidence in the next action"
    )