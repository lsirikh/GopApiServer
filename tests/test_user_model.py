"""
Test: User 모델 검증
"""


def test_user_model_exists():
    """Test that User model exists"""
    from app.models.user import User

    assert User is not None
    assert hasattr(User, '__tablename__')
    assert User.__tablename__ == "users"


def test_user_has_required_fields():
    """Test that User has username, hashed_password, role fields"""
    from app.models.user import User

    user = User(
        username="admin",
        hashed_password="hashed_password_here",
        role="admin"
    )

    assert user.username == "admin"
    assert user.hashed_password == "hashed_password_here"
    assert user.role == "admin"


def test_user_has_timestamps():
    """Test that User has created_at and updated_at"""
    from app.models.user import User
    from datetime import datetime

    user = User(
        username="test",
        hashed_password="hash",
        role="user"
    )

    assert hasattr(user, 'created_at')
    assert hasattr(user, 'updated_at')
