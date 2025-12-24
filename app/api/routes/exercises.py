import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.exercise import ExerciseCreateRequest, ExerciseResponse
from app.models.exercise import Exercise
from app.models.user import User
from app.models.exercise_template import ExerciseTemplate
from app.api.schemas.exercise import ExerciseUpdateRequest

router = APIRouter(prefix="/exercises", tags=["exercises"])


def normalize_name(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def create_exercise(
        payload: ExerciseCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ExerciseResponse:
    normalized = normalize_name(payload.name)

    exists = (
        db.query(Exercise)
        .filter(Exercise.user_id == current_user.id)
        .filter(Exercise.name_normalized == normalized)
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise already exists",
        )

    ex = Exercise(
        user_id=current_user.id,
        template_id=None,
        name=payload.name,
        name_normalized=normalized,
        muscle_group=payload.muscle_group.lower(),
        equipment=payload.equipment.lower(),
        category=payload.category.lower(),
        tracking_type=payload.tracking_type.lower(),
    )

    db.add(ex)
    db.commit()
    db.refresh(ex)

    return ExerciseResponse(
        id=ex.id,
        template_id=ex.template_id,
        name=ex.name,
        muscle_group=ex.muscle_group,
        equipment=ex.equipment,
        category=ex.category,
        tracking_type=ex.tracking_type,
    )


@router.get("", response_model=list[ExerciseResponse], status_code=status.HTTP_200_OK)
def list_exercises(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        q: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
) -> list[ExerciseResponse]:
    query = db.query(Exercise).filter(Exercise.user_id == current_user.id)

    if q:
        qn = normalize_name(q)
        query = query.filter(Exercise.name_normalized.ilike(f"%{qn}%"))

    items = (
        query.order_by(Exercise.name.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        ExerciseResponse(
            id=e.id,
            template_id=e.template_id,
            name=e.name,
            muscle_group=e.muscle_group,
            equipment=e.equipment,
            category=e.category,
            tracking_type=e.tracking_type,
        )
        for e in items
    ]


@router.post(
    "/from-template/{template_id}",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_exercise_from_template(
        template_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ExerciseResponse:
    template = db.query(ExerciseTemplate).filter(ExerciseTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    normalized = normalize_name(template.name)

    exists = (
        db.query(Exercise)
        .filter(Exercise.user_id == current_user.id)
        .filter(Exercise.name_normalized == normalized)
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise already exists",
        )

    # We keep a single muscle_group string in user exercises for MVP:
    muscle_group = (template.primary_muscles[0] if template.primary_muscles else "unknown")

    ex = Exercise(
        user_id=current_user.id,
        template_id=template.id,
        name=template.name,
        name_normalized=normalized,
        muscle_group=muscle_group,
        equipment=template.equipment,
        category=template.category,
        tracking_type=template.tracking_type,
    )

    db.add(ex)
    db.commit()
    db.refresh(ex)

    return ExerciseResponse(
        id=ex.id,
        template_id=ex.template_id,
        name=ex.name,
        muscle_group=ex.muscle_group,
        equipment=ex.equipment,
        category=ex.category,
        tracking_type=ex.tracking_type,
    )


@router.put(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    status_code=status.HTTP_200_OK,
)
def update_exercise(
        exercise_id: int,
        payload: ExerciseUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ExerciseResponse:
    ex = (
        db.query(Exercise)
        .filter(Exercise.id == exercise_id)
        .filter(Exercise.user_id == current_user.id)
        .first()
    )
    if not ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    # Name update + collision check
    if payload.name is not None:
        normalized = normalize_name(payload.name)
        collision = (
            db.query(Exercise)
            .filter(Exercise.user_id == current_user.id)
            .filter(Exercise.name_normalized == normalized)
            .filter(Exercise.id != ex.id)
            .first()
        )
        if collision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Exercise name already exists",
            )
        ex.name = payload.name
        ex.name_normalized = normalized

    if payload.muscle_group is not None:
        ex.muscle_group = payload.muscle_group.lower()

    if payload.equipment is not None:
        ex.equipment = payload.equipment.lower()

    if payload.category is not None:
        ex.category = payload.category.lower()

    if payload.tracking_type is not None:
        ex.tracking_type = payload.tracking_type.lower()

    db.commit()
    db.refresh(ex)

    return ExerciseResponse(
        id=ex.id,
        template_id=ex.template_id,
        name=ex.name,
        muscle_group=ex.muscle_group,
        equipment=ex.equipment,
        category=ex.category,
        tracking_type=ex.tracking_type,
    )


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_exercise(
        exercise_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> None:
    ex = (
        db.query(Exercise)
        .filter(Exercise.id == exercise_id)
        .filter(Exercise.user_id == current_user.id)
        .first()
    )
    if not ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    db.delete(ex)
    db.commit()
    return None
