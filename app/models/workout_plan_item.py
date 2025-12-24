from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkoutPlanItem(Base):
    __tablename__ = "workout_plan_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plans.id"), index=True, nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True, nullable=False)

    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # optional targets (MVP)
    target_sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    target_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_distance_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
