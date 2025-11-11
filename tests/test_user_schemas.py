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
        role="admin"
    )
    assert user_response.username == "admin"
    assert user_response.role == "admin"
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
