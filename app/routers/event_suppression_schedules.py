"""
Event Suppression Schedule API — 스케줄 기반 이벤트 수신 억제(정비 창).

PRD: docs/prds/event-suppression-schedule-prd.md v1.1 §3.5

6개 독립 엔드포인트(설정 추가/조회/변경/삭제 + 활성):
- POST   /api/event-suppression-schedules          생성          (events:edit)
- GET    /api/event-suppression-schedules          목록(필터·페이지) (events:view)
- GET    /api/event-suppression-schedules/active   활성 창       (events:view)
- GET    /api/event-suppression-schedules/{id}     단건          (events:view)
- PATCH  /api/event-suppression-schedules/{id}     변경          (events:edit)
- DELETE /api/event-suppression-schedules/{id}     삭제(soft-cancel)(events:delete)

RBAC: 라우트-레벨 require_perm_optional_async + 중앙 enforce_matrix(PERMISSION_MAP). role=ADMIN bypass.
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_async_db
from app.routers.auth import (
    get_current_account_user_optional_async,
    require_perm_optional_async,
)
from app.models.event_suppression import EventSuppressionSchedule
from app.models.device import Device
from app.models.device_group import DeviceGroup
from app.schemas.event_suppression import (
    EventSuppressionScheduleCreate,
    EventSuppressionScheduleUpdate,
    EventSuppressionScheduleResponse,
)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.services.config_log_service import (
    log_config_change_async, get_identifier, get_changed_fields, model_to_dict,
)
from app.services.event_suppression_service import suppression_status, get_active_schedules
from app.utils.datetime import utc_now, to_utc
from app.utils.enums import (
    EnumConfigResourceType, EnumConfigActionType,
    EnumSuppressionTargetType, EnumSuppressionStatus,
)

router = APIRouter(prefix="/event-suppression-schedules")


def _to_response(s: EventSuppressionSchedule, now=None) -> EventSuppressionScheduleResponse:
    """ORM → Response(파생 status 포함)."""
    return EventSuppressionScheduleResponse(
        id=s.id,
        name=s.name,
        description=s.description,
        target_type=s.target_type,
        target_device_id=s.target_device_id,
        target_group_id=s.target_group_id,
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


async def _assert_target_exists(db: AsyncSession, target_type, target_device_id, target_group_id):
    """대상 존재 검증(400). DEVICE→devices, GROUP→device_groups. ALL→무검증."""
    if target_type == EnumSuppressionTargetType.DEVICE:
        dev = (await db.execute(select(Device.id).where(Device.id == target_device_id))).scalar()
        if dev is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"success": False, "message": f"Device id {target_device_id} not found"})
    elif target_type == EnumSuppressionTargetType.GROUP:
        grp = (await db.execute(select(DeviceGroup.id).where(DeviceGroup.id == target_group_id))).scalar()
        if grp is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail={"success": False, "message": f"DeviceGroup id {target_group_id} not found"})


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
    """이벤트 억제 스케줄 생성(정비 창 추가).

    - **target_type**: device / group / all
    - **event_scope**: connection / detection / malfunction / all
    - **window_start~window_end**: 억제 시간창(종료 필수, 자동 만료)
    - **target_side**: 감지/감시 필터(group·all 적용, 기본 both)
    """
    await _assert_target_exists(db, data.target_type, data.target_device_id, data.target_group_id)

    schedule = EventSuppressionSchedule(
        name=data.name,
        description=data.description,
        target_type=data.target_type,
        target_device_id=data.target_device_id if data.target_type == EnumSuppressionTargetType.DEVICE else None,
        target_group_id=data.target_group_id if data.target_type == EnumSuppressionTargetType.GROUP else None,
        target_side=data.target_side,
        event_scope=data.event_scope,
        window_start=data.window_start,
        window_end=data.window_end,
        recurrence_rule=data.recurrence_rule,
        created_by=(current_user.id if current_user else None),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SUPPRESSION_SCHEDULE,
        resource_id=schedule.id,
        resource_name=f"SuppressionSchedule-{schedule.id} ({schedule.name})",
        action=EnumConfigActionType.CREATED,
        after_state=get_identifier(schedule),
        description="EventSuppressionSchedule 생성",
    )

    return ApiSingleResponse(
        success=True, message="억제 스케줄 생성 성공", data=_to_response(schedule),
    )


@router.get("", response_model=ApiResponse[list[EventSuppressionScheduleResponse]],
            dependencies=[Depends(require_perm_optional_async("events", "view"))])
async def list_suppression_schedules(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    status_filter: Optional[EnumSuppressionStatus] = Query(None, alias="status", description="상태 필터"),
    target_type: Optional[EnumSuppressionTargetType] = Query(None, description="대상 유형 필터"),
    device_id: Optional[int] = Query(None, description="대상 장비 ID 필터"),
    group_id: Optional[int] = Query(None, description="대상 그룹 ID 필터"),
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """억제 스케줄 목록(페이지네이션 + 상태/대상 필터)."""
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
        conds.append(EventSuppressionSchedule.target_device_id == device_id)
    if group_id is not None:
        conds.append(EventSuppressionSchedule.target_group_id == group_id)

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
    s = (await db.execute(
        select(EventSuppressionSchedule).where(EventSuppressionSchedule.id == schedule_id)
    )).scalars().first()
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
    """억제 스케줄 부분 수정(창/스코프/side/유형)."""
    s = (await db.execute(
        select(EventSuppressionSchedule).where(EventSuppressionSchedule.id == schedule_id)
    )).scalars().first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"success": False, "message": f"SuppressionSchedule {schedule_id} not found"})

    before_state = model_to_dict(s)
    fields = data.model_dump(exclude_unset=True)
    for k, v in fields.items():
        setattr(s, k, v)

    # target_type 에 맞지 않는 이전 스코프 FK 정리(H4a — POST 와 동일 규칙, stale FK 잔존 방지)
    if s.target_type == EnumSuppressionTargetType.DEVICE:
        s.target_group_id = None
    elif s.target_type == EnumSuppressionTargetType.GROUP:
        s.target_device_id = None
    elif s.target_type == EnumSuppressionTargetType.ALL:
        s.target_device_id = None
        s.target_group_id = None

    # 최종 상태 정합 검증(창 순서 — UTC 정규화 후 비교로 naive/aware TypeError→500 회피, H3/NFR-03)
    _ws, _we = to_utc(s.window_start), to_utc(s.window_end)
    if _ws is not None and _we is not None and _we <= _ws:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"success": False, "message": "window_end must be after window_start"})
    if s.target_type == EnumSuppressionTargetType.DEVICE and s.target_device_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"success": False, "message": "target_device_id required when target_type=device"})
    if s.target_type == EnumSuppressionTargetType.GROUP and s.target_group_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"success": False, "message": "target_group_id required when target_type=group"})
    await _assert_target_exists(db, s.target_type, s.target_device_id, s.target_group_id)

    await db.commit()
    await db.refresh(s)

    after_state = model_to_dict(s)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
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

    return ApiSingleResponse(success=True, message="억제 스케줄 수정 성공", data=_to_response(s))


@router.delete("/{schedule_id}", response_model=ApiSingleResponse[EventSuppressionScheduleResponse],
               dependencies=[Depends(require_perm_optional_async("events", "delete"))])
async def delete_suppression_schedule(
    schedule_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """억제 스케줄 삭제(soft-cancel = revoked_at 세팅 + is_active=false)."""
    s = (await db.execute(
        select(EventSuppressionSchedule).where(EventSuppressionSchedule.id == schedule_id)
    )).scalars().first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"success": False, "message": f"SuppressionSchedule {schedule_id} not found"})

    if s.revoked_at is None:
        s.revoked_at = utc_now()
    s.is_active = False
    await db.commit()
    await db.refresh(s)

    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SUPPRESSION_SCHEDULE,
        resource_id=s.id,
        resource_name=f"SuppressionSchedule-{s.id} ({s.name})",
        action=EnumConfigActionType.DELETED,
        before_state=get_identifier(s),
        description="EventSuppressionSchedule soft-cancel",
    )

    return ApiSingleResponse(success=True, message="억제 스케줄 삭제(취소) 성공", data=_to_response(s))
