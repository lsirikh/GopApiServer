"""
공통 세션 token family 폐기 서비스 (Session Authority PRD FR-01).

배경(Account_Auth_Session_Analysis_20260708 §12.2): logout/중복로그인/lock/deactivate/reset 등
폐기 경로가 제각각 구현되어 refresh JTI 누락·TTL 불일치가 발생했다. 이 서비스로 통합해
"access+refresh 둘 다, 각 JWT 의 실제 exp 로, 세션 마킹까지 원자적으로" 규칙을 강제한다.

- TTL: 설정값 추정(24h/7d) 대신 각 토큰의 **exp claim** 을 blacklist.expires_at 으로 사용(ACC-P1-02 동반).
- 만료된 토큰도 폐기 대상이므로 decode 시 exp 검증을 끄고 jti/exp 만 추출한다.
- dual-stack: 호출측 세션 종류에 맞춰 sync/async 두 버전 제공(login/refresh/logout=sync, users.py=async).
- NATS 통지는 caller 책임(기존 패턴, NATS_REVOKE_ENABLED 게이트) — 본 서비스는 DB 폐기(보안 핵심)만.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from app.utils.datetime import utc_now
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import UserSession
from app.services.token_blacklist_service import add_to_blacklist, add_to_blacklist_async

# exp claim 부재(비정상 토큰) 시 방어적 fallback TTL — refresh 수명 커버.
_FALLBACK_TTL = timedelta(days=30)


def _extract_jti_exp(token: Optional[str]) -> tuple[Optional[str], Optional[datetime]]:
    """토큰에서 (jti, exp=naive UTC) 추출. 서명은 검증하되 exp 만료는 무시(폐기 대상이므로).

    placeholder/손상 토큰은 (None, None) → 호출측이 skip.
    """
    if not token:
        return None, None
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except JWTError:
        return None, None
    jti = payload.get("jti")
    exp = payload.get("exp")
    exp_dt = datetime.utcfromtimestamp(exp) if exp else None
    return jti, exp_dt


def _iter_session_tokens(session: UserSession):
    """(token, token_type) 쌍 — access + refresh."""
    yield session.token, "access"
    yield session.refresh_token, "refresh"


def _blacklist_pairs(session: UserSession):
    """(jti, expires_at, token_type) — E1: session.token/refresh_token 은 이미 jti,
    만료는 stored expires_at/refresh_expires_at 사용(decode 불필요). 원문 미저장."""
    fb = utc_now() + _FALLBACK_TTL
    if session.token:
        yield session.token, (session.expires_at or fb), "access"
    if session.refresh_token:
        yield session.refresh_token, (session.refresh_expires_at or fb), "refresh"


def revoke_session_family(
    db: Session,
    session: UserSession,
    reason: str,
    actor_id: Optional[int] = None,  # noqa: ARG001 (감사 확장 여지)
    commit: bool = False,
) -> list[tuple[int, Optional[str]]]:
    """세션의 access+refresh jti 를 stored 만료로 블랙리스트 + 세션 폐기 마킹 (sync).

    E1/P1-10: session.token=access jti, refresh_token=refresh jti → decode 없이 직접 블랙리스트.
    Returns: [(session_id, access_jti)] — caller NATS 통지용. commit=True 면 즉시 커밋.
    """
    for jti, exp_dt, ttype in _blacklist_pairs(session):
        add_to_blacklist(db, jti=jti, expires_at=exp_dt, reason=reason,
                         user_id=session.user_id, token_type=ttype)
    session.is_active = False
    session.logged_out_at = utc_now()
    session.logout_reason = reason
    if commit:
        db.commit()
    return [(session.id, session.token)]


async def revoke_session_family_async(
    db: AsyncSession,
    session: UserSession,
    reason: str,
    actor_id: Optional[int] = None,  # noqa: ARG001
    commit: bool = False,
) -> list[tuple[int, Optional[str]]]:
    """revoke_session_family 의 async 버전 — users.py(lock/deactivate/reset) 용."""
    for jti, exp_dt, ttype in _blacklist_pairs(session):
        await add_to_blacklist_async(db, jti=jti, expires_at=exp_dt, reason=reason,
                                     user_id=session.user_id, token_type=ttype)
    session.is_active = False
    session.logged_out_at = utc_now()
    session.logout_reason = reason
    if commit:
        await db.commit()
    return [(session.id, session.token)]
