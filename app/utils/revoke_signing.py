"""
Revoke 메시지 정규화(canonical) + HMAC-SHA256 서명 유틸 — Force_Logout FR-SVF-07.

계약(C3, .NET 클라와 상호운용):
- 서명 입력 = `signature` 필드를 제외한 전체 payload 를
  sort_keys=True, separators=(",", ":"), ensure_ascii=False 로 직렬화한 UTF-8 바이트.
- null 필드(jti/session_id)는 생략하지 않고 명시적으로 직렬화(양측 결정성 보장).
- 서명 키는 JWT_SECRET_KEY 와 분리된 전용 REVOKE_SIGNING_KEY 사용(키 재사용 시 클라가 access 토큰 위조 가능).
- 무효화 권위는 서버 블랙리스트이며, 이 서명은 클라가 위조 revoke 를 거르고 선제적으로 UI 잠금하도록 돕는 용도.
"""
import hashlib
import hmac
import json
from typing import Optional

from app.utils.enums import EnumLogoutReason


def canonical_bytes(payload: dict) -> bytes:
    """`signature` 를 제외한 payload 의 정규화 직렬화 바이트(서명 입력)."""
    body = {k: v for k, v in payload.items() if k != "signature"}
    return json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sign_revoke(payload: dict, key: str) -> str:
    """payload(서명 제외)에 대한 HMAC-SHA256 hex 서명."""
    return hmac.new(key.encode("utf-8"), canonical_bytes(payload), hashlib.sha256).hexdigest()


def verify_revoke(payload: dict, key: str) -> bool:
    """payload['signature'] 를 상수시간 비교로 검증."""
    signature = payload.get("signature")
    if not signature:
        return False
    expected = sign_revoke(payload, key)
    return hmac.compare_digest(str(signature), expected)


def build_signed_revoke(
    *,
    message_id: str,
    session_id: Optional[str],
    jti: Optional[str],
    user_id: Optional[int],
    reason,
    issued_at: str,
    key: str,
) -> dict:
    """서명된 revoke payload dict 생성.

    reason 은 EnumLogoutReason 또는 그 value 문자열을 허용.
    null 의미론: jti 가 있으면 그 세션만, jti 가 없고 user_id 가 있으면 그 사용자 전체.
    """
    reason_value = reason.value if isinstance(reason, EnumLogoutReason) else str(reason)
    payload = {
        "message_id": message_id,
        "session_id": session_id,
        "jti": jti,
        "user_id": user_id,
        "reason": reason_value,
        "issued_at": issued_at,
    }
    payload["signature"] = sign_revoke(payload, key)
    return payload
