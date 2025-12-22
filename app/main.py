from fastapi import FastAPI

app = FastAPI(title="Fitness Tracker API", version="0.1.0")


@app.get("/")
def root() -> dict:
    return {"name": "Fitness Tracker API", "version": "0.1.0"}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
