import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .settings import settings

# Create a SQLite engine using the memory DB path (can be reused for analysis persistence)
engine = create_engine(f"sqlite:///{settings.MEMORY_DB_PATH}", echo=False, future=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Base class for declarative models
class Base(DeclarativeBase):
    pass

# Dependency helper (optional for FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
