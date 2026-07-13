"""
매트릭스 중앙 집행 테스트 — "권한 매트릭스 = 미들웨어" 방향
WS-B / 사용자 결정 2026-06-30

permission_map(중앙 맵) + matrix_enforcer(단일 집행점) 검증.
"""
import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.config import settings


def _run(coro):
    return asyncio.run(coro)


def _req(method, path, token=None):
    headers = []
    if token:
        headers.append((b"authorization", b"Bearer " + token.encode()))
    scope = {
        "type": "http",
        "method": method,
        "headers": headers,
        "route": SimpleNamespace(path=path),
        "query_string": b"",
    }
    return Request(scope)


def _make_user(db, role, role_perms, login_id):
    from app.models.user import AccountUser, UserGroup
    from app.utils.auth import hash_password

    rg = UserGroup(name=role, permissions=role_perms)
    u = AccountUser(login_id=login_id, password_hash=hash_password("pw123456"),
                    name="u", role=role, is_active=True)
    db.add_all([rg, u])
    db.commit()
    db.refresh(u)
    return u


def _token(login_id):
    from app.utils.auth import create_access_token
    return create_access_token(data={"sub": login_id})


# ── 중앙 맵 단위 ─────────────────────────────────────────────
class TestPermissionMap:
    def test_should_map_camera_create_to_cameras_edit(self):
        from app.security.permission_map import lookup_permission
        assert lookup_permission("POST", "/api/devices/cameras") == ("cameras", "edit")

    def test_should_normalize_path_params(self):
        from app.security.permission_map import lookup_permission
        assert lookup_permission("DELETE", "/api/devices/cameras/{camera_id}") == ("cameras", "delete")

    def test_should_return_none_for_unmapped(self):
        from app.security.permission_map import lookup_permission
        assert lookup_permission("GET", "/api/devices/cameras") is None
        assert lookup_permission("POST", "/api/auth/login") is None


# ── 집행기 ───────────────────────────────────────────────────
class TestMatrixEnforcer:
    def test_should_be_dormant_when_public(self, db_session, monkeypatch):
        from app.security.matrix_enforcer import enforce_matrix
        monkeypatch.setattr(settings, "AUTH_MODE", "public")
        # 토큰 없이 매핑된 쓰기 경로 → 휴면이라 예외 없음(현 동작 보존)
        _run(enforce_matrix(_req("POST", "/api/devices/cameras"), db_session))

    def test_should_deny_when_role_lacks_permission(self, db_session, monkeypatch):
        from app.security.matrix_enforcer import enforce_matrix
        monkeypatch.setattr(settings, "AUTH_MODE", "token")
        _make_user(db_session, "VIEWER", {"modules": {}}, "enf_viewer")
        req = _req("POST", "/api/devices/cameras", _token("enf_viewer"))
        with pytest.raises(HTTPException) as ei:
            _run(enforce_matrix(req, db_session))
        assert ei.value.status_code == 403

    def test_should_401_when_no_token_in_token_mode(self, db_session, monkeypatch):
        from app.security.matrix_enforcer import enforce_matrix
        monkeypatch.setattr(settings, "AUTH_MODE", "token")
        with pytest.raises(HTTPException) as ei:
            _run(enforce_matrix(_req("POST", "/api/devices/cameras"), db_session))
        assert ei.value.status_code == 401

    def test_should_bypass_when_admin(self, db_session, monkeypatch):
        from app.security.matrix_enforcer import enforce_matrix
        monkeypatch.setattr(settings, "AUTH_MODE", "token")
        _make_user(db_session, "ADMIN", {"modules": {}}, "enf_admin")
        # ADMIN 은 매트릭스 무관 통과(예외 없음)
        _run(enforce_matrix(_req("POST", "/api/devices/cameras", _token("enf_admin")), db_session))

    def test_should_allow_unmapped_route_in_token_mode(self, db_session, monkeypatch):
        from app.security.matrix_enforcer import enforce_matrix
        monkeypatch.setattr(settings, "AUTH_MODE", "token")
        _make_user(db_session, "VIEWER", {"modules": {}}, "enf_unmapped")
        # 미등록 경로(GET) → 요구 없음, 예외 없음
        _run(enforce_matrix(_req("GET", "/api/devices/cameras", _token("enf_unmapped")), db_session))

    def test_should_allow_when_grant_adds_permission(self, db_session, monkeypatch):
        from app.security.matrix_enforcer import enforce_matrix
        from app.models.user import UserGroup, UserGroupGrant
        monkeypatch.setattr(settings, "AUTH_MODE", "token")
        user = _make_user(db_session, "VIEWER", {"modules": {}}, "enf_grantee")
        gg = UserGroup(name="임시카메라", permissions={"modules": {"cameras": {"edit": True}}})
        db_session.add(gg)
        db_session.commit()
        db_session.refresh(gg)
        now = datetime.now(settings.tz).replace(tzinfo=None)
        db_session.add(UserGroupGrant(user_id=user.id, group_id=gg.id,
                                      valid_from=now - timedelta(hours=1),
                                      valid_until=now + timedelta(hours=10)))
        db_session.commit()
        # grant 합집합으로 cameras:edit 획득 → 통과(예외 없음)
        _run(enforce_matrix(_req("POST", "/api/devices/cameras", _token("enf_grantee")), db_session))
