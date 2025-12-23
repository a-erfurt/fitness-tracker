from datetime import datetime
from pydantic import BaseModel, Field


# -------- Workouts --------

class WorkoutCreateRequest(BaseModel):
    started_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)


class WorkoutResponse(BaseModel):
    id: int
    started_at: datetime
    ended_at: datetime | None
    notes: str | None


# -------- Workout Sets --------

class WorkoutSetCreateRequest(BaseModel):
    exercise_id: int
    set_number: int = Field(ge=1)

    reps: int | None = Field(default=None, ge=1)
    weight_kg: float | None = Field(default=None, ge=0)

    duration_seconds: int | None = Field(default=None, ge=1)
    distance_meters: int | None = Field(default=None, ge=1)

class WorkoutSetUpdateRequest(BaseModel):
    set_number: int | None = Field(default=None, ge=1)

    reps: int | None = Field(default=None, ge=1)
    weight_kg: float | None = Field(default=None, ge=0)

    duration_seconds: int | None = Field(default=None, ge=1)
    distance_meters: int | None = Field(default=None, ge=1)


class WorkoutSetResponse(BaseModel):
    id: int
    exercise_id: int
    set_number: int

    reps: int | None
    weight_kg: float | None
    duration_seconds: int | None
    distance_meters: int | None

class WorkoutDetailResponse(WorkoutResponse):
    sets: list[WorkoutSetResponse]