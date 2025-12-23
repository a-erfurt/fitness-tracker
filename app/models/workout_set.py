from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(primary_key=True)

    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"), index=True, nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True, nullable=False)

    set_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Strength
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    # Time / Distance
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)