"""permissions_changed NATS 발행 헬퍼 단위 테스트 — Permission_Group_Scheduling FR-06 (WS-A NATS 소유분).

검증:
- per-user subject 포맷(광역 금지).
- 서명 payload 가 REVOKE_SIGNING_KEY 로 검증되고, 변조 시 거부.
"""
from app.config import settings
from app.services.nats_revoke_publisher import (
    permissions_changed_subject,
    build_permissions_changed_message,
)
from app.utils.revoke_signing import verify_revoke


def test_should_build_per_user_subject_when_permissions_changed():
    """subject = sensorway.{unit}.account.{user_id}.permissions.changed (per-user, 광역 금지)."""
    assert permissions_changed_subject(7) == f"sensorway.{settings.NATS_UNIT_ID}.account.7.permissions.changed"


def test_should_sign_payload_when_built(monkeypatch):
    """payload 가 REVOKE_SIGNING_KEY 로 서명되고 verify 통과."""
    monkeypatch.setattr(settings, "REVOKE_SIGNING_KEY", "test-perm-key-1234567890")
    msg = build_permissions_changed_message(
        user_id=7, reason="GRANT_REVOKED", issued_at="2026-06-30T12:00:00Z"
    )
    assert msg["user_id"] == 7
    assert msg["reason"] == "GRANT_REVOKED"
    assert msg["issued_at"] == "2026-06-30T12:00:00Z"
    assert msg.get("signature")
    assert verify_revoke(msg, "test-perm-key-1234567890") is True


def test_should_reject_tampered_payload(monkeypatch):
    """서명 후 본문 변조 시 verify 실패."""
    monkeypatch.setattr(settings, "REVOKE_SIGNING_KEY", "test-perm-key-1234567890")
    msg = build_permissions_changed_message(user_id=7, reason="GRANT_CREATED")
    msg["reason"] = "TAMPERED"
    assert verify_revoke(msg, "test-perm-key-1234567890") is False
