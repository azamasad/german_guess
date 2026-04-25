import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("postgresql+psycopg2://germanguess_staging_db_user:P6KokiJM9dWaU2sOYWmc2dKowN7xX0QN@dpg-d7l2a3nlk1mc73bhjnm0-a/germanguess_staging_db")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()   