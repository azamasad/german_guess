import random
from sqlalchemy.orm import Session
from app.models import Question


# -----------------------------
# Create Question
# -----------------------------
def create_question(db: Session, question_data: dict):
    question = Question(**question_data)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


# -----------------------------
# Get All Questions
# -----------------------------
def get_all_questions(db: Session):
    return db.query(Question).all()


# -----------------------------
# Get Random Question
# -----------------------------
def get_random_question(db: Session, levels: list = None):

    query = db.query(Question)

    # Filter by CEFR level if provided
    if levels:
        query = query.filter(Question.level.in_(levels))

    questions = query.all()

    if not questions:
        return None

    return random.choice(questions)