"""
Test: 의존성 함수 검증
"""
from pathlib import Path


def test_dependencies_module_exists():
    """Test that dependencies.py module exists"""
    base_dir = Path(__file__).parent.parent
    dependencies_file = base_dir / "app" / "dependencies.py"

    assert dependencies_file.exists(), "app/dependencies.py should exist"
    assert dependencies_file.is_file(), "app/dependencies.py should be a file"


def test_get_db_dependency_exists():
    """Test that get_db dependency function exists"""
    from app.dependencies import get_db

    assert get_db is not None, "get_db should exist"
    assert callable(get_db), "get_db should be callable"


def test_get_db_returns_session():
    """Test that get_db returns a database session"""
    from app.dependencies import get_db
    from sqlalchemy.orm import Session

    # get_db is a generator, so we need to call next()
    db_gen = get_db()
    db = next(db_gen)

    assert db is not None, "db session should not be None"
    assert isinstance(db, Session), "db should be SQLAlchemy Session instance"

    # Clean up - close the generator
    try:
        next(db_gen)
    except StopIteration:
        pass  # Expected behavior
