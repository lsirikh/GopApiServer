"""
Connection Event API endpoints

PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
- device_id: Device FK (기존 controller, sensor, type_device 대체)
- device_description: Device 정보 스냅샷 (자동 생성)
- Response에 device nested 객체 포함 (Optional, Device 삭제 시 null)
- group_event 필드 제거됨

v6.0 P8 (VeryComplex 라우터 async 전환):
- get_db → get_async_db (Session → AsyncSession)
- get_current_account_user_optional → _async
- log_config_change → log_config_change_async
- db.query(...).filter/all/first → select().where() + await db.execute()
- db.commit/refresh/delete → await
- 응답 스키마 완전 유지 (Polymorphic device nested 포함).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, selectin_polymorphic
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async, require_perm_optional_async
from app.services.event_suppression_service import is_suppressed, record_suppression, suppressed_response
from app.models.event import ConnectionEvent
from app.models.device import Device, Sensor, Controller, Camera, Speaker, Enclosure, Lamp
from app.models.device_group import DeviceGroupMapping
from app.schemas.event import ConnectionEventCreate, ConnectionEventReplace, ConnectionEventResponse, ConnectionEventUpdate
from app.schemas.device import (
    DeviceGroupNestedResponse,
    DeviceNestedResponse,
    SensorNestedResponse,
    ControllerNestedResponse,
    CameraNestedResponse,
    SpeakerNestedResponse,
    LampNestedResponse,
)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.utils.enums import EnumDeviceType, EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change_async, get_changed_fields, model_to_dict
from typing import Union

router = APIRouter(tags=[])


def _generate_device_description(device: Device) -> str:
    """
    Device 정보 스냅샷 문자열 생성
    형식: "[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
    """
    return f"[{device.type_device.value}] {device.name_device} (number: {device.number_device}, id: {device.id})"


async def _build_device_nested_response(device: Optional[Device], db: AsyncSession) -> Optional[Union[SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse, SpeakerNestedResponse, LampNestedResponse, DeviceNestedResponse]]:
    """
    Device 객체를 타입에 맞는 Nested Response로 변환 (Polymorphic)

    PRD v1.1: Device 삭제 시 None 반환
    PRD v1.2: device_groups 필드 추가 (EventMapping 연동 필수)
    PRD v2.7: Device 타입별 Polymorphic Response 반환
    - Sensor → SensorNestedResponse
    - Controller → ControllerNestedResponse
    - Camera → CameraNestedResponse
    - Speaker → SpeakerNestedResponse
    - Enclosure → DeviceNestedResponse (전용 NestedResponse 없음)
    - Lamp → LampNestedResponse

    v6.0 P1 (Tidy First): lazy='dynamic' 접근을 명시적 db.query()로 교체
    (동작 불변, sync/async 양쪽 안전).
    v6.0 P8: AsyncSession 기반 select() + await 로 전환.
    """
    if device is None:
        return None

    # PRD v1.2: Build device_groups from group_mappings relationship
    # v6.0 P8: 명시적 select 쿼리 (AsyncSession)
    device_groups = []
    # v6.0-clone_deploy_bugfix (#3): async 세션에서 mapping.group lazy-load 는
    # greenlet_spawn 오류를 낸다. selectinload 로 eager 로딩 (detection_logs/malfunctions 패턴 동일).
    mappings_result = await db.execute(
        select(DeviceGroupMapping)
        .options(selectinload(DeviceGroupMapping.group))
        .where(DeviceGroupMapping.device_id == device.id)
    )
    mappings = mappings_result.scalars().all()
    for mapping in mappings:
        if mapping.group:
            device_groups.append(DeviceGroupNestedResponse(
                id=mapping.group.id,
                name=mapping.group.name
            ))

    # PRD v2.7: Polymorphic Response - Device 타입에 따라 적절한 스키마 반환
    if isinstance(device, Sensor):
        return SensorNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            version=device.version,
            status=device.status.value,
            is_enable=device.is_enable,
            controller_id=device.controller_id,
            device_groups=device_groups
        )
    elif isinstance(device, Camera):
        # PRD_Camera_Urls_JsonB.md: urls JSONB 통합 (rtsp_uri/rtsp_port 제거)
        from app.schemas.device import CameraUrls
        urls_data = None
        if device.urls:
            urls_data = CameraUrls.model_validate(device.urls) if isinstance(device.urls, dict) else device.urls
        return CameraNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            version=device.version,
            status=device.status.value,
            is_enable=device.is_enable,
            ip_address=device.ip_address,
            ip_port=device.ip_port,
            mode=device.mode.value if device.mode else "NONE",
            category=device.category.value if device.category else "NONE",
            is_record=device.is_record,
            urls=urls_data,
            device_groups=device_groups
        )
    elif isinstance(device, Controller):
        return ControllerNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            version=device.version,
            status=device.status.value,
            is_enable=device.is_enable,
            ip_address=device.ip_address,
            ip_port=device.ip_port,
            device_groups=device_groups
        )
    elif isinstance(device, Speaker):
        return SpeakerNestedResponse(
            id=device.id,
            category_device=device.category_device.value,
            number_device=device.number_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            status=device.status.value,
            is_enable=device.is_enable,
            speaker_type=device.speaker_type.value if device.speaker_type else "NORMAL",
            geolocation=device.geolocation,
        )
    elif isinstance(device, Lamp):
        return LampNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            version=device.version,
            status=device.status.value,
            is_enable=device.is_enable,
            ip_address=device.ip_address,
            ip_port=device.ip_port,
            user_name=device.user_name,
            description=device.description,
            geolocation=device.geolocation,
        )
    elif isinstance(device, Enclosure):
        return DeviceNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            status=device.status.value,
            is_enable=device.is_enable,
            version=device.version,
            device_groups=device_groups
        )
    else:
        # Fallback: 알 수 없는 Device 타입
        return DeviceNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            status=device.status.value,
            is_enable=device.is_enable,
            version=device.version,
            device_groups=device_groups
        )


@router.get("", response_model=ApiResponse[list[ConnectionEventResponse]])
async def get_connection_events(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    device_id: Optional[int] = Query(None, description="장치 ID로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    연결 이벤트 목록 조회 (페이지네이션)

    PRD v2.1: group_event, controller, sensor, type_device 필드 제거됨

    연결 이벤트 목록을 페이지네이션하여 조회합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **device_id**: 장치 ID로 필터링
    - **start_date**: 시작 날짜로 필터링
    - **end_date**: 종료 날짜로 필터링

    **Response**: 연결 이벤트 목록 및 페이지네이션 정보
    """
    # Build base statements
    stmt = select(ConnectionEvent).options(selectinload(ConnectionEvent.device).selectin_polymorphic([Sensor, Camera, Controller, Speaker, Enclosure, Lamp]))
    count_stmt = select(func.count()).select_from(ConnectionEvent)

    # Apply filters (PRD v2.1: device_id 기반 필터링)
    if device_id is not None:
        stmt = stmt.where(ConnectionEvent.device_id == device_id)
        count_stmt = count_stmt.where(ConnectionEvent.device_id == device_id)
    if start_date is not None:
        stmt = stmt.where(ConnectionEvent.created_at >= start_date)
        count_stmt = count_stmt.where(ConnectionEvent.created_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(ConnectionEvent.created_at <= end_date)
        count_stmt = count_stmt.where(ConnectionEvent.created_at <= end_date)

    # Get total count
    total = (await db.execute(count_stmt)).scalar() or 0

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events_result = await db.execute(
        stmt.order_by(ConnectionEvent.created_at.desc(), ConnectionEvent.id.desc()).offset(skip).limit(limit)
    )
    events = events_result.scalars().all()

    # PRD v2.1: Response uses device_id (no group_event, controller, sensor, type_device)
    # PRD v1.3: device_id, sequence 필드 제거 (device.id에 포함, sequence는 Request 전용)
    # PRD v1.4: category_event 필드 제거 (polymorphic 내부용)
    event_responses = [
        ConnectionEventResponse(
            id=e.id,
            type_event=e.type_event,
            device=await _build_device_nested_response(e.device, db),
            device_description=e.device_description,
            created_at=e.created_at,
            updated_at=e.updated_at
        )
        for e in events
    ]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Connection events retrieved successfully",
        data=event_responses,
        pagination=pagination
    )


@router.get("/{event_id}", response_model=ApiSingleResponse[ConnectionEventResponse])
async def get_connection_event(
    event_id: int,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    연결 이벤트 단건 조회

    특정 연결 이벤트의 상세 정보를 조회합니다.

    **파라미터**:
    - **event_id**: 연결 이벤트 ID (Path Parameter)

    **Response**: 연결 이벤트 상세 정보

    **Error**:
    - 404: 연결 이벤트를 찾을 수 없음
    """
    result = await db.execute(
        select(ConnectionEvent)
        .options(selectinload(ConnectionEvent.device).selectin_polymorphic([Sensor, Camera, Controller, Speaker, Enclosure, Lamp]))
        .where(ConnectionEvent.id == event_id)
    )
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # PRD v2.1: Response uses device_id
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = ConnectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        device=await _build_device_nested_response(event.device, db),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Connection event retrieved successfully",
        data=event_response
    )


@router.post("", response_model=ApiSingleResponse[ConnectionEventResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm_optional_async("events", "edit"))])
async def create_connection_event(
    event_data: ConnectionEventCreate,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    연결 이벤트 생성

    PRD v2.1: device_id로 장치 참조, device_description 자동 생성

    새로운 연결 이벤트를 생성합니다.

    **Request Body**:
    - **type_event**: 이벤트 유형 (필수)
    - **device_id**: 장치 ID (필수)

    **Response**: 생성된 연결 이벤트 정보 (device nested 포함)

    **Error**:
    - 400: Device를 찾을 수 없음
    """
    # PRD v1.1: Validate device_id exists
    device_result = await db.execute(
        select(Device).where(Device.id == event_data.device_id)
    )
    device = device_result.scalars().first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with id {event_data.device_id} not found"
        )

    # 이벤트 억제(정비 창) 게이트 — 억제 창 매치 시 저장·감사 생략(FR-05, db.add 전)
    _suppressed, _sched_id = await is_suppressed(db, device.id, device.category_device, "connection")
    if _suppressed:
        record_suppression(device.id, "connection", _sched_id)
        return suppressed_response("connection", _sched_id)

    # PRD v1.1: Generate device_description automatically
    device_description = _generate_device_description(device)

    # Create new connection event with device_id
    # PRD v2.1: group_event, sequence 필드 제거됨
    new_event = ConnectionEvent(
        category_event="connection",  # Polymorphic discriminator
        type_event=event_data.type_event,
        device_id=event_data.device_id,
        device_description=device_description
    )

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.CONNECTION_EVENT,
        resource_id=new_event.id,
        resource_name=f"ConnectionEvent-{new_event.id} ({new_event.type_event})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": new_event.id, "type_event": new_event.type_event},
        description="ConnectionEvent 생성"
    )

    # Build device nested response
    device_nested = await _build_device_nested_response(device, db)

    # PRD v2.1: Response uses device_id (no group_event, controller, sensor, type_device)
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = ConnectionEventResponse(
        id=new_event.id,
        type_event=new_event.type_event,
        device=device_nested,
        device_description=new_event.device_description,
        created_at=new_event.created_at,
        updated_at=new_event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Connection event created successfully",
        data=event_response
    )


@router.patch("/{event_id}", response_model=ApiSingleResponse[ConnectionEventResponse])
async def update_connection_event(
    event_id: int,
    event_data: ConnectionEventUpdate,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    연결 이벤트 부분 수정 (PATCH)

    PRD v2.1: device_id 기반으로 변경됨

    연결 이벤트의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **event_id**: 연결 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **type_event**: 이벤트 유형

    **Response**: 수정된 연결 이벤트 정보

    **Error**:
    - 404: 연결 이벤트를 찾을 수 없음
    """
    result = await db.execute(
        select(ConnectionEvent)
        .options(selectinload(ConnectionEvent.device).selectin_polymorphic([Sensor, Camera, Controller, Speaker, Enclosure, Lamp]))
        .where(ConnectionEvent.id == event_id)
    )
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(event)

    # Update fields if provided (PRD v2.1: only type_event is updatable, sequence 제거됨)
    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        # Only allow updating type_event
        if field in ['type_event']:
            setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(event)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        await log_config_change_async(
            db=db,
            resource_type=EnumConfigResourceType.CONNECTION_EVENT,
            resource_id=event.id,
            resource_name=f"ConnectionEvent-{event.id} ({event.type_event})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="ConnectionEvent 수정"
        )

    # PRD v2.1: Response uses device_id
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = ConnectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        device=await _build_device_nested_response(event.device, db),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Connection event updated successfully",
        data=event_response
    )


@router.put("/{event_id}", response_model=ApiSingleResponse[ConnectionEventResponse])
async def replace_connection_event(
    event_id: int,
    event_data: ConnectionEventReplace,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    연결 이벤트 전체 수정 (PUT)

    PRD v4.8 Phase 12-7b: device_id / device_description 변경 원천 차단
    - device_id: PUT으로 수정 불가 (v2.1 불변식 — device 바인딩은 생성 시점에 확정)
    - device_description: Device 스냅샷 보존 (생성 시점 값 유지)
    - device 재지정이 필요하면 DELETE 후 POST로 재생성

    연결 이벤트의 필드를 교체합니다. (device 바인딩 제외)

    **파라미터**:
    - **event_id**: 연결 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수, device_id/device_description 전송 시 422):
    - **type_event**: 이벤트 유형

    **자동 관리**:
    - **device / device_description**: 생성 시 바인딩된 값 유지 (Phase 12-7b)

    **Response**: 수정된 연결 이벤트 정보

    **Error**:
    - 404: 연결 이벤트를 찾을 수 없음
    - 422: device_id/device_description 등 금지 필드 전송
    """
    result = await db.execute(
        select(ConnectionEvent).where(ConnectionEvent.id == event_id)
    )
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # Replace allowed fields only (PUT = full replacement, device 바인딩 제외)
    # PRD v4.8 Phase 12-7b: device_id / device_description는 변경 불가 (스냅샷 보존)
    event.type_event = event_data.type_event
    # event.device_id / event.device_description는 변경하지 않음 (Phase 12-7b)

    await db.commit()
    await db.refresh(event)

    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = ConnectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        device=await _build_device_nested_response(event.device, db),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Connection event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiSingleResponse[None])
async def delete_connection_event(
    event_id: int,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    연결 이벤트 삭제

    특정 연결 이벤트를 삭제합니다.

    **파라미터**:
    - **event_id**: 연결 이벤트 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 연결 이벤트를 찾을 수 없음
    """
    result = await db.execute(
        select(ConnectionEvent).where(ConnectionEvent.id == event_id)
    )
    event = result.scalars().first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = event.id
    deleted_identifier = {"id": event.id, "type_event": event.type_event}
    deleted_name = f"ConnectionEvent-{event.id} ({event.type_event})"

    await db.delete(event)
    await db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.CONNECTION_EVENT,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="ConnectionEvent 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message=f"Connection event {event_id} deleted successfully",
        data=None
    )
