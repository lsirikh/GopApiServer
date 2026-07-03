"""
UserSession sweep — 만료된 세션 정리 스케줄러
v5.4 클라 지적 P1-A: session sweep + evict.

권위 = 요청시점 판정(get_current_account_user의 expires_at 검사 + jti 블랙리스트).
본 sweep = 만료된 활성 세션 행에 is_active=false + logout_reason=EXPIRED 마킹 (목록/UI 청소).

grant sweep과 동일한 방어 패턴:
- 앱 기동/주기를 sweep 실패가 막지 않음
- 자체 DB 세션 열고 닫음
- 예외는 호출측(스케줄러 래퍼)에서 흡수
"""
from __future__ import annotations

from datetime import datetime

from app.utils.enums import EnumLogoutReason


def find_expired_sessions(db, now: datetime):
    """만료된 활성 세션 조회 (expires_at < now AND is_active=true)."""
    from app.models.user import UserSession
    return db.query(UserSession).filter(
        UserSession.is_active == True,
        UserSession.expires_at < now,
    ).all()


async def run_session_sweep() -> int:
    """스케줄러 진입점 — 만료 세션 is_active=false + logout_reason=EXPIRED.

    Returns: 갱신된 세션 수.
    """
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        now = datetime.now(settings.tz).replace(tzinfo=None)
        expired = find_expired_sessions(db, now)
        if not expired:
            return 0
        for s in expired:
            s.is_active = False
            s.logout_reason = EnumLogoutReason.EXPIRED.value
            s.logged_out_at = now
        db.commit()
        return len(expired)
    finally:
        db.close()
