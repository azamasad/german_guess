import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Correct: read DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback to SQLite (local only)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./german_guess.db"

# SQLite special config
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()