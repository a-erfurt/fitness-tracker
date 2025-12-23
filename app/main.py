from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.api.routes.exercise_templates import router as exercise_templates_router
from app.api.routes.exercises import router as exercises_router

app = FastAPI(title="Fitness Tracker API", version="0.1.0")
app.include_router(auth_router)
app.include_router(exercise_templates_router)
app.include_router(exercises_router)

@app.get("/")
def root() -> dict:
    return {"name": "Fitness Tracker API", "version": "0.1.0"}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
