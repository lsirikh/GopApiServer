"""
Malfunction Event API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.event import MalfunctionEvent, EnumTrueFalse, EnumFaultType
from app.schemas.event import MalfunctionEventCreate, MalfunctionEventResponse, MalfunctionEventUpdate
from app.schemas.common import ApiResponse, PaginationMeta
from app.utils.enums import EnumDeviceType

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[MalfunctionEventResponse]])
async def get_malfunction_events(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    controller: Optional[int] = Query(None, description="Filter by controller"),
    sensor: Optional[int] = Query(None, description="Filter by sensor"),
    type_device: Optional[str] = Query(None, description="Filter by device type"),
    group_event: Optional[str] = Query(None, description="Filter by group_event"),
    action_reported: Optional[str] = Query(None, description="Filter by action_reported"),
    reason: Optional[str] = Query(None, description="Filter by fault reason"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of malfunction events with pagination and filters

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        controller: Filter by controller number
        sensor: Filter by sensor number
        type_device: Filter by device type
        group_event: Filter by group_event
        action_reported: Filter by action_reported
        reason: Filter by fault reason
        start_date: Filter by start date (event datetime >= start_date)
        end_date: Filter by end date (event datetime <= end_date)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of malfunction events and pagination metadata
    """
    # Build query
    query = db.query(MalfunctionEvent)

    # Apply filters
    if controller is not None:
        query = query.filter(MalfunctionEvent.controller == controller)
    if sensor is not None:
        query = query.filter(MalfunctionEvent.sensor == sensor)
    if type_device is not None:
        query = query.filter(MalfunctionEvent.type_device == type_device)
    if group_event is not None:
        query = query.filter(MalfunctionEvent.group_event == group_event)
    if action_reported is not None:
        query = query.filter(MalfunctionEvent.action_reported == action_reported)
    if reason is not None:
        query = query.filter(MalfunctionEvent.reason == reason)
    if start_date is not None:
        query = query.filter(MalfunctionEvent.datetime >= start_date)
    if end_date is not None:
        query = query.filter(MalfunctionEvent.datetime <= end_date)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by datetime desc)
    events = query.order_by(MalfunctionEvent.datetime.desc()).offset(skip).limit(limit).all()

    # Convert to response format
    event_responses = [
        MalfunctionEventResponse(
            id=e.id,
            group_event=e.group_event,
            type_event=e.type_event,
            controller=e.controller,
            sensor=e.sensor,
            type_device=e.type_device.value,
            sequence=e.sequence,
            action_reported=e.action_reported.value,
            reason=e.reason.value,
            first_start=e.first_start,
            first_end=e.first_end,
            second_start=e.second_start,
            second_end=e.second_end,
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
    Get a single malfunction event by ID

    Args:
        event_id: Malfunction event ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with malfunction event data

    Raises:
        HTTPException 404: If malfunction event not found
    """
    event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    event_response = MalfunctionEventResponse(
        id=event.id,
        group_event=event.group_event,
        type_event=event.type_event,
        controller=event.controller,
        sensor=event.sensor,
        type_device=event.type_device.value,
        sequence=event.sequence,
        action_reported=event.action_reported.value,
        reason=event.reason.value,
        first_start=event.first_start,
        first_end=event.first_end,
        second_start=event.second_start,
        second_end=event.second_end,
        datetime=event.datetime,
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
    Create a new malfunction event

    Args:
        event_data: Malfunction event creation data
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created malfunction event data

    Raises:
        HTTPException 422: If invalid enum value provided
    """
    # Convert string enum values to enum types
    try:
        event_action_reported = EnumTrueFalse(event_data.action_reported)
        fault_reason = EnumFaultType(event_data.reason)
        event_type_device = EnumDeviceType(event_data.type_device)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Create new malfunction event
    new_event = MalfunctionEvent(
        group_event=event_data.group_event,
        type_event=event_data.type_event,
        controller=event_data.controller,
        sensor=event_data.sensor,
        type_device=event_type_device,
        sequence=event_data.sequence,
        action_reported=event_action_reported,
        reason=fault_reason,
        first_start=event_data.first_start,
        first_end=event_data.first_end,
        second_start=event_data.second_start,
        second_end=event_data.second_end,
        datetime=event_data.datetime
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    event_response = MalfunctionEventResponse(
        id=new_event.id,
        group_event=new_event.group_event,
        type_event=new_event.type_event,
        controller=new_event.controller,
        sensor=new_event.sensor,
        type_device=new_event.type_device.value,
        sequence=new_event.sequence,
        action_reported=new_event.action_reported.value,
        reason=new_event.reason.value,
        first_start=new_event.first_start,
        first_end=new_event.first_end,
        second_start=new_event.second_start,
        second_end=new_event.second_end,
        datetime=new_event.datetime,
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
    Update a malfunction event (partial update)

    Args:
        event_id: Malfunction event ID
        event_data: Malfunction event update data (all fields optional)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated malfunction event data

    Raises:
        HTTPException 404: If malfunction event not found
        HTTPException 422: If invalid enum value provided
    """
    event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # Update fields if provided
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
        elif field == "type_device" and value is not None:
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

    event_response = MalfunctionEventResponse(
        id=event.id,
        group_event=event.group_event,
        type_event=event.type_event,
        controller=event.controller,
        sensor=event.sensor,
        type_device=event.type_device.value,
        sequence=event.sequence,
        action_reported=event.action_reported.value,
        reason=event.reason.value,
        first_start=event.first_start,
        first_end=event.first_end,
        second_start=event.second_start,
        second_end=event.second_end,
        datetime=event.datetime,
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
    Replace a malfunction event (full update - all fields required)

    Args:
        event_id: Malfunction event ID
        event_data: Complete malfunction event data (all fields required)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated malfunction event data

    Raises:
        HTTPException 404: If malfunction event not found
        HTTPException 422: If invalid enum value provided
    """
    event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    # Convert string enum values to enum types
    try:
        event_action_reported = EnumTrueFalse(event_data.action_reported)
        fault_reason = EnumFaultType(event_data.reason)
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
    event.action_reported = event_action_reported
    event.reason = fault_reason
    event.first_start = event_data.first_start
    event.first_end = event_data.first_end
    event.second_start = event_data.second_start
    event.second_end = event_data.second_end
    event.datetime = event_data.datetime

    db.commit()
    db.refresh(event)

    event_response = MalfunctionEventResponse(
        id=event.id,
        group_event=event.group_event,
        type_event=event.type_event,
        controller=event.controller,
        sensor=event.sensor,
        type_device=event.type_device.value,
        sequence=event.sequence,
        action_reported=event.action_reported.value,
        reason=event.reason.value,
        first_start=event.first_start,
        first_end=event.first_end,
        second_start=event.second_start,
        second_end=event.second_end,
        datetime=event.datetime,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Malfunction event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiResponse[dict])
async def delete_malfunction_event(
    event_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Delete a malfunction event

    Args:
        event_id: Malfunction event ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with deletion confirmation

    Raises:
        HTTPException 404: If malfunction event not found
    """
    event = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malfunction event with id {event_id} not found"
        )

    db.delete(event)
    db.commit()

    return ApiResponse(
        success=True,
        message="Malfunction event deleted successfully",
        data={"id": event_id}
    )
