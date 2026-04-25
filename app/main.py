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

# Static
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Sessions
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-change-later"
)

# -----------------------------
# Startup
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
def get_random_question():
    db = SessionLocal()
    try:
        questions = db.query(Question).all()
        return random.choice(questions) if questions else None
    finally:
        db.close()

def get_options(question):
    return [
        ("A", str(question.option_a)),
        ("B", str(question.option_b)),
        ("C", str(question.option_c)),
        ("D", str(question.option_d)),
    ]

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return RedirectResponse(url="/play-v2")


@app.get("/play-v2", response_class=HTMLResponse)
def play_v2(request: Request):
    question = get_random_question()

    if not question:
        return HTMLResponse("No questions available")

    return templates.TemplateResponse(
        "game_v2.html",
        {
            "request": request,
            "question": question,
            "options": get_options(question),
            "result": None,
            "score": request.session.get("score", 0)
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

    correct = str(selected_option) == str(question.correct_answer)

    # session scoring
    session = request.session
    session.setdefault("score", 0)

    if correct:
        session["score"] += 1

    result_text = "Correct ✅" if correct else f"Wrong ❌ (Correct: {question.correct_answer})"

    # next question
    next_question = get_random_question()

    return templates.TemplateResponse(
        "game_v2.html",
        {
            "request": request,
            "question": next_question,
            "options": get_options(next_question),
            "result": result_text,
            "score": session["score"]
        }
    )


@app.get("/reset")
def reset(request: Request):
    request.session.clear()
    return RedirectResponse(url="/play-v2")