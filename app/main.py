from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from app.database import engine, SessionLocal, Base
from app import models
from app.models import Question
from app.crud import create_question, get_random_question

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

# Static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Sessions
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-change-later"
)

# -----------------------------
# Startup (DB init + minimal seed)
# -----------------------------
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    if db.query(Question).count() == 0:
        create_question(db, {
            "sentence": "Die Aufgabe war anspruchsvoll.",
            "option_a": "schwierig",
            "option_b": "kompliziert",
            "option_c": "mühsam",
            "option_d": "anspruchsvoll",
            "correct_answer": "anspruchsvoll",
            "explanation": "High demand meaning",
            "level": "B2"
        })

    db.close()


# -----------------------------
# Helpers
# -----------------------------
def get_stats(session):
    answered = session.get("questions_answered", 0)
    correct = session.get("correct_answers", 0)
    accuracy = round((correct / answered) * 100) if answered else 0
    return answered, accuracy


def fetch_question(levels):
    db = SessionLocal()
    try:
        if levels:
            level_list = levels.split(",")
            question = get_random_question(db, level_list)
        else:
            question = get_random_question(db)
    finally:
        db.close()
    return question


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return RedirectResponse(url="/play-v2")


@app.get("/play-v2", response_class=HTMLResponse)
def play_v2(request: Request, levels: str = None):
    question = fetch_question(levels)

    if not question:
        return HTMLResponse("No questions available")

    answered, accuracy = get_stats(request.session)

    return templates.TemplateResponse(
        "game_v2.html",
        {
            "request": request,
            "question": question,
            "options": [
                ("A", question.option_a),
                ("B", question.option_b),
                ("C", question.option_c),
                ("D", question.option_d),
            ],
            "result": None,
            "accuracy": accuracy,
            "answered": answered,
            "levels": levels
        }
    )


@app.post("/play-v2", response_class=HTMLResponse)
def submit_v2(
    request: Request,
    question_id: int = Form(...),
    selected_option: str = Form(...)
):
    db = SessionLocal()
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
    finally:
        db.close()

    if not question:
        return HTMLResponse("Question not found")

    correct = selected_option == question.correct_answer

    session = request.session
    session.setdefault("score", 0)
    session.setdefault("questions_answered", 0)
    session.setdefault("correct_answers", 0)

    session["questions_answered"] += 1

    if correct:
        session["score"] += 1
        session["correct_answers"] += 1

    answered, accuracy = get_stats(session)

    result = {
        "correct": correct,
        "correct_answer": question.correct_answer,
        "selected_answer": selected_option,
        "explanation": question.explanation,
        "score": session["score"]
    }

    return templates.TemplateResponse(
        "game_v2.html",
        {
            "request": request,
            "question": question,
            "options": [
                ("A", question.option_a),
                ("B", question.option_b),
                ("C", question.option_c),
                ("D", question.option_d),
            ],
            "result": result,
            "accuracy": accuracy,
            "answered": answered
        }
    )


@app.get("/reset")
def reset(request: Request):
    request.session.clear()
    return RedirectResponse(url="/play-v2")