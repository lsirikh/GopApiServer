"""
EventMapping API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.integration import EventMapping
from app.schemas.integration import EventMappingCreate, EventMappingResponse, EventMappingUpdate
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[EventMappingResponse]])
async def get_event_mappings(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    name_event: Optional[str] = Query(None, description="Filter by name_event"),
    group_event: Optional[str] = Query(None, description="Filter by group_event"),
    category_event: Optional[str] = Query(None, description="Filter by category_event"),
    status: Optional[bool] = Query(None, description="Filter by status"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of event mappings with pagination and filters

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        name_event: Filter by name_event
        group_event: Filter by group_event
        category_event: Filter by category_event
        status: Filter by status
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of event mappings and pagination metadata
    """
    # Build query
    query = db.query(EventMapping)

    # Apply filters
    if name_event is not None:
        query = query.filter(EventMapping.name_event == name_event)
    if group_event is not None:
        query = query.filter(EventMapping.group_event == group_event)
    if category_event is not None:
        query = query.filter(EventMapping.category_event == category_event)
    if status is not None:
        query = query.filter(EventMapping.status == status)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    mappings = query.offset(skip).limit(limit).all()

    # Convert to response format
    mapping_responses = [
        EventMappingResponse(
            id=m.id,
            name_event=m.name_event,
            group_event=m.group_event,
            category_event=m.category_event,
            description=m.description,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in mappings
    ]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Event mappings retrieved successfully",
        data=mapping_responses,
        pagination=pagination
    )


@router.get("/{mapping_id}", response_model=ApiResponse[EventMappingResponse])
async def get_event_mapping(
    mapping_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get a single event mapping by ID

    Args:
        mapping_id: EventMapping ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with event mapping data

    Raises:
        HTTPException 404: If event mapping not found
    """
    mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    mapping_response = EventMappingResponse(
        id=mapping.id,
        name_event=mapping.name_event,
        group_event=mapping.group_event,
        category_event=mapping.category_event,
        description=mapping.description,
        status=mapping.status,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping retrieved successfully",
        data=mapping_response
    )


@router.post("", response_model=ApiResponse[EventMappingResponse], status_code=status.HTTP_201_CREATED)
async def create_event_mapping(
    mapping: EventMappingCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Create a new event mapping

    Args:
        mapping: EventMapping creation data
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created event mapping
    """
    new_mapping = EventMapping(
        name_event=mapping.name_event,
        group_event=mapping.group_event,
        category_event=mapping.category_event,
        description=mapping.description,
        status=mapping.status
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    mapping_response = EventMappingResponse(
        id=new_mapping.id,
        name_event=new_mapping.name_event,
        group_event=new_mapping.group_event,
        category_event=new_mapping.category_event,
        description=new_mapping.description,
        status=new_mapping.status,
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping created successfully",
        data=mapping_response
    )


@router.patch("/{mapping_id}", response_model=ApiResponse[EventMappingResponse])
async def update_event_mapping_partial(
    mapping_id: int,
    mapping: EventMappingUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Partially update an event mapping (PATCH)

    Args:
        mapping_id: EventMapping ID
        mapping: EventMapping update data (all fields optional)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated event mapping

    Raises:
        HTTPException 404: If event mapping not found
    """
    existing_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Update only provided fields
    update_data = mapping.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_mapping, field, value)

    db.commit()
    db.refresh(existing_mapping)

    mapping_response = EventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        group_event=existing_mapping.group_event,
        category_event=existing_mapping.category_event,
        description=existing_mapping.description,
        status=existing_mapping.status,
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping updated successfully",
        data=mapping_response
    )


@router.put("/{mapping_id}", response_model=ApiResponse[EventMappingResponse])
async def update_event_mapping_full(
    mapping_id: int,
    mapping: EventMappingCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Fully update an event mapping (PUT)

    Args:
        mapping_id: EventMapping ID
        mapping: EventMapping data (all fields required)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated event mapping

    Raises:
        HTTPException 404: If event mapping not found
    """
    existing_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Update all fields
    existing_mapping.name_event = mapping.name_event
    existing_mapping.group_event = mapping.group_event
    existing_mapping.category_event = mapping.category_event
    existing_mapping.description = mapping.description
    existing_mapping.status = mapping.status

    db.commit()
    db.refresh(existing_mapping)

    mapping_response = EventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        group_event=existing_mapping.group_event,
        category_event=existing_mapping.category_event,
        description=existing_mapping.description,
        status=existing_mapping.status,
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping updated successfully",
        data=mapping_response
    )


@router.delete("/{mapping_id}", response_model=ApiResponse[dict])
async def delete_event_mapping(
    mapping_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Delete an event mapping

    Args:
        mapping_id: EventMapping ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with deletion confirmation

    Raises:
        HTTPException 404: If event mapping not found
    """
    mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    db.delete(mapping)
    db.commit()

    return ApiResponse(
        success=True,
        message="Event mapping deleted successfully",
        data={"id": mapping_id}
    )
