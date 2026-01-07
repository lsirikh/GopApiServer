"""
Detection Event API endpoints

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
from app.models.event import DetectionEvent, ActionEvent, EnumTrueFalse, EnumDetectionType
from app.models.device import Device, Sensor, Controller, Camera
from app.schemas.event import DetectionEventCreate, DetectionEventResponse, DetectionEventUpdate, ActionEventResponse
from app.schemas.device import (
    DeviceGroupNestedResponse,
    SensorNestedResponse,
    ControllerNestedResponse,
    CameraNestedResponse
)
from app.schemas.common import ApiResponse, PaginationMeta
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
        # Fallback: 알 수 없는 Device 타입은 Controller 형식으로 반환
        return ControllerNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device.value,
            version=device.version,
            status=device.status.value,
            ip_address=getattr(device, 'ip_address', ''),
            ip_port=getattr(device, 'ip_port', 0),
            device_groups=device_groups
        )


@router.get("", response_model=ApiResponse[list[DetectionEventResponse]])
async def get_detection_events(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    device_id: Optional[int] = Query(None, description="장치 ID로 필터링"),
    action_reported: Optional[str] = Query(None, description="조치보고 여부로 필터링"),
    result: Optional[str] = Query(None, description="결과 유형으로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 이벤트 목록 조회 (페이지네이션)

    PRD v2.1: group_event, controller, sensor, type_device 필드 제거됨

    탐지 이벤트 목록을 페이지네이션하여 조회합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **device_id**: 장치 ID로 필터링
    - **action_reported**: 조치보고 여부로 필터링
    - **result**: 결과 유형으로 필터링
    - **start_date**: 시작 날짜로 필터링
    - **end_date**: 종료 날짜로 필터링

    **Response**: 탐지 이벤트 목록 및 페이지네이션 정보
    """
    # Build query with device eager loading (PRD v2.1)
    query = db.query(DetectionEvent).options(joinedload(DetectionEvent.device))

    # Apply filters (PRD v2.1: device_id 기반 필터링)
    if device_id is not None:
        query = query.filter(DetectionEvent.device_id == device_id)
    if action_reported is not None:
        query = query.filter(DetectionEvent.action_reported == action_reported)
    if result is not None:
        query = query.filter(DetectionEvent.result == result)
    if start_date is not None:
        query = query.filter(DetectionEvent.created_at >= start_date)
    if end_date is not None:
        query = query.filter(DetectionEvent.created_at <= end_date)

    # Get total count (without eager loading for performance)
    total = db.query(DetectionEvent).filter(*[
        f for f in [
            DetectionEvent.device_id == device_id if device_id is not None else None,
            DetectionEvent.action_reported == action_reported if action_reported is not None else None,
            DetectionEvent.result == result if result is not None else None,
            DetectionEvent.created_at >= start_date if start_date is not None else None,
            DetectionEvent.created_at <= end_date if end_date is not None else None,
        ] if f is not None
    ]).count() if any([device_id, action_reported, result, start_date, end_date]) else db.query(DetectionEvent).count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events = query.order_by(DetectionEvent.created_at.desc()).offset(skip).limit(limit).all()

    # Convert to response format (PRD v2.1: group_event 제거됨, device nested and device_description 포함)
    # PRD v1.3: device_id, sequence 필드 제거 (device.id에 포함, sequence는 Request 전용)
    # PRD v1.4: category_event 필드 제거 (polymorphic 내부용)
    event_responses = [
        DetectionEventResponse(
            id=e.id,
            type_event=e.type_event,
            action_reported=e.action_reported.value if hasattr(e.action_reported, 'value') else e.action_reported,
            result=e.result.value,
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
        message="Detection events retrieved successfully",
        data=event_responses,
        pagination=pagination
    )


@router.get("/{event_id}", response_model=ApiResponse[DetectionEventResponse])
async def get_detection_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 이벤트 단건 조회

    특정 탐지 이벤트의 상세 정보를 조회합니다.

    **파라미터**:
    - **event_id**: 탐지 이벤트 ID (Path Parameter)

    **Response**: 탐지 이벤트 상세 정보

    **Error**:
    - 404: 탐지 이벤트를 찾을 수 없음
    """
    # PRD v1.1: Eager load device relationship
    event = db.query(DetectionEvent).options(
        joinedload(DetectionEvent.device)
    ).filter(DetectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection event with id {event_id} not found"
        )

    # PRD v2.1: Include device nested and device_description (group_event 제거됨)
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = DetectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        result=event.result.value,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Detection event retrieved successfully",
        data=event_response
    )


@router.post("", response_model=ApiResponse[DetectionEventResponse], status_code=status.HTTP_201_CREATED)
async def create_detection_event(
    event_data: DetectionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 이벤트 생성

    새로운 탐지 이벤트를 생성합니다.

    **Request Body** (PRD v2.8):
    - **type_event**: 이벤트 유형 (필수)
    - **device_id**: 장치 ID (필수) - Device FK
    - **result**: 결과 유형 (필수)

    **자동 설정 (PRD v2.8)**:
    - **action_reported**: 항상 "False"로 시작 (ActionEvent 생성/삭제 시 시스템 자동 관리)

    **Response**: 생성된 탐지 이벤트 정보 (device nested 포함)

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
        event_result = EnumDetectionType(event_data.result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # PRD v1.1: Generate device_description automatically
    device_description = _generate_device_description(device)

    # Create new detection event with device_id
    # PRD v2.1: group_event, sequence 필드 제거됨
    # PRD v2.8: action_reported는 항상 "False"로 시작 (시스템 자동 관리)
    new_event = DetectionEvent(
        category_event="detection",  # Polymorphic discriminator
        type_event=event_data.type_event,
        device_id=event_data.device_id,
        device_description=device_description,
        action_reported=EnumTrueFalse.False_,  # PRD v2.8: 자동 설정
        result=event_result
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # PRD v2.1: Include device nested in response (group_event 제거됨)
    # PRD v1.3: device_id, sequence 필드 제거
    # PRD v1.4: category_event 필드 제거
    event_response = DetectionEventResponse(
        id=new_event.id,
        type_event=new_event.type_event,
        action_reported=new_event.action_reported.value if hasattr(new_event.action_reported, 'value') else new_event.action_reported,
        result=new_event.result.value,
        device=_build_device_nested_response(device),
        device_description=new_event.device_description,
        created_at=new_event.created_at,
        updated_at=new_event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Detection event created successfully",
        data=event_response
    )


@router.patch("/{event_id}", response_model=ApiResponse[DetectionEventResponse])
async def update_detection_event(
    event_id: int,
    event_data: DetectionEventUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 이벤트 부분 수정 (PATCH)

    PRD v2.1: device_id 기반으로 변경됨

    탐지 이벤트의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **event_id**: 탐지 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **type_event**: 이벤트 유형
    - **action_reported**: 조치보고 여부
    - **result**: 결과 유형

    **Response**: 수정된 탐지 이벤트 정보

    **Error**:
    - 404: 탐지 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    # PRD v1.1: Eager load device relationship
    event = db.query(DetectionEvent).options(
        joinedload(DetectionEvent.device)
    ).filter(DetectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection event with id {event_id} not found"
        )

    # Update fields if provided (PRD v2.1: type_event, action_reported, result만 수정 가능)
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
        elif field == "result" and value is not None:
            try:
                value = EnumDetectionType(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid result value: {value}"
                )

        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    # PRD v2.1: Response with device nested
    event_response = DetectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        result=event.result.value,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Detection event updated successfully",
        data=event_response
    )


@router.put("/{event_id}", response_model=ApiResponse[DetectionEventResponse])
async def replace_detection_event(
    event_id: int,
    event_data: DetectionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 이벤트 전체 수정 (PUT)

    PRD v2.1: device_id 기반으로 변경됨, device_description 자동 갱신

    탐지 이벤트의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **event_id**: 탐지 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **type_event**: 이벤트 유형
    - **device_id**: 장치 ID - Device FK
    - **result**: 결과 유형

    **자동 관리 (PRD v2.8)**:
    - **action_reported**: PUT 시에도 기존 값 유지 (시스템 자동 관리)

    **Response**: 수정된 탐지 이벤트 정보

    **Error**:
    - 400: Device를 찾을 수 없음
    - 404: 탐지 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    event = db.query(DetectionEvent).filter(DetectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection event with id {event_id} not found"
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
        detection_result = EnumDetectionType(event_data.result)
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
    event.result = detection_result

    db.commit()
    db.refresh(event)

    event_response = DetectionEventResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        result=event.result.value,
        device=_build_device_nested_response(device),
        device_description=event.device_description,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Detection event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiResponse[Optional[dict]])
async def delete_detection_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 이벤트 삭제

    특정 탐지 이벤트를 삭제합니다. 조치보고가 등록된 이벤트는 삭제할 수 없습니다.

    **파라미터**:
    - **event_id**: 탐지 이벤트 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 탐지 이벤트를 찾을 수 없음
    - 409: 조치보고가 등록된 탐지 이벤트는 삭제 불가
    """
    event = db.query(DetectionEvent).filter(DetectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection event with id {event_id} not found"
        )

    # Phase 18.2: Prevent deletion if action_reported is "True"
    if event.action_reported == "True":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="조치보고가 등록된 탐지 이벤트는 삭제할 수 없습니다. ActionEvent를 먼저 삭제해주세요. / Cannot delete Detection event with Action reported. Please delete the ActionEvent first."
        )

    db.delete(event)
    db.commit()

    return ApiResponse(
        success=True,
        message="Detection event deleted successfully",
        data=None
    )


@router.get("/{event_id}/action", response_model=ApiResponse[ActionEventResponse])
async def get_action_event_for_detection(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 이벤트의 조치 이벤트 조회

    특정 탐지 이벤트에 연결된 조치 이벤트를 조회합니다.

    **파라미터**:
    - **event_id**: 탐지 이벤트 ID (Path Parameter)

    **Response**: 조치 이벤트 정보 (연결된 원본 이벤트 포함)

    **Error**:
    - 404: 탐지 이벤트를 찾을 수 없음
    - 404: 해당 탐지 이벤트에 연결된 조치 이벤트가 없음
    """
    # 1. DetectionEvent 존재 확인
    detection = db.query(DetectionEvent).filter(DetectionEvent.id == event_id).first()
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection event not found with Id={event_id}"
        )

    # 2. ActionEvent 조회 (1:1 관계)
    # Note: from_event_id는 events.id FK로, Detection ID로 직접 조회 가능
    action = db.query(ActionEvent).filter(
        ActionEvent.from_event_id == event_id
    ).first()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="조치 보고가 등록되지 않은 탐지 이벤트입니다. / No action event found for this detection event."
        )

    # 3. ActionEventResponse 구성 (nested source event 포함)
    # PRD v1.3: device nested 포함, device_id/sequence 제외
    # PRD v1.4: category_event 필드 제거
    source_event_response = DetectionEventResponse(
        id=detection.id,
        type_event=detection.type_event,
        action_reported=detection.action_reported.value if hasattr(detection.action_reported, 'value') else detection.action_reported,
        result=detection.result.value,
        device=_build_device_nested_response(detection.device),
        device_description=detection.device_description,
        created_at=detection.created_at,
        updated_at=detection.updated_at
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
