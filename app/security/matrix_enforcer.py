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
from jose import JWTError

from app.dependencies import get_db
from app.security.permission_map import lookup_permission


def _resolve_user_from_request(request: Request, db: Session):
    """Authorization: Bearer 토큰을 직접 파싱해 AccountUser 해석(없으면 None).

    전역 의존성이라 미등록/public 경로에 401을 강요하지 않도록 **optional** 로 처리한다.
    jti 블랙리스트·활성/잠금 검사는 get_current_account_user_optional 과 동일 기준.
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


async def enforce_matrix(request: Request, db: Session = Depends(get_db)):
    """전역 매트릭스 집행 의존성."""
    from app.config import settings

    # 휴면(public) — 현 동작 보존(데코레이터/미들웨어 모두 무집행)
    if settings.AUTH_MODE != "token":
        return

    route = request.scope.get("route")
    perm = lookup_permission(request.method, getattr(route, "path", "")) if route is not None else None
    if perm is None:
        return  # 미등록 경로 → 요구 없음(default-allow)

    module, verb = perm
    user = _resolve_user_from_request(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role == "ADMIN":
        return  # ADMIN bypass — 매트릭스 무관

    # 유효권한 = 등급 매트릭스 ∪ 현재 유효 grant (요청시점)
    from app.routers.auth import _effective_allows
    if not _effective_allows(db, user, module, verb):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permission: requires {module}:{verb} (role: {user.role})",
        )
