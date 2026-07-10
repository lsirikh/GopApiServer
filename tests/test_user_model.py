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


# ============================================================
# UserSession Model Tests (PRD_UserSession_Improvement.md)
# ============================================================

class TestUserSessionModel:
    """US-1: UserSession 모델 필드 검증"""

    def test_user_session_no_device_type_field(self):
        """US-1.1: UserSession 모델에 device_type 필드 없음 확인"""
        from app.models.user import UserSession

        # device_type 필드가 없어야 함
        assert not hasattr(UserSession, 'device_type'), \
            "UserSession should not have device_type field (removed per PRD)"

    def test_user_session_no_location_field(self):
        """US-1.1: UserSession 모델에 location 필드 없음 확인"""
        from app.models.user import UserSession

        # location 필드가 없어야 함
        assert not hasattr(UserSession, 'location'), \
            "UserSession should not have location field (removed per PRD)"

    def test_user_session_has_created_at_field(self):
        """US-1.3: UserSession 모델에 created_at 필드 존재 확인"""
        from app.models.user import UserSession

        # created_at 필드가 있어야 함 (login_at 대체)
        assert hasattr(UserSession, 'created_at'), \
            "UserSession should have created_at field (replaces login_at)"

    def test_user_session_no_login_at_field(self):
        """US-1.3: UserSession 모델에 login_at 필드 없음 확인"""
        from app.models.user import UserSession

        # login_at 필드가 없어야 함 (created_at으로 변경됨)
        assert not hasattr(UserSession, 'login_at'), \
            "UserSession should not have login_at field (renamed to created_at)"

    def test_user_session_has_updated_at_field(self):
        """US-1.4: UserSession 모델에 updated_at 필드 존재 확인"""
        from app.models.user import UserSession

        # updated_at 필드가 있어야 함 (last_activity 대체)
        assert hasattr(UserSession, 'updated_at'), \
            "UserSession should have updated_at field (replaces last_activity)"

    def test_user_session_no_last_activity_field(self):
        """US-1.4: UserSession 모델에 last_activity 필드 없음 확인"""
        from app.models.user import UserSession

        # last_activity 필드가 없어야 함 (updated_at으로 변경됨)
        assert not hasattr(UserSession, 'last_activity'), \
            "UserSession should not have last_activity field (renamed to updated_at)"
