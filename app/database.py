import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read env variable (Render will provide this in staging)
DATABASE_URL = os.getenv("postgresql+psycopg2://germanguess_staging_db_user:P6KokiJM9dWaU2sOYWmc2dKowN7xX0QN@dpg-d7l2a3nlk1mc73bhjnm0-a/germanguess_staging_db")

# Fallback to SQLite for local development
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./german_guess.db"

# SQLite needs special flag
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

# Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base
Base = declarative_base()