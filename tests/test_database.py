"""
Test: 데이터베이스 연결 검증
"""
import os
from pathlib import Path


def test_database_module_exists():
    """Test that database.py module exists"""
    base_dir = Path(__file__).parent.parent
    database_file = base_dir / "app" / "database.py"

    assert database_file.exists(), "app/database.py should exist"
    assert database_file.is_file(), "app/database.py should be a file"


def test_database_creates_engine():
    """Test that database.py creates SQLAlchemy engine"""
    from app.database import engine
    from sqlalchemy.engine import Engine

    assert engine is not None, "engine should not be None"
    assert isinstance(engine, Engine), "engine should be SQLAlchemy Engine instance"


def test_database_creates_sessionlocal():
    """Test that database.py creates SessionLocal"""
    from app.database import SessionLocal
    from sqlalchemy.orm import sessionmaker

    assert SessionLocal is not None, "SessionLocal should not be None"
    assert isinstance(SessionLocal, sessionmaker), "SessionLocal should be sessionmaker instance"
