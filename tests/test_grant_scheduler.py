"""FR-07 — per-grant 만료 스케줄러.

실제 APScheduler 발화(시간 경과)는 통합영역이므로, **fake 스케줄러**로 job 배선
(등록/취소/지평/무주입)과 콜백·부팅 복원(NFR-05)을 결정론적으로 검증한다.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base
from app.services import grant_scheduler as gs


class FakeScheduler:
    def __init__(self):
        self.jobs: dict = {}

    def add_job(self, func, trigger, run_date=None, args=None, id=None, replace_existing=False):
        self.jobs[id] = {"func": func, "trigger": trigger, "run_date": run_date, "args": args}

    def remove_job(self, job_id):
        if job_id not in self.jobs:
            raise Exception("no such job")
        del self.jobs[job_id]


def _now():
    return datetime.now(settings.tz).replace(tzinfo=None)


def teardown_function():
    gs.set_scheduler(None)  # 테스트 간 격리 — 전역 스케줄러 참조 복원


def test_should_schedule_date_job_when_future_expiry():
    fake = FakeScheduler()
    gs.set_scheduler(fake)
    now = _now()
    vu = now + timedelta(hours=2)
    assert gs.schedule_grant_expiry(1, user_id=7, valid_until=vu, now=now) is True
    job = fake.jobs["grant_expiry:1"]
    assert job["trigger"] == "date"
    assert job["run_date"] == vu
    assert job["args"] == [7]


def test_should_not_schedule_when_permanent_grant():
    fake = FakeScheduler()
    gs.set_scheduler(fake)
    assert gs.schedule_grant_expiry(1, user_id=7, valid_until=None) is False
    assert fake.jobs == {}


def test_should_not_schedule_when_already_expired():
    fake = FakeScheduler()
    gs.set_scheduler(fake)
    now = _now()
    assert gs.schedule_grant_expiry(1, user_id=7, valid_until=now - timedelta(hours=1), now=now) is False
    assert fake.jobs == {}


def test_should_cancel_job_when_revoked():
    fake = FakeScheduler()
    gs.set_scheduler(fake)
    now = _now()
    gs.schedule_grant_expiry(1, user_id=7, valid_until=now + timedelta(hours=2), now=now)
    assert gs.cancel_grant_expiry(1) is True
    assert "grant_expiry:1" not in fake.jobs


def test_should_be_noop_when_scheduler_not_injected():
    gs.set_scheduler(None)
    assert gs.schedule_grant_expiry(1, user_id=7, valid_until=_now() + timedelta(hours=2)) is False
    assert gs.cancel_grant_expiry(1) is False


def test_should_respect_horizon_when_set(monkeypatch):
    fake = FakeScheduler()
    gs.set_scheduler(fake)
    monkeypatch.setattr(settings, "GRANT_JOB_HORIZON_HOURS", 24)
    now = _now()
    assert gs.schedule_grant_expiry(1, user_id=7, valid_until=now + timedelta(hours=48), now=now) is False  # 지평 밖
    assert gs.schedule_grant_expiry(2, user_id=7, valid_until=now + timedelta(hours=12), now=now) is True   # 지평 내
    assert set(fake.jobs) == {"grant_expiry:2"}


def test_should_fire_grant_expired_publish_on_callback(monkeypatch):
    calls = []

    async def _spy(*, user_id, reason="PERMISSIONS_CHANGED"):
        calls.append((user_id, reason))
        return True

    monkeypatch.setattr("app.services.nats_revoke_publisher.publish_permissions_changed", _spy)
    asyncio.run(gs._fire_expiry(7))
    assert calls == [(7, "GRANT_EXPIRED")]


def test_should_reschedule_future_active_grants_on_boot(monkeypatch):
    """NFR-05 — 부팅 시 미래 만료 active grant 만 재등록(과거/회수/상시 제외)."""
    from app.models.user import AccountUser, UserGroup, UserGroupGrant
    from app.utils.auth import hash_password

    fake = FakeScheduler()
    gs.set_scheduler(fake)

    async def _scenario():
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        monkeypatch.setattr("app.database.AsyncSessionLocal", session_local)
        now = _now()
        async with session_local() as s:
            u = AccountUser(login_id="sch_u", password_hash=hash_password("pw123456"), name="u", role="USER")
            g = UserGroup(name="sch_g", permissions={"modules": {}})
            s.add_all([u, g])
            await s.commit()
            await s.refresh(u)
            await s.refresh(g)
            # 미래(재등록 대상) / 과거(제외) / 상시=None(제외) / 회수(제외)
            s.add_all([
                UserGroupGrant(user_id=u.id, group_id=g.id, valid_from=now - timedelta(hours=1),
                               valid_until=now + timedelta(hours=5), is_active=True),
                UserGroupGrant(user_id=u.id, group_id=g.id, valid_from=now - timedelta(hours=5),
                               valid_until=now - timedelta(hours=1), is_active=True),
                UserGroupGrant(user_id=u.id, group_id=g.id, valid_from=now - timedelta(hours=1),
                               valid_until=None, is_active=True),
                UserGroupGrant(user_id=u.id, group_id=g.id, valid_from=now - timedelta(hours=1),
                               valid_until=now + timedelta(hours=9), is_active=True,
                               revoked_at=now - timedelta(minutes=5)),
            ])
            await s.commit()
        n = await gs.reschedule_future_grants()
        await engine.dispose()
        return n

    n = asyncio.run(_scenario())
    assert n == 1                       # 미래 미회수분 1건만
    assert len(fake.jobs) == 1
