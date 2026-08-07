"""억제 PATCH delta + NATS 싱크 상태 테스트.

두 PRD 를 함께 커버한다:
- **하드닝 FR-01**: junction 통째 재대입 → UNIQUE 위반 500 회귀 방지 (PATCH delta 전환)
- **sync-message FR-06**: `notified_status` 백스톱 재조정 / 멱등 / 취소 확정

DB 트리거·NATS 발행 자체는 PostgreSQL 전용이라 여기서 검증하지 않는다(라이브 E2E 담당).
여기서는 **트리거를 태우는 쪽 = 애플리케이션이 만드는 UPDATE** 가 정확한지 본다.

실행: env -u DATABASE_URL python -m pytest tests/test_event_suppression_sync.py -v
"""
from datetime import timedelta

import pytest
from sqlalchemy import select

import app.models  # noqa: F401 — 모델 등록(Base.metadata) 보장
from app.models.event_suppression import (
    EventSuppressionSchedule, EventSuppressionTargetDevice, EventSuppressionTargetGroup,
)
from app.utils.datetime import utc_now
from app.utils.enums import (
    EnumSuppressionTargetType, EnumSuppressionSide, EnumSuppressionEventScope,
    EnumSuppressionStatus,
)
from app.services import event_suppression_service as svc


async def _seed_devices(async_db, ids):
    """라우터의 `_assert_devices_exist` 를 통과시키기 위해 실제 Device 행을 시드한다."""
    from app.models.device import Device, Controller

    existing = set(
        (await async_db.execute(select(Device.id).where(Device.id.in_(ids)))).scalars().all()
    )
    for i in ids:
        if i in existing:
            continue
        # 조인상속 서브클래스(Controller)로 생성 — base Device 직접 생성은 polymorphic identity 경고 발생.
        # Sensor 는 controller_id NOT NULL 이라 부모가 필요해 Controller 를 쓴다(대상 존재 검증만이 목적).
        async_db.add(Controller(
            id=i, number_device=i, group_device=0,
            name_device=f"dev-{i}", type_device="Controller",
            ip_address=f"10.0.0.{i % 250 + 1}", ip_port=80,
        ))
    await async_db.commit()


async def _add(async_db, target_device_ids=None, target_group_ids=None, **kw):
    """테스트 헬퍼 — 억제 스케줄 1건 생성(대상은 junction)."""
    now = utc_now()
    base = dict(
        name="t", target_type=EnumSuppressionTargetType.DEVICE,
        target_side=EnumSuppressionSide.BOTH, event_scope=EnumSuppressionEventScope.DETECTION,
        window_start=now - timedelta(hours=1), window_end=now + timedelta(hours=1),
    )
    base.update(kw)
    if target_device_ids:
        await _seed_devices(async_db, target_device_ids)
    s = EventSuppressionSchedule(**base)
    s.target_devices = [EventSuppressionTargetDevice(device_id=d) for d in (target_device_ids or [])]
    s.target_groups = [EventSuppressionTargetGroup(group_id=g) for g in (target_group_ids or [])]
    async_db.add(s)
    await async_db.commit()
    return s


class _SessionCtx:
    """AsyncSessionLocal 대체 — 격리 async_db 를 그대로 돌려준다(운영 DB 무접촉)."""

    def __init__(self, db):
        self._db = db

    async def __aenter__(self):
        return self._db

    async def __aexit__(self, *a):
        return False


# ───────── 하드닝 FR-01: PATCH junction delta (UNIQUE 위반 500 회귀) ─────────
#
# 배경: junction 컬렉션을 통째 재대입하면 delete-orphan DELETE 보다 INSERT 가 먼저 나가
#   uq_suppression_target_* 를 위반해 500 이 났다. 대상 배열 미제공 PATCH 는 기존 ids 를
#   그대로 복원하므로 **이름만 바꿔도** 겹침 100% → 500 이었다. delta 전환으로 원천 차단.

@pytest.mark.asyncio
async def test_should_patch_name_when_device_targets_unchanged(async_db):
    """대상 배열 미제공 PATCH(이름만) — 과거 500 이던 가장 흔한 케이스."""
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleUpdate

    sched = await _add(async_db, target_device_ids=[11, 12])
    patched = await r.patch_suppression_schedule(
        sched.id, EventSuppressionScheduleUpdate(name="renamed"), current_user=None, db=async_db)
    assert patched.data.name == "renamed"
    assert sorted(patched.data.target_device_ids) == [11, 12]


@pytest.mark.asyncio
async def test_should_patch_targets_when_ids_overlap(async_db):
    """대상 추가 [11,12] → [11,12,13] — 겹치는 11·12 가 UNIQUE 를 위반하던 케이스."""
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleUpdate

    sched = await _add(async_db, target_device_ids=[11, 12])
    await _seed_devices(async_db, [13])
    patched = await r.patch_suppression_schedule(
        sched.id, EventSuppressionScheduleUpdate(target_device_ids=[11, 12, 13]),
        current_user=None, db=async_db)
    assert sorted(patched.data.target_device_ids) == [11, 12, 13]


@pytest.mark.asyncio
async def test_should_patch_targets_when_ids_partially_removed(async_db):
    """대상 축소 [11,12] → [11] — 유지되는 11 이 겹침."""
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleUpdate

    sched = await _add(async_db, target_device_ids=[11, 12])
    patched = await r.patch_suppression_schedule(
        sched.id, EventSuppressionScheduleUpdate(target_device_ids=[11]),
        current_user=None, db=async_db)
    assert patched.data.target_device_ids == [11]


@pytest.mark.asyncio
async def test_should_patch_targets_when_ids_disjoint(async_db):
    """완전 교체 [11] → [12] (겹침 0) — 수정 전에도 통과하던 유일한 케이스, 회귀 방지."""
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleUpdate

    sched = await _add(async_db, target_device_ids=[11])
    await _seed_devices(async_db, [12])
    patched = await r.patch_suppression_schedule(
        sched.id, EventSuppressionScheduleUpdate(target_device_ids=[12]),
        current_user=None, db=async_db)
    assert patched.data.target_device_ids == [12]


@pytest.mark.asyncio
async def test_should_patch_group_targets_when_ids_overlap(async_db):
    """group 모드도 동일 결함이었다 — 겹치는 그룹 id 유지 PATCH."""
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleUpdate
    from app.models.device_group import DeviceGroup

    g1, g2 = DeviceGroup(name="G-sync1"), DeviceGroup(name="G-sync2")
    async_db.add_all([g1, g2])
    await async_db.commit()
    await async_db.refresh(g1)
    await async_db.refresh(g2)

    sched = await _add(async_db, target_type=EnumSuppressionTargetType.GROUP,
                       target_group_ids=[g1.id])
    patched = await r.patch_suppression_schedule(
        sched.id, EventSuppressionScheduleUpdate(target_group_ids=[g1.id, g2.id]),
        current_user=None, db=async_db)
    assert sorted(patched.data.target_group_ids) == sorted([g1.id, g2.id])


@pytest.mark.asyncio
async def test_should_keep_targets_when_patch_window_only(async_db):
    """창 시간만 변경 — 대상 유지 + 500 아님."""
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleUpdate

    sched = await _add(async_db, target_device_ids=[11, 12])
    now = utc_now()
    patched = await r.patch_suppression_schedule(
        sched.id, EventSuppressionScheduleUpdate(
            window_start=now - timedelta(minutes=5), window_end=now + timedelta(hours=3)),
        current_user=None, db=async_db)
    assert sorted(patched.data.target_device_ids) == [11, 12]


def test_should_reuse_existing_rows_when_sync_targets_overlap():
    """_sync_targets 단위 — 겹치는 행은 **동일 객체 재사용**(재생성 금지)이라 UNIQUE 를 안 건드린다."""
    from app.routers.event_suppression_schedules import _sync_targets

    keep = EventSuppressionTargetDevice(device_id=11)
    drop = EventSuppressionTargetDevice(device_id=12)
    coll = [keep, drop]
    changed = _sync_targets(coll, EventSuppressionTargetDevice, "device_id", [11, 13])
    assert changed is True
    assert sorted(t.device_id for t in coll) == [11, 13]
    assert any(t is keep for t in coll)       # 겹치는 11 은 같은 객체 재사용
    assert all(t is not drop for t in coll)   # 빠진 12 는 제거


def test_should_report_no_change_when_sync_targets_identical():
    """대상이 동일하면 변경 없음 — 스퓨리어스 UPDATE/발행을 만들지 않는다."""
    from app.routers.event_suppression_schedules import _sync_targets

    coll = [EventSuppressionTargetDevice(device_id=11), EventSuppressionTargetDevice(device_id=12)]
    assert _sync_targets(coll, EventSuppressionTargetDevice, "device_id", [11, 12]) is False
    assert sorted(t.device_id for t in coll) == [11, 12]


# ───────── sync-message FR-06: notified_status 백스톱 ─────────

@pytest.mark.asyncio
async def test_should_reconcile_notified_status_when_sweep_runs(async_db, monkeypatch):
    """sweep 백스톱 — 파생상태와 어긋난 notified_status 를 맞춘다(= 트리거 발화 유도)."""
    import app.database as database

    sched = await _add(async_db, target_type=EnumSuppressionTargetType.ALL)
    assert sched.notified_status is None                      # 최초엔 미통지

    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: _SessionCtx(async_db))
    changed = await svc.run_suppression_sweep()

    assert changed >= 1
    await async_db.refresh(sched)
    assert sched.notified_status == svc.suppression_status(sched)


@pytest.mark.asyncio
async def test_should_not_reconcile_when_notified_status_already_matches(async_db, monkeypatch):
    """멱등 — 이미 일치하면 UPDATE 0행 = NATS 발행 0건."""
    import app.database as database

    sched = await _add(async_db, target_type=EnumSuppressionTargetType.ALL)
    sched.notified_status = svc.suppression_status(sched)
    await async_db.commit()

    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: _SessionCtx(async_db))
    assert await svc.run_suppression_sweep() == 0


@pytest.mark.asyncio
async def test_should_mark_expired_notified_status_when_window_ended(async_db, monkeypatch):
    """만료 창 — is_active=false 와 notified_status=expired 를 **같은 UPDATE** 로 처리(이중 통지 차단)."""
    import app.database as database

    now = utc_now()
    sched = await _add(async_db, target_type=EnumSuppressionTargetType.ALL,
                       window_start=now - timedelta(hours=2), window_end=now - timedelta(hours=1))
    assert sched.is_active is True

    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: _SessionCtx(async_db))
    assert await svc.run_suppression_sweep() >= 1
    await async_db.refresh(sched)
    assert sched.is_active is False
    assert sched.notified_status == EnumSuppressionStatus.EXPIRED.value

    # 재실행해도 추가 변경 없음(= 재발행 없음)
    assert await svc.run_suppression_sweep() == 0


@pytest.mark.asyncio
async def test_should_set_cancelled_notified_status_when_revoked(async_db):
    """취소 시 notified_status=cancelled 를 같은 UPDATE 로 확정 → sweep 재발화 없음."""
    from app.routers import event_suppression_schedules as r

    sched = await _add(async_db, target_type=EnumSuppressionTargetType.ALL)
    await r.delete_suppression_schedule(sched.id, current_user=None, db=async_db)
    await async_db.refresh(sched)

    assert sched.revoked_at is not None
    assert sched.is_active is False
    assert sched.notified_status == EnumSuppressionStatus.CANCELLED.value


# ───────── 스케줄러(창 경계 잡) ─────────

def test_should_not_schedule_when_scheduler_absent():
    """스케줄러 미주입 시 전부 무동작(테스트/휴면 환경 안전)."""
    from app.services import suppression_scheduler as sch

    sch.set_scheduler(None)

    class _S:
        id = 1
        revoked_at = None
        window_start = utc_now() + timedelta(hours=1)
        window_end = utc_now() + timedelta(hours=2)

    assert sch.schedule_window_boundaries(_S()) == 0
    assert sch.unschedule_window_boundaries(1) == 0


def test_should_schedule_two_jobs_when_window_in_future():
    """미래 창 — start/end 2건 등록. 취소된 창은 등록하지 않고 제거."""
    from app.services import suppression_scheduler as sch

    class _FakeScheduler:
        def __init__(self):
            self.jobs = {}

        def add_job(self, fn, trigger, run_date=None, args=None, id=None, **kw):
            self.jobs[id] = (run_date, args)

        def remove_job(self, job_id):
            if job_id not in self.jobs:
                raise KeyError(job_id)
            del self.jobs[job_id]

    fake = _FakeScheduler()
    sch.set_scheduler(fake)
    try:
        now = utc_now()

        class _S:
            id = 7
            revoked_at = None
            window_start = now + timedelta(hours=1)
            window_end = now + timedelta(hours=2)

        assert sch.schedule_window_boundaries(_S(), now=now) == 2
        assert set(fake.jobs) == {"suppression_start:7", "suppression_end:7"}

        class _Revoked(_S):
            revoked_at = now

        assert sch.schedule_window_boundaries(_Revoked(), now=now) == 0
        assert fake.jobs == {}          # 취소 시 기존 잡 제거
    finally:
        sch.set_scheduler(None)


def test_should_skip_past_boundaries_when_scheduling():
    """과거 경계는 등록하지 않는다(백스톱 sweep 이 재조정)."""
    from app.services import suppression_scheduler as sch

    class _FakeScheduler:
        def __init__(self):
            self.jobs = {}

        def add_job(self, fn, trigger, run_date=None, args=None, id=None, **kw):
            self.jobs[id] = run_date

        def remove_job(self, job_id):
            raise KeyError(job_id)

    fake = _FakeScheduler()
    sch.set_scheduler(fake)
    try:
        now = utc_now()

        class _S:
            id = 8
            revoked_at = None
            window_start = now - timedelta(hours=2)   # 이미 시작함
            window_end = now + timedelta(hours=1)     # 아직 안 끝남

        assert sch.schedule_window_boundaries(_S(), now=now) == 1   # end 만 등록
        assert set(fake.jobs) == {"suppression_end:8"}
    finally:
        sch.set_scheduler(None)
