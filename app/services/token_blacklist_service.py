"""
Token Blacklist Service — jti 블랙리스트 등록/조회 (캐시 포함)

PRD: v4.9 Phase 2-A4
- in-memory TTL 캐시 (60s) — 매 인증 요청마다 DB 조회 비용 절감
- logout 시 캐시 즉시 무효화
"""
from datetime import datetime, timedelta
from typing import Optional

try:
    from cachetools import TTLCache
    _cache = TTLCache(maxsize=10000, ttl=60)  # jti → True / False (60s TTL)
except ImportError:
    _cache = {}  # fallback: 캐시 없음 (DB만)

from sqlalchemy.orm import Session
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
        revoked_at=datetime.utcnow(),
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
    now = datetime.utcnow()
    count = db.query(TokenBlacklist).filter(TokenBlacklist.expires_at < now).delete()
    db.commit()
    return count
