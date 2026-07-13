"""
Force-Logout Propagation (P1) tests.
PRD: docs/prds/PRD_GOP_Server_Force_Logout.md
TDD: Red -> Green -> Refactor

Phase 0a (FR-SVF-03): plain POST /auth/logout must blacklist the PAIRED
refresh token jti, not only the access jti — otherwise a self-logged-out
client can immediately call /auth/refresh to resurrect the session.
"""
import pytest
from fastapi.testclient import TestClient

from app.models.user import AccountUser
from app.utils.auth import hash_password


def _make_user(test_db, login_id="fl_user", role="OPERATOR"):
    user = AccountUser(
        login_id=login_id,
        password_hash=hash_password("test1234"),
        name="Force Logout User",
        role=role,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def _login(client, login_id="fl_user", password="test1234"):
    resp = client.post("/api/auth/login", json={"login_id": login_id, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()["data"]


class TestLogoutRefreshFamily:
    """FR-SVF-03: logout invalidates the access+refresh token family."""

    def test_should_reject_refresh_when_session_logged_out(self, client: TestClient, test_db):
        # Arrange — a logged-in user holding access + refresh tokens
        _make_user(test_db)
        tokens = _login(client)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Act — user logs out (only the access token is presented)
        logout = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout.status_code == 200, f"Logout failed: {logout.json()}"

        # Assert — the paired refresh token must no longer mint new tokens
        refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert refreshed.status_code == 401, (
            "Refresh token must be rejected after logout (FR-SVF-03 token-family "
            f"revocation), got {refreshed.status_code}: {refreshed.json()}"
        )


class TestLastAdminSessionGuard:
    """FR-SVF-09: force-logout must not revoke the last active ADMIN session."""

    def test_should_reject_force_logout_when_last_active_admin_session(self, client: TestClient, test_db):
        # Arrange — exactly one admin with an active session (no other admin logged in)
        _make_user(test_db, login_id="lone_admin", role="ADMIN")
        tokens = _login(client, login_id="lone_admin")
        sessions = client.get(
            "/api/user-sessions",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        ).json()["data"]
        session_id = sessions[0]["id"]

        # Act — try to force-logout that single active admin session
        resp = client.delete(f"/api/user-sessions/{session_id}")

        # Assert — must be refused to avoid locking every admin out
        assert resp.status_code == 409, (
            f"Force-logout of the last active ADMIN session must be 409, got "
            f"{resp.status_code}: {resp.json()}"
        )

    def test_should_allow_force_logout_when_another_admin_session_active(self, client: TestClient, test_db):
        # Arrange — two admins, both with active sessions
        _make_user(test_db, login_id="admin_a", role="ADMIN")
        _make_user(test_db, login_id="admin_b", role="ADMIN")
        tok_a = _login(client, login_id="admin_a")
        _login(client, login_id="admin_b")
        sessions_a = client.get(
            "/api/user-sessions",
            headers={"Authorization": f"Bearer {tok_a['access_token']}"},
        ).json()["data"]
        admin_a_session = next(s for s in sessions_a if s["login_id"] == "admin_a")["id"]

        # Act — force-logout admin_a while admin_b is still active
        resp = client.delete(f"/api/user-sessions/{admin_a_session}")

        # Assert — allowed; another active admin session remains
        assert resp.status_code == 200, (
            f"Force-logout should succeed when another admin session is active, got "
            f"{resp.status_code}: {resp.json()}"
        )

    def test_should_reject_bulk_force_logout_when_last_admin(self, client: TestClient, test_db):
        # Arrange — a single admin with an active session
        user = _make_user(test_db, login_id="bulk_admin", role="ADMIN")
        _login(client, login_id="bulk_admin")

        # Act — bulk force-logout all of that admin's sessions
        resp = client.delete(f"/api/user-sessions/user/{user.id}")

        # Assert — refused (would leave zero active admin sessions)
        assert resp.status_code == 409, (
            f"Bulk force-logout of the last admin's sessions must be 409, got "
            f"{resp.status_code}: {resp.json()}"
        )


class TestSessionIdentity:
    """FR-SVF-01/02: stable session_id (== UserSession.id) surfaced as both a
    response field and a JWT `sid` claim; sid stays fixed across refresh while jti rotates."""

    def test_should_return_session_id_matching_user_session_on_login(self, client: TestClient, test_db):
        from app.models.user import UserSession
        from app.utils.auth import decode_token

        user = _make_user(test_db, login_id="sid_user")
        data = _login(client, login_id="sid_user")

        # response carries session_id == the persisted UserSession.id
        assert "session_id" in data, "login response must include session_id (FR-SVF-01)"
        sess = test_db.query(UserSession).filter(UserSession.user_id == user.id).first()
        assert data["session_id"] == str(sess.id)

        # the access JWT carries a matching `sid` claim (FR-SVF-02)
        token_data = decode_token(data["access_token"])
        assert token_data.sid == data["session_id"]

    def test_should_embed_same_sid_in_access_and_refresh_tokens(self, client: TestClient, test_db):
        from app.utils.auth import decode_token

        _make_user(test_db, login_id="sid_pair")
        data = _login(client, login_id="sid_pair")

        access = decode_token(data["access_token"])
        refresh = decode_token(data["refresh_token"], expected_type="refresh")
        assert access.sid is not None
        assert access.sid == refresh.sid, "access and refresh of one login must share sid"

    def test_should_keep_session_id_stable_across_refresh(self, client: TestClient, test_db):
        from app.models.user import UserSession
        from app.utils.auth import decode_token

        _make_user(test_db, login_id="sid_refresh")
        data = _login(client, login_id="sid_refresh")
        old_sid = data["session_id"]
        old_access_jti = decode_token(data["access_token"]).jti

        refreshed = client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert refreshed.status_code == 200, f"Refresh failed: {refreshed.json()}"
        rdata = refreshed.json()["data"]

        # session_id is stable; jti rotated; sid preserved in the new token
        assert rdata["session_id"] == old_sid, "session_id must NOT rotate on refresh"
        new = decode_token(rdata["access_token"])
        assert new.jti != old_access_jti, "access jti must rotate on refresh"
        assert new.sid == old_sid, "sid must be carried forward into the refreshed token"

        # the UserSession row is re-bound to the new token pair (no orphan)
        test_db.expire_all()
        sess = test_db.query(UserSession).filter(UserSession.id == int(old_sid)).first()
        assert sess.token == rdata["access_token"], "UserSession.token must track the refreshed access token"


class TestForceLogoutE2E:
    """NFR-SVF-01/02: force_logout revokes the access+refresh family and survives a restart."""

    def _admin_and_victim(self, client, test_db):
        # keep one admin logged in so the last-ADMIN guard never blocks; victim is a VIEWER
        _make_user(test_db, login_id="e2e_keep_admin", role="ADMIN")
        admin = _login(client, login_id="e2e_keep_admin")
        _make_user(test_db, login_id="e2e_victim", role="VIEWER")
        victim = _login(client, login_id="e2e_victim")
        sessions = client.get(
            "/api/user-sessions",
            headers={"Authorization": f"Bearer {admin['access_token']}"},
        ).json()["data"]
        vid = next(s for s in sessions if s["login_id"] == "e2e_victim")["id"]
        return admin, victim, vid

    def test_force_logout_revokes_access_and_refresh_family(self, client: TestClient, test_db):
        from app.utils.auth import decode_token
        from app.services.token_blacklist_service import is_blacklisted

        admin, victim, vid = self._admin_and_victim(client, test_db)
        resp = client.delete(
            f"/api/user-sessions/{vid}",
            headers={"Authorization": f"Bearer {admin['access_token']}"},
        )
        assert resp.status_code == 200, resp.json()

        # access jti is blacklisted (the exact check get_current_account_user enforces → 401)
        access_jti = decode_token(victim["access_token"]).jti
        assert is_blacklisted(test_db, access_jti) is True
        # refresh of the revoked family is rejected end-to-end
        rf = client.post("/api/auth/refresh", json={"refresh_token": victim["refresh_token"]})
        assert rf.status_code == 401

    def test_revocation_survives_cache_clear(self, client: TestClient, test_db):
        from app.utils.auth import decode_token
        from app.services import token_blacklist_service as tbs

        admin, victim, vid = self._admin_and_victim(client, test_db)
        client.delete(
            f"/api/user-sessions/{vid}",
            headers={"Authorization": f"Bearer {admin['access_token']}"},
        )
        access_jti = decode_token(victim["access_token"]).jti

        # simulate restart: in-memory cache empty, DB persists → still revoked (NFR-SVF-02)
        tbs._cache.clear()
        assert tbs.is_blacklisted(test_db, access_jti) is True


class TestRevoked401Code:
    """FR-SVF-10: revoked session → 401 with stable machine-readable error.code SESSION_REVOKED,
    distinct from a generic UNAUTHORIZED, so the client branches on code (not the message string)."""

    def test_revoked_refresh_returns_session_revoked_code(self, client: TestClient, test_db):
        _make_user(test_db, login_id="code_user")
        tokens = _login(client, login_id="code_user")
        client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tokens['access_token']}"})

        resp = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "SESSION_REVOKED"

    def test_invalid_refresh_keeps_generic_unauthorized(self, client: TestClient, test_db):
        # a malformed/invalid token is NOT a revocation → must stay generic UNAUTHORIZED
        resp = client.post("/api/auth/refresh", json={"refresh_token": "garbage.token.value"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    def test_get_current_account_user_raises_session_revoked_on_blacklisted_access(self, test_db):
        import asyncio
        from fastapi.security import HTTPAuthorizationCredentials
        from datetime import datetime, timedelta
        from app.routers.auth import get_current_account_user
        from app.exceptions import RevokedTokenError
        from app.models.user import AccountUser
        from app.utils.auth import hash_password, create_access_token, decode_token
        from app.services.token_blacklist_service import add_to_blacklist

        user = AccountUser(login_id="code_access", password_hash=hash_password("x"),
                           name="Code Access", role="VIEWER", is_active=True)
        test_db.add(user); test_db.commit()
        token = create_access_token(data={"sub": "code_access"})
        jti = decode_token(token).jti
        add_to_blacklist(db=test_db, jti=jti, expires_at=datetime.utcnow() + timedelta(hours=1),
                         reason="FORCED", user_id=user.id, token_type="access")

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(RevokedTokenError) as ei:
            asyncio.run(get_current_account_user(credentials=creds, db=test_db))
        assert ei.value.code == "SESSION_REVOKED"
