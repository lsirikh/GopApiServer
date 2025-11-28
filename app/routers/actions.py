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
    Update source event's action_reported field to "True" when ActionEvent is created

    Args:
        db: Database session
        event_id: Event ID to update
        event_type: Event type ("Intrusion" or "Fault")

    Note:
        Only Intrusion (DetectionEvent) and Fault (MalfunctionEvent) events have action_reported field.
        Connection events are skipped.
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
    Reset source event's action_reported field to "False" when ActionEvent is deleted

    Due to 1:1 relationship between source event and ActionEvent,
    we unconditionally reset to "False" without counting remaining ActionEvents.

    Args:
        db: Database session
        event_id: Event ID to update
        event_type: Event type ("Intrusion" or "Fault")

    Note:
        Only Intrusion (DetectionEvent) and Fault (MalfunctionEvent) events have action_reported field.
        Connection events are skipped.
        This function does NOT commit - the caller is responsible for committing.
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
    Load source event by ID and type, and return appropriate response schema

    Args:
        db: Database session
        event_id: Event ID to load
        event_type: Event type ("Intrusion", "Fault", or "Connection")

    Returns:
        DetectionEventResponse, MalfunctionEventResponse, or ConnectionEventResponse

    Raises:
        HTTPException 404: If event not found
        HTTPException 400: If invalid event_type
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
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Optional[str] = Query(None, description="Filter by user"),
    from_event: Optional[int] = Query(None, description="Filter by from_event"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of action events with pagination and filters

    Returns action events with nested source event objects. Each action event's
    `from_event` field contains the full source event data (detection, malfunction,
    or connection) instead of just the ID.

    The response uses batch loading to optimize performance - all source events
    are loaded in a single query per event type, avoiding N+1 query problems.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        user: Filter by user who performed the action
        from_event: Filter by referenced source event ID
        start_date: Filter by start date (event datetime >= start_date)
        end_date: Filter by end date (event datetime <= end_date)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of action events and pagination metadata.
        Each action event includes a nested source event object in the `from_event` field.
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
    Get a single action event by ID

    Returns an action event with its nested source event object. The `from_event`
    field contains the full source event data (detection, malfunction, or connection)
    instead of just the ID.

    Args:
        event_id: Action event ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with action event data including nested source event object

    Raises:
        HTTPException 404: If action event not found or source event not found
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
    Create a new action event

    This endpoint creates a new action event that references a source event
    (detection, malfunction, or connection event) using polymorphic reference.

    Args:
        event_data: Action event creation data including:
            - from_event: ID of the source event
            - from_type_event: Type of source event ("Intrusion", "Fault", or "Connection")
            - content: Description of the action taken
            - user: User who performed the action
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created action event data. The `from_event` field in the
        response contains the full nested source event object (not just the ID).

    Raises:
        HTTPException 404: If the referenced source event is not found
        HTTPException 400: If invalid from_type_event is provided

    Example:
        ```json
        {
            "type_event": "Action",
            "content": "Verified and cleared the alert",
            "user": "admin",
            "from_event": 123,
            "from_type_event": "Intrusion",
            "datetime": "2025-11-12T14:00:00"
        }
        ```
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
    Update an action event (partial update)

    Args:
        event_id: Action event ID
        event_data: Action event update data (all fields optional)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated action event data

    Raises:
        HTTPException 404: If action event not found
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
    Replace an action event (full update - all fields required)

    Args:
        event_id: Action event ID
        event_data: Complete action event data (all fields required)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated action event data

    Raises:
        HTTPException 404: If action event not found
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
    Delete an action event

    Args:
        event_id: Action event ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with deletion confirmation

    Raises:
        HTTPException 404: If action event not found
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
