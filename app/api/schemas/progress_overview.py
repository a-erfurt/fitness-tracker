from pydantic import BaseModel


class TopExerciseItem(BaseModel):
    exercise_id: int
    exercise_name: str
    sets_count: int


class ProgressOverviewResponse(BaseModel):
    workouts_this_week: int
    sets_this_week: int
    top_exercises_this_week: list[TopExerciseItem]