from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db_service import get_session_detail, init_db, list_sessions
from main import run_meal_planner_request


app = FastAPI(title="AI Meal Planner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MealPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    age: int | None = Field(default=0, ge=0, le=120)
    weight: int | None = Field(default=0, ge=0, le=400)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/meal-plan")
def create_meal_plan(request: MealPlanRequest) -> dict[str, Any]:
    try:
        return run_meal_planner_request(request.prompt, request.age, request.weight)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/sessions")
def sessions(limit: int = 20) -> list[dict[str, Any]]:
    return list_sessions(limit=max(1, min(limit, 100)))


@app.get("/api/sessions/{session_id}")
def session_detail(session_id: int) -> dict[str, Any]:
    detail = get_session_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return detail
