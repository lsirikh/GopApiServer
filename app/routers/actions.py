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
from app.models.event import ActionEvent
from app.schemas.event import ActionEventCreate, ActionEventResponse, ActionEventUpdate
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[ActionEventResponse]])
async def get_action_events(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    user: Optional[str] = Query(None, description="Filter by user"),
    from_event_id: Optional[int] = Query(None, description="Filter by from_event_id"),
    from_event_type: Optional[str] = Query(None, description="Filter by from_event_type"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of action events with pagination and filters

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        user: Filter by user
        from_event_id: Filter by referenced event ID
        from_event_type: Filter by referenced event type
        start_date: Filter by start date (event datetime >= start_date)
        end_date: Filter by end date (event datetime <= end_date)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of action events and pagination metadata
    """
    # Build query
    query = db.query(ActionEvent)

    # Apply filters
    if user is not None:
        query = query.filter(ActionEvent.user == user)
    if from_event_id is not None:
        query = query.filter(ActionEvent.from_event_id == from_event_id)
    if from_event_type is not None:
        query = query.filter(ActionEvent.from_event_type == from_event_type)
    if start_date is not None:
        query = query.filter(ActionEvent.datetime >= start_date)
    if end_date is not None:
        query = query.filter(ActionEvent.datetime <= end_date)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by datetime desc)
    events = query.order_by(ActionEvent.datetime.desc()).offset(skip).limit(limit).all()

    # Convert to response format
    event_responses = [
        ActionEventResponse(
            id=e.id,
            type_event=e.type_event,
            content=e.content,
            user=e.user,
            from_event_id=e.from_event_id,
            from_event_type=e.from_event_type,
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

    Args:
        event_id: Action event ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with action event data

    Raises:
        HTTPException 404: If action event not found
    """
    event = db.query(ActionEvent).filter(ActionEvent.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action event with id {event_id} not found"
        )

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event_id=event.from_event_id,
        from_event_type=event.from_event_type,
        datetime=event.datetime,
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

    Args:
        event_data: Action event creation data
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created action event data
    """
    # Create new action event
    new_event = ActionEvent(
        type_event=event_data.type_event,
        content=event_data.content,
        user=event_data.user,
        from_event_id=event_data.from_event_id,
        from_event_type=event_data.from_event_type,
        datetime=event_data.datetime
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    event_response = ActionEventResponse(
        id=new_event.id,
        type_event=new_event.type_event,
        content=new_event.content,
        user=new_event.user,
        from_event_id=new_event.from_event_id,
        from_event_type=new_event.from_event_type,
        datetime=new_event.datetime,
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

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event_id=event.from_event_id,
        from_event_type=event.from_event_type,
        datetime=event.datetime,
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
    event.from_event_id = event_data.from_event_id
    event.from_event_type = event_data.from_event_type
    event.datetime = event_data.datetime

    db.commit()
    db.refresh(event)

    event_response = ActionEventResponse(
        id=event.id,
        type_event=event.type_event,
        content=event.content,
        user=event.user,
        from_event_id=event.from_event_id,
        from_event_type=event.from_event_type,
        datetime=event.datetime,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    return ApiResponse(
        success=True,
        message="Action event replaced successfully",
        data=event_response
    )


@router.delete("/{event_id}", response_model=ApiResponse[dict])
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

    db.delete(event)
    db.commit()

    return ApiResponse(
        success=True,
        message="Action event deleted successfully",
        data={"id": event_id}
    )
