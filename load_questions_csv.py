from __future__ import annotations

import csv
from pathlib import Path

from app.crud import create_question, question_exists
from app.database import SessionLocal

CSV_PATH = Path("questions.csv")


def load_questions(csv_path: Path = CSV_PATH) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sentence = row["sentence"].strip()
                if question_exists(db, sentence):
                    skipped += 1
                    continue

                create_question(
                    db,
                    {
                        "sentence": sentence,
                        "option_a": row["option_a"].strip(),
                        "option_b": row["option_b"].strip(),
                        "option_c": row["option_c"].strip(),
                        "option_d": row["option_d"].strip(),
                        "correct_answer": row["correct_answer"].strip(),
                        "explanation": row["explanation"].strip(),
                        "level": row["level"].strip().upper(),
                    },
                )
                inserted += 1
    finally:
        db.close()

    print(f"Inserted: {inserted}")
    print(f"Skipped duplicates: {skipped}")


if __name__ == "__main__":
    load_questions()
