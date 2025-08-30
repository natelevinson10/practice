from pydantic import BaseModel

class EvaluationResult(BaseModel):
    fully_answered: bool
    reason: str