import json
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.exercise_template import ExerciseTemplate


DATA_FILE = Path("data/free-exercise-db.exercises.json")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:100] or "exercise"


def map_tracking_type(category: str) -> str:
    # MVP rule: strength -> weight_reps, everything else -> time
    # (we can refine later, e.g. distance for running/cycling)
    if category.lower() == "strength":
        return "weight_reps"
    return "time"


def seed() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA_FILE}")

    items = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    db: Session = SessionLocal()
    try:
        created = 0
        skipped = 0

        for item in items:
            source_id = item.get("id")
            name = item.get("name")
            category = (item.get("category") or "strength").lower()
            equipment = (item.get("equipment") or "body").lower()

            if not source_id or not name:
                skipped += 1
                continue

            exists = db.query(ExerciseTemplate).filter(ExerciseTemplate.source_id == source_id).first()
            if exists:
                skipped += 1
                continue

            primary = item.get("primaryMuscles") or []
            secondary = item.get("secondaryMuscles") or []
            instructions = item.get("instructions") or []

            template = ExerciseTemplate(
                source_id=source_id,
                slug=slugify(source_id),
                name=name,
                description=None,      # keep null for now (LP later)
                image_url=None,        # you will add your own images later
                category=category,
                equipment=equipment,
                tracking_type=map_tracking_type(category),
                force=item.get("force"),
                level=item.get("level"),
                mechanic=item.get("mechanic"),
                primary_muscles=primary,
                secondary_muscles=secondary,
                instructions=instructions,
            )

            db.add(template)
            created += 1

        db.commit()
        print(f"Seed done. created={created}, skipped={skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()