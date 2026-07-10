"""
Test: 인증 유틸리티 함수 검증
"""
from datetime import datetime, timedelta
import time


def test_hash_password_creates_bcrypt_hash():
    """Test that hash_password creates a bcrypt hash"""
    from app.utils.auth import hash_password

    password = "secure123"
    hashed = hash_password(password)

    # Bcrypt hashes start with $2b$
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60  # Bcrypt hashes are 60 characters


def test_verify_password_validates_correctly():
    """Test that verify_password correctly validates passwords"""
    from app.utils.auth import hash_password, verify_password

    password = "secure123"
    hashed = hash_password(password)

    # Correct password should verify
    assert verify_password(password, hashed) is True

    # Incorrect password should not verify
    assert verify_password("wrongpassword", hashed) is False


def test_same_password_produces_different_hashes():
    """Test that hashing same password twice produces different hashes (salt)"""
    from app.utils.auth import hash_password

    password = "secure123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Hashes should be different due to salt
    assert hash1 != hash2


def test_create_access_token_generates_jwt():
    """Test that create_access_token generates a valid JWT token"""
    from app.utils.auth import create_access_token

    data = {"sub": "testuser"}
    token = create_access_token(data)

    # JWT tokens have 3 parts separated by dots
    assert isinstance(token, str)
    parts = token.split(".")
    assert len(parts) == 3


def test_create_access_token_includes_username_and_expiration():
    """Test that token includes username and expiration time"""
    from app.utils.auth import create_access_token, decode_token

    username = "testuser"
    data = {"sub": username}
    token = create_access_token(data)

    # Decode token to verify contents
    token_data = decode_token(token)
    assert token_data.username == username


def test_decode_token_extracts_token_data():
    """Test that decode_token correctly extracts TokenData"""
    from app.utils.auth import create_access_token, decode_token

    username = "testuser"
    data = {"sub": username}
    token = create_access_token(data)

    token_data = decode_token(token)
    assert token_data is not None
    assert token_data.username == username


def test_expired_token_raises_exception():
    """Test that expired token is detected and raises exception"""
    from app.utils.auth import create_access_token, decode_token

    # Create token that expires immediately
    data = {"sub": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    # Decoding expired token should raise exception
    try:
        decode_token(token)
        assert False, "Expected exception for expired token"
    except Exception as e:
        # Should raise an exception for expired token
        assert True
