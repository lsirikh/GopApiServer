"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from typing import Optional
from datetime import datetime, timedelta

from app.dependencies import get_db
# NOTE: User는 레거시 모델 (users 테이블). 신규 코드는 AccountUser (account_users 테이블) 사용할 것.
from app.models.user import User, AccountUser, UserSession, UserLoginLog
from app.schemas.user import Token, UserResponse, AccountLoginRequest, RefreshTokenRequest, AccountUserResponse
from app.utils.auth import verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter(tags=[])

# HTTPBearer for Swagger UI (new)
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="JWT Bearer token authentication. Login via POST /api/auth/login to get token.",
    auto_error=False
)

# Legacy OAuth2 scheme (for backward compatibility)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/oauth2", auto_error=False)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login/oauth2", auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    [LEGACY] JWT 토큰에서 현재 인증된 사용자를 가져오는 의존성 (Legacy User 모델)
    → 신규 코드는 get_current_account_user() 사용할 것.

    Args:
        credentials: HTTPBearer 인증 정보
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

    if not credentials:
        raise credentials_exception

    token = credentials.credentials

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


async def get_current_account_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> AccountUser:
    """
    JWT 토큰에서 현재 인증된 AccountUser를 가져오는 의존성

    Swagger UI에서 "Authorize" 버튼으로 Bearer 토큰 입력 가능

    Args:
        credentials: HTTPBearer 인증 정보
        db: 데이터베이스 세션

    Returns:
        인증된 사용자의 AccountUser 객체

    Raises:
        HTTPException 401: 토큰이 유효하지 않거나 사용자가 존재하지 않음
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials

    try:
        token_data = decode_token(token)
        login_id = token_data.username

        if login_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(AccountUser).filter(AccountUser.login_id == login_id).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User | None:
    """
    [LEGACY] AUTH_MODE 설정에 따른 선택적 인증 의존성 (Legacy User 모델)
    → 내부적으로 get_current_user()를 호출하므로 Legacy User 조회를 수행함.

    Args:
        credentials: HTTPBearer 인증 정보 (AUTH_MODE=public인 경우 선택)
        db: 데이터베이스 세션

    Returns:
        인증된 경우 User 객체, AUTH_MODE=public이고 토큰이 없는 경우 None

    Raises:
        HTTPException 401: AUTH_MODE=token이고 토큰이 유효하지 않거나 누락됨
    """
    # Import settings inside function to allow test mocking
    from app.config import settings

    token = credentials.credentials if credentials else None

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
        return await get_current_user(credentials=credentials, db=db)

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


@router.post("/login")
async def login(
    login_data: AccountLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    로그인 (Account)

    AccountUser 모델을 사용하는 JSON 기반 로그인입니다.

    **Request Body** (JSON):
    - **login_id**: 로그인 ID (필수)
    - **password**: 비밀번호 (필수)

    **Response**: success, data (access_token, token_type 포함)

    **Error**:
    - 401: 잘못된 인증정보
    - 403: 비활성 또는 잠긴 계정
    """
    # Import settings for timezone
    from app.config import settings

    # Account-based login with JSON body
    user = db.query(AccountUser).filter(AccountUser.login_id == login_data.login_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login_id or password",
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked",
        )

    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        # Increment failed login count
        user.failed_login_count += 1

        # Lock account after 5 failed attempts
        if user.failed_login_count >= 5:
            user.is_locked = True
            user.lock_reason = "Too many failed login attempts"
            user.locked_at = datetime.now(settings.tz)

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login_id or password",
        )

    # Create JWT tokens
    access_token = create_access_token(data={"sub": user.login_id})
    refresh_token = create_refresh_token(data={"sub": user.login_id})

    # Extract client info from request (US-2: PRD_UserSession_Improvement.md)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Create UserSession record
    session = UserSession(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now(settings.tz) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        is_active=True,
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(session)

    # Create UserLoginLog record
    login_log = UserLoginLog(
        user_id=user.id,
        login_id=user.login_id,
        action="LOGIN",
        result="SUCCESS",
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(login_log)
    db.commit()

    # Get permissions from user's group
    permissions = None
    if user.group and user.group.permissions:
        permissions = user.group.permissions

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "login_id": user.login_id,
                "name": user.name,
                "email": user.email,
                "department": user.department,
                "role": user.role,
                "group_id": user.group_id,
                "permissions": permissions
            }
        }
    }


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    로그아웃

    현재 세션을 비활성화합니다.

    **Request Header**:
    - **Authorization**: Bearer {access_token} (필수)

    **Response**: success: true

    **Error**:
    - 401: 유효하지 않은 토큰
    """
    # Import settings for timezone
    from app.config import settings

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Decode token to get user info
    try:
        token_data = decode_token(token)
        login_id = token_data.username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find and deactivate the session
    session = db.query(UserSession).filter(
        UserSession.token == token,
        UserSession.is_active == True
    ).first()

    if session:
        session.is_active = False
        session.logged_out_at = datetime.now(settings.tz)
        session.logout_reason = "USER_LOGOUT"

        # Create UserLoginLog record
        logout_log = UserLoginLog(
            user_id=session.user_id,
            login_id=login_id,
            action="LOGOUT",
            result="SUCCESS"
        )
        db.add(logout_log)
        db.commit()

    return {"success": True}


@router.post("/refresh")
async def refresh(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    토큰 갱신

    Refresh token을 사용하여 새로운 access token을 발급합니다.

    **Request Body** (JSON):
    - **refresh_token**: 리프레시 토큰 (필수)

    **Response**: success, data (access_token, refresh_token, token_type 포함)

    **Error**:
    - 401: 유효하지 않은 리프레시 토큰
    """
    # Import settings for timezone
    from app.config import settings

    try:
        # Decode refresh token
        token_data = decode_token(refresh_data.refresh_token)
        login_id = token_data.username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user exists
    user = db.query(AccountUser).filter(AccountUser.login_id == login_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new tokens
    access_token = create_access_token(data={"sub": user.login_id})
    new_refresh_token = create_refresh_token(data={"sub": user.login_id})

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    }


@router.post("/login/oauth2", response_model=Token, deprecated=True)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    [DEPRECATED] 로그인 (Legacy OAuth2)

    ⚠️ 이 엔드포인트는 레거시 호환성을 위해 유지됩니다.
    새로운 클라이언트는 POST /api/auth/login 을 사용하세요.

    레거시 User 모델을 사용하는 OAuth2 폼 기반 로그인입니다.

    **Request Body** (OAuth2 폼 형식):
    - **username**: 사용자 이름 (필수)
    - **password**: 비밀번호 (필수)

    **Response**: access_token과 token_type이 포함된 Token 객체

    **Error**:
    - 401: 잘못된 사용자 이름 또는 비밀번호
    """
    # [LEGACY] OAuth2 폼 기반 로그인 — Legacy User (users 테이블) 조회
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


@router.get("/me", response_model=AccountUserResponse)
async def get_me(current_user: AccountUser = Depends(get_current_account_user)):
    """
    현재 사용자 정보 조회

    현재 인증된 사용자의 정보를 조회합니다.

    **Response**: AccountUserResponse (비밀번호 제외)

    **Error**:
    - 401: 유효하지 않은 토큰
    """
    return current_user
