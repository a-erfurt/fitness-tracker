from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.workout_plan import (
    WorkoutPlanCreateRequest,
    WorkoutPlanDetailResponse,
    WorkoutPlanItemCreateRequest,
    WorkoutPlanItemResponse,
    WorkoutPlanResponse,
    WorkoutPlanItemUpdateRequest
)
from app.models.exercise import Exercise
from app.models.user import User
from app.models.workout_plan import WorkoutPlan
from app.models.workout_plan_item import WorkoutPlanItem

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
        payload: WorkoutPlanCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> WorkoutPlanResponse:
    plan = WorkoutPlan(user_id=current_user.id, name=payload.name)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return WorkoutPlanResponse(id=plan.id, name=plan.name)


@router.get("", response_model=list[WorkoutPlanResponse], status_code=status.HTTP_200_OK)
def list_plans(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> list[WorkoutPlanResponse]:
    plans = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.user_id == current_user.id)
        .order_by(WorkoutPlan.id.desc())
        .all()
    )
    return [WorkoutPlanResponse(id=p.id, name=p.name) for p in plans]


@router.get("/{plan_id}", response_model=WorkoutPlanDetailResponse, status_code=status.HTTP_200_OK)
def get_plan(
        plan_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> WorkoutPlanDetailResponse:
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id)
        .filter(WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    items = (
        db.query(WorkoutPlanItem)
        .filter(WorkoutPlanItem.plan_id == plan.id)
        .order_by(WorkoutPlanItem.position.asc(), WorkoutPlanItem.id.asc())
        .all()
    )

    return WorkoutPlanDetailResponse(
        id=plan.id,
        name=plan.name,
        items=[
            WorkoutPlanItemResponse(
                id=i.id,
                exercise_id=i.exercise_id,
                position=i.position,
                target_sets=i.target_sets,
                target_reps=i.target_reps,
                target_weight_kg=float(i.target_weight_kg) if i.target_weight_kg is not None else None,
                target_duration_seconds=i.target_duration_seconds,
                target_distance_meters=i.target_distance_meters,
            )
            for i in items
        ],
    )


@router.post(
    "/{plan_id}/items",
    response_model=WorkoutPlanItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_item(
        plan_id: int,
        payload: WorkoutPlanItemCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> WorkoutPlanItemResponse:
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id)
        .filter(WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    ex = (
        db.query(Exercise)
        .filter(Exercise.id == payload.exercise_id)
        .filter(Exercise.user_id == current_user.id)
        .first()
    )
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    item = WorkoutPlanItem(
        plan_id=plan.id,
        exercise_id=ex.id,
        position=payload.position,
        target_sets=payload.target_sets,
        target_reps=payload.target_reps,
        target_weight_kg=payload.target_weight_kg,
        target_duration_seconds=payload.target_duration_seconds,
        target_distance_meters=payload.target_distance_meters,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return WorkoutPlanItemResponse(
        id=item.id,
        exercise_id=item.exercise_id,
        position=item.position,
        target_sets=item.target_sets,
        target_reps=item.target_reps,
        target_weight_kg=float(item.target_weight_kg) if item.target_weight_kg is not None else None,
        target_duration_seconds=item.target_duration_seconds,
        target_distance_meters=item.target_distance_meters,
    )


@router.put(
    "/{plan_id}/items/{item_id}",
    response_model=WorkoutPlanItemResponse,
    status_code=status.HTTP_200_OK,
)
def update_item(
        plan_id: int,
        item_id: int,
        payload: WorkoutPlanItemUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> WorkoutPlanItemResponse:
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id)
        .filter(WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    item = (
        db.query(WorkoutPlanItem)
        .filter(WorkoutPlanItem.id == item_id)
        .filter(WorkoutPlanItem.plan_id == plan.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Partial updates
    if payload.position is not None:
        item.position = payload.position

    if payload.target_sets is not None:
        item.target_sets = payload.target_sets
    if payload.target_reps is not None:
        item.target_reps = payload.target_reps
    if payload.target_weight_kg is not None:
        item.target_weight_kg = payload.target_weight_kg
    if payload.target_duration_seconds is not None:
        item.target_duration_seconds = payload.target_duration_seconds
    if payload.target_distance_meters is not None:
        item.target_distance_meters = payload.target_distance_meters

    db.commit()
    db.refresh(item)

    return WorkoutPlanItemResponse(
        id=item.id,
        exercise_id=item.exercise_id,
        position=item.position,
        target_sets=item.target_sets,
        target_reps=item.target_reps,
        target_weight_kg=float(item.target_weight_kg) if item.target_weight_kg is not None else None,
        target_duration_seconds=item.target_duration_seconds,
        target_distance_meters=item.target_distance_meters,
    )


@router.delete(
    "/{plan_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
        plan_id: int,
        item_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> None:
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id)
        .filter(WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    item = (
        db.query(WorkoutPlanItem)
        .filter(WorkoutPlanItem.id == item_id)
        .filter(WorkoutPlanItem.plan_id == plan.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    db.delete(item)
    db.commit()
    return None
