"""FR-04 — run_grant_sweep(async) 발행/감사 오케스트레이션 검증.

RISK-02: run_grant_sweep 은 자체 `AsyncSessionLocal`(앱 async 엔진)을 열므로(grant_service.py:82),
테스트에서는 `app.database.AsyncSessionLocal` 을 **격리 aiosqlite sessionmaker 로 몽키패치**해
운영/공유 DB 접촉 없이 검증한다(V-04 확인 결과).

검증:
- 만료 grant 의 is_active=False 로 내림 + GRANT_EXPIRED 감사 기록 (표시/통지용, 보안 비의존)
- 영향 사용자별 publish_permissions_changed 를 **사용자당 1회(dedup)** 호출
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base


def _now():
    return datetime.now(settings.tz).replace(tzinfo=None)


async def _make_isolated_sessionmaker():
    """격리 aiosqlite 엔진 + sessionmaker (StaticPool 로 :memory: 유지)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _seed_user_grant(session_local, login_id, valid_until_delta):
    from app.models.user import AccountUser, UserGroup, UserGroupGrant
    from app.utils.auth import hash_password

    async with session_local() as s:
        user = AccountUser(login_id=login_id, password_hash=hash_password("pw123456"),
                           name="u", role="USER")
        group = UserGroup(name=f"grp_{login_id}", permissions={"modules": {}})
        s.add_all([user, group])
        await s.commit()
        await s.refresh(user)
        await s.refresh(group)
        now = _now()
        grant = UserGroupGrant(
            user_id=user.id, group_id=group.id,
            valid_from=now - timedelta(days=2),
            valid_until=now + valid_until_delta,
            is_active=True,
        )
        s.add(grant)
        await s.commit()
        await s.refresh(grant)
        return user.id, grant.id


def test_should_deactivate_and_audit_when_run_sweep(monkeypatch):
    from app.models.user import UserGroupGrant
    from app.models.audit_log import AuditLog
    import app.services.grant_service as gs

    async def _scenario():
        engine, session_local = await _make_isolated_sessionmaker()
        # RISK-02: run_grant_sweep 이 여는 자체 세션을 격리 DB 로 강제
        monkeypatch.setattr("app.database.AsyncSessionLocal", session_local)
        try:
            _, expired_id = await _seed_user_grant(session_local, "sw_exp", -timedelta(days=1))  # 만료
            _, live_id = await _seed_user_grant(session_local, "sw_live", timedelta(days=10))     # 유효

            n = await gs.run_grant_sweep()

            async with session_local() as s:
                exp = (await s.execute(select(UserGroupGrant).where(UserGroupGrant.id == expired_id))).scalars().first()
                live = (await s.execute(select(UserGroupGrant).where(UserGroupGrant.id == live_id))).scalars().first()
                audits = (await s.execute(select(AuditLog).where(AuditLog.action_type == "GRANT_EXPIRED"))).scalars().all()
            assert exp.is_active is False   # 만료분 내림
            assert live.is_active is True   # 유효분 불변
            assert len(audits) == 1         # GRANT_EXPIRED 감사 1건
            return n
        finally:
            await engine.dispose()

    assert asyncio.run(_scenario()) == 1


def test_should_publish_once_per_user_when_sweep(monkeypatch):
    import app.services.grant_service as gs

    calls: list[int] = []

    async def _spy(*, user_id, reason="PERMISSIONS_CHANGED"):
        calls.append(user_id)
        return True

    async def _scenario():
        engine, session_local = await _make_isolated_sessionmaker()
        monkeypatch.setattr("app.database.AsyncSessionLocal", session_local)
        # 발행기 스파이 — run_grant_sweep 이 lazy import 하는 모듈 심볼을 패치
        monkeypatch.setattr("app.services.nats_revoke_publisher.publish_permissions_changed", _spy)
        try:
            # 사용자 A 에 만료 grant 2개 + 사용자 B 에 만료 grant 1개 → 발행은 사용자당 1회여야
            a1_user, _ = await _seed_user_grant(session_local, "sw_a", -timedelta(days=1))
            # 같은 사용자 A 에 두 번째 만료 grant
            from app.models.user import UserGroup, UserGroupGrant
            async with session_local() as s:
                g2 = UserGroup(name="grp_a2", permissions={"modules": {}})
                s.add(g2)
                await s.commit()
                await s.refresh(g2)
                now = _now()
                s.add(UserGroupGrant(user_id=a1_user, group_id=g2.id,
                                     valid_from=now - timedelta(days=2),
                                     valid_until=now - timedelta(days=1), is_active=True))
                await s.commit()
            b_user, _ = await _seed_user_grant(session_local, "sw_b", -timedelta(days=1))

            await gs.run_grant_sweep()
            return a1_user, b_user
        finally:
            await engine.dispose()

    a_user, b_user = asyncio.run(_scenario())
    assert len(calls) == 2                     # 사용자당 1회 (A 2 grant → 1회 dedup, B → 1회)
    assert set(calls) == {a_user, b_user}
