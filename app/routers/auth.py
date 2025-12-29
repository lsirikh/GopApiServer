"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import Token, UserResponse
from app.utils.auth import verify_password, create_access_token, decode_token

router = APIRouter(tags=[])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    JWT 토큰에서 현재 인증된 사용자를 가져오는 의존성

    Args:
        token: Authorization 헤더의 JWT 토큰
        db: 데이터베이스 세션

    Returns:
        인증된 사용자의 User 객체

    Raises:
        HTTPException 401: 토큰이 유효하지 않거나 사용자가 존재하지 않음
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token and get username
        token_data = decode_token(token)
        username = token_data.username

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme_optional)
) -> User | None:
    """
    AUTH_MODE 설정에 따른 선택적 인증 의존성

    Args:
        token: Authorization 헤더의 JWT 토큰 (AUTH_MODE=public인 경우 선택)
        db: 데이터베이스 세션

    Returns:
        인증된 경우 User 객체, AUTH_MODE=public이고 토큰이 없는 경우 None

    Raises:
        HTTPException 401: AUTH_MODE=token이고 토큰이 유효하지 않거나 누락됨
    """
    # Import settings inside function to allow test mocking
    from app.config import settings

    # In token mode, authentication is required
    if settings.AUTH_MODE == "token":
        # Token is required in token mode
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Validate token
        return await get_current_user(token=token, db=db)

    # In public mode, authentication is optional
    if token:
        # If token is provided, try to authenticate
        try:
            token_data = decode_token(token)
            username = token_data.username
            if username:
                user = db.query(User).filter(User.username == username).first()
                if user:
                    return user
        except JWTError:
            pass

    # No token or invalid token in public mode - return None
    return None


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    로그인

    사용자 인증 후 JWT 토큰을 반환합니다.

    **Request Body** (OAuth2 폼 형식):
    - **username**: 사용자 이름 (필수)
    - **password**: 비밀번호 (필수)

    **Response**: access_token과 token_type이 포함된 Token 객체

    **Error**:
    - 401: 잘못된 사용자 이름 또는 비밀번호
    """
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    현재 사용자 정보 조회

    현재 인증된 사용자의 정보를 조회합니다.

    **Response**: 사용자 이름과 역할이 포함된 UserResponse (비밀번호 제외)

    **Error**:
    - 401: 유효하지 않은 토큰
    """
    return current_user
