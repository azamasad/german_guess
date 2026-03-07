from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    sentence = Column(Text, nullable=False)

    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)

    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)

    level = Column(String, nullable=False)