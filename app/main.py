from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from app.logger import setup_logger
from app.database import engine, SessionLocal
from app import models
from app.models import Question
from app.crud import create_question, get_random_question

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

# static files (logo etc.)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

logger = setup_logger()

app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-change-later"
)

# -----------------------------
# Startup
# -----------------------------
@app.on_event("startup")
def startup_event():

    logger.info("Application started")

    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    if db.query(Question).count() == 0:

        sample_question = {
            "sentence": "Die Aufgabe war anspruchsvoll.",
            "option_a": "schwierig",
            "option_b": "kompliziert",
            "option_c": "mühsam",
            "option_d": "anspruchsvoll",
            "correct_answer": "anspruchsvoll",
            "explanation": "‚anspruchsvoll‘ implies high demands, not just difficulty.",
            "level": "B2"
        }

        create_question(db, sample_question)

        logger.info("Inserted sample question")

    db.close()


# -----------------------------
# Homepage → redirect to UI
# -----------------------------
@app.get("/")
def home():
    return RedirectResponse(url="/play")


# -----------------------------
# API Random Question
# -----------------------------
@app.get("/game")
def get_game_question(levels: str = None):

    db = SessionLocal()

    if levels:
        level_list = levels.split(",")
        question = get_random_question(db, level_list)
    else:
        question = get_random_question(db)

    db.close()

    if not question:
        return {"error": "No questions available"}

    return {
        "id": question.id,
        "sentence": question.sentence,
        "options": {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d,
        }
    }


# -----------------------------
# UI Play Game
# -----------------------------
@app.get("/play", response_class=HTMLResponse)
def play_game(request: Request, levels: str = None):

    db = SessionLocal()

    if levels:
        level_list = levels.split(",")
        question = get_random_question(db, level_list)
    else:
        question = get_random_question(db)

    db.close()

    if not question:
        return HTMLResponse("No questions available")

    answered = request.session.get("questions_answered", 0)

    accuracy = 0
    if answered > 0:
        accuracy = round(
            request.session.get("correct_answers", 0) /
            answered * 100
        )

    return templates.TemplateResponse(
        "game.html",
        {
            "request": request,
            "question": question,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d,
            },
            "result": None,
            "accuracy": accuracy,
            "answered": answered,
            "levels": levels
        }
    )


# -----------------------------
# Submit Answer
# -----------------------------
@app.post("/play", response_class=HTMLResponse)
def submit_answer(
    request: Request,
    question_id: int = Form(...),
    selected_option: str = Form(...)
):

    db = SessionLocal()

    question = db.query(Question).filter(Question.id == question_id).first()

    db.close()

    correct = selected_option == question.correct_answer

    if "score" not in request.session:
        request.session["score"] = 0
    if "questions_answered" not in request.session:
        request.session["questions_answered"] = 0
    if "correct_answers" not in request.session:
        request.session["correct_answers"] = 0

    request.session["questions_answered"] += 1

    if correct:
        request.session["score"] += 1
        request.session["correct_answers"] += 1

    answered = request.session["questions_answered"]

    accuracy = 0
    if answered > 0:
        accuracy = round(
            request.session["correct_answers"] /
            answered * 100
        )

    result = {
        "correct": correct,
        "correct_answer": question.correct_answer,
        "selected_answer": selected_option,
        "explanation": question.explanation,
        "score": request.session["score"]
    }

    return templates.TemplateResponse(
        "game.html",
        {
            "request": request,
            "question": question,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d,
            },
            "result": result,
            "accuracy": accuracy,
            "answered": answered
        }
    )


# -----------------------------
# Reset Progress
# -----------------------------
@app.get("/reset")
def reset_score(request: Request):

    request.session["score"] = 0
    request.session["questions_answered"] = 0
    request.session["correct_answers"] = 0

    return RedirectResponse(url="/play", status_code=302)