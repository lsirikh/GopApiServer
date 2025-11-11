"""
Pytest fixtures and configuration
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


@pytest.fixture(scope="function")
def test_db():
    """
    Create a test database for each test function
    """
    # Create in-memory SQLite database for testing
    TEST_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)
