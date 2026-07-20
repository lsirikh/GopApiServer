"""FR-02 — token 모드 grant 집행 (전역 enforce_matrix 경로).

`enforce_matrix` 는 모든 HTTP 요청이 통과하는 전역 choke point(main.py:427)다.
본 테스트는 **실 Request + 실 AsyncSession(격리 aiosqlite)** 으로 enforce_matrix 를 구동해
grant 수명주기별 집행을 검증한다 — 전송/라우팅까지의 full TestClient E2E 는 dual-stack
sqlite 취약성이 있어, 집행 본질인 enforce_matrix 를 직접 태우는 방식으로 대체(SETUP-02 대체).

대상: POST /api/devices/cameras → (cameras, edit)  [VER-02 확정]
경계초(valid_until==now, 마이크로초)의 결정론 검증은 TEST-01(now 주입)이 담당한다.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base
from app.utils.auth import create_access_token, hash_password

TARGET_METHOD = "POST"
TARGET_PATH = "/api/devices/cameras"  # → cameras:edit


def _now():
    return datetime.now(settings.tz).replace(tzinfo=None)


def _req(method: str, path: str, login_id: str | None):
    headers = []
    if login_id is not None:
        token = create_access_token(data={"sub": login_id})
        headers.append((b"authorization", b"Bearer " + token.encode()))
    scope = {
        "type": "http", "method": method, "headers": headers,
        "route": SimpleNamespace(path=path), "query_string": b"",
    }
    return Request(scope)


def _enforce(*, user_role="USER", grant=None, send_token=True, login_id="g2_user"):
    """격리 aiosqlite 에 사용자(권한없는 등급) + 선택 grant 시드 후 enforce_matrix 실행.

    grant = (valid_from, valid_until, is_active, revoked_at) | None
    반환: "ALLOW" (통과) | int(HTTP status, 예외 시)
    """
    async def _inner():
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            from app.models.user import AccountUser, UserGroup, UserGroupGrant
            async with session_local() as s:
                role_group = UserGroup(name=user_role, permissions={"modules": {}})  # 권한 없음
                user = AccountUser(login_id=login_id, password_hash=hash_password("pw123456"),
                                   name="u", role=user_role, is_active=True)
                s.add_all([role_group, user])
                await s.commit()
                await s.refresh(user)
                if grant is not None:
                    vf, vu, is_active, revoked = grant
                    gg = UserGroup(name="grant_cam", permissions={"modules": {"cameras": {"edit": True}}})
                    s.add(gg)
                    await s.commit()
                    await s.refresh(gg)
                    s.add(UserGroupGrant(user_id=user.id, group_id=gg.id,
                                         valid_from=vf, valid_until=vu,
                                         is_active=is_active, revoked_at=revoked))
                    await s.commit()

                from app.security.matrix_enforcer import enforce_matrix
                req = _req(TARGET_METHOD, TARGET_PATH, login_id if send_token else None)
                try:
                    await enforce_matrix(req, s)
                    return "ALLOW"
                except HTTPException as e:
                    return e.status_code
        finally:
            await engine.dispose()

    return asyncio.run(_inner())


@pytest.fixture
def token_mode(monkeypatch):
    """AUTH_MODE=token 로 전역 집행 활성 (테스트 후 자동 복원)."""
    monkeypatch.setattr(settings, "AUTH_MODE", "token")


def test_should_allow_when_grant_valid(token_mode):
    now = _now()
    assert _enforce(grant=(now - timedelta(hours=1), now + timedelta(hours=10), True, None)) == "ALLOW"


def test_should_403_when_grant_expired(token_mode):
    now = _now()
    # is_active=True(스윕 미실행)라도 만료면 차단 — 요청시점 권위(NFR-01)
    assert _enforce(grant=(now - timedelta(hours=5), now - timedelta(hours=1), True, None)) == 403


def test_should_403_when_grant_revoked(token_mode):
    now = _now()
    assert _enforce(grant=(now - timedelta(hours=1), now + timedelta(hours=10), True, now - timedelta(minutes=5))) == 403


def test_should_403_when_grant_pending(token_mode):
    now = _now()
    assert _enforce(grant=(now + timedelta(hours=2), now + timedelta(hours=10), True, None)) == 403


def test_should_403_when_no_grant_and_role_lacks_permission(token_mode):
    assert _enforce(grant=None) == 403


def test_should_allow_when_admin_regardless_of_grant(token_mode):
    assert _enforce(user_role="ADMIN", grant=None) == "ALLOW"


def test_should_401_when_no_token(token_mode):
    assert _enforce(grant=None, send_token=False) == 401
