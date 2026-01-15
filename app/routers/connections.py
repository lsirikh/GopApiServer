"""
Connection Event API endpoints

PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
- device_id: Device FK (기존 controller, sensor, type_device 대체)
- device_description: Device 정보 스냅샷 (자동 생성)
- Response에 device nested 객체 포함 (Optional, Device 삭제 시 null)
- group_event 필드 제거됨
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.event import ConnectionEvent
from app.models.device import Device, Sensor, Controller, Camera
from app.schemas.event import ConnectionEventCreate, ConnectionEventResponse, ConnectionEventUpdate
from app.schemas.device import (
    DeviceGroupNestedResponse,
    SensorNestedResponse,
    ControllerNestedResponse,
    CameraNestedResponse
)
from app.schemas.common import ApiResponse, PaginationMeta
from app.utils.enums import EnumDeviceType
from typing import Union

router = APIRouter(tags=[])


def _generate_device_description(device: Device) -> str:
    """
    Device 정보 스냅샷 문자열 생성
    형식: "[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
    """
    return f"[{device.type_device.value}] {device.name_device} (number: {device.number_device}, id: {device.id})"


def _build_device_nested_response(device: Optional[Device]) -> Optional[Union[SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse]]:
    """
    Device 객체를 타입에 맞는 Nested Response로 변환 (Polymorphic)

    PRD v1.1: Device 삭제 시 None 반환
    PRD v1.2: device_groups 필드 추가 (EventMapping 연동 필수)
    PRD v2.7: Device 타입별 Polymorphic Response 반환
    - Sensor → SensorNestedResponse
    - Controller → ControllerNestedResponse
    - Camera → CameraNestedResponse
    """
    if device is None:
        return None

    # PRD v1.2: Build device_groups from group_mappings relationship
    device_groups = []
    if hasattr(device, 'group_mappings') and device.group_mappings is not None:
        mappings = device.group_mappings.all() if hasattr(device.group_mappings, 'all') else device.group_mappings
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
    else:
        # Fallback: 알 수 없는 Device 타입 (발생하지 않아야 함)
        return None


@router.get("", response_model=ApiResponse[list[ConnectionEventResponse]])
async def get_connection_events(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    device_id: Optional[int] = Query(None, description="장치 ID로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    # Build query with joinedload for device
    query = db.query(ConnectionEvent).options(joinedload(ConnectionEvent.device))

    # Apply filters (PRD v2.1: device_id 기반 필터링)
    if device_id is not None:
        query = query.filter(ConnectionEvent.device_id == device_id)
    if start_date is not None:
        query = query.filter(ConnectionEvent.created_at >= start_date)
    if end_date is not None:
        query = query.filter(ConnectionEvent.created_at <= end_date)

    # Get total count
    count_query = db.query(ConnectionEvent)
    if device_id is not None:
        count_query = count_query.filter(ConnectionEvent.device_id == device_id)
    if start_date is not None:
        count_query = count_query.filter(ConnectionEvent.created_at >= start_date)
    if end_date is not None:
        count_query = count_query.filter(ConnectionEvent.created_at <= end_date)
    total = count_query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events = query.order_by(ConnectionEvent.created_at.desc()).offset(skip).limit(limit).all()

    # PRD v2.1: Response uses device_id (no group_event, controller, sensor, type_device)
    # PRD v1.3: device_id, sequence 필드 제거 (device.id에 포함, sequence는 Request 전용)
    # PRD v1.4: category_event 필드 제거 (polymorphic 내부용)
    event_responses = [
        ConnectionEventResponse(
            id=e.id,
            type_event=e.type_event,
            device=_build_device_nested_response(e.device),
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


@router.get("/{event_id}", response_model=ApiResponse[ConnectionEventResponse])
async def get_connection_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    event = db.query(ConnectionEvent).options(
        joinedload(ConnectionEvent.device)
    ).filter(ConnectionEvent.id == event_id).first()

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
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Connection event retrieved successfully",
        data=event_response
    )


@router.post("", response_model=ApiResponse[ConnectionEventResponse], status_code=status.HTTP_201_CREATED)
async def create_connection_event(
    event_data: ConnectionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    device = db.query(Device).filter(Device.id == event_data.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with id {event_data.device_id} not found"
        )

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
    db.commit()
    db.refresh(new_event)

    # Build device nested response
    device_nested = _build_device_nested_response(device)

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

    return ApiResponse(
        success=True,
        message="Connection event created successfully",
        data=event_response
    )


@router.patch("/{event_id}", response_model=ApiResponse[ConnectionEventResponse])
async def update_connection_event(
    event_id: int,
    event_data: ConnectionEventUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    event = db.query(ConnectionEvent).options(
        joinedload(ConnectionEvent.device)
    ).filter(ConnectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # Update fields if provided (PRD v2.1: only type_event is updatable, sequence 제거됨)
    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        # Only allow updating type_event
        if field in ['type_event']:
            setattr(event, field, value)

    db.commit()
    db.refresh(event)

    # PRD v2.1: Response uses device_id
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = ConnectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Connection event updated successfully",
        data=event_response
    )


@router.put("/{event_id}", response_model=ApiResponse[ConnectionEventResponse])
async def replace_connection_event(
    event_id: int,
    event_data: ConnectionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    연결 이벤트 전체 수정 (PUT)

    PRD v2.1: device_id 기반으로 변경됨, device_description 자동 갱신

    연결 이벤트의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **event_id**: 연결 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **type_event**: 이벤트 유형
    - **device_id**: 장치 ID

    **Response**: 수정된 연결 이벤트 정보

    **Error**:
    - 400: Device를 찾을 수 없음
    - 404: 연결 이벤트를 찾을 수 없음
    """
    event = db.query(ConnectionEvent).filter(ConnectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # PRD v2.1: Validate device_id exists
    device = db.query(Device).filter(Device.id == event_data.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with id {event_data.device_id} not found"
        )

    # PRD v2.1: Generate device_description automatically
    device_description = _generate_device_description(device)

    # Replace all fields (PUT = full replacement)
    # PRD v2.1: sequence 필드 제거됨
    event.type_event = event_data.type_event
    event.device_id = event_data.device_id
    event.device_description = device_description

    db.commit()
    db.refresh(event)

    # PRD v2.1: Response uses device_id
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = ConnectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        device=_build_device_nested_response(device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Connection event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiResponse[Optional[dict]])
async def delete_connection_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    event = db.query(ConnectionEvent).filter(ConnectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    db.delete(event)
    db.commit()

    return ApiResponse(
        success=True,
        message="Connection event deleted successfully",
        data=None
    )
