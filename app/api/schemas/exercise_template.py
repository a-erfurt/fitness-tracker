from pydantic import BaseModel


class ExerciseTemplateResponse(BaseModel):
    id: int
    source_id: str
    slug: str
    name: str
    category: str
    equipment: str
    tracking_type: str