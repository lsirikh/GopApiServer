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
from app.models.user import User, AccountUser, UserSession, UserLoginLog, UserGroup
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

    PRD v4.9 Phase 2-A4: jti 블랙리스트 검증 추가 (logout/lock/password-change 토큰 즉시 무효화)

    Raises:
        HTTPException 401: 토큰 무효 / 사용자 부재 / jti 블랙리스트 등재
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

        # PRD v4.9 Phase 2-A4: jti 블랙리스트 검증
        from app.services.token_blacklist_service import is_blacklisted
        if is_blacklisted(db, token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise credentials_exception

    user = db.query(AccountUser).filter(AccountUser.login_id == login_id).first()

    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: str):
    """역할(role) 기반 인가 의존성 팩토리 — PRD-GOP-01 V-PG-01 §7.
    인증된 AccountUser 의 role 이 allowed_roles 에 없으면 403. 기존 인증 의존성(get_current_account_user 등)은
    토큰만 검증하고 role 을 인가에 미사용했음 → 권한상승(T1): 아무 인증사용자가 PUT /users/{id} 로 임의 계정을
    ADMIN 격상 가능. 본 의존성이 서버측 RBAC 집행 지점. (FastAPI use_cache 로 get_current_account_user 1회 평가)"""
    async def _role_checker(current_user: AccountUser = Depends(get_current_account_user)) -> AccountUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role: requires one of {list(allowed_roles)} (current role: {current_user.role})",
            )
        return current_user
    return _role_checker


# 계정 관리(사용자 CRUD/lock/reset)는 ADMIN 전용 (account:admin)
require_admin = require_role("ADMIN")


def require_perm(module: str, verb: str):
    """권한(module:verb) 기반 인가 의존성 팩토리 — v5.1 FR-SV-04 (PRD_GOP_Server_RBAC_Enforcement).

    인증된 AccountUser 의 역할(등급) 그룹 매트릭스에서 modules[module][verb]=True 확인 → 통과.
    그 외 403. ADMIN 은 매트릭스 무관 bypass.

    권한 원천(OQ-PG-01 Option A, login 도메인 정합 — auth.py:298~305):
    - 1순위: user.role 명의 등급 그룹(`UserGroup.name == user.role`) permissions JSONB
    - 2순위(폴백): user.group_id 의 그룹 permissions

    Args:
        module: EnumPermissionModule 키 (예: 'devices', 'events', 'cameras', 'reports', ...)
        verb: EnumPermissionVerb 키 ('view', 'edit', 'delete', 'control')

    Note:
        - jti 블랙리스트 검사는 get_current_account_user 가 이미 수행 (의존 chain).
        - FR-SV-05 enums 선행: 미정의 모듈/verb를 require_perm 인자로 받으면 권한이 영구 부재 → 의도적 차단.
        - 비계정 도메인(cameras/sensors/devices/...) write 라우터에 순차 부착 권고 (FR-SV-04 본 차수 + 다음 차수).
    """
    async def _perm_checker(
        db: Session = Depends(get_db),
        current_user: AccountUser = Depends(get_current_account_user),
    ) -> AccountUser:
        # ADMIN bypass — 매트릭스 무관
        if current_user.role == "ADMIN":
            return current_user

        # 역할명 등급 그룹 우선, 폴백으로 user.group_id
        group = db.query(UserGroup).filter(UserGroup.name == current_user.role).first()
        if not group and current_user.group_id:
            group = db.query(UserGroup).filter(UserGroup.id == current_user.group_id).first()

        perms = (group.permissions or {}) if group else {}
        modules_perms = perms.get("modules", {}) if isinstance(perms, dict) else {}
        verbs_perms = modules_perms.get(module, {}) if isinstance(modules_perms, dict) else {}

        if not isinstance(verbs_perms, dict) or not verbs_perms.get(verb):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission: requires {module}:{verb} (role: {current_user.role})",
            )
        return current_user

    return _perm_checker


async def get_current_account_user_optional(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AccountUser | None:
    """AUTH_MODE 의존 선택적 인증 의존성 — v5.1 FR-SV-03 (AccountUser 기반).

    레거시 `get_current_user_optional`(Legacy User 모델 + jti 검사 없음)을 대체하는 신규 헬퍼.
    비계정 도메인(cameras/sensors/devices/...) 라우터가 본 의존성으로 이주하면:
    - AUTH_MODE=public 일 때 토큰 없으면 None (현재 동작 유지)
    - AUTH_MODE=token 일 때 토큰 필수 (401)
    - 토큰 있으면 AccountUser 객체 + jti 블랙리스트 검사 (logout/강등 후 즉시 차단)

    ★ AUTH_MODE=public→token 전환은 본 헬퍼만으로는 발효 안 됨 — 비계정 라우터 의존성 교체(FR-SV-08) +
    클라 Bearer 부착(상위 PRD GOP_Permission_Enforcement) **동시 배포** 필수.

    Returns:
        인증된 경우 AccountUser, AUTH_MODE=public + 토큰 없음 시 None.

    Raises:
        HTTPException 401: AUTH_MODE=token 인데 토큰 누락/무효 또는 jti 블랙리스트 등재.
    """
    from app.config import settings
    from app.services.token_blacklist_service import is_blacklisted

    token = credentials.credentials if credentials else None

    # token 모드: 토큰 필수
    if settings.AUTH_MODE == "token":
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await get_current_account_user(credentials=credentials, db=db)

    # public 모드: 토큰 선택
    if not token:
        return None
    try:
        token_data = decode_token(token)
        # jti 블랙리스트 검사 (logout/강등 즉시 무효화)
        if token_data.jti and is_blacklisted(db, token_data.jti):
            return None
        login_id = token_data.username
        if not login_id:
            return None
        user = db.query(AccountUser).filter(AccountUser.login_id == login_id).first()
        if not user or not user.is_active or user.is_locked:
            return None
        return user
    except JWTError:
        return None


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
            user.locked_at = datetime.now(settings.tz).replace(tzinfo=None)

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
        expires_at=datetime.now(settings.tz).replace(tzinfo=None) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
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

    # 권한 = 역할(등급) 단위 (PRD-GOP-01 OQ-PG-01 = Option A): user.role 명의 등급 그룹 매트릭스를 사용.
    # 등급 그룹이 없으면 레거시 group_id 그룹으로 폴백.
    permissions = None
    role_group = db.query(UserGroup).filter(UserGroup.name == user.role).first()
    if role_group and role_group.permissions:
        permissions = role_group.permissions
    elif user.group and user.group.permissions:
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
        session.logged_out_at = datetime.now(settings.tz).replace(tzinfo=None)
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

    # PRD v4.9 Phase 2-A4: jti 블랙리스트 등록 — logout 후 access_token 즉시 무효화
    if token_data.jti:
        from app.services.token_blacklist_service import add_to_blacklist
        from datetime import timedelta as _td
        # access_token TTL = JWT_EXPIRATION_HOURS (block 기간은 토큰 원래 exp까지)
        expires_at = datetime.utcnow() + _td(hours=settings.JWT_EXPIRATION_HOURS)
        user_id = session.user_id if session else None
        add_to_blacklist(
            db=db,
            jti=token_data.jti,
            expires_at=expires_at,
            reason="LOGOUT",
            user_id=user_id,
            token_type="access",
        )

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
        # PRD v4.9 Phase 2-A4: expected_type='refresh' 가드 — access_token으로 refresh 호출 차단
        token_data = decode_token(refresh_data.refresh_token, expected_type="refresh")
        login_id = token_data.username
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )

    # PRD v4.9 Phase 2-A4: jti 블랙리스트 확인 (이미 폐기된 refresh 차단)
    from app.services.token_blacklist_service import is_blacklisted, add_to_blacklist
    from datetime import timedelta as _td
    if is_blacklisted(db, token_data.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Verify user exists
    user = db.query(AccountUser).filter(AccountUser.login_id == login_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # PRD v4.9 Phase 2-A4: rotation — 옛 refresh jti 블랙리스트 등록 (replay 차단)
    if token_data.jti:
        old_refresh_expires = datetime.utcnow() + _td(days=settings.JWT_REFRESH_EXPIRATION_DAYS)
        add_to_blacklist(
            db=db,
            jti=token_data.jti,
            expires_at=old_refresh_expires,
            reason="REFRESH_ROTATION",
            user_id=user.id,
            token_type="refresh",
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
