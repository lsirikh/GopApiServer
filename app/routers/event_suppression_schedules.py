"""
Event Suppression Schedule API — 스케줄 기반 이벤트 수신 억제(정비 창), 복수 대상.

PRD: event-suppression-schedule-prd.md v1.1 + event-suppression-multi-target-prd.md v1.0

6개 엔드포인트: POST(생성) / GET(목록·필터) / GET active / GET {id} / PATCH / DELETE(soft-cancel).
대상은 모드(device/group/all 배타) 내 복수 — junction 2테이블(target_devices/target_groups).
RBAC: 라우트-레벨 require_perm_optional_async + 중앙 enforce_matrix(PERMISSION_MAP). role=ADMIN bypass.
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import noload
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_async_db
from app.routers.auth import (
    get_current_account_user_optional_async,
    require_perm_optional_async,
)
from app.models.event_suppression import (
    EventSuppressionSchedule, EventSuppressionTargetDevice, EventSuppressionTargetGroup,
)
from app.models.device import Device
from app.models.device_group import DeviceGroup
from app.schemas.event_suppression import (
    EventSuppressionScheduleCreate,
    EventSuppressionScheduleUpdate,
    EventSuppressionScheduleResponse,
    EventSuppressionBulkDeleteRequest,
    EventSuppressionBulkDeleteResult,
)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.services.config_log_service import (
    log_config_change_async, get_identifier, get_changed_fields, model_to_dict,
)
from app.services.event_suppression_service import suppression_status, get_active_schedules
from app.services import suppression_scheduler
from app.utils.datetime import utc_now, to_utc
from app.utils.enums import (
    EnumConfigResourceType, EnumConfigActionType,
    EnumSuppressionTargetType, EnumSuppressionStatus,
)

router = APIRouter(prefix="/event-suppression-schedules")


def _dedupe(ids) -> list[int]:
    return list(dict.fromkeys(ids or []))


def _sync_targets(collection, model, key_attr: str, new_ids: list[int]) -> bool:
    """junction 컬렉션을 **delta** 로 동기화. 반환 = 실제 변경 여부.

    ★ 왜 통째 재대입(`s.target_devices = [...]`)을 쓰면 안 되는가:
      relationship 이 cascade="all, delete-orphan" 이라 재대입 시 기존 행은 orphan DELETE,
      새 객체는 INSERT 로 **같은 flush** 에 예약된다. SQLAlchemy unit-of-work 는 동일 mapper 에서
      INSERT 를 DELETE 보다 먼저 수행하므로, 겹치는 (schedule_id, device_id) 가 하나라도 있으면
      uq_suppression_target_device / uq_suppression_target_group 위반 → IntegrityError → 500.
      대상 배열 미제공 PATCH 는 기존 ids 를 그대로 복원하므로 겹침 100% → 이름만 바꿔도 500이었다.
    → 겹치는 행은 **재사용**하고 제거분만 remove / 신규분만 append 해서 위반을 원천 차단한다.
    """
    current = {getattr(t, key_attr): t for t in collection}
    target = set(new_ids)
    removed = [k for k in current if k not in target]
    added = [k for k in new_ids if k not in current]
    for k in removed:
        collection.remove(current[k])
    for k in added:
        collection.append(model(**{key_attr: k}))
    return bool(removed or added)


def _to_response(s: EventSuppressionSchedule, now=None) -> EventSuppressionScheduleResponse:
    """ORM → Response. target_devices/target_groups junction 은 lazy='selectin' 로 로드됨."""
    return EventSuppressionScheduleResponse(
        id=s.id,
        name=s.name,
        description=s.description,
        target_type=s.target_type,
        target_device_ids=[t.device_id for t in s.target_devices],
        target_group_ids=[t.group_id for t in s.target_groups],
        target_side=s.target_side,
        event_scope=s.event_scope,
        window_start=s.window_start,
        window_end=s.window_end,
        recurrence_rule=s.recurrence_rule,
        is_active=s.is_active,
        status=suppression_status(s, now),
        revoked_at=s.revoked_at,
        created_by=s.created_by,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


async def _reload(db: AsyncSession, schedule_id: int) -> EventSuppressionSchedule:
    """junction 을 selectin 으로 재로드(쓰기 후 응답 조립 안전)."""
    return (await db.execute(
        select(EventSuppressionSchedule).where(EventSuppressionSchedule.id == schedule_id)
    )).scalars().first()


async def _assert_devices_exist(db: AsyncSession, device_ids: list[int]):
    if not device_ids:
        return
    found = set((await db.execute(select(Device.id).where(Device.id.in_(device_ids)))).scalars().all())
    missing = [d for d in device_ids if d not in found]
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"success": False, "message": f"Device id(s) not found: {missing}"})


async def _assert_groups_exist(db: AsyncSession, group_ids: list[int]):
    if not group_ids:
        return
    found = set((await db.execute(select(DeviceGroup.id).where(DeviceGroup.id.in_(group_ids)))).scalars().all())
    missing = [g for g in group_ids if g not in found]
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"success": False, "message": f"DeviceGroup id(s) not found: {missing}"})


@router.post(
    "", response_model=ApiSingleResponse[EventSuppressionScheduleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_perm_optional_async("events", "edit"))],
)
async def create_suppression_schedule(
    data: EventSuppressionScheduleCreate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """이벤트 억제 스케줄 생성 — 모드(device/group/all) 내 복수 대상.

    - **target_type**: device / group / all
    - **target_device_ids**: device 시 ≥1 · **target_group_ids**: group 시 ≥1
    - **event_scope**: connection / detection / malfunction / all
    - **window_start~window_end**: 억제 시간창(종료 필수, 자동 만료)
    """
    schedule = EventSuppressionSchedule(
        name=data.name,
        description=data.description,
        target_type=data.target_type,
        target_side=data.target_side,
        event_scope=data.event_scope,
        window_start=data.window_start,
        window_end=data.window_end,
        recurrence_rule=data.recurrence_rule,
        created_by=(current_user.id if current_user else None),
    )
    if data.target_type == EnumSuppressionTargetType.DEVICE:
        ids = _dedupe(data.target_device_ids)
        await _assert_devices_exist(db, ids)
        schedule.target_devices = [EventSuppressionTargetDevice(device_id=d) for d in ids]
    elif data.target_type == EnumSuppressionTargetType.GROUP:
        ids = _dedupe(data.target_group_ids)
        await _assert_groups_exist(db, ids)
        schedule.target_groups = [EventSuppressionTargetGroup(group_id=g) for g in ids]

    db.add(schedule)
    await db.commit()

    # 창 경계 전이 통지 잡 등록(best-effort — 실패해도 sweep 백스톱이 재조정)
    suppression_scheduler.schedule_window_boundaries(schedule)

    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SUPPRESSION_SCHEDULE,
        resource_id=schedule.id,
        resource_name=f"SuppressionSchedule-{schedule.id} ({schedule.name})",
        action=EnumConfigActionType.CREATED,
        after_state=get_identifier(schedule),
        description="EventSuppressionSchedule 생성",
    )

    s = await _reload(db, schedule.id)
    return ApiSingleResponse(success=True, message="억제 스케줄 생성 성공", data=_to_response(s))


@router.get("", response_model=ApiResponse[list[EventSuppressionScheduleResponse]],
            dependencies=[Depends(require_perm_optional_async("events", "view"))])
async def list_suppression_schedules(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    status_filter: Optional[EnumSuppressionStatus] = Query(None, alias="status", description="상태 필터"),
    target_type: Optional[EnumSuppressionTargetType] = Query(None, description="대상 유형 필터"),
    device_id: Optional[int] = Query(None, description="대상 장비 ID 필터(배열 포함 매치)"),
    group_id: Optional[int] = Query(None, description="대상 그룹 ID 필터(배열 포함 매치)"),
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """억제 스케줄 목록(페이지네이션 + 상태/대상 필터). device_id/group_id 는 junction 포함 매치."""
    now = utc_now()
    stmt = select(EventSuppressionSchedule)
    count_stmt = select(func.count()).select_from(EventSuppressionSchedule)

    conds = []
    if status_filter is not None:
        if status_filter == EnumSuppressionStatus.CANCELLED:
            conds.append(EventSuppressionSchedule.revoked_at.isnot(None))
        elif status_filter == EnumSuppressionStatus.PENDING:
            conds.append(EventSuppressionSchedule.revoked_at.is_(None))
            conds.append(EventSuppressionSchedule.window_start > now)
        elif status_filter == EnumSuppressionStatus.EXPIRED:
            conds.append(EventSuppressionSchedule.revoked_at.is_(None))
            conds.append(EventSuppressionSchedule.window_end <= now)
        elif status_filter == EnumSuppressionStatus.ACTIVE:
            conds.append(EventSuppressionSchedule.revoked_at.is_(None))
            conds.append(EventSuppressionSchedule.window_start <= now)
            conds.append(EventSuppressionSchedule.window_end > now)
    if target_type is not None:
        conds.append(EventSuppressionSchedule.target_type == target_type)
    if device_id is not None:
        conds.append(EventSuppressionSchedule.target_devices.any(
            EventSuppressionTargetDevice.device_id == device_id))
    if group_id is not None:
        conds.append(EventSuppressionSchedule.target_groups.any(
            EventSuppressionTargetGroup.group_id == group_id))

    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)

    total = (await db.execute(count_stmt)).scalar() or 0
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    rows = (await db.execute(
        stmt.order_by(EventSuppressionSchedule.id.desc()).offset(skip).limit(limit)
    )).scalars().all()

    return ApiResponse(
        success=True,
        message="억제 스케줄 목록 조회 성공",
        data=[_to_response(s, now) for s in rows],
        pagination=PaginationMeta(page=page, limit=limit, total=total, total_pages=total_pages),
    )


@router.get("/active", response_model=ApiResponse[list[EventSuppressionScheduleResponse]],
            dependencies=[Depends(require_perm_optional_async("events", "view"))])
async def list_active_suppression_schedules(
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """현재 활성(진행 중) 억제 창 — UI 배너 및 외부(.NET) 조회 훅."""
    now = utc_now()
    rows = await get_active_schedules(db, now)
    return ApiResponse(
        success=True,
        message="활성 억제 창 조회 성공",
        data=[_to_response(s, now) for s in rows],
    )


@router.get("/{schedule_id}", response_model=ApiSingleResponse[EventSuppressionScheduleResponse],
            dependencies=[Depends(require_perm_optional_async("events", "view"))])
async def get_suppression_schedule(
    schedule_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """억제 스케줄 단건 조회."""
    s = await _reload(db, schedule_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"success": False, "message": f"SuppressionSchedule {schedule_id} not found"})
    return ApiSingleResponse(success=True, message="억제 스케줄 조회 성공", data=_to_response(s))


@router.patch("/{schedule_id}", response_model=ApiSingleResponse[EventSuppressionScheduleResponse],
              dependencies=[Depends(require_perm_optional_async("events", "edit"))])
async def patch_suppression_schedule(
    schedule_id: int,
    data: EventSuppressionScheduleUpdate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """억제 스케줄 부분 수정. 대상 배열 제공 시 해당 모드 junction 전체 교체."""
    s = await _reload(db, schedule_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"success": False, "message": f"SuppressionSchedule {schedule_id} not found"})

    before_state = model_to_dict(s)
    before_devices, before_groups = list(s.device_ids), list(s.group_ids)

    fields = data.model_dump(exclude_unset=True)
    new_device_ids = fields.pop("target_device_ids", None)
    new_group_ids = fields.pop("target_group_ids", None)

    # S3-06 가드 (2026-08-07 감사): 명시적 `null` → NOT NULL 컬럼에 None 이 setattr 되어 commit 에서
    # IntegrityError → **500**. `exclude_unset=True` 는 "보내지 않음"과 "명시적 null"을 구분하지 못하므로
    # 여기서 NOT NULL 대상만 걸러 **422** 로 거부한다. (nullable: description / recurrence_rule)
    _non_nullable = ("name", "target_type", "target_side", "event_scope", "window_start", "window_end")
    _nulled = [k for k in _non_nullable if k in fields and fields[k] is None]
    if _nulled:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False,
                    "message": f"These fields cannot be set to null: {', '.join(_nulled)}"},
        )

    for k, v in fields.items():  # 스칼라 컬럼만 (name/description/target_type/side/scope/window/recurrence)
        setattr(s, k, v)

    # 창 순서 검증(H3: UTC 정규화 후 비교)
    _ws, _we = to_utc(s.window_start), to_utc(s.window_end)
    if _ws is not None and _we is not None and _we <= _ws:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"success": False, "message": "window_end must be after window_start"})

    # 최종 모드에 맞춰 대상 junction 재구성(제공 배열 우선, 없으면 기존 유지, 반대 모드 정리)
    final_type = s.target_type
    if final_type == EnumSuppressionTargetType.DEVICE:
        ids = _dedupe(new_device_ids) if new_device_ids is not None else before_devices
        if len(ids) < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail={"success": False, "message": "target_device_ids requires ≥1 when target_type=device"})
        await _assert_devices_exist(db, ids)
        _sync_targets(s.target_devices, EventSuppressionTargetDevice, "device_id", ids)
        _sync_targets(s.target_groups, EventSuppressionTargetGroup, "group_id", [])
    elif final_type == EnumSuppressionTargetType.GROUP:
        ids = _dedupe(new_group_ids) if new_group_ids is not None else before_groups
        if len(ids) < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail={"success": False, "message": "target_group_ids requires ≥1 when target_type=group"})
        await _assert_groups_exist(db, ids)
        _sync_targets(s.target_groups, EventSuppressionTargetGroup, "group_id", ids)
        _sync_targets(s.target_devices, EventSuppressionTargetDevice, "device_id", [])
    else:  # ALL — 대상 없음
        _sync_targets(s.target_devices, EventSuppressionTargetDevice, "device_id", [])
        _sync_targets(s.target_groups, EventSuppressionTargetGroup, "group_id", [])

    await db.commit()

    # 창이 바뀌었을 수 있으므로 경계 잡 재등록(replace_existing=True 로 멱등)
    suppression_scheduler.schedule_window_boundaries(s)

    after_state = model_to_dict(s)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes or new_device_ids is not None or new_group_ids is not None:
        await log_config_change_async(
            db=db,
            resource_type=EnumConfigResourceType.SUPPRESSION_SCHEDULE,
            resource_id=s.id,
            resource_name=f"SuppressionSchedule-{s.id} ({s.name})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="EventSuppressionSchedule 수정",
        )

    s2 = await _reload(db, schedule_id)
    return ApiSingleResponse(success=True, message="억제 스케줄 수정 성공", data=_to_response(s2))


@router.delete("/{schedule_id}", response_model=ApiSingleResponse[EventSuppressionScheduleResponse],
               dependencies=[Depends(require_perm_optional_async("events", "delete"))])
async def delete_suppression_schedule(
    schedule_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """억제 스케줄 삭제(soft-cancel = revoked_at 세팅 + is_active=false)."""
    s = await _reload(db, schedule_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"success": False, "message": f"SuppressionSchedule {schedule_id} not found"})

    if s.revoked_at is None:
        s.revoked_at = utc_now()
    s.is_active = False
    s.notified_status = EnumSuppressionStatus.CANCELLED.value  # 취소 통지 상태 확정(sweep 재발화 방지)
    await db.commit()

    # 취소됐으므로 남은 경계 잡 제거(발화해도 멱등이지만 불필요한 잡을 남기지 않음)
    suppression_scheduler.unschedule_window_boundaries(s.id)

    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SUPPRESSION_SCHEDULE,
        resource_id=s.id,
        resource_name=f"SuppressionSchedule-{s.id} ({s.name})",
        action=EnumConfigActionType.DELETED,
        before_state=get_identifier(s),
        description="EventSuppressionSchedule soft-cancel",
    )

    s2 = await _reload(db, schedule_id)
    return ApiSingleResponse(success=True, message="억제 스케줄 삭제(취소) 성공", data=_to_response(s2))


@router.post("/bulk-delete", response_model=ApiSingleResponse[EventSuppressionBulkDeleteResult],
             dependencies=[Depends(require_perm_optional_async("events", "delete"))])
async def bulk_delete_suppression_schedules(
    data: EventSuppressionBulkDeleteRequest,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """취소·종료(terminal) 억제 스케줄 **일괄 하드삭제**(물리 제거, 목록 정리용).

    - soft-cancel(DELETE {id})과 달리 행+junction 을 완전 제거(복구 불가).
    - **안전장치**: 활성(active)/예정(pending) 스케줄은 삭제하지 않고 `skipped_ids` 로 반환(먼저 취소 필요).
    - 존재하지 않는 id 는 `not_found_ids` 로 분리 보고.
    """
    ids = _dedupe(data.ids)
    now = utc_now()
    # ★ 동시성(TOCTOU) 안전: FOR UPDATE 로 대상 행을 잠근 뒤 최신 커밋 상태로 status 재판정.
    #   조회~삭제 사이 다른 세션의 PATCH(창 연장 등)로 terminal→active 로 뒤바뀐 행이
    #   오삭제되는 것을 차단(잠금 획득 후 값 재평가 → active/pending 이면 skip).
    # ★ noload: junction 을 세션에 **로드하지 않는다**.
    #   lazy="selectin" 으로 자식이 세션에 올라오면 passive_deletes 여부와 무관하게 ORM 이 자식 DELETE 를
    #   부모보다 먼저 실행한다. 그러면 junction statement 트리거가 (아직 살아있는) 부모를 보고
    #   중복 SYNC(UPDATED)를 쏜다. 로드하지 않으면 부모 DELETE 선행 → FK CASCADE 순서가 되어
    #   트리거의 부모 JOIN 이 0행 → DELETED 1건만 발행된다. 삭제 판정엔 junction 이 필요 없다.
    rows = (await db.execute(
        select(EventSuppressionSchedule)
        .where(EventSuppressionSchedule.id.in_(ids))
        .options(noload(EventSuppressionSchedule.target_devices),
                 noload(EventSuppressionSchedule.target_groups))
        .with_for_update()
    )).scalars().all()
    found_ids = {s.id for s in rows}

    deleted: list[int] = []
    skipped: list[int] = []
    for s in rows:
        st = suppression_status(s, now)
        if st in (EnumSuppressionStatus.CANCELLED.value, EnumSuppressionStatus.EXPIRED.value):
            await db.delete(s)   # cascade: target_devices/target_groups junction 동반 삭제(all,delete-orphan + FK CASCADE)
            deleted.append(s.id)
        else:
            skipped.append(s.id)   # active/pending — 먼저 취소해야 삭제 가능(오삭제 방지)

    not_found = [i for i in ids if i not in found_ids]
    await db.commit()

    # 하드삭제된 스케줄의 잔여 경계 잡 제거(발화해도 행이 없어 no-op 이지만 잡을 남기지 않음)
    for sid in deleted:
        suppression_scheduler.unschedule_window_boundaries(sid)

    for sid in deleted:
        await log_config_change_async(
            db=db,
            resource_type=EnumConfigResourceType.SUPPRESSION_SCHEDULE,
            resource_id=sid,
            resource_name=f"SuppressionSchedule-{sid}",
            action=EnumConfigActionType.DELETED,
            description="EventSuppressionSchedule 하드삭제(일괄, 목록 정리)",
        )

    return ApiSingleResponse(
        success=True,
        message=f"삭제 {len(deleted)}건 · 스킵(활성/예정) {len(skipped)}건 · 없음 {len(not_found)}건",
        data=EventSuppressionBulkDeleteResult(
            deleted_ids=deleted, skipped_ids=skipped, not_found_ids=not_found,
        ),
    )
