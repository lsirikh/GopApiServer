"""
Test: User 스키마 검증
"""
from pydantic import BaseModel


def test_user_create_schema_exists():
    """Test that UserCreate schema accepts username and password"""
    from app.schemas.user import UserCreate

    assert issubclass(UserCreate, BaseModel)

    user_data = UserCreate(username="admin", password="secret123")
    assert user_data.username == "admin"
    assert user_data.password == "secret123"


def test_user_response_schema_excludes_password():
    """Test that UserResponse does not include password"""
    from app.schemas.user import UserResponse

    assert issubclass(UserResponse, BaseModel)

    # UserResponse should have username, role, id but not password
    user_response = UserResponse(
        id=1,
        username="admin",
        role="ADMIN"
    )
    assert user_response.username == "admin"
    assert user_response.role == "ADMIN"
    assert user_response.id == 1
    assert not hasattr(user_response, 'password')
    assert not hasattr(user_response, 'hashed_password')


def test_token_schema_exists():
    """Test that Token schema has access_token and token_type"""
    from app.schemas.user import Token

    assert issubclass(Token, BaseModel)

    token = Token(access_token="some_token", token_type="bearer")
    assert token.access_token == "some_token"
    assert token.token_type == "bearer"


def test_token_data_schema_exists():
    """Test that TokenData schema exists"""
    from app.schemas.user import TokenData

    assert issubclass(TokenData, BaseModel)

    token_data = TokenData(username="admin")
    assert token_data.username == "admin"


# ============================================================
# UserSessionResponse Schema Tests (PRD_UserSession_Improvement.md)
# ============================================================

class TestUserSessionResponseSchema:
    """US-1.6: UserSessionResponse 스키마 필드 검증"""

    def test_user_session_response_has_created_at(self):
        """US-1.6: UserSessionResponse 스키마에 created_at 필드 존재"""
        from app.schemas.user import UserSessionResponse
        from datetime import datetime

        # created_at 필드가 있어야 함
        fields = UserSessionResponse.model_fields
        assert 'created_at' in fields, \
            "UserSessionResponse should have created_at field"

    def test_user_session_response_has_updated_at(self):
        """US-1.6: UserSessionResponse 스키마에 updated_at 필드 존재"""
        from app.schemas.user import UserSessionResponse

        # updated_at 필드가 있어야 함
        fields = UserSessionResponse.model_fields
        assert 'updated_at' in fields, \
            "UserSessionResponse should have updated_at field"

    def test_user_session_response_no_device_type(self):
        """US-1.6: UserSessionResponse 스키마에 device_type 필드 없음"""
        from app.schemas.user import UserSessionResponse

        # device_type 필드가 없어야 함
        fields = UserSessionResponse.model_fields
        assert 'device_type' not in fields, \
            "UserSessionResponse should not have device_type field"

    def test_user_session_response_no_location(self):
        """US-1.6: UserSessionResponse 스키마에 location 필드 없음"""
        from app.schemas.user import UserSessionResponse

        # location 필드가 없어야 함
        fields = UserSessionResponse.model_fields
        assert 'location' not in fields, \
            "UserSessionResponse should not have location field"

    def test_user_session_response_no_login_at(self):
        """US-1.6: UserSessionResponse 스키마에 login_at 필드 없음"""
        from app.schemas.user import UserSessionResponse

        # login_at 필드가 없어야 함 (created_at으로 대체됨)
        fields = UserSessionResponse.model_fields
        assert 'login_at' not in fields, \
            "UserSessionResponse should not have login_at field (renamed to created_at)"

    def test_user_session_response_no_last_activity(self):
        """US-1.6: UserSessionResponse 스키마에 last_activity 필드 없음"""
        from app.schemas.user import UserSessionResponse

        # last_activity 필드가 없어야 함 (updated_at으로 대체됨)
        fields = UserSessionResponse.model_fields
        assert 'last_activity' not in fields, \
            "UserSessionResponse should not have last_activity field (renamed to updated_at)"


# ============================================================
# US-3: UserSessionResponse JOIN Fields (PRD_UserSession_Improvement.md)
# ============================================================

class TestUserSessionResponseJoinFields:
    """US-3.1: UserSessionResponse JOIN 필드 검증"""

    def test_user_session_response_has_login_id(self):
        """US-3.1: UserSessionResponse 스키마에 login_id 필드 존재 (Optional)"""
        from app.schemas.user import UserSessionResponse

        fields = UserSessionResponse.model_fields
        assert 'login_id' in fields, \
            "UserSessionResponse should have login_id field for JOIN"

    def test_user_session_response_has_role(self):
        """US-3.1: UserSessionResponse 스키마에 role 필드 존재 (Optional)"""
        from app.schemas.user import UserSessionResponse

        fields = UserSessionResponse.model_fields
        assert 'role' in fields, \
            "UserSessionResponse should have role field for JOIN"

    def test_user_session_response_keeps_user_id(self):
        """US-3.1: UserSessionResponse 스키마에 user_id 필드 유지 (하위 호환)"""
        from app.schemas.user import UserSessionResponse

        fields = UserSessionResponse.model_fields
        assert 'user_id' in fields, \
            "UserSessionResponse should keep user_id for backward compatibility"
