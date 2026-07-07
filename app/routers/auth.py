"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.dependencies import get_db, get_async_db
# NOTE: User는 레거시 모델 (users 테이블). 신규 코드는 AccountUser (account_users 테이블) 사용할 것.
from app.models.user import AccountUser, UserSession, UserLoginLog, UserGroup, UserGroupGrant
from app.schemas.user import Token, AccountLoginRequest, RefreshTokenRequest, AccountUserResponse
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

        # PRD v4.9 Phase 2-A4: jti 블랙리스트 검증 / FR-SVF-10: 안정 코드 SESSION_REVOKED 노출
        from app.services.token_blacklist_service import is_blacklisted, get_blacklist_reason
        if is_blacklisted(db, token_data.jti):
            from app.exceptions import RevokedTokenError
            raise RevokedTokenError(reason=get_blacklist_reason(db, token_data.jti))

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


def _resolve_role_group(db: Session, user: AccountUser) -> UserGroup | None:
    """권한 원천 그룹 = 사용자에게 **명시 배정된 그룹(group_id)** — ADR_Permission_Model_v5.2 (R10①).

    ★ `name==role` 자동해석 **폐기**(임시 등급상승·rename 붕괴 위험 제거).
    role 은 ADMIN 특권 라벨일 뿐 권한 원천이 아니다(기능권한 = 배정 그룹 + grant).
    배정(group_id) 안 한 비-ADMIN 은 권한 0(명시·안전). ADMIN bypass 는 호출 측(require_perm 등).
    """
    if user.group_id:
        return db.query(UserGroup).filter(UserGroup.id == user.group_id).first()
    return None


def _role_group_allows(group: UserGroup | None, module: str, verb: str) -> bool:
    """등급 그룹 permissions 매트릭스에서 modules[module][verb] 가 True 인지."""
    perms = (group.permissions or {}) if group else {}
    modules_perms = perms.get("modules", {}) if isinstance(perms, dict) else {}
    verbs_perms = modules_perms.get(module, {}) if isinstance(modules_perms, dict) else {}
    return isinstance(verbs_perms, dict) and bool(verbs_perms.get(verb))


def _kst_now() -> datetime:
    """settings.tz(KST) 기준 naive now — grant 저장/비교 컨벤션 일치."""
    from app.config import settings
    return datetime.now(settings.tz).replace(tzinfo=None)


def _active_grants(db: Session, user: AccountUser, now=None) -> list:
    """현재 유효한(요청시점) grant 행 목록 — FR-02 (PRD_Permission_Group_Scheduling §3.2).

    유효 = revoked_at IS NULL AND valid_from <= now AND (valid_until IS NULL OR valid_until > now).
    ★ is_active(sweep 비정규화)는 **보지 않는다** — sweep 지연/미실행 시 보안구멍 방지(NFR-01).
    """
    if now is None:
        now = _kst_now()
    return db.query(UserGroupGrant).filter(
        UserGroupGrant.user_id == user.id,
        UserGroupGrant.revoked_at.is_(None),
        UserGroupGrant.valid_from <= now,
        or_(UserGroupGrant.valid_until.is_(None), UserGroupGrant.valid_until > now),
    ).all()


def _active_grant_groups(db: Session, user: AccountUser, now=None) -> list:
    """현재 유효 grant 들의 권한그룹 목록(_active_grants 파생)."""
    return [g.group for g in _active_grants(db, user, now) if g.group is not None]


def _merge_modules(target: dict, src) -> None:
    """src.modules 의 truthy verb 를 target.modules 에 OR 병합(합집합).

    R11 가드: modules 가 dict 아니면(레거시 list 등) 무시 — 로그인 경로 500 회귀 방지.
    (라이브 그룹은 strict schema라 전부 dict이나, 레거시/오염 데이터에도 견고하게.)
    """
    if not isinstance(src, dict):
        return
    modules = src.get("modules")
    if not isinstance(modules, dict):
        return
    for module, verbs in modules.items():
        if not isinstance(verbs, dict):
            continue
        tgt_verbs = target.setdefault("modules", {}).setdefault(module, {})
        for verb, val in verbs.items():
            if val:
                tgt_verbs[verb] = True


def effective_permissions_payload(db: Session, user: AccountUser, now=None) -> dict:
    """클라 노출용 유효권한 페이로드 — FR-06/FR-07.

    = 등급 매트릭스 ∪ 현재 유효 grant 그룹 매트릭스(modules OR, device_groups 합집합).
    valid_until = 활성 grant 중 가장 임박한 만료(없으면 None=상시). 클라 캐시 만료시점.
    """
    if now is None:
        now = _kst_now()
    merged: dict = {"modules": {}, "device_groups": []}

    def _add_device_groups(perms):
        if isinstance(perms, dict):
            for dg in (perms.get("device_groups") or []):
                if dg not in merged["device_groups"]:
                    merged["device_groups"].append(dg)

    role_group = _resolve_role_group(db, user)
    if role_group and isinstance(role_group.permissions, dict):
        _merge_modules(merged, role_group.permissions)
        _add_device_groups(role_group.permissions)

    earliest_until = None
    for grant in _active_grants(db, user, now):
        grp = grant.group
        if grp and isinstance(grp.permissions, dict):
            _merge_modules(merged, grp.permissions)
            _add_device_groups(grp.permissions)
        if grant.valid_until is not None and (earliest_until is None or grant.valid_until < earliest_until):
            earliest_until = grant.valid_until

    merged["valid_until"] = earliest_until
    return merged


def _effective_allows(db: Session, user: AccountUser, module: str, verb: str, now=None) -> bool:
    """유효권한 = 등급 매트릭스 ∪ 현재 유효 grant 그룹 매트릭스 — FR-02.

    ADMIN bypass 는 호출 측(require_perm 등)에서 처리. 여기서는 비-ADMIN 합집합 판정만.
    """
    if _role_group_allows(_resolve_role_group(db, user), module, verb):
        return True
    for grant_group in _active_grant_groups(db, user, now):
        if _role_group_allows(grant_group, module, verb):
            return True
    return False


def require_perm(module: str, verb: str):
    """권한(module:verb) 기반 인가 의존성 팩토리 — v5.1 FR-SV-04 (PRD_GOP_Server_RBAC_Enforcement).

    인증된 AccountUser 의 역할(등급) 그룹 매트릭스에서 modules[module][verb]=True 확인 → 통과.
    그 외 403. ADMIN 은 매트릭스 무관 bypass. **토큰 필수**(get_current_account_user).

    Args:
        module: EnumPermissionModule 키 (예: 'devices', 'events', 'cameras', 'reports', ...)
        verb: EnumPermissionVerb 키 ('view', 'edit', 'delete', 'control')

    Note:
        - jti 블랙리스트 검사는 get_current_account_user 가 이미 수행 (의존 chain).
        - FR-SV-05 enums 선행: 미정의 모듈/verb를 require_perm 인자로 받으면 권한이 영구 부재 → 의도적 차단.
        - AUTH_MODE 무관 토큰 강제가 필요한 도메인(reports)에 사용. 비계정 도메인의 점진 롤아웃은
          require_perm_optional(휴면형) 사용.
    """
    async def _perm_checker(
        db: Session = Depends(get_db),
        current_user: AccountUser = Depends(get_current_account_user),
    ) -> AccountUser:
        # ADMIN bypass — 매트릭스 무관
        if current_user.role == "ADMIN":
            return current_user
        # 유효권한 = 등급 매트릭스 ∪ 현재 유효 grant (FR-02, 요청시점 계산)
        if not _effective_allows(db, current_user, module, verb):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission: requires {module}:{verb} (role: {current_user.role})",
            )
        return current_user

    return _perm_checker


def require_perm_optional(module: str, verb: str):
    """휴면(dormant) 권한 집행 의존성 팩토리 — v5.x FR-SV-04 (배포-대기형).

    require_perm 과 동일한 등급 매트릭스 집행이지만 **AUTH_MODE=public 에서는 완전 무집행**(현 동작 보존).
    비계정 도메인(cameras/sensors/controllers/actions/detections/malfunctions/servers) write 라우터에
    지금 부착해도 public 모드에선 무해 → 클라(.NET 3종) Bearer 동시배포일에 `AUTH_MODE=token` 플립만으로
    일괄 활성화(점진 롤아웃, FR-SV-03 ②①·클라 ③ 동시 배포 전제).

    동작:
    - **public 모드**: 항상 통과(토큰 유무·역할 무관). 현 라우터 동작과 100% 동일.
    - **token 모드**: get_current_account_user_optional 가 토큰 없으면 401(+jti 블랙리스트 검사).
        ADMIN bypass / 매트릭스 modules[module][verb] 없으면 403.

    require_perm(엄격, 토큰 항상 필수)과의 차이: public 모드 무집행 여부. reports 처럼 AUTH_MODE 무관
    강제가 필요하면 require_perm 사용.
    """
    async def _perm_checker_optional(
        db: Session = Depends(get_db),
        current_user: "AccountUser | None" = Depends(get_current_account_user_optional),
    ) -> "AccountUser | None":
        from app.config import settings
        # public 모드: 전환 대기(미집행) — 현 동작 완전 보존
        if settings.AUTH_MODE != "token":
            return current_user
        # token 모드: optional 이 토큰 필수/jti 검사를 이미 수행 → current_user 존재 보장
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if current_user.role == "ADMIN":
            return current_user
        # 유효권한 = 등급 매트릭스 ∪ 현재 유효 grant (FR-02, 요청시점 계산)
        if not _effective_allows(db, current_user, module, verb):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission: requires {module}:{verb} (role: {current_user.role})",
            )
        return current_user

    return _perm_checker_optional


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

        # FR-SVS-05: 잠금 임계를 런타임 설정에서 읽음(기존 하드코딩 >= 5 대체). 0이면 잠금 비활성.
        from app.services import settings_service
        from app.services.settings_service import SettingKey
        _lockout_threshold = settings_service.get(db, SettingKey.LOCKOUT_THRESHOLD)
        if _lockout_threshold and user.failed_login_count >= _lockout_threshold:
            user.is_locked = True
            user.lock_reason = "Too many failed login attempts"
            user.locked_at = datetime.now(settings.tz).replace(tzinfo=None)

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login_id or password",
        )

    # Extract client info from request (US-2: PRD_UserSession_Improvement.md)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # FR-SVS-05: 토큰/세션 만료를 런타임 설정에서 읽음(시드 기본값 = .env 와 동일하므로 미설정 시 기존 동작).
    # v6.0-session_enabled: session_enabled=False 면 10년(사실상 무기한) — 세션 기간성 마스터 스위치.
    from app.services import settings_service
    from app.services.settings_service import SettingKey
    _timeout_hours, _refresh_days = settings_service.resolve_session_expiry(db)

    # v5.4 클라 지적 P1-B: SUPERSEDED — 로그인 시 같은 계정의 활성 세션들을 evict.
    # 1) is_active=False + logout_reason=DUPLICATE 마킹
    # 2) 각 세션 access token jti → 블랙리스트 등록 (revoke 즉시 발효)
    # 3) NATS auth.revoke 발행 (best-effort, 게이트 off 시 무동작)
    #
    # 이렇게 하지 않으면 로그인마다 user_sessions 누적 + 이전 토큰 계속 유효(취약).
    from app.services.token_blacklist_service import add_to_blacklist as _add_to_blacklist
    from app.services.nats_revoke_publisher import publish_session_revoke as _publish_revoke
    from app.utils.enums import EnumLogoutReason as _EnumLogoutReason
    _superseded_sessions = db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active == True,
    ).all()
    _revoke_targets = []  # (session_id, jti) — commit 후 NATS 발행용
    _now_naive = datetime.now(settings.tz).replace(tzinfo=None)
    for _old in _superseded_sessions:
        _old.is_active = False
        _old.logout_reason = _EnumLogoutReason.DUPLICATE.value  # SUPERSEDED == DUPLICATE
        _old.logged_out_at = _now_naive
        # jti 추출 → 블랙리스트 (revoke 발효는 jti 블랙리스트 hit로 즉시)
        try:
            _td = decode_token(_old.token)
            if _td.jti:
                _add_to_blacklist(
                    db, jti=_td.jti,
                    expires_at=_old.expires_at,
                    reason="DUPLICATE",
                    user_id=user.id,
                    token_type="access",
                )
                _revoke_targets.append((_old.id, _td.jti))
        except Exception:
            _revoke_targets.append((_old.id, None))  # jti 파싱 실패해도 세션 자체는 마킹됨

    # FR-SVF-01/02: 세션 행을 먼저 flush 하여 id(= session_id)를 확보한 뒤,
    # 그 id를 sid 클레임으로 박은 access+refresh 토큰을 발급한다(refresh로 회전하지 않는 식별자).
    # token 컬럼은 NOT NULL+unique 이므로 임시 unique placeholder 로 flush → 발급 후 실제 토큰으로 갱신.
    import uuid as _uuid
    _placeholder = f"pending-{_uuid.uuid4()}"
    session = UserSession(
        user_id=user.id,
        token=_placeholder,
        refresh_token=f"{_placeholder}-r",
        expires_at=datetime.now(settings.tz).replace(tzinfo=None) + timedelta(hours=_timeout_hours),
        is_active=True,
        ip_address=client_ip,
        user_agent=user_agent
    )
    db.add(session)
    db.flush()  # session.id 확보 (commit 전)

    # Create JWT tokens — sid = UserSession.id, 만료는 런타임 설정 적용
    access_token = create_access_token(
        data={"sub": user.login_id, "sid": str(session.id)}, expires_delta=timedelta(hours=_timeout_hours))
    refresh_token = create_refresh_token(
        data={"sub": user.login_id, "sid": str(session.id)}, expires_delta=timedelta(days=_refresh_days))

    # 실제 발급 토큰으로 placeholder 교체
    session.token = access_token
    session.refresh_token = refresh_token

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

    # v5.4 P1-B: SUPERSEDED 세션들에 대해 NATS revoke 발행 (best-effort, commit 이후 순서)
    for _sid, _jti in _revoke_targets:
        try:
            await _publish_revoke(
                user_id=user.id,
                session_id=_sid,
                jti=_jti,
                reason=_EnumLogoutReason.DUPLICATE,
            )
        except Exception:
            pass  # best-effort — 발행 실패가 로그인을 막지 않음

    # 권한 = 등급 매트릭스 ∪ 현재 유효 grant (FR-07, PRD_Permission_Group_Scheduling).
    # effective_permissions_payload 가 역할명 그룹(Option A) + group_id 폴백 + grant 합집합 + valid_until 산출.
    _perm_now = _kst_now()
    permissions = effective_permissions_payload(db, user, _perm_now)
    if permissions.get("valid_until") is not None:
        # 클라 시계 보정용 — KST aware 로 직렬화(+09:00)
        permissions["valid_until"] = permissions["valid_until"].replace(tzinfo=settings.tz)

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "session_id": str(session.id),  # FR-SVF-01: 불변 세션 식별자(클라 강제로그아웃 매칭키)
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

    # FR-SVF-03: 토큰 패밀리 무효화 — paired refresh jti도 블랙리스트 등록.
    # access만 등재하면 셀프 로그아웃 후 저장된 refresh_token으로 /refresh 호출 시
    # 새 토큰을 발급받아 세션이 부활함. force_logout_session(user_sessions.py:368-376) 동일 패턴.
    if session and session.refresh_token:
        from app.services.token_blacklist_service import add_to_blacklist
        from app.services import settings_service as _ss
        from app.services.settings_service import SettingKey as _SK
        from datetime import timedelta as _td
        # v6.0-blacklist_ttl_dynamic (2026-07-07): 블랙리스트 TTL을 런타임 refresh_expiration_days 에서 읽음.
        # 정적 env(JWT_REFRESH_EXPIRATION_DAYS)를 쓰면 설정으로 refresh 만료를 늘려도 블랙리스트가 먼저
        # 만료되어 폐기된 refresh 가 부활하는 틈이 생김.
        _refresh_days = _ss.get(db, _SK.REFRESH_EXPIRATION_DAYS)
        try:
            refresh_data = decode_token(session.refresh_token, expected_type="refresh")
            if refresh_data.jti:
                add_to_blacklist(
                    db=db,
                    jti=refresh_data.jti,
                    expires_at=datetime.utcnow() + _td(days=_refresh_days),
                    reason="LOGOUT",
                    user_id=session.user_id,
                    token_type="refresh",
                )
        except JWTError:
            pass

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
        from app.exceptions import RevokedTokenError
        from app.services.token_blacklist_service import get_blacklist_reason
        raise RevokedTokenError(
            reason=get_blacklist_reason(db, token_data.jti),
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
    # v6.0-blacklist_ttl_dynamic (2026-07-07): TTL을 런타임 refresh_expiration_days 에서 읽음.
    from app.services import settings_service as _ss
    from app.services.settings_service import SettingKey as _SK
    if token_data.jti:
        old_refresh_expires = datetime.utcnow() + _td(days=_ss.get(db, _SK.REFRESH_EXPIRATION_DAYS))
        add_to_blacklist(
            db=db,
            jti=token_data.jti,
            expires_at=old_refresh_expires,
            reason="REFRESH_ROTATION",
            user_id=user.id,
            token_type="refresh",
        )

    # FR-SVF-01/02: sid(세션 식별자)는 refresh로 회전하지 않는다 — 옛 토큰의 sid를 그대로 승계.
    sid = token_data.sid
    token_payload = {"sub": user.login_id}
    if sid:
        token_payload["sid"] = sid

    # Create new tokens (sid 승계, jti만 회전). FR-SVS-05: 만료는 런타임 설정 적용.
    # v6.0-session_enabled: session_enabled=False 면 10년(무기한) — login 과 동일 정책.
    from app.services import settings_service
    from app.services.settings_service import SettingKey
    _timeout_hours, _refresh_days = settings_service.resolve_session_expiry(db)
    access_token = create_access_token(data=token_payload, expires_delta=timedelta(hours=_timeout_hours))
    new_refresh_token = create_refresh_token(data=token_payload, expires_delta=timedelta(days=_refresh_days))

    # FR-SVF-01: 세션 행을 새 토큰 쌍으로 재바인딩(orphan 방지) — force_logout이 현재 토큰의
    # jti를 무효화하도록. sid 없는 레거시 토큰은 건너뜀(점진 롤아웃 호환).
    if sid:
        try:
            session = db.query(UserSession).filter(
                UserSession.id == int(sid),
                UserSession.is_active == True,
            ).first()
        except (TypeError, ValueError):
            session = None
        if session:
            session.token = access_token
            session.refresh_token = new_refresh_token
            db.commit()

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "session_id": sid
        }
    }


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


# ---------------------------------------------------------------------------
# v6.0 P4 — Dual-stack async 버전
# ---------------------------------------------------------------------------
# 기존 sync 시그니처는 완전히 유지된다. 아래는 AsyncSession 기반 병행 구현으로
# async 라우터(신규 마이그레이션 대상)에서 동일 로직을 사용하기 위한 신설 함수군이다.
# 규칙:
#   - 로직은 sync 버전과 100% 동치 (permissions merge, grant 유효성, ADMIN bypass 등).
#   - relationship (UserGroupGrant.group) 은 selectinload 로 미리 로드 → async lazy-load 회피.
#   - AUTH_MODE / 블랙리스트 / 예외 처리 정책은 모두 sync 경로와 동일.
# ---------------------------------------------------------------------------


async def _resolve_role_group_async(db: AsyncSession, user: AccountUser) -> UserGroup | None:
    """_resolve_role_group 의 async 버전 — group_id 기반 조회 (R10①).

    ADR_Permission_Model_v5.2: 배정 그룹만 권한 원천, name==role 자동해석 폐기.
    """
    if user.group_id:
        stmt = select(UserGroup).where(UserGroup.id == user.group_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    return None


async def _active_grants_async(db: AsyncSession, user: AccountUser, now=None) -> list:
    """_active_grants 의 async 버전 — 요청시점 유효 grant 조회 (FR-02).

    is_active(sweep 비정규화)는 보지 않음(NFR-01). relationship 을 selectinload 로 로드.
    """
    if now is None:
        now = _kst_now()
    stmt = (
        select(UserGroupGrant)
        .where(
            UserGroupGrant.user_id == user.id,
            UserGroupGrant.revoked_at.is_(None),
            UserGroupGrant.valid_from <= now,
            or_(UserGroupGrant.valid_until.is_(None), UserGroupGrant.valid_until > now),
        )
        .options(selectinload(UserGroupGrant.group))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _active_grant_groups_async(db: AsyncSession, user: AccountUser, now=None) -> list:
    """_active_grant_groups 의 async 버전 — 유효 grant 파생 그룹 목록."""
    grants = await _active_grants_async(db, user, now)
    return [g.group for g in grants if g.group is not None]


async def effective_permissions_payload_async(db: AsyncSession, user: AccountUser, now=None) -> dict:
    """effective_permissions_payload 의 async 버전 — 클라 노출용 유효권한 페이로드 (FR-06/FR-07).

    등급 매트릭스 ∪ 현재 유효 grant 그룹 매트릭스 (modules OR, device_groups 합집합).
    valid_until = 활성 grant 중 가장 임박한 만료(없으면 None=상시).
    """
    if now is None:
        now = _kst_now()
    merged: dict = {"modules": {}, "device_groups": []}

    def _add_device_groups(perms):
        if isinstance(perms, dict):
            for dg in (perms.get("device_groups") or []):
                if dg not in merged["device_groups"]:
                    merged["device_groups"].append(dg)

    role_group = await _resolve_role_group_async(db, user)
    if role_group and isinstance(role_group.permissions, dict):
        _merge_modules(merged, role_group.permissions)
        _add_device_groups(role_group.permissions)

    earliest_until = None
    grants = await _active_grants_async(db, user, now)
    for grant in grants:
        grp = grant.group
        if grp and isinstance(grp.permissions, dict):
            _merge_modules(merged, grp.permissions)
            _add_device_groups(grp.permissions)
        if grant.valid_until is not None and (earliest_until is None or grant.valid_until < earliest_until):
            earliest_until = grant.valid_until

    merged["valid_until"] = earliest_until
    return merged


async def _effective_allows_async(db: AsyncSession, user: AccountUser, module: str, verb: str, now=None) -> bool:
    """_effective_allows 의 async 버전 — 등급 매트릭스 ∪ 현재 유효 grant 그룹 매트릭스 (FR-02).

    ADMIN bypass 는 호출 측(require_perm_async 등)에서 처리. 비-ADMIN 합집합 판정만 담당.
    """
    role_group = await _resolve_role_group_async(db, user)
    if _role_group_allows(role_group, module, verb):
        return True
    grant_groups = await _active_grant_groups_async(db, user, now)
    for grant_group in grant_groups:
        if _role_group_allows(grant_group, module, verb):
            return True
    return False


async def get_current_account_user_async(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> AccountUser:
    """get_current_account_user 의 async 버전 — JWT 검증 + jti 블랙리스트 검사.

    PRD v4.9 Phase 2-A4 동일: logout/lock/password-change 토큰 즉시 무효화.

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

        # PRD v4.9 Phase 2-A4: jti 블랙리스트 검증 / FR-SVF-10: 안정 코드 SESSION_REVOKED 노출
        from app.services.token_blacklist_service import is_blacklisted_async, get_blacklist_reason_async
        if await is_blacklisted_async(db, token_data.jti):
            from app.exceptions import RevokedTokenError
            raise RevokedTokenError(reason=await get_blacklist_reason_async(db, token_data.jti))

    except JWTError:
        raise credentials_exception

    stmt = select(AccountUser).where(AccountUser.login_id == login_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_account_user_optional_async(
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AccountUser | None:
    """get_current_account_user_optional 의 async 버전 — AUTH_MODE 의존 선택적 인증.

    - AUTH_MODE=public + 토큰 없음 → None
    - AUTH_MODE=token + 토큰 없음 → 401
    - 토큰 있음 → AccountUser + jti 블랙리스트 검사
    """
    from app.config import settings
    from app.services.token_blacklist_service import is_blacklisted_async

    token = credentials.credentials if credentials else None

    # token 모드: 토큰 필수
    if settings.AUTH_MODE == "token":
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await get_current_account_user_async(credentials=credentials, db=db)

    # public 모드: 토큰 선택
    if not token:
        return None
    try:
        token_data = decode_token(token)
        # jti 블랙리스트 검사 (logout/강등 즉시 무효화)
        if token_data.jti and await is_blacklisted_async(db, token_data.jti):
            return None
        login_id = token_data.username
        if not login_id:
            return None
        stmt = select(AccountUser).where(AccountUser.login_id == login_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user or not user.is_active or user.is_locked:
            return None
        return user
    except JWTError:
        return None


def require_role_async(*allowed_roles: str):
    """require_role 의 async 버전 — 역할(role) 기반 인가 의존성 팩토리 (PRD-GOP-01 V-PG-01 §7).

    반환되는 dependency 는 async, 내부에서 get_current_account_user_async 를 사용한다.
    """
    async def _role_checker(current_user: AccountUser = Depends(get_current_account_user_async)) -> AccountUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role: requires one of {list(allowed_roles)} (current role: {current_user.role})",
            )
        return current_user
    return _role_checker


# 계정 관리(사용자 CRUD/lock/reset) ADMIN 전용 (account:admin) — async 버전
require_admin_async = require_role_async("ADMIN")


def require_perm_async(module: str, verb: str):
    """require_perm 의 async 버전 — 권한(module:verb) 기반 인가 의존성 팩토리 (FR-SV-04).

    ADMIN bypass. 매트릭스 modules[module][verb]=True 없으면 403. **토큰 필수**.
    AUTH_MODE 무관 강제(reports 등) 도메인에 사용.
    """
    async def _perm_checker(
        db: AsyncSession = Depends(get_async_db),
        current_user: AccountUser = Depends(get_current_account_user_async),
    ) -> AccountUser:
        # ADMIN bypass — 매트릭스 무관
        if current_user.role == "ADMIN":
            return current_user
        # 유효권한 = 등급 매트릭스 ∪ 현재 유효 grant (FR-02, 요청시점 계산)
        if not await _effective_allows_async(db, current_user, module, verb):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission: requires {module}:{verb} (role: {current_user.role})",
            )
        return current_user

    return _perm_checker


def require_perm_optional_async(module: str, verb: str):
    """require_perm_optional 의 async 버전 — 휴면(dormant) 권한 집행 (FR-SV-04, 배포-대기형).

    - **public 모드**: 항상 통과(토큰 유무·역할 무관). 현 라우터 동작과 100% 동일.
    - **token 모드**: 토큰 필수(+jti 블랙리스트 검사), ADMIN bypass, 매트릭스 미보유 시 403.
    """
    async def _perm_checker_optional(
        db: AsyncSession = Depends(get_async_db),
        current_user: "AccountUser | None" = Depends(get_current_account_user_optional_async),
    ) -> "AccountUser | None":
        from app.config import settings
        # public 모드: 전환 대기(미집행) — 현 동작 완전 보존
        if settings.AUTH_MODE != "token":
            return current_user
        # token 모드: optional 이 토큰 필수/jti 검사를 이미 수행 → current_user 존재 보장
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if current_user.role == "ADMIN":
            return current_user
        # 유효권한 = 등급 매트릭스 ∪ 현재 유효 grant (FR-02, 요청시점 계산)
        if not await _effective_allows_async(db, current_user, module, verb):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission: requires {module}:{verb} (role: {current_user.role})",
            )
        return current_user

    return _perm_checker_optional


@router.get("/me/permissions")
async def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """현재 사용자의 유효권한 스냅샷 조회 — FR-06 (PRD_Permission_Group_Scheduling).

    클라(Dotnet.Monitoring)가 grant 만료로 stale 된 권한을 재평가하는 경로.
    로그인 스냅샷과 동일 계산(등급 매트릭스 ∪ 현재 유효 grant).

    **Response data**:
    - **modules**: 모듈별 권한(view/edit/delete/control)
    - **device_groups**: 접근 가능 디바이스 그룹 ID
    - **valid_until**: 가장 임박한 grant 만료(KST, 없으면 null=상시) — 클라 캐시 만료시점
    - **server_time**: 서버 현재 시각(KST) — 클라-서버 시계 편차 보정용

    **Error**: 401 (유효하지 않은 토큰)
    """
    from app.config import settings

    now = _kst_now()
    payload = effective_permissions_payload(db, current_user, now)
    valid_until = payload.get("valid_until")
    return {
        "success": True,
        "data": {
            "modules": payload.get("modules", {}),
            "device_groups": payload.get("device_groups", []),
            "valid_until": valid_until.replace(tzinfo=settings.tz) if valid_until is not None else None,
            "server_time": now.replace(tzinfo=settings.tz),
        },
    }
