"""
Token Blacklist Service — jti 블랙리스트 등록/조회 (캐시 포함)

PRD: v4.9 Phase 2-A4
- in-memory TTL 캐시 (60s) — 매 인증 요청마다 DB 조회 비용 절감
- logout 시 캐시 즉시 무효화
"""
from datetime import datetime, timedelta
from app.utils.datetime import utc_now
from typing import Optional

try:
    from cachetools import TTLCache
    _cache = TTLCache(maxsize=10000, ttl=60)  # jti → True / False (60s TTL)
except ImportError:
    _cache = {}  # fallback: 캐시 없음 (DB만)

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.token_blacklist import TokenBlacklist


def is_blacklisted(db: Session, jti: str) -> bool:
    """jti가 블랙리스트에 있는지 확인 (캐시 우선)"""
    if jti is None:
        return False

    cached = _cache.get(jti) if isinstance(_cache, dict) else _cache.get(jti, None)
    if cached is True:
        return True

    row = db.query(TokenBlacklist.id).filter(TokenBlacklist.jti == jti).first()
    is_listed = row is not None

    try:
        _cache[jti] = is_listed
    except Exception:
        pass

    return is_listed


def get_blacklist_reason(db: Session, jti: str) -> Optional[str]:
    """jti의 블랙리스트 사유(LOGOUT/FORCED/PASSWORD_CHANGE 등) 조회 — FR-SVF-10 details.reason 용.

    폐기된 토큰에 대해서만 호출되므로(드묾) 추가 단건 인덱스 조회 비용은 무시 가능.
    """
    if jti is None:
        return None
    row = db.query(TokenBlacklist.reason).filter(TokenBlacklist.jti == jti).first()
    return row[0] if row else None


def add_to_blacklist(
    db: Session,
    jti: str,
    expires_at: datetime,
    reason: str,
    user_id: Optional[int] = None,
    token_type: str = "access",
) -> TokenBlacklist:
    """블랙리스트 등록 + 캐시 즉시 갱신"""
    if jti is None:
        return None

    existing = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    if existing:
        return existing

    entry = TokenBlacklist(
        jti=jti,
        user_id=user_id,
        token_type=token_type,
        reason=reason,
        expires_at=expires_at,
        revoked_at=utc_now(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    try:
        _cache[jti] = True
    except Exception:
        pass

    return entry


def cleanup_expired(db: Session) -> int:
    """APScheduler가 1시간마다 호출 — exp 경과 row 정리"""
    now = utc_now()
    count = db.query(TokenBlacklist).filter(TokenBlacklist.expires_at < now).delete()
    db.commit()
    return count


# ---------------------------------------------------------------------------
# Async 버전 (v6.0 P3) — dual-stack: 기존 sync 함수는 그대로 유지
# ---------------------------------------------------------------------------

async def is_blacklisted_async(db: AsyncSession, jti: str) -> bool:
    """jti가 블랙리스트에 있는지 확인 (캐시 우선) — async 버전"""
    if jti is None:
        return False

    cached = _cache.get(jti) if isinstance(_cache, dict) else _cache.get(jti, None)
    if cached is True:
        return True

    stmt = select(TokenBlacklist.id).where(TokenBlacklist.jti == jti)
    result = await db.execute(stmt)
    row = result.first()
    is_listed = row is not None

    try:
        _cache[jti] = is_listed
    except Exception:
        pass

    return is_listed


async def get_blacklist_reason_async(db: AsyncSession, jti: str) -> Optional[str]:
    """jti의 블랙리스트 사유 조회 — FR-SVF-10 details.reason 용 (async 버전)."""
    if jti is None:
        return None
    stmt = select(TokenBlacklist.reason).where(TokenBlacklist.jti == jti)
    result = await db.execute(stmt)
    row = result.first()
    return row[0] if row else None


async def add_to_blacklist_async(
    db: AsyncSession,
    jti: str,
    expires_at: datetime,
    reason: str,
    user_id: Optional[int] = None,
    token_type: str = "access",
) -> Optional[TokenBlacklist]:
    """블랙리스트 등록 + 캐시 즉시 갱신 (async 버전)"""
    if jti is None:
        return None

    stmt = select(TokenBlacklist).where(TokenBlacklist.jti == jti)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    if existing:
        return existing

    entry = TokenBlacklist(
        jti=jti,
        user_id=user_id,
        token_type=token_type,
        reason=reason,
        expires_at=expires_at,
        revoked_at=utc_now(),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    try:
        _cache[jti] = True
    except Exception:
        pass

    return entry


async def cleanup_expired_async(db: AsyncSession) -> int:
    """APScheduler가 1시간마다 호출 — exp 경과 row 정리 (async 버전)"""
    now = utc_now()
    stmt = delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0


async def run_blacklist_cleanup() -> int:
    """ACC-P1-05 (2026-07-09): 스케줄러 zero-arg 진입점.

    기존엔 cleanup_expired_async 가 존재하나 스케줄러에 미등록이라 만료 row 가 계속 누적됐다
    (실측 388행 중 357행 만료 잔존). 자체 AsyncSession 을 열어 정리한다(다른 sweep 패턴과 동일).
    """
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        return await cleanup_expired_async(db)
