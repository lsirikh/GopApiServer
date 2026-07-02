"""
Detection Log API endpoints (Read-Only)

PRD: PRD_DetectionLog_API.md v1.0
- DetectionEvent + ActionEvent LEFT JOIN
- 탐지 로그 화면 전용 (CRUD 미제공)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.routers.auth import get_current_account_user_optional
from app.models.event import DetectionEvent, ActionEvent
from app.models.device import Device, Sensor, Controller, Camera, Speaker, Enclosure, Lamp
from app.schemas.event import DetectionLogResponse, ActionNested
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
from typing import Union

router = APIRouter(tags=[])


def _build_device_nested_response(device: Optional[Device]) -> Optional[Union[SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse, SpeakerNestedResponse, LampNestedResponse, DeviceNestedResponse]]:
    """Device 객체를 타입에 맞는 Nested Response로 변환 (Polymorphic)"""
    if device is None:
        return None

    device_groups = []
    if hasattr(device, 'group_mappings') and device.group_mappings is not None:
        mappings = device.group_mappings.all() if hasattr(device.group_mappings, 'all') else device.group_mappings
        for mapping in mappings:
            if mapping.group:
                device_groups.append(DeviceGroupNestedResponse(
                    id=mapping.group.id,
                    name=mapping.group.name
                ))

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


def _build_actions_nested(actions) -> list[ActionNested]:
    """Event.actions 리스트를 ActionNested 리스트로 변환 (PRD_ActionEvent_1N v2.0)"""
    if not actions:
        return []
    return [
        ActionNested(
            id=action.id,
            content=action.content,
            user=action.user,
            created_at=action.created_at,
            updated_at=action.updated_at
        )
        for action in actions
    ]


@router.get("", response_model=ApiResponse[list[DetectionLogResponse]])
async def get_detection_logs(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    device_id: Optional[int] = Query(None, description="장치 ID로 필터링"),
    action_reported: Optional[str] = Query(None, description="조치보고 여부로 필터링"),
    result: Optional[str] = Query(None, description="결과 유형으로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_account_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 로그 목록 조회 (DetectionEvent + ActionEvent LEFT JOIN)

    탐지 이벤트와 조치보고를 JOIN하여 한 레코드로 반환합니다.
    조치보고가 없는 탐지 이벤트는 action=null로 반환됩니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **device_id**: 장치 ID로 필터링
    - **action_reported**: 조치보고 여부로 필터링 ("True" / "False")
    - **result**: 결과 유형으로 필터링
    - **start_date**: 시작 날짜로 필터링
    - **end_date**: 종료 날짜로 필터링
    """
    # LEFT JOIN: Device + ActionEvent eager loading
    query = db.query(DetectionEvent).options(
        selectinload(DetectionEvent.device),
        selectinload(DetectionEvent.actions)
    )

    # Apply filters
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

    # Count (without eager loading)
    count_filters = [
        f for f in [
            DetectionEvent.device_id == device_id if device_id is not None else None,
            DetectionEvent.action_reported == action_reported if action_reported is not None else None,
            DetectionEvent.result == result if result is not None else None,
            DetectionEvent.created_at >= start_date if start_date is not None else None,
            DetectionEvent.created_at <= end_date if end_date is not None else None,
        ] if f is not None
    ]
    total = db.query(DetectionEvent).filter(*count_filters).count() if count_filters else db.query(DetectionEvent).count()

    # Pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    events = query.order_by(DetectionEvent.created_at.desc(), DetectionEvent.id.desc()).offset(skip).limit(limit).all()

    # Convert to response
    log_responses = [
        DetectionLogResponse(
            id=e.id,
            type_event=e.type_event,
            action_reported=e.action_reported.value if hasattr(e.action_reported, 'value') else e.action_reported,
            result=e.result.value,
            device=_build_device_nested_response(e.device),
            device_description=e.device_description,
            detail=e.detail,
            actions=_build_actions_nested(e.actions),
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
        message=f"{total} detection logs retrieved",
        data=log_responses,
        pagination=pagination
    )


@router.get("/{event_id}", response_model=ApiSingleResponse[DetectionLogResponse])
async def get_detection_log(
    event_id: int,
    current_user = Depends(get_current_account_user_optional),
    db: Session = Depends(get_db)
):
    """
    탐지 로그 단건 조회

    특정 탐지 이벤트와 연결된 조치보고를 함께 조회합니다.

    **파라미터**:
    - **event_id**: 탐지 이벤트 ID (Path Parameter)

    **Error**:
    - 404: 탐지 로그를 찾을 수 없음
    """
    event = db.query(DetectionEvent).options(
        selectinload(DetectionEvent.device),
        selectinload(DetectionEvent.actions)
    ).filter(DetectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection log with id {event_id} not found"
        )

    log_response = DetectionLogResponse(
        id=event.id,
        type_event=event.type_event,
        action_reported=event.action_reported.value if hasattr(event.action_reported, 'value') else event.action_reported,
        result=event.result.value,
        device=_build_device_nested_response(event.device),
        device_description=event.device_description,
        detail=event.detail,
        actions=_build_actions_nested(event.actions),
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Detection log retrieved successfully",
        data=log_response
    )
