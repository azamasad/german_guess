import csv
from app.database import SessionLocal
from app.models import Question

db = SessionLocal()

with open("questions.csv", newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        q = Question(
            sentence=row["sentence"],
            option_a=row["option_a"],
            option_b=row["option_b"],
            option_c=row["option_c"],
            option_d=row["option_d"],
            correct_answer=row["correct_answer"],
            explanation=row["explanation"],
            level=row["level"]
        )
        db.add(q)

db.commit()
db.close()

print("✅ Data loaded")