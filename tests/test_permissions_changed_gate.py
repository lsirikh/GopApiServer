"""FR-06 — grant 통지 발행기 `publish_permissions_changed` 게이트 + best-effort.

기존 `test_permissions_changed_publish.py` 는 subject/message **빌더**만, `test_revoke_publisher.py`
는 **세션-revoke** 발행기만 다뤘다(DOC-05 지적). 본 테스트는 grant 발행기 자체의
게이트(off→무발행)·활성(on→서명 발행)·best-effort(다운→무예외)를 직접 커버한다.
"""
from __future__ import annotations

import asyncio
import json

from app.config import settings
from app.services import nats_revoke_publisher as pub


def test_should_not_publish_when_gate_off(monkeypatch):
    monkeypatch.setattr(settings, "NATS_REVOKE_ENABLED", False)

    async def _boom(*a, **k):
        raise AssertionError("게이트 off 인데 connect 시도됨")

    monkeypatch.setattr("nats.connect", _boom)
    result = asyncio.run(pub.publish_permissions_changed(user_id=7, reason="GRANT_EXPIRED"))
    assert result is False


def test_should_publish_signed_per_user_subject_when_gate_on(monkeypatch):
    monkeypatch.setattr(settings, "NATS_REVOKE_ENABLED", True)
    captured: dict = {}

    class _FakeNC:
        async def publish(self, subject, payload):
            captured["subject"] = subject
            captured["payload"] = payload

        async def flush(self, timeout=None):
            pass

        async def close(self):
            pass

    async def _connect(*a, **k):
        return _FakeNC()

    monkeypatch.setattr("nats.connect", _connect)
    result = asyncio.run(pub.publish_permissions_changed(user_id=7, reason="GRANT_CREATED"))

    assert result is True
    assert captured["subject"] == f"sensorway.{settings.NATS_UNIT_ID}.account.7.permissions.changed"
    msg = json.loads(captured["payload"].decode("utf-8"))
    assert msg["user_id"] == 7
    assert msg["reason"] == "GRANT_CREATED"
    assert msg.get("signature")  # 서명 포함


def test_should_swallow_error_when_gate_on_but_nats_down(monkeypatch):
    monkeypatch.setattr(settings, "NATS_REVOKE_ENABLED", True)

    async def _fail(*a, **k):
        raise ConnectionError("nats down")

    monkeypatch.setattr("nats.connect", _fail)
    result = asyncio.run(pub.publish_permissions_changed(user_id=7, reason="GRANT_REVOKED"))
    assert result is False  # best-effort: 예외 전파 없이 False
