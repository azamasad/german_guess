from __future__ import annotations

from typing import Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Question


VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}


def normalize_levels(levels: str | None) -> list[str]:
    if not levels:
        return []
    cleaned = []
    for level in levels.split(","):
        token = level.strip().upper()
        if token in VALID_LEVELS and token not in cleaned:
            cleaned.append(token)
    return cleaned


def get_question_by_id(db: Session, question_id: int) -> Question | None:
    return db.query(Question).filter(Question.id == question_id).first()


def count_questions(db: Session, levels: Iterable[str]) -> int:
    query = db.query(func.count(Question.id))
    levels = list(levels)
    if levels:
        query = query.filter(Question.level.in_(levels))
    return int(query.scalar() or 0)


def get_random_question_excluding(
    db: Session,
    levels: Iterable[str],
    excluded_ids: Iterable[int],
) -> Question | None:
    levels = list(levels)
    excluded_ids = [int(v) for v in excluded_ids]

    query = db.query(Question)
    if levels:
        query = query.filter(Question.level.in_(levels))
    if excluded_ids:
        query = query.filter(~Question.id.in_(excluded_ids))

    return query.order_by(func.random()).limit(1).first()


def question_exists(db: Session, sentence: str) -> bool:
    return (
        db.query(Question.id)
        .filter(Question.sentence == sentence)
        .limit(1)
        .first()
        is not None
    )


def create_question(db: Session, question_data: dict) -> Question:
    question = Question(**question_data)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question
