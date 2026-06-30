"""
Authentication utility functions
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.schemas.user import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Dictionary with token payload data (should include 'sub' for subject/username)
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT refresh token with longer expiration

    Args:
        data: Dictionary with token payload data (should include 'sub' for subject/username)
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # PRD v4.9 Phase 2-A3: settings.JWT_REFRESH_EXPIRATION_DAYS (이전 하드코딩 7일)
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)

    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def decode_token(token: str, expected_type: Optional[str] = None) -> TokenData:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string
        expected_type: PRD v4.9 Phase 2-A4 — 'refresh' 또는 None (access). 'refresh'면 payload.type='refresh' 강제

    Returns:
        TokenData with username + jti + token_type extracted from token

    Raises:
        JWTError: If token is invalid or expired or type mismatch
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        token_jti: str = payload.get("jti")
        token_type: str = payload.get("type")  # access: None / refresh: "refresh"
        token_sid: str = payload.get("sid")    # FR-SVF-02: 세션 식별자(== UserSession.id), 없을 수 있음(레거시 토큰)

        if username is None:
            raise JWTError("Username not found in token")

        # PRD v4.9 Phase 2-A4: refresh 전용 가드 — access_token으로 refresh 호출 차단
        if expected_type == "refresh" and token_type != "refresh":
            raise JWTError("Token type mismatch — refresh token required")

        return TokenData(username=username, jti=token_jti, token_type=token_type, sid=token_sid)

    except JWTError:
        raise
