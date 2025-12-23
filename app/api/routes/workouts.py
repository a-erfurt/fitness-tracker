from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.workout import WorkoutCreateRequest, WorkoutResponse
from app.models.workout import Workout
from app.models.user import User
from app.api.schemas.workout import WorkoutSetCreateRequest, WorkoutSetResponse
from app.models.exercise import Exercise
from app.models.workout_set import WorkoutSet
from app.api.schemas.workout import WorkoutDetailResponse
from app.api.schemas.workout import WorkoutSetUpdateRequest

router = APIRouter(prefix="/workouts", tags=["workouts"])

def validate_set_payload(tracking_type: str, reps, weight_kg, duration_seconds, distance_meters) -> None:
    if tracking_type == "weight_reps":
        if reps is None or weight_kg is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="weight_reps requires reps and weight_kg",
            )
    elif tracking_type == "time":
        if duration_seconds is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="time requires duration_seconds",
            )
    elif tracking_type == "distance":
        if distance_meters is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="distance requires distance_meters",
            )


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def start_workout(
    payload: WorkoutCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutResponse:
    started_at = payload.started_at or datetime.now(tz=timezone.utc)

    w = Workout(
        user_id=current_user.id,
        started_at=started_at,
        ended_at=None,
        notes=payload.notes,
    )
    db.add(w)
    db.commit()
    db.refresh(w)

    return WorkoutResponse(
        id=w.id,
        started_at=w.started_at,
        ended_at=w.ended_at,
        notes=w.notes,
    )


@router.post("/{workout_id}/end", response_model=WorkoutResponse, status_code=status.HTTP_200_OK)
def end_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutResponse:
    w = (
        db.query(Workout)
        .filter(Workout.id == workout_id)
        .filter(Workout.user_id == current_user.id)
        .first()
    )
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    if w.ended_at is not None:
        # already ended - keep idempotent behavior
        return WorkoutResponse(id=w.id, started_at=w.started_at, ended_at=w.ended_at, notes=w.notes)

    w.ended_at = datetime.now(tz=timezone.utc)
    db.commit()
    db.refresh(w)

    return WorkoutResponse(
        id=w.id,
        started_at=w.started_at,
        ended_at=w.ended_at,
        notes=w.notes,
    )

@router.post(
    "/{workout_id}/sets",
    response_model=WorkoutSetResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_set(
    workout_id: int,
    payload: WorkoutSetCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutSetResponse:
    # Workout must belong to user
    w = (
        db.query(Workout)
        .filter(Workout.id == workout_id)
        .filter(Workout.user_id == current_user.id)
        .first()
    )
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    # Exercise must belong to user
    ex = (
        db.query(Exercise)
        .filter(Exercise.id == payload.exercise_id)
        .filter(Exercise.user_id == current_user.id)
        .first()
    )
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    tracking = ex.tracking_type

    if tracking == "weight_reps":
        if payload.reps is None or payload.weight_kg is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="weight_reps requires reps and weight_kg",
            )

    elif tracking == "time":
        if payload.duration_seconds is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="time requires duration_seconds",
            )

    elif tracking == "distance":
        if payload.distance_meters is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="distance requires distance_meters",
            )

    s = WorkoutSet(
        workout_id=w.id,
        exercise_id=ex.id,
        set_number=payload.set_number,
        reps=payload.reps,
        weight_kg=payload.weight_kg,
        duration_seconds=payload.duration_seconds,
        distance_meters=payload.distance_meters,
    )

    db.add(s)
    db.commit()
    db.refresh(s)

    return WorkoutSetResponse(
        id=s.id,
        exercise_id=s.exercise_id,
        set_number=s.set_number,
        reps=s.reps,
        weight_kg=float(s.weight_kg) if s.weight_kg is not None else None,
        duration_seconds=s.duration_seconds,
        distance_meters=s.distance_meters,
    )

@router.get("", response_model=list[WorkoutResponse], status_code=status.HTTP_200_OK)
def list_workouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
) -> list[WorkoutResponse]:
    items = (
        db.query(Workout)
        .filter(Workout.user_id == current_user.id)
        .order_by(Workout.started_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        WorkoutResponse(
            id=w.id,
            started_at=w.started_at,
            ended_at=w.ended_at,
            notes=w.notes,
        )
        for w in items
    ]

@router.get("/{workout_id}", response_model=WorkoutDetailResponse, status_code=status.HTTP_200_OK)
def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutDetailResponse:
    w = (
        db.query(Workout)
        .filter(Workout.id == workout_id)
        .filter(Workout.user_id == current_user.id)
        .first()
    )
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    sets = (
        db.query(WorkoutSet)
        .filter(WorkoutSet.workout_id == w.id)
        .order_by(WorkoutSet.exercise_id.asc(), WorkoutSet.set_number.asc(), WorkoutSet.id.asc())
        .all()
    )

    return WorkoutDetailResponse(
        id=w.id,
        started_at=w.started_at,
        ended_at=w.ended_at,
        notes=w.notes,
        sets=[
            WorkoutSetResponse(
                id=s.id,
                exercise_id=s.exercise_id,
                set_number=s.set_number,
                reps=s.reps,
                weight_kg=float(s.weight_kg) if s.weight_kg is not None else None,
                duration_seconds=s.duration_seconds,
                distance_meters=s.distance_meters,
            )
            for s in sets
        ],
    )

@router.put(
    "/{workout_id}/sets/{set_id}",
    response_model=WorkoutSetResponse,
    status_code=status.HTTP_200_OK,
)
def update_set(
    workout_id: int,
    set_id: int,
    payload: WorkoutSetUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutSetResponse:
    # Workout must belong to user
    w = (
        db.query(Workout)
        .filter(Workout.id == workout_id)
        .filter(Workout.user_id == current_user.id)
        .first()
    )
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    s = (
        db.query(WorkoutSet)
        .filter(WorkoutSet.id == set_id)
        .filter(WorkoutSet.workout_id == w.id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

    ex = (
        db.query(Exercise)
        .filter(Exercise.id == s.exercise_id)
        .filter(Exercise.user_id == current_user.id)
        .first()
    )
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    # Apply partial updates
    if payload.set_number is not None:
        s.set_number = payload.set_number

    if payload.reps is not None:
        s.reps = payload.reps
    if payload.weight_kg is not None:
        s.weight_kg = payload.weight_kg
    if payload.duration_seconds is not None:
        s.duration_seconds = payload.duration_seconds
    if payload.distance_meters is not None:
        s.distance_meters = payload.distance_meters

    # Validate after applying (but careful: if user doesn't send required fields,
    # we still validate against the final state on the set)
    validate_set_payload(
        ex.tracking_type,
        s.reps,
        s.weight_kg,
        s.duration_seconds,
        s.distance_meters,
    )

    db.commit()
    db.refresh(s)

    return WorkoutSetResponse(
        id=s.id,
        exercise_id=s.exercise_id,
        set_number=s.set_number,
        reps=s.reps,
        weight_kg=float(s.weight_kg) if s.weight_kg is not None else None,
        duration_seconds=s.duration_seconds,
        distance_meters=s.distance_meters,
    )

@router.delete(
    "/{workout_id}/sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_set(
    workout_id: int,
    set_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    w = (
        db.query(Workout)
        .filter(Workout.id == workout_id)
        .filter(Workout.user_id == current_user.id)
        .first()
    )
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    s = (
        db.query(WorkoutSet)
        .filter(WorkoutSet.id == set_id)
        .filter(WorkoutSet.workout_id == w.id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

    db.delete(s)
    db.commit()
    return None