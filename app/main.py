from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import random

from app.database import engine, SessionLocal, Base
from app.models import Question
from app.crud import create_question

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

# -----------------------------
# Startup
# -----------------------------
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    if db.query(Question).count() == 0:
        create_question(db, {
            "sentence": "She ___ to the market every Saturday morning.",
            "option_a": "go",
            "option_b": "goes",
            "option_c": "going",
            "option_d": "gone",
            "correct_answer": "goes",
            "explanation": "With third-person singular subjects we add -s.",
            "level": "A1"
        })
    db.close()

# -----------------------------
# Helpers
# -----------------------------
def get_random_question(levels=None):
    db = SessionLocal()
    try:
        query = db.query(Question)

        if levels:
            level_list = levels.split(",")
            query = query.filter(Question.level.in_(level_list))

        questions = query.all()
        return random.choice(questions) if questions else None
    finally:
        db.close()


def get_stats(session):
    answered = session.get("answered", 0)
    correct = session.get("correct", 0)
    accuracy = int((correct / answered) * 100) if answered else 0
    return answered, correct, accuracy


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return RedirectResponse("/play-v2")


@app.get("/play-v2", response_class=HTMLResponse)
def play(request: Request, levels: str = None):

    q = get_random_question(levels)

    if not q:
        return HTMLResponse("No questions available for selected level")

    answered, score, accuracy = get_stats(request.session)

    return templates.TemplateResponse("game_v2.html", {
        "request": request,
        "question": q,
        "options": [
            ("A", q.option_a),
            ("B", q.option_b),
            ("C", q.option_c),
            ("D", q.option_d),
        ],
        "result": None,
        "answered": answered,
        "score": score,
        "accuracy": accuracy,
        "levels": levels or ""
    })


@app.post("/play-v2", response_class=HTMLResponse)
def submit(
    request: Request,
    question_id: int = Form(...),
    selected_option: str = Form(...),
    levels: str = Form(None)
):
    db = SessionLocal()
    try:
        q = db.query(Question).filter(Question.id == question_id).first()
    finally:
        db.close()

    correct = selected_option == q.correct_answer

    session = request.session
    session["answered"] = session.get("answered", 0) + 1

    if correct:
        session["correct"] = session.get("correct", 0) + 1

    answered, score, accuracy = get_stats(session)

    next_q = get_random_question(levels)

    return templates.TemplateResponse("game_v2.html", {
        "request": request,
        "question": next_q,
        "options": [
            ("A", next_q.option_a),
            ("B", next_q.option_b),
            ("C", next_q.option_c),
            ("D", next_q.option_d),
        ],
        "result": {
            "correct": correct,
            "explanation": q.explanation
        },
        "answered": answered,
        "score": score,
        "accuracy": accuracy,
        "levels": levels or ""
    })


@app.get("/reset")
def reset(request: Request):
    request.session.clear()
    return RedirectResponse("/play-v2")