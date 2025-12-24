from pydantic import BaseModel, Field


class PlanReorderItem(BaseModel):
    item_id: int
    position: int = Field(ge=1)


class PlanReorderRequest(BaseModel):
    items: list[PlanReorderItem] = Field(min_length=1)
