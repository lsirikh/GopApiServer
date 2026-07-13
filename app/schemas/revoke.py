"""
Revoke 메시지 스키마 — Force_Logout FR-SVF-06.

per-session NATS revoke 페이로드 계약(서명 포함):
{message_id, session_id, jti, user_id, reason(enum), issued_at, signature}

null 의미론: jti 가 있으면 그 세션만 무효화, jti 가 없고 user_id 가 있으면 그 사용자 전체.
reason 은 EnumLogoutReason 으로 제한(FR-SVF-12: free text / URL 금지 → 클라 피싱 표면 제거).
"""
from typing import Optional
from pydantic import BaseModel

from app.utils.enums import EnumLogoutReason


class RevokePayload(BaseModel):
    """NATS account.session.revoke 페이로드 계약."""
    message_id: str
    session_id: Optional[str] = None
    jti: Optional[str] = None
    user_id: Optional[int] = None
    reason: EnumLogoutReason
    issued_at: str
    signature: Optional[str] = None
