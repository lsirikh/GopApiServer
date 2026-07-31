"""이벤트 억제 스케줄 테스트 — event-suppression-schedule PRD v1.1 Phase 3.

- 순수 함수(파생 side / side 매치 / 파생 status): DB 무의존.
- is_suppressed 게이트: 격리 aiosqlite(async_db 픽스처) — 운영/공유 DB 무접촉.

실행: env -u DATABASE_URL python -m pytest tests/test_event_suppression.py -v
"""
from datetime import timedelta

import pytest

import app.models  # noqa: F401 — 모델 등록(Base.metadata) 보장
from app.models.event_suppression import (
    EventSuppressionSchedule, EventSuppressionTargetDevice, EventSuppressionTargetGroup,
)
from app.models.device_group import DeviceGroupMapping
from app.utils.datetime import utc_now
from app.utils.enums import (
    EnumSuppressionTargetType, EnumSuppressionSide, EnumSuppressionEventScope,
    EnumSuppressionStatus, EnumDeviceCategory,
)
from app.services import event_suppression_service as svc


# ───────── 순수 함수: 감지/감시 side 파생 (D5) ─────────

def test_should_derive_detection_side_when_sensor_or_controller():
    assert svc._derive_side("sensor") == "detection"
    assert svc._derive_side("controller") == "detection"
    assert svc._derive_side(EnumDeviceCategory.SENSOR) == "detection"


def test_should_derive_surveillance_side_when_camera():
    assert svc._derive_side("camera") == "surveillance"
    assert svc._derive_side(EnumDeviceCategory.CAMERA) == "surveillance"


def test_should_derive_auxiliary_side_when_speaker_lamp_enclosure():
    for c in ("speaker", "lamp", "enclosure"):
        assert svc._derive_side(c) == "auxiliary"


# ───────── 순수 함수: side 매치 ─────────

def test_should_match_all_sides_when_target_both():
    assert svc._side_matches("detection", EnumSuppressionSide.BOTH)
    assert svc._side_matches("surveillance", EnumSuppressionSide.BOTH)
    assert svc._side_matches("auxiliary", EnumSuppressionSide.BOTH)


def test_should_match_only_same_side_when_target_specific():
    assert svc._side_matches("detection", EnumSuppressionSide.DETECTION)
    assert not svc._side_matches("surveillance", EnumSuppressionSide.DETECTION)
    assert not svc._side_matches("auxiliary", EnumSuppressionSide.DETECTION)


# ───────── 순수 함수: 파생 status (우선순위 CANCELLED>PENDING>EXPIRED>ACTIVE) ─────────

def _fake_sched(**kw):
    now = utc_now()
    base = dict(window_start=now - timedelta(hours=1), window_end=now + timedelta(hours=1), revoked_at=None)
    base.update(kw)
    return type("_S", (), base)()


def test_should_return_active_when_within_window():
    assert svc.suppression_status(_fake_sched()) == EnumSuppressionStatus.ACTIVE.value


def test_should_return_pending_when_before_start():
    now = utc_now()
    s = _fake_sched(window_start=now + timedelta(hours=1), window_end=now + timedelta(hours=2))
    assert svc.suppression_status(s) == EnumSuppressionStatus.PENDING.value


def test_should_return_expired_when_after_end():
    now = utc_now()
    s = _fake_sched(window_start=now - timedelta(hours=2), window_end=now - timedelta(hours=1))
    assert svc.suppression_status(s) == EnumSuppressionStatus.EXPIRED.value


def test_should_return_cancelled_when_revoked_regardless_of_window():
    s = _fake_sched(revoked_at=utc_now())
    assert svc.suppression_status(s) == EnumSuppressionStatus.CANCELLED.value


# ───────── DB: is_suppressed 게이트 (격리 aiosqlite) ─────────

async def _add(async_db, target_device_id=None, target_group_id=None,
               target_device_ids=None, target_group_ids=None, **kw):
    """테스트 헬퍼 — 단일(target_device_id) / 복수(target_device_ids) 모두 junction 으로 생성."""
    now = utc_now()
    base = dict(
        name="t", target_type=EnumSuppressionTargetType.DEVICE,
        target_side=EnumSuppressionSide.BOTH, event_scope=EnumSuppressionEventScope.DETECTION,
        window_start=now - timedelta(hours=1), window_end=now + timedelta(hours=1),
    )
    base.update(kw)
    s = EventSuppressionSchedule(**base)
    dev_ids = target_device_ids if target_device_ids is not None else (
        [target_device_id] if target_device_id is not None else [])
    grp_ids = target_group_ids if target_group_ids is not None else (
        [target_group_id] if target_group_id is not None else [])
    s.target_devices = [EventSuppressionTargetDevice(device_id=d) for d in dev_ids]
    s.target_groups = [EventSuppressionTargetGroup(group_id=g) for g in grp_ids]
    async_db.add(s)
    await async_db.commit()
    return s


@pytest.mark.asyncio
async def test_should_suppress_when_device_scope_matches_active_window(async_db):
    await _add(async_db, target_type=EnumSuppressionTargetType.DEVICE, target_device_id=10)
    sup, sid = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is True and sid is not None


@pytest.mark.asyncio
async def test_should_not_suppress_when_no_schedule(async_db):
    sup, sid = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is False and sid is None


@pytest.mark.asyncio
async def test_should_not_suppress_when_window_expired(async_db):
    now = utc_now()
    await _add(async_db, target_device_id=10,
               window_start=now - timedelta(hours=2), window_end=now - timedelta(hours=1))
    sup, _ = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is False


@pytest.mark.asyncio
async def test_should_not_suppress_when_window_not_started(async_db):
    now = utc_now()
    await _add(async_db, target_device_id=10,
               window_start=now + timedelta(hours=1), window_end=now + timedelta(hours=2))
    sup, _ = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is False


@pytest.mark.asyncio
async def test_should_not_suppress_when_category_differs(async_db):
    await _add(async_db, target_device_id=10, event_scope=EnumSuppressionEventScope.CONNECTION)
    sup, _ = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is False


@pytest.mark.asyncio
async def test_should_suppress_all_categories_when_event_scope_all(async_db):
    await _add(async_db, target_device_id=10, event_scope=EnumSuppressionEventScope.ALL)
    for cat in ("detection", "malfunction", "connection"):
        sup, _ = await svc.is_suppressed(async_db, 10, "sensor", cat)
        assert sup is True, cat


@pytest.mark.asyncio
async def test_should_not_suppress_action_category(async_db):
    await _add(async_db, target_device_id=10, event_scope=EnumSuppressionEventScope.ALL)
    sup, _ = await svc.is_suppressed(async_db, 10, "sensor", "action")
    assert sup is False


@pytest.mark.asyncio
async def test_should_not_suppress_when_revoked(async_db):
    await _add(async_db, target_device_id=10, revoked_at=utc_now())
    sup, _ = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is False


@pytest.mark.asyncio
async def test_should_suppress_when_group_scope_and_device_is_member(async_db):
    await _add(async_db, target_type=EnumSuppressionTargetType.GROUP,
               target_group_id=5, target_device_id=None)
    async_db.add(DeviceGroupMapping(device_id=10, category_device=EnumDeviceCategory.SENSOR, group_id=5))
    await async_db.commit()
    sup, sid = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is True and sid is not None


@pytest.mark.asyncio
async def test_should_not_suppress_when_group_scope_and_device_not_member(async_db):
    await _add(async_db, target_type=EnumSuppressionTargetType.GROUP,
               target_group_id=5, target_device_id=None)
    sup, _ = await svc.is_suppressed(async_db, 999, "sensor", "detection")
    assert sup is False


@pytest.mark.asyncio
async def test_should_respect_side_filter_when_all_scope_detection_only(async_db):
    await _add(async_db, target_type=EnumSuppressionTargetType.ALL, target_device_id=None,
               target_side=EnumSuppressionSide.DETECTION, event_scope=EnumSuppressionEventScope.ALL)
    sup_sensor, _ = await svc.is_suppressed(async_db, 1, "sensor", "detection")     # 감지쪽 → 억제
    sup_camera, _ = await svc.is_suppressed(async_db, 2, "camera", "detection")     # 감시쪽 → 미억제
    assert sup_sensor is True
    assert sup_camera is False


@pytest.mark.asyncio
async def test_should_match_all_scope_when_side_both(async_db):
    await _add(async_db, target_type=EnumSuppressionTargetType.ALL, target_device_id=None,
               target_side=EnumSuppressionSide.BOTH, event_scope=EnumSuppressionEventScope.MALFUNCTION)
    sup_cam, _ = await svc.is_suppressed(async_db, 7, "camera", "malfunction")
    sup_spk, _ = await svc.is_suppressed(async_db, 8, "speaker", "malfunction")     # 보조도 both면 매치
    assert sup_cam is True
    assert sup_spk is True


@pytest.mark.asyncio
async def test_should_track_suppressed_count_when_recorded():
    before = svc.get_suppressed_counts().get("detection", 0)
    svc.record_suppression(10, "detection", 1)
    after = svc.get_suppressed_counts().get("detection", 0)
    assert after == before + 1


# ───────── DB: CRUD 라우터 수명주기 (엔드포인트 함수 직접 호출) ─────────

@pytest.mark.asyncio
async def test_crud_lifecycle_via_router(async_db):
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import (
        EventSuppressionScheduleCreate, EventSuppressionScheduleUpdate,
    )
    now = utc_now()
    data = EventSuppressionScheduleCreate(
        name="GOP 공사창", target_type=EnumSuppressionTargetType.ALL,
        event_scope=EnumSuppressionEventScope.ALL,
        window_start=now - timedelta(minutes=10), window_end=now + timedelta(hours=2),
    )
    created = await r.create_suppression_schedule(data, current_user=None, db=async_db)
    sid = created.data.id
    assert sid is not None
    assert created.data.status == EnumSuppressionStatus.ACTIVE.value

    listed = await r.list_suppression_schedules(
        page=1, limit=20, status_filter=None, target_type=None,
        device_id=None, group_id=None, current_user=None, db=async_db,
    )
    assert listed.pagination.total == 1

    active = await r.list_active_suppression_schedules(current_user=None, db=async_db)
    assert len(active.data) == 1

    got = await r.get_suppression_schedule(sid, current_user=None, db=async_db)
    assert got.data.id == sid

    patched = await r.patch_suppression_schedule(
        sid, EventSuppressionScheduleUpdate(name="변경된 작업명"), current_user=None, db=async_db,
    )
    assert patched.data.name == "변경된 작업명"

    deleted = await r.delete_suppression_schedule(sid, current_user=None, db=async_db)
    assert deleted.data.status == EnumSuppressionStatus.CANCELLED.value
    assert deleted.data.revoked_at is not None

    active_after = await r.list_active_suppression_schedules(current_user=None, db=async_db)
    assert len(active_after.data) == 0


@pytest.mark.asyncio
async def test_create_rejects_window_end_before_start():
    from app.schemas.event_suppression import EventSuppressionScheduleCreate
    now = utc_now()
    with pytest.raises(ValueError):
        EventSuppressionScheduleCreate(
            name="bad", target_type=EnumSuppressionTargetType.ALL,
            event_scope=EnumSuppressionEventScope.DETECTION,
            window_start=now + timedelta(hours=2), window_end=now + timedelta(hours=1),
        )


@pytest.mark.asyncio
async def test_create_requires_device_id_when_target_device():
    from app.schemas.event_suppression import EventSuppressionScheduleCreate
    now = utc_now()
    with pytest.raises(ValueError):
        EventSuppressionScheduleCreate(
            name="bad", target_type=EnumSuppressionTargetType.DEVICE,
            event_scope=EnumSuppressionEventScope.DETECTION,
            window_start=now, window_end=now + timedelta(hours=1),
        )


# ───────── code-review 수정 검증 (H2/H3/H4a) ─────────

@pytest.mark.asyncio
async def test_should_fail_open_and_rollback_when_gate_query_errors():
    """H2: 게이트 조회 예외 시 rollback 으로 세션 복구 + (False,None) 반환(진짜 fail-open)."""
    class _BrokenDB:
        def __init__(self):
            self.rolled_back = False

        async def execute(self, *a, **k):
            raise RuntimeError("db boom")

        async def rollback(self):
            self.rolled_back = True

    db = _BrokenDB()
    sup, sid = await svc.is_suppressed(db, 10, "sensor", "detection")
    assert sup is False and sid is None
    assert db.rolled_back is True  # 세션 복구 호출됨 → 호출부 db.add/commit 가능


@pytest.mark.asyncio
async def test_patch_rejects_mixed_tz_window_with_422_not_500(async_db):
    """H3: PATCH 창 비교가 naive/aware 혼용에도 TypeError(500) 없이 422 로 처리."""
    from datetime import datetime
    from fastapi import HTTPException
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import (
        EventSuppressionScheduleCreate, EventSuppressionScheduleUpdate,
    )
    now = utc_now()
    created = await r.create_suppression_schedule(
        EventSuppressionScheduleCreate(
            name="x", target_type=EnumSuppressionTargetType.ALL,
            event_scope=EnumSuppressionEventScope.ALL,
            window_start=now - timedelta(hours=1), window_end=now + timedelta(hours=1),
        ), current_user=None, db=async_db,
    )
    sid = created.data.id
    with pytest.raises(HTTPException) as ei:  # naive 과거 window_end → 422(TypeError 아님)
        await r.patch_suppression_schedule(
            sid, EventSuppressionScheduleUpdate(window_end=datetime(2000, 1, 1, 0, 0, 0)),
            current_user=None, db=async_db,
        )
    assert ei.value.status_code == 422


@pytest.mark.asyncio
async def test_patch_replaces_targets_when_type_changes(async_db):
    """멀티타깃: target_type 변경 시 이전 모드 junction 정리 + 새 모드 대상 반영."""
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleUpdate
    from app.models.device_group import DeviceGroup

    grp = DeviceGroup(name="G-mt")
    async_db.add(grp)
    await async_db.commit()
    await async_db.refresh(grp)

    sched = await _add(async_db, target_type=EnumSuppressionTargetType.DEVICE, target_device_ids=[42])

    patched = await r.patch_suppression_schedule(
        sched.id, EventSuppressionScheduleUpdate(
            target_type=EnumSuppressionTargetType.GROUP, target_group_ids=[grp.id],
        ), current_user=None, db=async_db,
    )
    assert patched.data.target_type == EnumSuppressionTargetType.GROUP
    assert patched.data.target_group_ids == [grp.id]
    assert patched.data.target_device_ids == []  # 이전 DEVICE junction 정리됨


# ───────── 멀티타깃 (복수 대상) ─────────

@pytest.mark.asyncio
async def test_should_suppress_when_device_in_multi_device_set(async_db):
    await _add(async_db, target_type=EnumSuppressionTargetType.DEVICE, target_device_ids=[10, 11, 12])
    for d in (10, 11, 12):
        sup, _ = await svc.is_suppressed(async_db, d, "sensor", "detection")
        assert sup is True, d
    sup_out, _ = await svc.is_suppressed(async_db, 99, "sensor", "detection")
    assert sup_out is False


@pytest.mark.asyncio
async def test_should_suppress_when_multi_group_intersects_membership(async_db):
    await _add(async_db, target_type=EnumSuppressionTargetType.GROUP, target_group_ids=[5, 6, 7])
    # device 10 은 대상 그룹 집합 중 하나(6)에만 속함 → 교집합 ≠ ∅ → 억제
    async_db.add(DeviceGroupMapping(device_id=10, category_device=EnumDeviceCategory.SENSOR, group_id=6))
    await async_db.commit()
    sup, _ = await svc.is_suppressed(async_db, 10, "sensor", "detection")
    assert sup is True
    # device 20 은 어느 대상 그룹에도 미소속 → 미억제
    sup2, _ = await svc.is_suppressed(async_db, 20, "sensor", "detection")
    assert sup2 is False


@pytest.mark.asyncio
async def test_crud_multi_group_and_filter_via_router(async_db):
    from app.models.device_group import DeviceGroup
    from app.routers import event_suppression_schedules as r
    from app.schemas.event_suppression import EventSuppressionScheduleCreate

    now = utc_now()
    g1, g2 = DeviceGroup(name="mt-g1"), DeviceGroup(name="mt-g2")
    async_db.add_all([g1, g2])
    await async_db.commit()
    await async_db.refresh(g1)
    await async_db.refresh(g2)

    created = await r.create_suppression_schedule(
        EventSuppressionScheduleCreate(
            name="다중그룹 정비", target_type=EnumSuppressionTargetType.GROUP,
            target_group_ids=[g1.id, g2.id], event_scope=EnumSuppressionEventScope.ALL,
            window_start=now - timedelta(minutes=5), window_end=now + timedelta(hours=1),
        ), current_user=None, db=async_db,
    )
    assert set(created.data.target_group_ids) == {g1.id, g2.id}

    # 목록 필터: 그룹 중 하나로 필터 → junction 포함 매치
    listed = await r.list_suppression_schedules(
        page=1, limit=20, status_filter=None, target_type=None,
        device_id=None, group_id=g1.id, current_user=None, db=async_db,
    )
    assert listed.pagination.total == 1


@pytest.mark.asyncio
async def test_create_rejects_empty_ids_when_device_mode():
    from app.schemas.event_suppression import EventSuppressionScheduleCreate
    now = utc_now()
    with pytest.raises(ValueError):  # device 모드인데 배열 비어있음
        EventSuppressionScheduleCreate(
            name="bad", target_type=EnumSuppressionTargetType.DEVICE, target_device_ids=[],
            event_scope=EnumSuppressionEventScope.DETECTION,
            window_start=now, window_end=now + timedelta(hours=1),
        )
