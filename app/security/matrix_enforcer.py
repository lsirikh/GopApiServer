"""
매트릭스 중앙 집행 — 단일 choke point (미들웨어형)
PRD: "권한 매트릭스 = 미들웨어" 방향 (사용자 결정 2026-06-30)

- 앱 전역 의존성으로 부착(main.py FastAPI(dependencies=[...])) → 모든 라우트가 한 곳을 통과.
- 경로→(module,verb)는 permission_map.PERMISSION_MAP(중앙 1곳). 매트릭스(그룹 JSONB)는 정책/데이터.
- 휴면(AUTH_MODE=public): 무집행 — 기존 데코레이터/현 동작 100% 보존(안전 롤아웃).
- token 모드: 등록 경로만 매트릭스로 allow/deny. ADMIN bypass. grant 합집합(_effective_allows) 반영.
- 미등록 경로 = 요구 없음(default-allow). 추후 default-deny 전환은 본 enforcer 한 줄 정책.
"""
from __future__ import annotations

from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.dependencies import get_db, get_async_db
from app.security.permission_map import lookup_permission

import logging

logger = logging.getLogger(__name__)

# FR-09 공개 allowlist — default-deny(enforce) 시에도 무인증 통과 허용.
# 인프라(docs/openapi/health/root) + 무인증 auth. 전체 확정은 observe 모드 라이브 수집으로 보강.
_PUBLIC_PREFIXES = ("/docs", "/redoc", "/openapi", "/health", "/static", "/favicon")
_PUBLIC_EXACT = {"/"}
_PUBLIC_ROUTES = {("POST", "/api/auth/login"), ("POST", "/api/auth/refresh")}


def is_public_allowlisted(method: str, path: str) -> bool:
    """default-deny(enforce) 시에도 통과할 공개 경로 여부."""
    if path in _PUBLIC_EXACT or path.startswith(_PUBLIC_PREFIXES):
        return True
    return (method.upper(), path) in _PUBLIC_ROUTES


def _resolve_user_from_request(request: Request, db: Session):
    """Authorization: Bearer 토큰을 직접 파싱해 AccountUser 해석(없으면 None).

    전역 의존성이라 미등록/public 경로에 401을 강요하지 않도록 **optional** 로 처리한다.
    jti 블랙리스트·활성/잠금 검사는 get_current_account_user_optional 과 동일 기준.

    (sync 버전 — 기존 caller 호환용 유지. 실제 enforce_matrix 는 async 버전 사용.)
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()

    from app.utils.auth import decode_token
    from app.services.token_blacklist_service import is_blacklisted
    from app.models.user import AccountUser

    try:
        token_data = decode_token(token)
    except JWTError:
        return None
    if token_data.jti and is_blacklisted(db, token_data.jti):
        return None
    login_id = token_data.username
    if not login_id:
        return None
    user = db.query(AccountUser).filter(AccountUser.login_id == login_id).first()
    if not user or not user.is_active or user.is_locked:
        return None
    return user


async def _resolve_user_from_request_async(request: Request, db: AsyncSession):
    """Authorization: Bearer 토큰을 직접 파싱해 AccountUser 해석(없으면 None) — AsyncSession 버전.

    sync `_resolve_user_from_request` 와 반환/판정 규칙 완전 동일:
    - 헤더 없음/형식 오류/JWT 오류 → None
    - jti 블랙리스트 → None
    - 사용자 없음/비활성/잠금 → None
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()

    from sqlalchemy import select
    from app.utils.auth import decode_token
    from app.services.token_blacklist_service import is_blacklisted_async
    from app.models.user import AccountUser

    try:
        token_data = decode_token(token)
    except JWTError:
        return None
    if token_data.jti and await is_blacklisted_async(db, token_data.jti):
        # FR-SEC-01: 폐기 토큰은 route 의존성과 동형으로 SESSION_REVOKED(401) 발화 — read/write shape 일치.
        from app.exceptions import RevokedTokenError
        from app.services.token_blacklist_service import get_blacklist_reason_async
        raise RevokedTokenError(reason=await get_blacklist_reason_async(db, token_data.jti))
    login_id = token_data.username
    if not login_id:
        return None
    result = await db.execute(select(AccountUser).where(AccountUser.login_id == login_id))
    user = result.scalars().first()
    if not user or not user.is_active or user.is_locked:
        return None
    return user


async def enforce_matrix(request: Request, db: AsyncSession = Depends(get_async_db)):
    """전역 매트릭스 집행 의존성.

    매 요청마다 실행되므로 내부 DB 접근은 AsyncSession 기반으로 통일해
    이벤트루프 블로킹을 회피한다. 시그니처(반환 계약)는 동일:
    - 통과 시 None 반환
    - 인증 실패 → 401 HTTPException
    - 권한 부족 → 403 HTTPException
    """
    from app.config import settings

    # 휴면(public) — 현 동작 보존(데코레이터/미들웨어 모두 무집행)
    if settings.AUTH_MODE != "token":
        return

    # FR-RBAC-03: 중첩 마운트에서 request.scope["route"].path 가 prefix-strip 된 상대경로가 되어
    #   절대경로 맵과 안 맞던 버그(전 라우트 무집행). 실제 절대경로(request.url.path)를 숫자 ID 정규화해 조회.
    import re as _re
    path = request.url.path
    perm = lookup_permission(request.method, _re.sub(r"/\d+", "/{}", path))
    if perm is None:
        # FR-09 미등록 경로 정책: off=통과(현행) / observe=로그+통과 / enforce=allowlist 외 403.
        mode = getattr(settings, "MATRIX_DENY_MODE", "off")
        if mode == "off" or is_public_allowlisted(request.method, path):
            return  # 현행 default-allow 또는 공개 allowlist
        if mode == "observe":
            logger.warning("[default-deny observe] 미분류 경로 %s %s (enforce 시 403)", request.method, path)
            return  # 관찰만 — 아직 차단 안 함(미분류 수집용)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unregistered route denied (matrix default-deny)",
        )

    module, verb = perm
    user = await _resolve_user_from_request_async(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role == "ADMIN":
        return  # ADMIN bypass — 매트릭스 무관

    # 유효권한 = 등급 매트릭스 ∪ 현재 유효 grant (요청시점)
    from app.routers.auth import _effective_allows_async
    if not await _effective_allows_async(db, user, module, verb):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permission: requires {module}:{verb} (role: {user.role})",
        )
