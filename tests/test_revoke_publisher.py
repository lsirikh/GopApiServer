"""
NATS revoke publisher (P1 Phase 3) tests.
PRD: docs/prds/PRD_GOP_Server_Force_Logout.md (FR-SVF-05/07/11)

The publisher is gated behind settings.NATS_REVOKE_ENABLED (default False) and is
best-effort: a NATS failure must NEVER raise into force_logout (the DB blacklist is
the authority, FR-SVF-11). Subject is per-session (C2), never a wide all.> subject.
"""
import asyncio
import pytest

from app.config import settings
from app.utils.enums import EnumLogoutReason
from app.utils.revoke_signing import verify_revoke
from app.services import nats_revoke_publisher as pub


class TestRevokeSubject:
    def test_subject_is_per_session_and_not_broadcast(self):
        subject = pub.revoke_subject(user_id=7, session_id=42)
        assert subject == f"sensorway.{settings.NATS_UNIT_ID}.account.7.session.42.revoke"
        assert ".all." not in subject and not subject.endswith(".>")


class TestBuildRevokeMessage:
    def test_message_is_signed_and_complete(self):
        msg = pub.build_revoke_message(
            user_id=7, session_id=42, jti="j1", reason=EnumLogoutReason.FORCED,
        )
        for field in ("message_id", "session_id", "jti", "user_id", "reason", "issued_at", "signature"):
            assert field in msg
        assert msg["session_id"] == "42"
        assert msg["reason"] == "FORCED"
        # signature verifies with the configured signing key
        assert verify_revoke(msg, settings.REVOKE_SIGNING_KEY) is True


class TestPublishBestEffort:
    def test_returns_false_when_disabled(self, monkeypatch):
        # default off: must NOT attempt to connect, just return False
        monkeypatch.setattr(settings, "NATS_REVOKE_ENABLED", False)

        async def _boom(*a, **k):
            raise AssertionError("connect must not be called when disabled")

        monkeypatch.setattr("nats.connect", _boom)
        result = asyncio.run(pub.publish_session_revoke(
            user_id=7, session_id=42, jti="j1", reason=EnumLogoutReason.FORCED))
        assert result is False

    def test_swallows_connection_errors_when_enabled(self, monkeypatch):
        # enabled but NATS down: best-effort → returns False, never raises
        monkeypatch.setattr(settings, "NATS_REVOKE_ENABLED", True)

        async def _fail(*a, **k):
            raise ConnectionError("nats down")

        monkeypatch.setattr("nats.connect", _fail)
        result = asyncio.run(pub.publish_session_revoke(
            user_id=7, session_id=42, jti="j1", reason=EnumLogoutReason.FORCED))
        assert result is False  # did not raise


class TestForceLogoutWiring:
    """force_logout 핸들러가 publisher 를 올바른 인자로 호출하고, 발행 실패에도 200 을 유지(FR-SVF-11)."""

    def _viewer_session(self, test_db):
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password
        from app.config import settings as _s
        from datetime import datetime, timedelta

        target = AccountUser(login_id="wire_viewer", password_hash=hash_password("x"),
                             name="Wire Viewer", role="VIEWER", is_active=True)
        test_db.add(target); test_db.commit(); test_db.refresh(target)
        sess = UserSession(user_id=target.id, token="wire_tok", refresh_token="wire_ref",
                           ip_address="127.0.0.1",
                           expires_at=datetime.now(_s.tz) + timedelta(hours=1), is_active=True)
        test_db.add(sess); test_db.commit(); test_db.refresh(sess)
        return sess

    def test_force_logout_invokes_publisher_with_session_id(self, client, test_db, monkeypatch):
        calls = []

        async def _spy(**kwargs):
            calls.append(kwargs)
            return True

        monkeypatch.setattr(pub, "publish_session_revoke", _spy)
        sess = self._viewer_session(test_db)

        resp = client.delete(f"/api/user-sessions/{sess.id}")
        assert resp.status_code == 200, resp.json()
        assert len(calls) == 1
        assert str(calls[0]["session_id"]) == str(sess.id)
        assert calls[0]["user_id"] == sess.user_id

    def test_force_logout_succeeds_when_publish_enabled_but_nats_down(self, client, test_db, monkeypatch):
        from app.config import settings as _s
        monkeypatch.setattr(_s, "NATS_REVOKE_ENABLED", True)

        async def _fail(*a, **k):
            raise ConnectionError("nats down")

        monkeypatch.setattr("nats.connect", _fail)
        sess = self._viewer_session(test_db)

        resp = client.delete(f"/api/user-sessions/{sess.id}")
        assert resp.status_code == 200, resp.json()  # best-effort: 발행 실패가 막지 않음
