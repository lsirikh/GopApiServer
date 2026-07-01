"""
Malfunction Event API endpoints

PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
- device_id: Device FK (기존 controller, sensor, type_device 대체)
- device_description: Device 정보 스냅샷 (자동 생성)
- Response에 device nested 객체 포함 (Optional, Device 삭제 시 null)
- group_event 필드 제거됨
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional, require_perm_optional
from app.models.event import MalfunctionEvent, ActionEvent, EnumTrueFalse, EnumFaultType
from app.models.device import Device, Sensor, Controller, Camera, Speaker, Enclosure, Lamp
from app.schemas.event import MalfunctionEventCreate, MalfunctionEventReplace, MalfunctionEventResponse, MalfunctionEventUpdate, ActionEventResponse
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
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change, get_changed_fields, model_to_dict
from typing import Union

router = APIRouter(tags=[])


def _generate_device_description(device: Device) -> str:
    """
    Device 정보 스냅샷 문자열 생성

    PRD v1.1: device_description 자동 생성
    형식: "[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
    """
    return f"[{device.type_device.value}] {device.name_device} (number: {device.number_device}, id: {device.id})"


def _build_device_nested_response(device: Optional[Device]) -> Optional[Union[SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse, SpeakerNestedResponse, LampNestedResponse, DeviceNestedResponse]]:
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
    query = db.query(MalfunctionEvent).options(selectinload(MalfunctionEvent.device))

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

    # Get total count (필터 적용된 쿼리 기준)
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events = query.order_by(MalfunctionEvent.created_at.desc(), MalfunctionEvent.id.desc()).offset(skip).limit(limit).all()

    # Convert to response format (PRD v2.1: group_event 제거됨, device nested and device_description 포함)
    # PRD v1.3: device_id, sequence 필드 제거 (device.id에 포함, sequence는 Request 전용)
    # PRD v1.4: category_event 필드 제거 (polymorphic 내부용)
    # PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB
    event_responses = [
        MalfunctionEventResponse(
            id=e.id,
            type_event=e.type_event,
            action_reported=e.action_reported.value if hasattr(e.action_reported, 'value') else e.action_reported,
            reason=e.reason.value,
            device=_build_device_nested_response(e.device),
            device_description=e.device_description,
            detail=e.detail,
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


@router.get("/{event_id}", response_model=ApiSingleResponse[MalfunctionEventResponse])
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
        selectinload(MalfunctionEvent.device)
    ).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # PRD v2.1: Include device nested and device_description (group_event 제거됨)
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    # PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB
    event_response = MalfunctionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        reason=event.reason.value,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        detail=event.detail,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Malfunction event retrieved successfully",
        data=event_response
    )


@router.post("", response_model=ApiSingleResponse[MalfunctionEventResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm_optional("events", "edit"))])
async def create_malfunction_event(
    event_data: MalfunctionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 생성

    PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB

    새로운 장애 이벤트를 생성합니다.

    **Request Body**:
    - **type_event**: 이벤트 유형 (필수)
    - **device_id**: 장치 ID (필수) - Device FK
    - **reason**: 장애 원인 (필수)
    - **detail**: 케이블 위치 정보 (선택, first_start, first_end, second_start, second_end)

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

    # PRD_Malfunction_Device_Status v1.1: 장비 상태를 ERROR로 변경
    device.status = EnumDeviceStatus.ERROR

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
    # PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB
    new_event = MalfunctionEvent(
        category_event="malfunction",  # Polymorphic discriminator
        type_event=event_data.type_event,
        device_id=event_data.device_id,
        device_description=device_description,
        action_reported=EnumTrueFalse.False_,  # PRD v2.8: 자동 설정
        reason=fault_reason,
        detail=event_data.detail  # 케이블 위치 정보 포함
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.MALFUNCTION_EVENT,
        resource_id=new_event.id,
        resource_name=f"MalfunctionEvent-{new_event.id} ({new_event.type_event})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": new_event.id, "type_event": new_event.type_event},
        description="MalfunctionEvent 생성"
    )

    # PRD v2.1: Include device nested in response (group_event 제거됨)
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    # PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB
    event_response = MalfunctionEventResponse(
        id=new_event.id,
        type_event=new_event.type_event,
        action_reported=new_event.action_reported.value if hasattr(new_event.action_reported, 'value') else new_event.action_reported,
        reason=new_event.reason.value,
        device=_build_device_nested_response(device),
        device_description=new_event.device_description,
        detail=new_event.detail,
        created_at=new_event.created_at,
        updated_at=new_event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Malfunction event created successfully",
        data=event_response
    )


@router.patch("/{event_id}", response_model=ApiSingleResponse[MalfunctionEventResponse], dependencies=[Depends(require_perm_optional("events", "edit"))])
async def update_malfunction_event(
    event_id: int,
    event_data: MalfunctionEventUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 부분 수정 (PATCH)

    PRD v2.1: device_id 기반으로 변경됨
    PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB

    장애 이벤트의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **type_event**: 이벤트 유형
    - **action_reported**: 조치보고 여부
    - **reason**: 장애 원인
    - **detail**: 케이블 위치 정보 (first_start, first_end, second_start, second_end)

    **Response**: 수정된 장애 이벤트 정보

    **Error**:
    - 404: 장애 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    # PRD v1.1: Eager load device relationship
    event = db.query(MalfunctionEvent).options(
        selectinload(MalfunctionEvent.device)
    ).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(event)

    # Update fields if provided
    # PRD_Event_Field_Normalization.md v1.0: type_event, action_reported, reason, detail만 수정 가능
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

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(event)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.MALFUNCTION_EVENT,
            resource_id=event.id,
            resource_name=f"MalfunctionEvent-{event.id} ({event.type_event})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="MalfunctionEvent 수정"
        )

    # PRD v2.1: Response with device nested
    # PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB
    event_response = MalfunctionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        reason=event.reason.value,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        detail=event.detail,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Malfunction event updated successfully",
        data=event_response
    )


@router.put("/{event_id}", response_model=ApiSingleResponse[MalfunctionEventResponse], dependencies=[Depends(require_perm_optional("events", "edit"))])
async def replace_malfunction_event(
    event_id: int,
    event_data: MalfunctionEventReplace,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트 전체 수정 (PUT)

    PRD v4.8 Phase 12-7b: device_id / device_description 변경 원천 차단
    - device_id: PUT으로 수정 불가 (v2.1 불변식 — device 바인딩은 생성 시점에 확정)
    - device_description: Device 스냅샷 보존 (생성 시점 값 유지)
    - device 재지정이 필요하면 DELETE 후 POST로 재생성
    PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB

    장애 이벤트의 필드를 교체합니다. (device 바인딩 제외)

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수, device_id/device_description 전송 시 422):
    - **type_event**: 이벤트 유형
    - **reason**: 장애 원인
    - **detail**: 케이블 위치 정보 (first_start, first_end, second_start, second_end)

    **자동 관리**:
    - **action_reported**: PUT 시에도 기존 값 유지 (시스템 자동 관리, PRD v2.8)
    - **device / device_description**: 생성 시 바인딩된 값 유지 (Phase 12-7b)

    **Response**: 수정된 장애 이벤트 정보

    **Error**:
    - 404: 장애 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값 / device_id/device_description 등 금지 필드 전송
    """
    event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # Convert string enum values to enum types
    try:
        fault_reason = EnumFaultType(event_data.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Replace allowed fields only (PUT = full replacement, device 바인딩 제외)
    # PRD v4.8 Phase 12-7b: device_id / device_description는 변경 불가 (스냅샷 보존)
    # PRD v2.8: action_reported는 시스템 자동 관리 (기존 값 유지)
    # PRD_Event_Field_Normalization.md v1.0: first_start/end, second_start/end → detail JSONB
    event.type_event = event_data.type_event
    # event.device_id / event.device_description는 변경하지 않음 (Phase 12-7b)
    # event.action_reported는 변경하지 않음 (시스템 자동 관리)
    event.reason = fault_reason
    event.detail = event_data.detail  # 케이블 위치 정보 포함

    db.commit()
    db.refresh(event)

    event_response = MalfunctionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        reason=event.reason.value,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        detail=event.detail,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Malfunction event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiSingleResponse[None], dependencies=[Depends(require_perm_optional("events", "delete"))])
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

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = event.id
    deleted_identifier = {"id": event.id, "type_event": event.type_event}
    deleted_name = f"MalfunctionEvent-{event.id} ({event.type_event})"

    db.delete(event)
    db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.MALFUNCTION_EVENT,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="MalfunctionEvent 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message=f"Malfunction event {event_id} deleted successfully",
        data=None
    )


@router.get("/{event_id}/actions", response_model=ApiResponse[list[ActionEventResponse]])
async def get_action_events_for_malfunction(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    장애 이벤트의 조치 이벤트 목록 조회

    특정 장애 이벤트에 연결된 조치 이벤트 목록을 조회합니다.
    PRD: PRD_ActionEvent_1N_Refactoring.md v2.0 — 1:N 관계 리스트 반환

    **파라미터**:
    - **event_id**: 장애 이벤트 ID (Path Parameter)

    **Response**: 조치 이벤트 목록 (빈 리스트 허용)

    **Error**:
    - 404: 장애 이벤트를 찾을 수 없음
    """
    # 1. MalfunctionEvent 존재 확인
    malfunction = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()
    if not malfunction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event not found with Id={event_id}"
        )

    # 2. ActionEvent 목록 조회 (1:N 관계)
    actions = db.query(ActionEvent).filter(
        ActionEvent.from_event_id == event_id
    ).order_by(ActionEvent.created_at.desc()).all()

    # 3. source event response 구성
    source_event_response = MalfunctionEventResponse(
        id=malfunction.id,
        type_event=malfunction.type_event,
        action_reported=malfunction.action_reported.value if hasattr(malfunction.action_reported, 'value') else malfunction.action_reported,
        reason=malfunction.reason.value,
        device=_build_device_nested_response(malfunction.device),
        device_description=malfunction.device_description,
        detail=malfunction.detail,
        created_at=malfunction.created_at,
        updated_at=malfunction.updated_at
    )

    # 4. ActionEventResponse 리스트 구성
    action_responses = [
        ActionEventResponse(
            id=action.id,
            type_event=action.type_event,
            content=action.content,
            user=action.user,
            from_event=source_event_response,
            created_at=action.created_at,
            updated_at=action.updated_at
        )
        for action in actions
    ]

    return ApiResponse(
        success=True,
        message="Action events retrieved successfully",
        data=action_responses
    )
