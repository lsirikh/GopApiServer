"""
NATS revoke publisher — Force_Logout FR-SVF-05/07/08/11.

per-session 전용 subject 로 서명된 revoke 메시지를 발행한다(best-effort).
무효화 권위는 서버 DB 블랙리스트이며, NATS 발행 실패가 force_logout 을 막지 않는다(FR-SVF-11):
발행은 클라가 ≤60s 블랙리스트 캐시 staleness 창을 건너뛰고 선제적으로 UI 를 잠그게 하는 가속 경로.

★ 활성화 게이트: settings.NATS_REVOKE_ENABLED (기본 False).
  subject 스킴이 클라 EffectiveSubject 와 매칭되는지 확인(V-SVF-05) + 발행 ACL(FR-SVF-08) 을
  적용한 뒤에만 True 로 켠다. False 인 동안 publish_session_revoke 는 즉시 False 를 반환(무동작).

성능 주: 현재는 발행마다 connect 한다(force_logout 은 드문 관리자 동작이라 허용).
  활성화 후 트래픽이 늘면 lifespan 관리 장기 연결로 최적화한다.
"""
import json
import logging
import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.utils.enums import EnumLogoutReason
from app.utils.revoke_signing import build_signed_revoke

logger = logging.getLogger(__name__)


def revoke_subject(user_id: int, session_id) -> str:
    """per-session 전용 subject (계약 C2) — 광역 all.> 금지.

    sensorway.{unit}.account.{user_id}.session.{session_id}.revoke
    """
    return f"sensorway.{settings.NATS_UNIT_ID}.account.{user_id}.session.{session_id}.revoke"


def build_revoke_message(
    *,
    user_id: Optional[int],
    session_id,
    jti: Optional[str],
    reason: EnumLogoutReason,
    issued_at: Optional[str] = None,
) -> dict:
    """서명된 revoke payload dict 생성(발행 본문).

    null 의미론: jti 가 있으면 그 세션만, jti 가 없고 user_id 가 있으면 그 사용자 전체.
    issued_at 은 RFC3339 UTC 'Z' 고정 포맷(.NET 과 동일 canonical 보장).
    """
    if issued_at is None:
        issued_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return build_signed_revoke(
        message_id=str(_uuid.uuid4()),
        session_id=None if session_id is None else str(session_id),
        jti=jti,
        user_id=user_id,
        reason=reason,
        issued_at=issued_at,
        key=settings.REVOKE_SIGNING_KEY,
    )


async def publish_session_revoke(
    *,
    user_id: int,
    session_id,
    jti: Optional[str],
    reason: EnumLogoutReason = EnumLogoutReason.FORCED,
) -> bool:
    """단일 세션 revoke 를 best-effort 로 발행. 실패해도 예외를 던지지 않는다(FR-SVF-11).

    Returns:
        True  — 발행 성공
        False — 비활성(게이트 off) 또는 발행 실패(로그만 남김)
    """
    if not settings.NATS_REVOKE_ENABLED:
        return False

    subject = revoke_subject(user_id, session_id)
    message = build_revoke_message(user_id=user_id, session_id=session_id, jti=jti, reason=reason)
    try:
        import nats
        nc = await nats.connect(
            settings.NATS_URL, connect_timeout=2, max_reconnect_attempts=1
        )
        try:
            await nc.publish(subject, json.dumps(message).encode("utf-8"))
            await nc.flush(timeout=2)
        finally:
            await nc.close()
        return True
    except Exception as e:  # best-effort: 발행 실패가 force_logout 을 막지 않음
        logger.warning("revoke publish failed (subject=%s): %s", subject, e)
        return False
