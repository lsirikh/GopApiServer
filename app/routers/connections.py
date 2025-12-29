"""
Connection Event API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.event import ConnectionEvent
from app.schemas.event import ConnectionEventCreate, ConnectionEventResponse, ConnectionEventUpdate
from app.schemas.common import ApiResponse, PaginationMeta
from app.utils.enums import EnumDeviceType

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[ConnectionEventResponse]])
async def get_connection_events(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    controller: Optional[int] = Query(None, description="컨트롤러 번호로 필터링"),
    sensor: Optional[int] = Query(None, description="센서 번호로 필터링"),
    type_device: Optional[str] = Query(None, description="장치 유형으로 필터링"),
    group_event: Optional[str] = Query(None, description="이벤트 그룹으로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    연결 이벤트 목록 조회 (페이지네이션)

    연결 이벤트 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **controller**: 컨트롤러 번호로 필터링
    - **sensor**: 센서 번호로 필터링
    - **type_device**: 장치 유형으로 필터링
    - **group_event**: 이벤트 그룹으로 필터링
    - **start_date**: 시작 날짜로 필터링
    - **end_date**: 종료 날짜로 필터링

    **Response**: 연결 이벤트 목록 및 페이지네이션 정보
    """
    # Build query
    query = db.query(ConnectionEvent)

    # Apply filters
    if controller is not None:
        query = query.filter(ConnectionEvent.controller == controller)
    if sensor is not None:
        query = query.filter(ConnectionEvent.sensor == sensor)
    if type_device is not None:
        query = query.filter(ConnectionEvent.type_device == type_device)
    if group_event is not None:
        query = query.filter(ConnectionEvent.group_event == group_event)
    if start_date is not None:
        query = query.filter(ConnectionEvent.created_at >= start_date)
    if end_date is not None:
        query = query.filter(ConnectionEvent.created_at <= end_date)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events = query.order_by(ConnectionEvent.created_at.desc()).offset(skip).limit(limit).all()

    # Convert to response format
    event_responses = [
        ConnectionEventResponse(
            id=e.id,
            group_event=e.group_event,
            type_event=e.type_event,
            controller=e.controller,
            sensor=e.sensor,
            type_device=e.type_device.value,
            sequence=e.sequence,
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
    event = db.query(ConnectionEvent).filter(ConnectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    event_response = ConnectionEventResponse(
        id=event.id,
        group_event=event.group_event,
        type_event=event.type_event,
        controller=event.controller,
        sensor=event.sensor,
        type_device=event.type_device.value,
        sequence=event.sequence,
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

    새로운 연결 이벤트를 생성합니다.

    **Request Body**:
    - **group_event**: 이벤트 그룹 (필수)
    - **type_event**: 이벤트 유형 (필수)
    - **controller**: 컨트롤러 번호 (필수)
    - **sensor**: 센서 번호 (필수)
    - **type_device**: 장치 유형 (필수)
    - **sequence**: 시퀀스 번호 (필수)

    **Response**: 생성된 연결 이벤트 정보

    **Error**:
    - 422: 유효하지 않은 enum 값
    """
    # Convert string enum values to enum types
    try:
        event_type_device = EnumDeviceType(event_data.type_device)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Create new connection event
    new_event = ConnectionEvent(
        group_event=event_data.group_event,
        type_event=event_data.type_event,
        controller=event_data.controller,
        sensor=event_data.sensor,
        type_device=event_type_device,
        sequence=event_data.sequence
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    event_response = ConnectionEventResponse(
        id=new_event.id,
        group_event=new_event.group_event,
        type_event=new_event.type_event,
        controller=new_event.controller,
        sensor=new_event.sensor,
        type_device=new_event.type_device.value,
        sequence=new_event.sequence,
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

    연결 이벤트의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **event_id**: 연결 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **group_event**: 이벤트 그룹
    - **type_event**: 이벤트 유형
    - **controller**: 컨트롤러 번호
    - **sensor**: 센서 번호
    - **type_device**: 장치 유형
    - **sequence**: 시퀀스 번호

    **Response**: 수정된 연결 이벤트 정보

    **Error**:
    - 404: 연결 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    event = db.query(ConnectionEvent).filter(ConnectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # Update fields if provided
    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "type_device" and value is not None:
            try:
                value = EnumDeviceType(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid type_device value: {value}"
                )

        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    event_response = ConnectionEventResponse(
        id=event.id,
        group_event=event.group_event,
        type_event=event.type_event,
        controller=event.controller,
        sensor=event.sensor,
        type_device=event.type_device.value,
        sequence=event.sequence,
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

    연결 이벤트의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **event_id**: 연결 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **group_event**: 이벤트 그룹
    - **type_event**: 이벤트 유형
    - **controller**: 컨트롤러 번호
    - **sensor**: 센서 번호
    - **type_device**: 장치 유형
    - **sequence**: 시퀀스 번호

    **Response**: 수정된 연결 이벤트 정보

    **Error**:
    - 404: 연결 이벤트를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    event = db.query(ConnectionEvent).filter(ConnectionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection event with id {event_id} not found"
        )

    # Convert string enum values to enum types
    try:
        event_type_device = EnumDeviceType(event_data.type_device)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Replace all fields (PUT = full replacement)
    event.group_event = event_data.group_event
    event.type_event = event_data.type_event
    event.controller = event_data.controller
    event.sensor = event_data.sensor
    event.type_device = event_type_device
    event.sequence = event_data.sequence

    db.commit()
    db.refresh(event)

    event_response = ConnectionEventResponse(
        id=event.id,
        group_event=event.group_event,
        type_event=event.type_event,
        controller=event.controller,
        sensor=event.sensor,
        type_device=event.type_device.value,
        sequence=event.sequence,
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
