"""
Action Event API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.event import ActionEvent, DetectionEvent, MalfunctionEvent, ConnectionEvent
from app.schemas.event import (
    ActionEventCreate, ActionEventResponse, ActionEventUpdate,
    DetectionEventResponse, MalfunctionEventResponse, ConnectionEventResponse
)
from app.schemas.common import ApiResponse, PaginationMeta
from app.utils.enums import EnumTrueFalse
from typing import Union

router = APIRouter(tags=[])


# Helper function to update source event action_reported
def update_source_action_reported(db: Session, event_id: int, event_type: str) -> None:
    """
    ActionEvent 생성 시 원본 이벤트의 action_reported 필드를 "True"로 업데이트

    Args:
        db: 데이터베이스 세션
        event_id: 업데이트할 이벤트 ID
        event_type: 이벤트 유형 ("Intrusion" 또는 "Fault")

    Note:
        Intrusion (DetectionEvent)과 Fault (MalfunctionEvent) 이벤트만 action_reported 필드를 가집니다.
        Connection 이벤트는 건너뜁니다.
    """
    if event_type == "Intrusion":
        source = db.query(DetectionEvent).filter(DetectionEvent.id == event_id).first()
        if source:
            source.action_reported = "True"
            db.commit()
    elif event_type == "Fault":
        source = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()
        if source:
            source.action_reported = "True"
            db.commit()
    # Connection events are skipped (no action_reported field)


# Helper function to reset source event action_reported
def reset_source_action_reported(db: Session, event_id: int, event_type: str) -> None:
    """
    ActionEvent 삭제 시 원본 이벤트의 action_reported 필드를 "False"로 리셋

    원본 이벤트와 ActionEvent의 1:1 관계로 인해 남은 ActionEvent 수를 세지 않고
    무조건 "False"로 리셋합니다.

    Args:
        db: 데이터베이스 세션
        event_id: 업데이트할 이벤트 ID
        event_type: 이벤트 유형 ("Intrusion" 또는 "Fault")

    Note:
        Intrusion (DetectionEvent)과 Fault (MalfunctionEvent) 이벤트만 action_reported 필드를 가집니다.
        Connection 이벤트는 건너뜁니다.
        이 함수는 커밋하지 않습니다 - 호출자가 커밋해야 합니다.
    """
    if event_type == "Intrusion":
        source = db.query(DetectionEvent).filter(DetectionEvent.id == event_id).first()
        if source:
            source.action_reported = "False"
    elif event_type == "Fault":
        source = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()
        if source:
            source.action_reported = "False"
    # Connection events are skipped (no action_reported field)


# Helper function to load source event
def load_source_event(db: Session, event_id: int, event_type: str) -> Union[DetectionEventResponse, MalfunctionEventResponse, ConnectionEventResponse]:
    """
    ID와 유형으로 원본 이벤트를 로드하고 적절한 응답 스키마를 반환

    Args:
        db: 데이터베이스 세션
        event_id: 로드할 이벤트 ID
        event_type: 이벤트 유형 ("Intrusion", "Fault", 또는 "Connection")

    Returns:
        DetectionEventResponse, MalfunctionEventResponse, 또는 ConnectionEventResponse

    Raises:
        HTTPException 404: 이벤트를 찾을 수 없음
        HTTPException 400: 유효하지 않은 event_type
    """
    # Query only the specific table based on event_type (1 query instead of 3!)
    if event_type == "Intrusion":
        event = db.query(DetectionEvent).filter(DetectionEvent.id == event_id).first()
        if event:
            return DetectionEventResponse.model_validate(event)
    elif event_type == "Fault":
        event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()
        if event:
            return MalfunctionEventResponse.model_validate(event)
    elif event_type == "Connection":
        event = db.query(ConnectionEvent).filter(ConnectionEvent.id == event_id).first()
        if event:
            return ConnectionEventResponse.model_validate(event)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event_type: {event_type}. Must be 'Intrusion', 'Fault', or 'Connection'"
        )

    # Not found in the specified table
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Source event with id {event_id} and type '{event_type}' not found"
    )


@router.get("", response_model=ApiResponse[list[ActionEventResponse]])
async def get_action_events(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    user: Optional[str] = Query(None, description="사용자로 필터링"),
    from_event: Optional[int] = Query(None, description="원본 이벤트 ID로 필터링"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜로 필터링 (이벤트 생성일 >= start_date)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜로 필터링 (이벤트 생성일 <= end_date)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    조치 이벤트 목록 조회 (페이지네이션)

    조치 이벤트 목록을 페이지네이션하여 조회합니다. 각 조치 이벤트의 `from_event` 필드에는
    원본 이벤트(탐지, 장애, 연결)의 전체 데이터가 포함됩니다.

    응답은 배치 로딩을 사용하여 성능을 최적화합니다 - 모든 원본 이벤트는 이벤트 유형별로
    단일 쿼리로 로드되어 N+1 쿼리 문제를 방지합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **user**: 조치를 수행한 사용자로 필터링
    - **from_event**: 원본 이벤트 ID로 필터링
    - **start_date**: 시작 날짜로 필터링
    - **end_date**: 종료 날짜로 필터링

    **Response**: 조치 이벤트 목록 및 페이지네이션 정보 (각 이벤트에 중첩된 원본 이벤트 포함)
    """
    # Build query
    query = db.query(ActionEvent)

    # Apply filters
    if user is not None:
        query = query.filter(ActionEvent.user == user)
    if from_event is not None:
        query = query.filter(ActionEvent.from_event == from_event)
    if start_date is not None:
        query = query.filter(ActionEvent.created_at >= start_date)
    if end_date is not None:
        query = query.filter(ActionEvent.created_at <= end_date)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by created_at desc)
    events = query.order_by(ActionEvent.created_at.desc()).offset(skip).limit(limit).all()

    # Batch load source events to avoid N+1 query problem
    # Group events by type for efficient querying
    detection_ids = [e.from_event for e in events if e.from_type_event == "Intrusion"]
    malfunction_ids = [e.from_event for e in events if e.from_type_event == "Fault"]
    connection_ids = [e.from_event for e in events if e.from_type_event == "Connection"]

    # Query only the necessary tables based on event types
    # Use composite key (event_type, event_id) to handle ID collisions across tables
    event_map = {}

    if detection_ids:
        detections = db.query(DetectionEvent).filter(DetectionEvent.id.in_(detection_ids)).all()
        for detection in detections:
            event_map[("Intrusion", detection.id)] = DetectionEventResponse.model_validate(detection)

    if malfunction_ids:
        malfunctions = db.query(MalfunctionEvent).filter(MalfunctionEvent.id.in_(malfunction_ids)).all()
        for malfunction in malfunctions:
            event_map[("Fault", malfunction.id)] = MalfunctionEventResponse.model_validate(malfunction)

    if connection_ids:
        connections = db.query(ConnectionEvent).filter(ConnectionEvent.id.in_(connection_ids)).all()
        for connection in connections:
            event_map[("Connection", connection.id)] = ConnectionEventResponse.model_validate(connection)

    # Convert to response format with nested source events
    event_responses = []
    for e in events:
        source_event = event_map.get((e.from_type_event, e.from_event))
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


@router.get("/{event_id}", response_model=ApiResponse[ActionEventResponse])
async def get_action_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    조치 이벤트 단건 조회

    특정 조치 이벤트의 상세 정보를 조회합니다. `from_event` 필드에는
    원본 이벤트(탐지, 장애, 연결)의 전체 데이터가 포함됩니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Response**: 조치 이벤트 상세 정보 (중첩된 원본 이벤트 객체 포함)

    **Error**:
    - 404: 조치 이벤트 또는 원본 이벤트를 찾을 수 없음
    """
    event = db.query(ActionEvent).filter(ActionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # Load nested source event with type for efficient querying
    source_event = load_source_event(db, event.from_event, event.from_type_event)

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event=source_event,  # Nested event object
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Action event retrieved successfully",
        data=event_response
    )


@router.post("", response_model=ApiResponse[ActionEventResponse], status_code=status.HTTP_201_CREATED)
async def create_action_event(
    event_data: ActionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    조치 이벤트 생성

    새로운 조치 이벤트를 생성합니다. 이 엔드포인트는 다형성 참조를 사용하여
    원본 이벤트(탐지, 장애, 연결)를 참조하는 조치 이벤트를 생성합니다.

    **Request Body**:
    - **type_event**: 이벤트 유형 (필수)
    - **content**: 조치 내용 설명 (필수)
    - **user**: 조치를 수행한 사용자 (필수)
    - **from_event**: 원본 이벤트 ID (필수)
    - **from_type_event**: 원본 이벤트 유형 - "Intrusion", "Fault", "Connection" (필수)
    - **created_at**: 조치 일시 (선택)

    **Response**: 생성된 조치 이벤트 정보 (중첩된 원본 이벤트 객체 포함)

    **Error**:
    - 404: 참조된 원본 이벤트를 찾을 수 없음
    - 400: 유효하지 않은 from_type_event 값
    """
    # Create new action event
    new_event = ActionEvent(
        type_event=event_data.type_event,
        content=event_data.content,
        user=event_data.user,
        from_event=event_data.from_event,
        from_type_event=event_data.from_type_event,
        created_at=event_data.created_at
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # Update source event's action_reported to "True" (only for Intrusion and Fault events)
    update_source_action_reported(db, new_event.from_event, new_event.from_type_event)

    # Load nested source event with type for efficient querying
    source_event = load_source_event(db, new_event.from_event, new_event.from_type_event)

    event_response = ActionEventResponse(
        id=new_event.id,
        type_event=new_event.type_event,
        content=new_event.content,
        user=new_event.user,
        from_event=source_event,  # Nested event object
        created_at=new_event.created_at,
        updated_at=new_event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Action event created successfully",
        data=event_response
    )


@router.patch("/{event_id}", response_model=ApiResponse[ActionEventResponse])
async def update_action_event(
    event_id: int,
    event_data: ActionEventUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    조치 이벤트 부분 수정 (PATCH)

    조치 이벤트의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **type_event**: 이벤트 유형
    - **content**: 조치 내용 설명
    - **user**: 조치를 수행한 사용자

    **Response**: 수정된 조치 이벤트 정보

    **Error**:
    - 404: 조치 이벤트를 찾을 수 없음
    """
    event = db.query(ActionEvent).filter(ActionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # Update fields if provided
    update_data = event_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    # Load nested source event with type for efficient querying
    source_event = load_source_event(db, event.from_event, event.from_type_event)

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event=source_event,  # Nested event object
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Action event updated successfully",
        data=event_response
    )


@router.put("/{event_id}", response_model=ApiResponse[ActionEventResponse])
async def replace_action_event(
    event_id: int,
    event_data: ActionEventCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    조치 이벤트 전체 수정 (PUT)

    조치 이벤트의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **type_event**: 이벤트 유형
    - **content**: 조치 내용 설명
    - **user**: 조치를 수행한 사용자
    - **from_event**: 원본 이벤트 ID
    - **from_type_event**: 원본 이벤트 유형

    **Response**: 수정된 조치 이벤트 정보

    **Error**:
    - 404: 조치 이벤트를 찾을 수 없음
    """
    event = db.query(ActionEvent).filter(ActionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # Replace all fields (PUT = full replacement)
    event.type_event = event_data.type_event
    event.content = event_data.content
    event.user = event_data.user
    event.from_event = event_data.from_event
    event.from_type_event = event_data.from_type_event

    db.commit()
    db.refresh(event)

    # Load nested source event with type for efficient querying
    source_event = load_source_event(db, event.from_event, event.from_type_event)

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event=source_event,  # Nested event object
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Action event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiResponse[Optional[dict]])
async def delete_action_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    조치 이벤트 삭제

    특정 조치 이벤트를 삭제합니다. 삭제 시 원본 이벤트의 action_reported 필드가
    "False"로 리셋됩니다.

    **파라미터**:
    - **event_id**: 조치 이벤트 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 조치 이벤트를 찾을 수 없음
    """
    event = db.query(ActionEvent).filter(ActionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    # Reset source event's action_reported to "False" (1:1 relationship)
    reset_source_action_reported(db, event.from_event, event.from_type_event)

    db.delete(event)
    db.commit()

    return ApiResponse(
        success=True,
        message="Action event deleted successfully",
        data=None
    )
