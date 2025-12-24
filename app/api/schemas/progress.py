from pydantic import BaseModel


class ExercisePRResponse(BaseModel):
    exercise_id: int
    exercise_name: str
    tracking_type: str

    best_weight_kg: float | None = None
    best_reps: int | None = None

    best_duration_seconds: int | None = None
    best_distance_meters: int | None = None
