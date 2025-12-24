from datetime import datetime
from pydantic import BaseModel


class ProgressPoint(BaseModel):
    timestamp: datetime
    value: float


class ExerciseHistoryResponse(BaseModel):
    exercise_id: int
    exercise_name: str
    tracking_type: str
    points: list[ProgressPoint]
