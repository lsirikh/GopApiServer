"""
Malfunction Event API endpoints

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
from app.models.event import MalfunctionEvent, ActionEvent, EnumTrueFalse, EnumFaultType
from app.models.device import Device, Sensor, Controller, Camera
from app.schemas.event import MalfunctionEventCreate, MalfunctionEventResponse, MalfunctionEventUpdate, ActionEventResponse
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

    PRD v1.1: device_description 자동 생성
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
            ip_address=device.ip_address,
            ip_port=device.ip_port,
            device_groups=device_groups
        )
    else:
        # Fallback: 알 수 없는 Device 타입 (발생하지 않아야 함)
        return None


@router.get("", response_model=ApiResponse[list[MalfunctionEventResponse]])
async def get_malfunction_events(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    device_id: Optional[int] = Query(None, description="장치 ID로 필터링"),
    action_reported: Optional[str] = Query(None, description="조치보고 여부로 필터링"),
    reason: Optional[str] = Query(None, description="장애 원인으로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 목록 조회 (페이지네이션)

    PRD v2.1: group_event, controller, sensor, type_device 필드 제거됨

    장애 이벤트 목록을 페이지네이션하여 조회합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **device_id**: 장치 ID로 필터링
    - **action_reported**: 조치보고 여부로 필터링
    - **reason**: 장애 원인으로 필터링
    - **start_date**: 시작 날짜로 필터링
    - **end_date**: 종료 날짜로 필터링

    **Response**: 장애 이벤트 목록 및 페이지네이션 정보
    """
    # Build query with device eager loading (PRD v2.1)
    query = db.query(MalfunctionEvent).options(joinedload(MalfunctionEvent.device))

    # Apply filters (PRD v2.1: device_id 기반 필터링)
    if device_id is not None:
        query = query.filter(MalfunctionEvent.device_id == device_id)
    if action_reported is not None:
        query = query.filter(MalfunctionEvent.action_reported == action_reported)
    if reason is not None:
        query = query.filter(MalfunctionEvent.reason == reason)
    if start_date is not None:
        query = query.filter(MalfunctionEvent.created_at >= start_date)
    if end_date is not None:
        query = query.filter(MalfunctionEvent.created_at <= end_date)

    # Get total count
    total = db.query(MalfunctionEvent).count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events = query.order_by(MalfunctionEvent.created_at.desc()).offset(skip).limit(limit).all()

    # Convert to response format (PRD v2.1: group_event 제거됨, device nested and device_description 포함)
    # PRD v1.3: device_id, sequence 필드 제거 (device.id에 포함, sequence는 Request 전용)
    # PRD v1.4: category_event 필드 제거 (polymorphic 내부용)
    event_responses = [
        MalfunctionEventResponse(
            id=e.id,
            type_event=e.type_event,
            action_reported=e.action_reported.value if hasattr(e.action_reported, 'value') else e.action_reported,
            reason=e.reason.value,
            first_start=e.first_start,
            first_end=e.first_end,
            second_start=e.second_start,
            second_end=e.second_end,
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
        message="Malfunction events retrieved successfully",
        data=event_responses,
        pagination=pagination
    )


@router.get("/{event_id}", response_model=ApiResponse[MalfunctionEventResponse])
async def get_malfunction_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 단건 조회

    특정 장애 이벤트의 상세 정보를 조회합니다.

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Response**: 장애 이벤트 상세 정보

    **Error**:
    - 404: 장애 이벤트를 찾을 수 없음
    """
    # PRD v1.1: Eager load device relationship
    event = db.query(MalfunctionEvent).options(
        joinedload(MalfunctionEvent.device)
    ).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # PRD v2.1: Include device nested and device_description (group_event 제거됨)
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = MalfunctionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        reason=event.reason.value,
        first_start=event.first_start,
        first_end=event.first_end,
        second_start=event.second_start,
        second_end=event.second_end,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Malfunction event retrieved successfully",
        data=event_response
    )


@router.post("", response_model=ApiResponse[MalfunctionEventResponse], status_code=status.HTTP_201_CREATED)
async def create_malfunction_event(
    event_data: MalfunctionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 생성

    새로운 장애 이벤트를 생성합니다.

    **Request Body** (PRD v2.8):
    - **type_event**: 이벤트 유형 (필수)
    - **device_id**: 장치 ID (필수) - Device FK
    - **reason**: 장애 원인 (필수)
    - **first_start**: 첫 번째 시작 시간 (필수)
    - **first_end**: 첫 번째 종료 시간 (필수)
    - **second_start**: 두 번째 시작 시간 (필수)
    - **second_end**: 두 번째 종료 시간 (필수)

    **자동 설정 (PRD v2.8)**:
    - **action_reported**: 항상 "False"로 시작 (ActionEvent 생성/삭제 시 시스템 자동 관리)

    **Response**: 생성된 장애 이벤트 정보 (device nested 포함)

    **Error**:
    - 400: 존재하지 않는 device_id
    - 422: 유효하지 않은 enum 값
    """
    # PRD v1.1: Validate device_id exists
    device = db.query(Device).filter(Device.id == event_data.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with id {event_data.device_id} not found"
        )

    # Convert string enum values to enum types
    try:
        fault_reason = EnumFaultType(event_data.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # PRD v1.1: Generate device_description automatically
    device_description = _generate_device_description(device)

    # Create new malfunction event with device_id
    # PRD v2.1: group_event, sequence 필드 제거됨
    # PRD v2.8: action_reported는 항상 "False"로 시작 (시스템 자동 관리)
    new_event = MalfunctionEvent(
        category_event="malfunction",  # Polymorphic discriminator
        type_event=event_data.type_event,
        device_id=event_data.device_id,
        device_description=device_description,
        action_reported=EnumTrueFalse.False_,  # PRD v2.8: 자동 설정
        reason=fault_reason,
        first_start=event_data.first_start,
        first_end=event_data.first_end,
        second_start=event_data.second_start,
        second_end=event_data.second_end
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # PRD v2.1: Include device nested in response (group_event 제거됨)
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = MalfunctionEventResponse(
        id=new_event.id,
        type_event=new_event.type_event,
        action_reported=new_event.action_reported.value if hasattr(new_event.action_reported, 'value') else new_event.action_reported,
        reason=new_event.reason.value,
        first_start=new_event.first_start,
        first_end=new_event.first_end,
        second_start=new_event.second_start,
        second_end=new_event.second_end,
        device=_build_device_nested_response(device),
        device_description=new_event.device_description,
        created_at=new_event.created_at,
        updated_at=new_event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Malfunction event created successfully",
        data=event_response
    )


@router.patch("/{event_id}", response_model=ApiResponse[MalfunctionEventResponse])
async def update_malfunction_event(
    event_id: int,
    event_data: MalfunctionEventUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 부분 수정 (PATCH)

    PRD v2.1: device_id 기반으로 변경됨

    장애 이벤트의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **type_event**: 이벤트 유형
    - **action_reported**: 조치보고 여부
    - **reason**: 장애 원인
    - **first_start**: 첫 번째 시작 시간
    - **first_end**: 첫 번째 종료 시간
    - **second_start**: 두 번째 시작 시간
    - **second_end**: 두 번째 종료 시간

    **Response**: 수정된 장애 이벤트 정보

    **Error**:
    - 404: 장애 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    # PRD v1.1: Eager load device relationship
    event = db.query(MalfunctionEvent).options(
        joinedload(MalfunctionEvent.device)
    ).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # Update fields if provided (PRD v2.1: type_event, action_reported, reason, first/second_start/end만 수정 가능)
    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "action_reported" and value is not None:
            try:
                value = EnumTrueFalse(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid action_reported value: {value}"
                )
        elif field == "reason" and value is not None:
            try:
                value = EnumFaultType(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid reason value: {value}"
                )

        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    # PRD v2.1: Response with device nested
    event_response = MalfunctionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        reason=event.reason.value,
        first_start=event.first_start,
        first_end=event.first_end,
        second_start=event.second_start,
        second_end=event.second_end,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Malfunction event updated successfully",
        data=event_response
    )


@router.put("/{event_id}", response_model=ApiResponse[MalfunctionEventResponse])
async def replace_malfunction_event(
    event_id: int,
    event_data: MalfunctionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 전체 수정 (PUT)

    PRD v2.1: device_id 기반으로 변경됨, device_description 자동 갱신

    장애 이벤트의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **type_event**: 이벤트 유형
    - **device_id**: 장치 ID
    - **reason**: 장애 원인
    - **first_start**: 첫 번째 시작 시간
    - **first_end**: 첫 번째 종료 시간
    - **second_start**: 두 번째 시작 시간
    - **second_end**: 두 번째 종료 시간

    **자동 관리 (PRD v2.8)**:
    - **action_reported**: PUT 시에도 기존 값 유지 (시스템 자동 관리)

    **Response**: 수정된 장애 이벤트 정보

    **Error**:
    - 400: Device를 찾을 수 없음
    - 404: 장애 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # PRD v2.1: Validate device_id exists
    device = db.query(Device).filter(Device.id == event_data.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with id {event_data.device_id} not found"
        )

    # Convert string enum values to enum types
    try:
        fault_reason = EnumFaultType(event_data.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # PRD v2.1: Generate device_description automatically
    device_description = _generate_device_description(device)

    # Replace all fields (PUT = full replacement)
    # PRD v2.1: device_id 기반, group_event/sequence 필드 제거됨
    # PRD v2.8: action_reported는 시스템 자동 관리 (기존 값 유지)
    event.type_event = event_data.type_event
    event.device_id = event_data.device_id
    event.device_description = device_description
    # event.action_reported는 변경하지 않음 (시스템 자동 관리)
    event.reason = fault_reason
    event.first_start = event_data.first_start
    event.first_end = event_data.first_end
    event.second_start = event_data.second_start
    event.second_end = event_data.second_end

    db.commit()
    db.refresh(event)

    event_response = MalfunctionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        reason=event.reason.value,
        first_start=event.first_start,
        first_end=event.first_end,
        second_start=event.second_start,
        second_end=event.second_end,
        device=_build_device_nested_response(device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Malfunction event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiResponse[Optional[dict]])
async def delete_malfunction_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 삭제

    특정 장애 이벤트를 삭제합니다. 조치보고가 등록된 이벤트는 삭제할 수 없습니다.

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 장애 이벤트를 찾을 수 없음
    - 409: 조치보고가 등록된 장애 이벤트는 삭제 불가
    """
    event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # Phase 18.2: Prevent deletion if action_reported is "True"
    if event.action_reported == "True":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="조치보고가 등록된 장애 이벤트는 삭제할 수 없습니다. ActionEvent를 먼저 삭제해주세요. / Cannot delete Malfunction event with Action reported. Please delete the ActionEvent first."
        )

    db.delete(event)
    db.commit()

    return ApiResponse(
        success=True,
        message="Malfunction event deleted successfully",
        data=None
    )


@router.get("/{event_id}/action", response_model=ApiResponse[ActionEventResponse])
async def get_action_event_for_malfunction(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트의 조치 이벤트 조회

    특정 장애 이벤트에 연결된 조치 이벤트를 조회합니다.

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Response**: 조치 이벤트 정보 (연결된 원본 이벤트 포함)

    **Error**:
    - 404: 장애 이벤트를 찾을 수 없음
    - 404: 해당 장애 이벤트에 연결된 조치 이벤트가 없음
    """
    # 1. MalfunctionEvent 존재 확인
    malfunction = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()
    if not malfunction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event not found with Id={event_id}"
        )

    # 2. ActionEvent 조회 (1:1 관계)
    # Note: from_event_id는 events.id FK로, Malfunction ID로 직접 조회 가능
    action = db.query(ActionEvent).filter(
        ActionEvent.from_event_id == event_id
    ).first()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="조치 보고가 등록되지 않은 장애 이벤트입니다. / No action event found for this malfunction event."
        )

    # 3. ActionEventResponse 구성 (nested source event 포함)
    # PRD v1.3: device nested 포함, device_id/sequence 제외
    # PRD v1.4: category_event 필드 제거
    source_event_response = MalfunctionEventResponse(
        id=malfunction.id,
        type_event=malfunction.type_event,
        action_reported=malfunction.action_reported.value if hasattr(malfunction.action_reported, 'value') else malfunction.action_reported,
        reason=malfunction.reason.value,
        first_start=malfunction.first_start,
        first_end=malfunction.first_end,
        second_start=malfunction.second_start,
        second_end=malfunction.second_end,
        device=_build_device_nested_response(malfunction.device),
        device_description=malfunction.device_description,
        created_at=malfunction.created_at,
        updated_at=malfunction.updated_at
    )

    action_response = ActionEventResponse(
        id=action.id,
        type_event=action.type_event,
        content=action.content,
        user=action.user,
        from_event=source_event_response,  # Nested event object with device nested
        created_at=action.created_at,
        updated_at=action.updated_at
    )

    return ApiResponse(
        success=True,
        message="Action event retrieved successfully",
        data=action_response
    )
