from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.progress import ExercisePRResponse
from app.models.exercise import Exercise
from app.models.user import User
from app.models.workout_set import WorkoutSet
from app.api.schemas.progress_history import ExerciseHistoryResponse, ProgressPoint
from app.models.workout import Workout
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from app.api.schemas.progress_overview import ProgressOverviewResponse, TopExerciseItem

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/prs", response_model=list[ExercisePRResponse], status_code=status.HTTP_200_OK)
def list_personal_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExercisePRResponse]:
    # Load all user exercises
    exercises = (
        db.query(Exercise)
        .filter(Exercise.user_id == current_user.id)
        .order_by(Exercise.name.asc())
        .all()
    )

    results: list[ExercisePRResponse] = []

    for ex in exercises:
        sets = (
            db.query(WorkoutSet)
            .filter(WorkoutSet.exercise_id == ex.id)
            .all()
        )

        if not sets:
            results.append(
                ExercisePRResponse(
                    exercise_id=ex.id,
                    exercise_name=ex.name,
                    tracking_type=ex.tracking_type,
                )
            )
            continue

        if ex.tracking_type == "weight_reps":
            best = None
            for s in sets:
                if s.weight_kg is None:
                    continue
                if best is None or s.weight_kg > best.weight_kg:
                    best = s
            results.append(
                ExercisePRResponse(
                    exercise_id=ex.id,
                    exercise_name=ex.name,
                    tracking_type=ex.tracking_type,
                    best_weight_kg=float(best.weight_kg) if best and best.weight_kg is not None else None,
                    best_reps=best.reps if best else None,
                )
            )

        elif ex.tracking_type == "time":
            best_seconds = max((s.duration_seconds or 0) for s in sets)
            results.append(
                ExercisePRResponse(
                    exercise_id=ex.id,
                    exercise_name=ex.name,
                    tracking_type=ex.tracking_type,
                    best_duration_seconds=best_seconds if best_seconds > 0 else None,
                )
            )

        elif ex.tracking_type == "distance":
            best_meters = max((s.distance_meters or 0) for s in sets)
            results.append(
                ExercisePRResponse(
                    exercise_id=ex.id,
                    exercise_name=ex.name,
                    tracking_type=ex.tracking_type,
                    best_distance_meters=best_meters if best_meters > 0 else None,
                )
            )

        else:
            # unknown tracking type -> return empty PR values
            results.append(
                ExercisePRResponse(
                    exercise_id=ex.id,
                    exercise_name=ex.name,
                    tracking_type=ex.tracking_type,
                )
            )

    return results

@router.get(
    "/exercises/{exercise_id}/history",
    response_model=ExerciseHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def exercise_history(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExerciseHistoryResponse:
    ex = (
        db.query(Exercise)
        .filter(Exercise.id == exercise_id)
        .filter(Exercise.user_id == current_user.id)
        .first()
    )
    if not ex:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    # Join WorkoutSet -> Workout to get a timestamp (started_at)
    rows = (
        db.query(WorkoutSet, Workout)
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .filter(WorkoutSet.exercise_id == ex.id)
        .filter(Workout.user_id == current_user.id)
        .order_by(Workout.started_at.asc(), WorkoutSet.set_number.asc(), WorkoutSet.id.asc())
        .all()
    )

    points: list[ProgressPoint] = []

    # workout_id -> best_value + timestamp
    best_by_workout: dict[int, tuple[float, object]] = {}

    for s, w in rows:
        if ex.tracking_type == "weight_reps":
            if s.weight_kg is None or s.reps is None:
                continue
            value = float(s.weight_kg) * float(s.reps)

        elif ex.tracking_type == "time":
            if s.duration_seconds is None:
                continue
            value = float(s.duration_seconds)

        elif ex.tracking_type == "distance":
            if s.distance_meters is None:
                continue
            value = float(s.distance_meters)

        else:
            continue

        current = best_by_workout.get(w.id)
        if current is None or value > current[0]:
            best_by_workout[w.id] = (value, w.started_at)

    # Convert to list of points, sorted by time
    for _, (value, ts) in sorted(best_by_workout.items(), key=lambda x: x[1][1]):
        points.append(ProgressPoint(timestamp=ts, value=value))

    return ExerciseHistoryResponse(
        exercise_id=ex.id,
        exercise_name=ex.name,
        tracking_type=ex.tracking_type,
        points=points,
    )

@router.get(
    "/overview",
    response_model=ProgressOverviewResponse,
    status_code=status.HTTP_200_OK,
)
def overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProgressOverviewResponse:
    now = datetime.now(tz=timezone.utc)

    # Start of week (Monday 00:00) in UTC
    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())

    # Workouts this week
    workouts_this_week = (
        db.query(func.count(Workout.id))
        .filter(Workout.user_id == current_user.id)
        .filter(Workout.started_at >= start_of_week)
        .filter(Workout.started_at <= now)
        .scalar()
    ) or 0

    # Sets this week (join sets -> workouts in range)
    sets_this_week = (
        db.query(func.count(WorkoutSet.id))
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .filter(Workout.user_id == current_user.id)
        .filter(Workout.started_at >= start_of_week)
        .filter(Workout.started_at <= now)
        .scalar()
    ) or 0

    # Top exercises this week by number of sets
    rows = (
        db.query(
            WorkoutSet.exercise_id,
            func.count(WorkoutSet.id).label("sets_count"),
        )
        .join(Workout, Workout.id == WorkoutSet.workout_id)
        .filter(Workout.user_id == current_user.id)
        .filter(Workout.started_at >= start_of_week)
        .filter(Workout.started_at <= now)
        .group_by(WorkoutSet.exercise_id)
        .order_by(func.count(WorkoutSet.id).desc())
        .limit(5)
        .all()
    )

    # Map exercise_id -> name
    exercise_ids = [r.exercise_id for r in rows]
    name_map = {}
    if exercise_ids:
        ex_rows = (
            db.query(Exercise.id, Exercise.name)
            .filter(Exercise.user_id == current_user.id)
            .filter(Exercise.id.in_(exercise_ids))
            .all()
        )
        name_map = {eid: name for eid, name in ex_rows}

    top = [
        TopExerciseItem(
            exercise_id=r.exercise_id,
            exercise_name=name_map.get(r.exercise_id, "Unknown"),
            sets_count=int(r.sets_count),
        )
        for r in rows
    ]

    return ProgressOverviewResponse(
        workouts_this_week=int(workouts_this_week),
        sets_this_week=int(sets_this_week),
        top_exercises_this_week=top,
    )