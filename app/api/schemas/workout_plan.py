from pydantic import BaseModel, Field


class WorkoutPlanCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class WorkoutPlanResponse(BaseModel):
    id: int
    name: str


class WorkoutPlanItemCreateRequest(BaseModel):
    exercise_id: int
    position: int = Field(ge=1)

    target_sets: int | None = Field(default=None, ge=1)
    target_reps: int | None = Field(default=None, ge=1)
    target_weight_kg: float | None = Field(default=None, ge=0)
    target_duration_seconds: int | None = Field(default=None, ge=1)
    target_distance_meters: int | None = Field(default=None, ge=1)


class WorkoutPlanItemResponse(BaseModel):
    id: int
    exercise_id: int
    position: int

    target_sets: int | None
    target_reps: int | None
    target_weight_kg: float | None
    target_duration_seconds: int | None
    target_distance_meters: int | None


class WorkoutPlanDetailResponse(WorkoutPlanResponse):
    items: list[WorkoutPlanItemResponse]