"""FR-01 — 경계초(valid_until == now) 삼중 인코딩 회귀 테스트.

grant 유효성 술어가 세 곳에 병렬 존재(4-b):
  - grant_status / is_valid_now      (app/services/grant_service.py, 순수함수)
  - _active_grants (sync)            (app/routers/auth.py:147-152)
  - _active_grants_async (async)     (app/routers/auth.py:942-960)
경계초(valid_until == now)에서 셋이 **동일하게 차단(EXPIRED)** 함을 못박아, 한 곳만
수정돼도 회귀가 잡히게 한다. 좌경계(valid_from == now)는 즉시 유효(포함)임도 검증.

- 결정론(NFR-02): 고정 now 주입 — 실시간 clock/sleep 미사용.
- 안전(NFR-03): async 술어는 앱 prod DB가 아니라 **로컬 aiosqlite in-memory** 로 자체 완결.
- 근거: docs/Analysis/grant-enforcement-sim/SIMULATION_REPORT.md Unit A (48/48 PASS).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.user import AccountUser, UserGroup, UserGroupGrant
from app.routers.auth import _active_grants, _active_grants_async
from app.services.grant_service import (
    grant_status, is_valid_now, STATUS_ACTIVE, STATUS_EXPIRED,
)
from app.utils.auth import hash_password

# 고정 시각 — 결정론(NFR-02). 시뮬 harness와 동일 값.
FIXED_NOW = datetime(2026, 7, 21, 12, 0, 0)
ONE_HOUR = timedelta(hours=1)


class _FakeGrant:
    """grant_status/is_valid_now(순수함수)용 최소 duck-type."""
    def __init__(self, revoked_at, valid_from, valid_until):
        self.revoked_at = revoked_at
        self.valid_from = valid_from
        self.valid_until = valid_until


def _seed_grant_sync(db, valid_from, valid_until, is_active=True, revoked_at=None):
    """sync 세션에 사용자+그룹+grant 시드 후 (user, grant) 반환."""
    user = AccountUser(login_id="bnd_user", password_hash=hash_password("pw123456"),
                       name="경계사용자", role="USER")
    group = UserGroup(name="bnd_grp", permissions={"modules": {"cameras": {"control": True}}})
    db.add_all([user, group])
    db.commit()
    db.refresh(user)
    db.refresh(group)
    grant = UserGroupGrant(user_id=user.id, group_id=group.id,
                           valid_from=valid_from, valid_until=valid_until,
                           is_active=is_active, revoked_at=revoked_at)
    db.add(grant)
    db.commit()
    db.refresh(grant)
    return user, grant


def _count_active_grants_async(valid_from, valid_until, now, is_active=True, revoked_at=None):
    """로컬 aiosqlite in-memory 에서 _active_grants_async 를 실행해 유효 grant 수 반환.

    앱 prod AsyncSessionLocal 을 쓰지 않으므로 운영/공유 DB 무접촉(NFR-03).
    pytest-asyncio 설정 의존을 피하려 sync 컨텍스트에서 asyncio.run 으로 구동.
    """
    async def _inner() -> int:
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with Session() as s:
                user = AccountUser(login_id="bnd_user_a", password_hash=hash_password("pw123456"),
                                   name="경계사용자a", role="USER")
                group = UserGroup(name="bnd_grp_a",
                                  permissions={"modules": {"cameras": {"control": True}}})
                s.add_all([user, group])
                await s.commit()
                await s.refresh(user)
                await s.refresh(group)
                grant = UserGroupGrant(user_id=user.id, group_id=group.id,
                                       valid_from=valid_from, valid_until=valid_until,
                                       is_active=is_active, revoked_at=revoked_at)
                s.add(grant)
                await s.commit()
                rows = await _active_grants_async(s, user, now=now)
                return len(rows)
        finally:
            await engine.dispose()

    return asyncio.run(_inner())


# ─────────────────────────── 순수함수(grant_status) ───────────────────────────

def test_should_expire_when_valid_until_equals_now():
    grant = _FakeGrant(None, FIXED_NOW - ONE_HOUR, FIXED_NOW)
    assert grant_status(grant, FIXED_NOW) == STATUS_EXPIRED
    assert is_valid_now(grant, FIXED_NOW) is False


def test_should_activate_when_valid_from_equals_now():
    grant = _FakeGrant(None, FIXED_NOW, None)
    assert grant_status(grant, FIXED_NOW) == STATUS_ACTIVE
    assert is_valid_now(grant, FIXED_NOW) is True


# ─────────────────────────── sync _active_grants ───────────────────────────

def test_should_exclude_from_active_grants_when_valid_until_equals_now(db_session):
    user, _ = _seed_grant_sync(db_session, FIXED_NOW - ONE_HOUR, FIXED_NOW, is_active=True)
    assert _active_grants(db_session, user, now=FIXED_NOW) == []


def test_should_ignore_is_active_flag_when_boundary(db_session):
    # is_active=True(스윕 미실행)라도 경계초면 차단 — 집행은 is_active 비의존(NFR-01).
    user, _ = _seed_grant_sync(db_session, FIXED_NOW - ONE_HOUR, FIXED_NOW, is_active=True)
    assert _active_grants(db_session, user, now=FIXED_NOW) == []


def test_should_include_active_grant_when_valid_from_equals_now(db_session):
    user, _ = _seed_grant_sync(db_session, FIXED_NOW, None, is_active=True)
    rows = _active_grants(db_session, user, now=FIXED_NOW)
    assert len(rows) == 1  # 좌경계 포함 — valid_from 부터 유효


# ─────────────────────── async _active_grants_async (삼중 정합) ───────────────────────

def test_should_exclude_when_valid_until_equals_now_async():
    # sync 와 동일 술어 → 경계초 차단이 async 에서도 성립(삼중 정합).
    assert _count_active_grants_async(FIXED_NOW - ONE_HOUR, FIXED_NOW, FIXED_NOW) == 0


def test_should_include_when_valid_from_equals_now_async():
    assert _count_active_grants_async(FIXED_NOW, None, FIXED_NOW) == 1
