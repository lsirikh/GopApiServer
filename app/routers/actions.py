"""
Action Event API endpoints

PRD v1.3: from_event에 device nested 포함
- device_id, sequence 필드 제거
- device: DeviceNestedResponse (Optional, Device 삭제 시 null)

PRD v1.5: from_type_event 필드 제거
- from_event_id만으로 원본 이벤트 참조 (polymorphic relationship으로 타입 자동 확인)

v6.0 P8 (VeryComplex): 라우터 async 전환
- Session → AsyncSession, get_db → get_async_db
- get_current_account_user_optional → _async, require_perm_optional → _async
- log_config_change → log_config_change_async (P6)
- polymorphic Event + Device 를 selectin_polymorphic + selectinload 로 eager-load
- source_event / device / group 모두 명시 preload → MissingGreenlet 회피
- 응답 스키마 100% 유지
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectin_polymorphic, selectinload
from typing import Optional, Union
from datetime import datetime, timezone, timedelta
from app.utils.datetime import to_utc, utc_now
import math

_KST = timezone(timedelta(hours=9))


def _to_kst_naive(dt_val: datetime | None) -> datetime | None:
    """timezone-aware datetime → KST naive (DB 저장용). naive는 이미 KST로 간주."""
    # datetime-unification: 입력을 aware UTC 로 정규화(timestamptz 저장/비교용, naive는 DISPLAY_TZ 간주)
    return to_utc(dt_val)


from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async, require_perm_optional_async
from app.models.event import ActionEvent, Event, DetectionEvent, MalfunctionEvent, ConnectionEvent
from app.models.device import Device, Controller, Sensor, Camera, Speaker, Enclosure, Lamp
from app.models.device_group import DeviceGroupMapping
from app.schemas.event import (
    ActionEventCreate, ActionEventReplace, ActionEventResponse, ActionEventUpdate,
    DetectionEventResponse, MalfunctionEventResponse, ConnectionEventResponse
)
from app.schemas.device import DeviceNestedResponse, DeviceGroupNestedResponse
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.utils.enums import EnumTrueFalse, EnumConfigResourceType, EnumConfigActionType, EnumDeviceStatus
from app.services.config_log_service import log_config_change_async, get_changed_fields, model_to_dict

router = APIRouter(tags=[])


# ─── Polymorphic type registries (async loader options) ───────────────────
_EVENT_POLYMORPHIC_TYPES = [DetectionEvent, MalfunctionEvent, ConnectionEvent]
_DEVICE_POLYMORPHIC_TYPES = [Controller, Sensor, Camera, Speaker, Enclosure, Lamp]


def _source_event_load_options():
    """Event 하위 폴리모픽 + device(폴리모픽) eager-load 옵션.

    v6.0 P8: source_event · source_event.device · device 하위 subtype 컬럼(ip_address 등)
    모두 selectin 으로 pre-fetch — async 라우터에서 lazy-load 트리거 금지.
    """
    return [
        selectin_polymorphic(Event, _EVENT_POLYMORPHIC_TYPES),
        selectinload(Event.device).selectin_polymorphic(_DEVICE_POLYMORPHIC_TYPES),
    ]


async def _load_source_event(db: AsyncSession, event_id: int) -> Optional[Event]:
    """단일 원본 Event 를 폴리모픽 + device 포함하여 async 로드."""
    stmt = select(Event).options(*_source_event_load_options()).where(Event.id == event_id)
    return (await db.execute(stmt)).scalars().first()


async def _build_device_nested_response(device: Optional[Device], db: AsyncSession) -> Optional[DeviceNestedResponse]:
    """
    Device 객체를 DeviceNestedResponse로 변환

    PRD v1.3: from_event 내 device nested 포함

    v6.0 P1 (Tidy First): lazy='dynamic' `device.group_mappings.all()` 제거 →
    명시적 `DeviceGroupMapping` 쿼리로 교체 (async 안전)

    v6.0 P8 (async): `db.execute(select(...))` 로 재작성 + mapping.group 은
    selectinload 로 pre-fetch (lazy-load 회피)
    """
    if device is None:
        return None

    # Build device_groups from group_mappings (async — selectinload group)
    device_groups = []
    mappings = (await db.execute(
        select(DeviceGroupMapping)
        .options(selectinload(DeviceGroupMapping.group))
        .where(DeviceGroupMapping.device_id == device.id)
    )).scalars().all()
    for mapping in mappings:
        if mapping.group:
            device_groups.append(DeviceGroupNestedResponse(
                id=mapping.group.id,
                name=mapping.group.name
            ))

    # PRD_Camera_Urls_JsonB.md: urls JSONB 통합 (rtsp_uri/rtsp_port 제거)
    from app.schemas.device import CameraUrls
    urls_data = None
    raw_urls = getattr(device, 'urls', None)
    if raw_urls:
        urls_data = CameraUrls.model_validate(raw_urls) if isinstance(raw_urls, dict) else raw_urls

    return DeviceNestedResponse(
        id=device.id,
        number_device=device.number_device,
        group_device=device.group_device,
        name_device=device.name_device,
        type_device=device.type_device.value,
        status=device.status.value,
        is_enable=device.is_enable,
        version=device.version,
        ip_address=getattr(device, 'ip_address', None),
        ip_port=getattr(device, 'ip_port', None),
        controller_id=getattr(device, 'controller_id', None),
        mode=getattr(device, 'mode', None).value if hasattr(device, 'mode') and getattr(device, 'mode', None) else None,
        category=getattr(device, 'category', None).value if hasattr(device, 'category') and getattr(device, 'category', None) else None,
        is_record=getattr(device, 'is_record', None),
        urls=urls_data,
        device_groups=device_groups
    )


# Helper function to update source event action_reported
async def update_source_action_reported(db: AsyncSession, source_event: Event) -> None:
    """
    ActionEvent 생성 시 원본 이벤트의 action_reported 필드를 "True"로 업데이트

    PRD v1.5: polymorphic relationship을 통해 이벤트 타입 자동 확인

    Args:
        db: 데이터베이스 세션
        source_event: 원본 이벤트 객체 (polymorphic - DetectionEvent, MalfunctionEvent, ConnectionEvent)

    Note:
        DetectionEvent와 MalfunctionEvent만 action_reported 필드를 가집니다.
        ConnectionEvent는 건너뜁니다.
    """
    if source_event is None:
        return

    # DetectionEvent와 MalfunctionEvent만 action_reported 필드를 가짐
    if isinstance(source_event, (DetectionEvent, MalfunctionEvent)):
        source_event.action_reported = "True"
        await db.commit()


# Helper function to reset source event action_reported
async def reset_source_action_reported(db: AsyncSession, source_event: Event, excluding_action_id: int) -> None:
    """
    ActionEvent 삭제 시 원본 이벤트의 action_reported 필드를 카운트 기반으로 관리

    PRD: PRD_ActionEvent_1N_Refactoring.md v2.0
    - 삭제 대상 ActionEvent를 제외하고 남은 ActionEvent 수를 확인
    - 0개이면 "False", 1개 이상이면 "True" 유지

    Args:
        db: 데이터베이스 세션
        source_event: 원본 이벤트 객체 (polymorphic)
        excluding_action_id: 삭제 대상 ActionEvent ID (카운트에서 제외)

    Note:
        DetectionEvent와 MalfunctionEvent만 action_reported 필드를 가집니다.
        ConnectionEvent는 건너뜁니다.
        이 함수는 커밋하지 않습니다 - 호출자가 커밋해야 합니다.
    """
    if source_event is None:
        return

    # DetectionEvent와 MalfunctionEvent만 action_reported 필드를 가짐
    if isinstance(source_event, (DetectionEvent, MalfunctionEvent)):
        remaining_count = (await db.execute(
            select(func.count()).select_from(ActionEvent).where(
                ActionEvent.from_event_id == source_event.id,
                ActionEvent.id != excluding_action_id,
            )
        )).scalar() or 0
        if remaining_count == 0:
            source_event.action_reported = "False"


# Helper function to build source event response from polymorphic event
async def build_source_event_response(event: Event, db: AsyncSession) -> Union[DetectionEventResponse, MalfunctionEventResponse, ConnectionEventResponse]:
    """
    Polymorphic Event 객체를 적절한 응답 스키마로 변환

    PRD v1.3: device nested 포함, device_id/sequence 제외
    PRD v1.4: category_event 필드 제거
    PRD v1.5: polymorphic relationship을 통해 이벤트 타입 자동 확인

    v6.0 P1 (Tidy First): `db` 인자 추가 — 하위 `_build_device_nested_response`
    가 명시적 DeviceGroupMapping 쿼리를 수행하기 위함
    v6.0 P8 (async): async 함수화 — 내부 device nested 도 await

    Args:
        event: 원본 이벤트 객체 (polymorphic - DetectionEvent, MalfunctionEvent, ConnectionEvent)
        db: 데이터베이스 세션 (device_groups 조회용)

    Returns:
        DetectionEventResponse, MalfunctionEventResponse, 또는 ConnectionEventResponse
    """
    if isinstance(event, DetectionEvent):
        device_nested = await _build_device_nested_response(event.device, db)
        return DetectionEventResponse(
            id=event.id,
            type_event=event.type_event,
            action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
            result=event.result.value,
            device=device_nested,
            device_description=event.device_description,
            detail=event.detail,
            created_at=event.created_at,
            updated_at=event.updated_at
        )
    elif isinstance(event, MalfunctionEvent):
        device_nested = await _build_device_nested_response(event.device, db)
        return MalfunctionEventResponse(
            id=event.id,
            type_event=event.type_event,
            action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
            reason=event.reason.value,
            device=device_nested,
            device_description=event.device_description,
            detail=event.detail,
            created_at=event.created_at,
            updated_at=event.updated_at
        )
    elif isinstance(event, ConnectionEvent):
        device_nested = await _build_device_nested_response(event.device, db)
        return ConnectionEventResponse(
            id=event.id,
            type_event=event.type_event,
            device=device_nested,
            device_description=event.device_description,
            created_at=event.created_at,
            updated_at=event.updated_at
        )
    else:
        # Base Event 클래스인 경우 (should not happen in normal operation)
        raise ValueError(f"Unknown event type: {type(event).__name__}")


@router.get("", response_model=ApiResponse[list[ActionEventResponse]])
async def get_action_events(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    user: Optional[str] = Query(None, description="사용자로 필터링"),
    from_event_id: Optional[int] = Query(None, description="원본 이벤트 ID로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    조치 이벤트 목록 조회 (페이지네이션)

    PRD v1.5: polymorphic relationship을 통해 원본 이벤트 자동 로드

    조치 이벤트 목록을 페이지네이션하여 조회합니다. 각 조치 이벤트의 `from_event` 필드에는
    원본 이벤트(탐지, 장애, 연결)의 전체 데이터가 포함됩니다.

    응답은 배치 로딩을 사용하여 성능을 최적화합니다 - 모든 원본 이벤트는 단일 쿼리로
    로드되어 N+1 쿼리 문제를 방지합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **user**: 조치를 수행한 사용자로 필터링
    - **from_event_id**: 원본 이벤트 ID로 필터링
    - **start_date**: 시작 날짜로 필터링
    - **end_date**: 종료 날짜로 필터링

    **Response**: 조치 이벤트 목록 및 페이지네이션 정보 (각 이벤트에 중첩된 원본 이벤트 포함)
    """
    # Build filters
    filters = []
    if user is not None:
        filters.append(ActionEvent.user == user)
    if from_event_id is not None:
        filters.append(ActionEvent.from_event_id == from_event_id)
    if start_date is not None:
        filters.append(ActionEvent.created_at >= start_date)
    if end_date is not None:
        filters.append(ActionEvent.created_at <= end_date)

    # Get total count
    count_stmt = select(func.count()).select_from(ActionEvent)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events_stmt = select(ActionEvent)
    if filters:
        events_stmt = events_stmt.where(*filters)
    events_stmt = (
        events_stmt
        .order_by(ActionEvent.created_at.desc(), ActionEvent.id.desc())
        .offset(skip)
        .limit(limit)
    )
    events = (await db.execute(events_stmt)).scalars().all()

    # Batch load source events to avoid N+1 query problem
    # PRD v1.5: Polymorphic relationship을 통해 단일 쿼리로 원본 이벤트 로드
    source_event_ids = [e.from_event_id for e in events if e.from_event_id is not None]

    # Query Event base class with polymorphic loading (automatically loads subtypes)
    event_map = {}
    if source_event_ids:
        source_stmt = (
            select(Event)
            .options(*_source_event_load_options())
            .where(Event.id.in_(source_event_ids))
        )
        source_events = (await db.execute(source_stmt)).scalars().all()
        for source_event in source_events:
            event_map[source_event.id] = await build_source_event_response(source_event, db)

    # Convert to response format with nested source events
    event_responses = []
    for e in events:
        source_event = event_map.get(e.from_event_id)
        if source_event is None:
            # Skip events with missing source (should not happen in normal operation)
            continue

        event_responses.append(
            ActionEventResponse(
                id=e.id,
                type_event=e.type_event,
                content=e.content,
                user=e.user,
                from_event=source_event,  # Nested event object
                created_at=e.created_at,
                updated_at=e.updated_at
            )
        )

    # Update total based on actual returned events
    # (events with missing source are skipped, so recalculate)
    skipped_count = len(events) - len(event_responses)
    if skipped_count > 0:
        total = total - skipped_count
        total_pages = math.ceil(total / limit) if total > 0 else 1

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Action events retrieved successfully",
        data=event_responses,
        pagination=pagination
    )


@router.get("/{event_id}", response_model=ApiSingleResponse[ActionEventResponse])
async def get_action_event(
    event_id: int,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    조치 이벤트 단건 조회

    PRD v1.5: polymorphic relationship을 통해 원본 이벤트 자동 로드

    특정 조치 이벤트의 상세 정보를 조회합니다. `from_event` 필드에는
    원본 이벤트(탐지, 장애, 연결)의 전체 데이터가 포함됩니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Response**: 조치 이벤트 상세 정보 (중첩된 원본 이벤트 객체 포함)

    **Error**:
    - 404: 조치 이벤트 또는 원본 이벤트를 찾을 수 없음
    """
    event = (await db.execute(
        select(ActionEvent).where(ActionEvent.id == event_id)
    )).scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # Load nested source event via polymorphic query (async — no lazy load)
    source_event = None
    if event.from_event_id is not None:
        source_event = await _load_source_event(db, event.from_event_id)
    if source_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source event with id {event.from_event_id} not found"
        )

    source_event_response = await build_source_event_response(source_event, db)

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event=source_event_response,  # Nested event object
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Action event retrieved successfully",
        data=event_response
    )


@router.post("", response_model=ApiSingleResponse[ActionEventResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm_optional_async("events", "edit"))])
async def create_action_event(
    event_data: ActionEventCreate,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    조치 이벤트 생성

    PRD v1.5: from_type_event 필드 제거 - from_event_id만으로 원본 이벤트 참조

    새로운 조치 이벤트를 생성합니다. 이 엔드포인트는 다형성 참조를 사용하여
    원본 이벤트(탐지, 장애, 연결)를 참조하는 조치 이벤트를 생성합니다.

    **Request Body**:
    - **type_event**: 이벤트 유형 (필수)
    - **content**: 조치 내용 설명 (필수)
    - **user**: 조치를 수행한 사용자 (필수)
    - **from_event_id**: 원본 이벤트 ID (필수)
    - **created_at**: 조치 일시 (선택)

    **Response**: 생성된 조치 이벤트 정보 (중첩된 원본 이벤트 객체 포함)

    **Error**:
    - 404: 참조된 원본 이벤트를 찾을 수 없음
    """
    # Verify source event exists (polymorphic query with device/subtype preload)
    source_event = await _load_source_event(db, event_data.from_event_id)
    if not source_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source event with id {event_data.from_event_id} not found"
        )

    # PRD_Malfunction_Device_Status v1.1: 조치 완료 시 원본 장비 ACTIVATED 복구
    if source_event.device_id:
        device = (await db.execute(
            select(Device).where(Device.id == source_event.device_id)
        )).scalars().first()
        if device:
            device.status = EnumDeviceStatus.ACTIVATED

    # Create new action event
    new_event = ActionEvent(
        type_event=event_data.type_event,
        content=event_data.content,
        user=event_data.user,
        from_event_id=event_data.from_event_id,
        created_at=_to_kst_naive(event_data.created_at)
    )

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.ACTION_EVENT,
        resource_id=new_event.id,
        resource_name=f"ActionEvent-{new_event.id} ({new_event.type_event})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": new_event.id, "type_event": new_event.type_event},
        description="ActionEvent 생성"
    )

    # Update source event's action_reported to "True" (only for Detection and Malfunction events)
    await update_source_action_reported(db, source_event)

    # Build response with nested source event
    source_event_response = await build_source_event_response(source_event, db)

    event_response = ActionEventResponse(
        id=new_event.id,
        type_event=new_event.type_event,
        content=new_event.content,
        user=new_event.user,
        from_event=source_event_response,  # Nested event object
        created_at=new_event.created_at,
        updated_at=new_event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Action event created successfully",
        data=event_response
    )


@router.patch("/{event_id}", response_model=ApiSingleResponse[ActionEventResponse], dependencies=[Depends(require_perm_optional_async("events", "edit"))])
async def update_action_event(
    event_id: int,
    event_data: ActionEventUpdate,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    조치 이벤트 부분 수정 (PATCH)

    PRD v1.5: from_type_event 필드 제거 - polymorphic relationship 사용

    조치 이벤트의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **type_event**: 이벤트 유형
    - **content**: 조치 내용 설명
    - **user**: 조치를 수행한 사용자

    **주의**: from_event_id는 PATCH로 변경 불가 (PRD v1.6 + v4.8 Phase 12). 전송 시 422 거부.
    원본 이벤트 재지정이 필요하면 DELETE 후 POST로 재생성하세요.

    **Response**: 수정된 조치 이벤트 정보

    **Error**:
    - 404: 조치 이벤트를 찾을 수 없음
    - 422: from_event_id 포함 시 (extra="forbid")
    """
    event = (await db.execute(
        select(ActionEvent).where(ActionEvent.id == event_id)
    )).scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(event)

    # Update fields if provided
    # PRD v1.6 + v4.8 Phase 12: from_event_id 차단 — ActionEventUpdate 스키마에서 제거됨 (Pydantic 422 자동)
    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(event)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        await log_config_change_async(
            db=db,
            resource_type=EnumConfigResourceType.ACTION_EVENT,
            resource_id=event.id,
            resource_name=f"ActionEvent-{event.id} ({event.type_event})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="ActionEvent 수정"
        )

    # Load nested source event via polymorphic query (async — no lazy load)
    source_event = None
    if event.from_event_id is not None:
        source_event = await _load_source_event(db, event.from_event_id)
    if source_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source event with id {event.from_event_id} not found"
        )

    source_event_response = await build_source_event_response(source_event, db)

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event=source_event_response,  # Nested event object
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Action event updated successfully",
        data=event_response
    )


@router.put("/{event_id}", response_model=ApiSingleResponse[ActionEventResponse], dependencies=[Depends(require_perm_optional_async("events", "edit"))])
async def replace_action_event(
    event_id: int,
    event_data: ActionEventReplace,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    조치 이벤트 전체 수정 (PUT)

    PRD v1.6 + v4.8 Phase 12: from_event_id 변경 원천 차단 (차장님 결재)

    조치 이벤트의 type_event/content/user 필드를 교체합니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **type_event**: 이벤트 유형
    - **content**: 조치 내용 설명
    - **user**: 조치를 수행한 사용자

    **주의**: from_event_id는 PUT으로 변경 불가 (PRD v1.6). 전송 시 422 거부.
    원본 이벤트 재지정이 필요하면 DELETE 후 POST로 재생성하세요.

    **Response**: 수정된 조치 이벤트 정보

    **Error**:
    - 404: 조치 이벤트를 찾을 수 없음
    - 422: from_event_id 포함 시 (extra="forbid")
    """
    event = (await db.execute(
        select(ActionEvent).where(ActionEvent.id == event_id)
    )).scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # PRD v1.6 + v4.8 Phase 12: from_event_id 차단 — ActionEventReplace 스키마에서 제거됨
    # 기존 event.from_event_id 보존, source_event 는 폴리모픽 쿼리로 재조회 (async safe)
    source_event = None
    if event.from_event_id is not None:
        source_event = await _load_source_event(db, event.from_event_id)
    if source_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source event with id {event.from_event_id} not found"
        )

    # Replace fields (PUT = full replacement, from_event_id 제외)
    event.type_event = event_data.type_event
    event.content = event_data.content
    event.user = event_data.user
    # event.from_event_id 는 절대 수정하지 않음 (PRD v1.6)

    await db.commit()
    await db.refresh(event)

    # Build response with nested source event
    source_event_response = await build_source_event_response(source_event, db)

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event=source_event_response,  # Nested event object
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Action event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiSingleResponse[None], dependencies=[Depends(require_perm_optional_async("events", "delete"))])
async def delete_action_event(
    event_id: int,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    조치 이벤트 삭제

    PRD v1.5: polymorphic relationship을 통해 원본 이벤트 자동 로드

    특정 조치 이벤트를 삭제합니다. 삭제 시 원본 이벤트의 action_reported 필드가
    "False"로 리셋됩니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 조치 이벤트를 찾을 수 없음
    """
    event = (await db.execute(
        select(ActionEvent).where(ActionEvent.id == event_id)
    )).scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = event.id
    deleted_identifier = {"id": event.id, "type_event": event.type_event}
    deleted_name = f"ActionEvent-{event.id} ({event.type_event})"

    # Reset source event's action_reported based on remaining count (1:N relationship)
    # PRD: PRD_ActionEvent_1N_Refactoring.md v2.0
    # v6.0 P8 (async): source_event 를 폴리모픽 쿼리로 재조회 (event.source_event lazy 접근 금지)
    source_event = None
    if event.from_event_id is not None:
        source_event = await _load_source_event(db, event.from_event_id)
    await reset_source_action_reported(db, source_event, excluding_action_id=event.id)

    await db.delete(event)
    await db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.ACTION_EVENT,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="ActionEvent 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message=f"Action event {event_id} deleted successfully",
        data=None
    )
