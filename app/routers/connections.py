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
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    controller: Optional[int] = Query(None, description="Filter by controller"),
    sensor: Optional[int] = Query(None, description="Filter by sensor"),
    type_device: Optional[str] = Query(None, description="Filter by device type"),
    group_event: Optional[str] = Query(None, description="Filter by group_event"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of connection events with pagination and filters

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        controller: Filter by controller number
        sensor: Filter by sensor number
        type_device: Filter by device type
        group_event: Filter by group_event
        start_date: Filter by start date (event datetime >= start_date)
        end_date: Filter by end date (event datetime <= end_date)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of connection events and pagination metadata
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
        query = query.filter(ConnectionEvent.datetime >= start_date)
    if end_date is not None:
        query = query.filter(ConnectionEvent.datetime <= end_date)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by datetime desc)
    events = query.order_by(ConnectionEvent.datetime.desc()).offset(skip).limit(limit).all()

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
            datetime=e.datetime,
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
    Get a single connection event by ID

    Args:
        event_id: Connection event ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with connection event data

    Raises:
        HTTPException 404: If connection event not found
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
        datetime=event.datetime,
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
    Create a new connection event

    Args:
        event_data: Connection event creation data
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created connection event data

    Raises:
        HTTPException 422: If invalid enum value provided
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
        sequence=event_data.sequence,
        datetime=event_data.datetime
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
        datetime=new_event.datetime,
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
    Update a connection event (partial update)

    Args:
        event_id: Connection event ID
        event_data: Connection event update data (all fields optional)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated connection event data

    Raises:
        HTTPException 404: If connection event not found
        HTTPException 422: If invalid enum value provided
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
        datetime=event.datetime,
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
    Replace a connection event (full update - all fields required)

    Args:
        event_id: Connection event ID
        event_data: Complete connection event data (all fields required)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated connection event data

    Raises:
        HTTPException 404: If connection event not found
        HTTPException 422: If invalid enum value provided
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
    event.datetime = event_data.datetime

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
        datetime=event.datetime,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Connection event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiResponse[dict])
async def delete_connection_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Delete a connection event

    Args:
        event_id: Connection event ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with deletion confirmation

    Raises:
        HTTPException 404: If connection event not found
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
        data={"id": event_id}
    )
