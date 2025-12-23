from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.exercise_template import ExerciseTemplateResponse
from app.models.exercise_template import ExerciseTemplate

router = APIRouter(prefix="/exercise-templates", tags=["exercise-templates"])


@router.get("", response_model=list[ExerciseTemplateResponse], status_code=status.HTTP_200_OK)
def list_templates(
    response: Response,
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="Search by name (contains)"),
    category: str | None = Query(default=None),
    equipment: str | None = Query(default=None),
    tracking_type: str | None = Query(default=None),
    muscle: str | None = Query(default=None, description="Matches primary/secondary muscles"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ExerciseTemplateResponse]:
    query = db.query(ExerciseTemplate)

    if q:
        query = query.filter(ExerciseTemplate.name.ilike(f"%{q}%"))

    if category:
        query = query.filter(ExerciseTemplate.category == category.lower())

    if equipment:
        query = query.filter(ExerciseTemplate.equipment == equipment.lower())

    if tracking_type:
        query = query.filter(ExerciseTemplate.tracking_type == tracking_type.lower())

    if muscle:
        m = muscle.lower()
        # JSONB contains: list contains the string
        query = query.filter(
            (ExerciseTemplate.primary_muscles.contains([m]))
            | (ExerciseTemplate.secondary_muscles.contains([m]))
        )

    total = query.count()
    response.headers["X-Total-Count"] = str(total)

    items = (
        query.order_by(ExerciseTemplate.name.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        ExerciseTemplateResponse(
            id=t.id,
            source_id=t.source_id,
            slug=t.slug,
            name=t.name,
            category=t.category,
            equipment=t.equipment,
            tracking_type=t.tracking_type,
        )
        for t in items
    ]