from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExerciseTemplate(Base):
    __tablename__ = "exercise_templates"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Stable ID from dataset (e.g. "Close-Grip_Barbell_Bench_Press")
    source_id: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )

    # Our own stable key for internal routing/urls
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    # Neutral name (English for now, LP later)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional media (URL only, later you can point to your own images/CDN)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category: Mapped[str] = mapped_column(String(50), nullable=False)      # e.g. strength/cardio
    equipment: Mapped[str] = mapped_column(String(50), nullable=False)     # barbell/dumbbell/machine/body only
    tracking_type: Mapped[str] = mapped_column(String(30), nullable=False) # weight_reps/time/distance

    # Extra dataset metadata (useful for filters)
    force: Mapped[str | None] = mapped_column(String(20), nullable=True)      # push/pull/static
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)      # beginner/...
    mechanic: Mapped[str | None] = mapped_column(String(20), nullable=True)   # compound/isolation

    primary_muscles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    secondary_muscles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    instructions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)