from __future__ import annotations

import os
from pathlib import Path
import logging

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")

DATABASE_URL = os.getenv("DATABASE_URL")
ENV = os.getenv("ENV")
SESSION_SECRET = os.getenv("SESSION_SECRET")

from app.database import Base, SessionLocal, engine
from app.services import quiz_service


app = FastAPI()
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

if (ENV or "").lower() in {"production", "prod"} and not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is required in production")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET or "dev-secret-change-me",
)


@app.on_event("startup")
def startup() -> None:
    logger.info("Application startup")
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def normalize_levels(levels: str | None) -> str:
    if levels == "beginner":
        return "A1,A2"
    if levels == "intermediate":
        return "B1,B2"
    if levels == "advanced":
        return "C1,C2"
    if not levels:
        return "B1,B2"
    return levels

def infer_ui_level(levels: str | None) -> str:
    normalized = normalize_levels(levels)
    if normalized == "A1,A2":
        return "beginner"
    if normalized == "C1,C2":
        return "advanced"
    return "intermediate"

def get_question_with_fallback(db: Session, session: dict, levels: str):
    question, stats, error = quiz_service.get_or_create_question(db, session, levels)
    if question is None and error and "No questions found for selected CEFR levels." in error:
        question, stats, error = quiz_service.get_or_create_question(db, session, None)
    return question, stats, error


@app.get("/")
def home() -> RedirectResponse:
    return RedirectResponse("/play-v2")


@app.get("/play-v2", response_class=HTMLResponse)
def play(request: Request, levels: str | None = None, db: Session = Depends(get_db)):
    levels = normalize_levels(levels)
    ui_level = infer_ui_level(levels)
    question, stats, error = get_question_with_fallback(db, request.session, levels)
    return templates.TemplateResponse(
        "game_v2.html",
        {
            "request": request,
            "question": question,
            "stats": stats,
            "levels": levels,
            "ui_level": ui_level,
            "result": None,
            "error": error,
        },
    )


@app.get("/api/quiz")
def get_quiz(request: Request, levels: str | None = None, db: Session = Depends(get_db)):
    levels = normalize_levels(levels)
    question, stats, error = quiz_service.get_or_create_question(db, request.session, levels)
    if error:
        return JSONResponse({"ok": False, "error": error, "stats": stats.__dict__}, status_code=404)
    return {
        "ok": True,
        "question": question.__dict__,
        "stats": stats.__dict__,
    }


@app.post("/api/quiz/answer")
def answer_quiz(
    request: Request,
    question_id: int = Form(...),
    selected_option: str = Form(...),
    levels: str | None = Form(None),
    db: Session = Depends(get_db),
):
    levels = normalize_levels(levels)
    payload, _stats, _ = quiz_service.submit_answer(db, request.session, question_id, selected_option, levels)
    if payload is None:
        return JSONResponse({"ok": False, "error": "Invalid request."}, status_code=400)

    return {
        "ok": True,
        "feedback": payload["feedback"],
        "next_question": payload["next_question"].__dict__ if payload["next_question"] else None,
        "stats": payload["stats"].__dict__,
        "error": payload["error"],
    }


@app.post("/play-v2", response_class=HTMLResponse)
def submit_legacy(
    request: Request,
    question_id: int = Form(...),
    selected_option: str = Form(...),
    levels: str | None = Form(None),
    db: Session = Depends(get_db),
):
    levels = normalize_levels(levels)
    ui_level = infer_ui_level(levels)
    payload, _stats, _ = quiz_service.submit_answer(db, request.session, question_id, selected_option, levels)
    if payload and payload.get("error") and "No questions found for selected CEFR levels." in payload["error"]:
        next_question, stats, error = quiz_service.get_or_create_question(db, request.session, None)
        payload["next_question"] = next_question
        payload["stats"] = stats
        payload["error"] = error
    return templates.TemplateResponse(
        "game_v2.html",
        {
            "request": request,
            "question": payload["answered_question"],
            "stats": payload["stats"],
            "levels": levels,
            "ui_level": ui_level,
            "result": payload["feedback"],
            "error": payload["error"],
        },
    )


@app.get("/reset")
def reset(request: Request) -> RedirectResponse:
    quiz_service.reset_progress(request.session)
    return RedirectResponse("/play-v2")
