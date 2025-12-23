from pydantic import BaseModel, Field


class ExerciseCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    muscle_group: str = Field(min_length=2, max_length=50)
    equipment: str = Field(min_length=2, max_length=50)
    category: str = Field(min_length=2, max_length=50)
    tracking_type: str = Field(min_length=2, max_length=30)

class ExerciseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    muscle_group: str | None = Field(default=None, min_length=2, max_length=50)
    equipment: str | None = Field(default=None, min_length=2, max_length=50)
    category: str | None = Field(default=None, min_length=2, max_length=50)
    tracking_type: str | None = Field(default=None, min_length=2, max_length=30)


class ExerciseResponse(BaseModel):
    id: int
    template_id: int | None
    name: str
    muscle_group: str
    equipment: str
    category: str
    tracking_type: str