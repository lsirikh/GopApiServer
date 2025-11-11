"""
Dependency functions for FastAPI
"""
from typing import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides a database session.
    Yields a SQLAlchemy Session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
