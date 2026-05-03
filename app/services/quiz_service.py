from __future__ import annotations

from dataclasses import dataclass

from app import crud

SESSION_KEY = "quiz_state"
MAX_RECENT_IDS = 100


@dataclass
class QuizPayload:
    question_id: int
    sentence: str
    options: list[dict[str, str]]
    levels: str


@dataclass
class QuizStats:
    answered: int
    correct: int
    accuracy: int
    total: int
    progress_text: str


@dataclass
class QuizState:
    answered: int = 0
    correct: int = 0
    recent_question_ids: list[int] | None = None
    current_question_id: int | None = None

    def __post_init__(self) -> None:
        if self.recent_question_ids is None:
            self.recent_question_ids = []


def _serialize_state(state: QuizState) -> dict:
    return {
        "answered": state.answered,
        "correct": state.correct,
        "recent_question_ids": state.recent_question_ids[-MAX_RECENT_IDS:],
        "current_question_id": state.current_question_id,
    }


def _load_state(session: dict) -> QuizState:
    raw = session.get(SESSION_KEY) or {}
    return QuizState(
        answered=int(raw.get("answered", 0)),
        correct=int(raw.get("correct", 0)),
        recent_question_ids=[int(v) for v in raw.get("recent_question_ids", [])][-MAX_RECENT_IDS:],
        current_question_id=raw.get("current_question_id"),
    )


def _save_state(session: dict, state: QuizState) -> None:
    session[SESSION_KEY] = _serialize_state(state)


def _stats_from_state(state: QuizState, total: int) -> QuizStats:
    safe_total = max(0, int(total))
    accuracy = int((state.correct / state.answered) * 100) if state.answered else 0
    return QuizStats(
        answered=state.answered,
        correct=state.correct,
        accuracy=accuracy,
        total=safe_total,
        progress_text=f"{state.answered}/{safe_total}",
    )


def _to_payload(question, levels: list[str]) -> QuizPayload:
    return QuizPayload(
        question_id=question.id,
        sentence=question.sentence,
        options=[
            {"key": "A", "value": question.option_a},
            {"key": "B", "value": question.option_b},
            {"key": "C", "value": question.option_c},
            {"key": "D", "value": question.option_d},
        ],
        levels=",".join(levels),
    )


def get_or_create_question(db, session: dict, level_str: str | None):
    levels = crud.normalize_levels(level_str)
    state = _load_state(session)
    available = crud.count_questions(db, levels)

    if state.current_question_id:
        current = crud.get_question_by_id(db, state.current_question_id)
        if current is not None and (not levels or current.level in levels):
            return _to_payload(current, levels), _stats_from_state(state, available), None

    if available == 0:
        return None, _stats_from_state(state, available), "No questions found for selected CEFR levels."

    recent_ids = state.recent_question_ids
    if len(recent_ids) >= available:
        recent_ids = []

    question = crud.get_random_question_excluding(db, levels, recent_ids)
    if question is None:
        recent_ids = []
        question = crud.get_random_question_excluding(db, levels, recent_ids)

    if question is None:
        return None, _stats_from_state(state, available), "No question available right now."

    state.current_question_id = question.id
    _save_state(session, state)
    return _to_payload(question, levels), _stats_from_state(state, available), None


def submit_answer(db, session: dict, question_id: int, selected_option: str, level_str: str | None):
    levels = crud.normalize_levels(level_str)
    state = _load_state(session)
    total_available = crud.count_questions(db, levels)

    question = crud.get_question_by_id(db, question_id)
    if question is None:
        return None, _stats_from_state(state, total_available), "Question not found."

    is_correct = selected_option == question.correct_answer
    state.answered += 1
    if is_correct:
        state.correct += 1

    state.current_question_id = None
    # No-repeat safety hook: keep recent IDs in session and exclude them when selecting the next question.
    if question.id not in state.recent_question_ids:
        state.recent_question_ids.append(question.id)
    state.recent_question_ids = state.recent_question_ids[-MAX_RECENT_IDS:]

    _save_state(session, state)

    feedback = {
        "correct": is_correct,
        "correct_answer": question.correct_answer,
        "selected_answer": selected_option,
        "explanation": question.explanation,
    }

    answered_question = _to_payload(question, levels)
    next_question, stats, error = get_or_create_question(db, session, ",".join(levels))
    return {
        "feedback": feedback,
        "answered_question": answered_question,
        "next_question": next_question,
        "stats": stats,
        "error": error,
    }, stats, None


def reset_progress(session: dict) -> None:
    if SESSION_KEY in session:
        del session[SESSION_KEY]
