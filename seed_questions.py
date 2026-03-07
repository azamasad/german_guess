import csv
from app.database import SessionLocal
from app.models import Question

CSV_FILE = "questions.csv"

def seed_questions():
    db = SessionLocal()

    inserted = 0
    skipped = 0

    with open(CSV_FILE, newline='', encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            existing = db.query(Question).filter(
                Question.sentence == row["sentence"]
            ).first()

            if existing:
                skipped += 1
                continue

            question = Question(
                sentence=row["sentence"],
                option_a=row["option_a"],
                option_b=row["option_b"],
                option_c=row["option_c"],
                option_d=row["option_d"],
                correct_answer=row["correct_answer"],
                explanation=row["explanation"],
                level=row["level"]
            )

            db.add(question)
            inserted += 1

    db.commit()
    db.close()

    print(f"Inserted: {inserted}")
    print(f"Skipped (duplicates): {skipped}")

if __name__ == "__main__":
    seed_questions()