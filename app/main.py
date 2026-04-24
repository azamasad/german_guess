from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

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
# Routes (SAFE TEST VERSION)
# -----------------------------
@app.get("/")
def home():
    return RedirectResponse(url="/play-v2")


@app.get("/play-v2", response_class=HTMLResponse)
def play_v2(request: Request):
    return templates.TemplateResponse(
        "game_v2.html",
        {
            "request": request,
            "question": {
                "sentence": "Test sentence"
            },
            "options": [
                ("A", "eins"),
                ("B", "zwei"),
                ("C", "drei"),
                ("D", "vier"),
            ]
        }
    )


@app.get("/reset")
def reset(request: Request):
    request.session.clear()
    return RedirectResponse(url="/play-v2")