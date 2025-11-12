"""
Controller API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Controller, EnumDeviceType, EnumDeviceStatus
from app.schemas.device import ControllerCreate, ControllerResponse, ControllerUpdate
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[ControllerResponse]])
async def get_controllers(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    group_device: Optional[int] = Query(None, description="Filter by group_device"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of controllers with pagination and filters

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        group_device: Filter by group_device
        status: Filter by status
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of controllers and pagination metadata
    """
    # Build query
    query = db.query(Controller)

    # Apply filters
    if group_device is not None:
        query = query.filter(Controller.group_device == group_device)
    if status is not None:
        query = query.filter(Controller.status == status)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    controllers = query.offset(skip).limit(limit).all()

    # Convert to response format
    controller_responses = [
        ControllerResponse(
            id=c.id,
            number_device=c.number_device,
            group_device=c.group_device,
            name_device=c.name_device,
            type_device=c.type_device.value,  # Convert enum to string
            version=c.version,
            status=c.status.value,  # Convert enum to string
            ip_address=c.ip_address,
            ip_port=c.ip_port,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in controllers
    ]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Controllers retrieved successfully",
        data=controller_responses,
        pagination=pagination
    )


@router.get("/{controller_id}", response_model=ApiResponse[ControllerResponse])
async def get_controller(
    controller_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get a single controller by ID

    Args:
        controller_id: Controller ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with controller data

    Raises:
        HTTPException 404: If controller not found
    """
    controller = db.query(Controller).filter(Controller.id == controller_id).first()

    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {controller_id} not found"
        )

    controller_response = ControllerResponse(
        id=controller.id,
        number_device=controller.number_device,
        group_device=controller.group_device,
        name_device=controller.name_device,
        type_device=controller.type_device.value,
        version=controller.version,
        status=controller.status.value,
        ip_address=controller.ip_address,
        ip_port=controller.ip_port,
        created_at=controller.created_at,
        updated_at=controller.updated_at
    )

    return ApiResponse(
        success=True,
        message="Controller retrieved successfully",
        data=controller_response
    )


@router.post("", response_model=ApiResponse[ControllerResponse], status_code=status.HTTP_201_CREATED)
async def create_controller(
    controller_data: ControllerCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Create a new controller

    Args:
        controller_data: Controller creation data
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created controller data

    Raises:
        HTTPException 409: If controller with same number_device already exists
    """
    # Check for duplicate number_device
    existing = db.query(Controller).filter(
        Controller.number_device == controller_data.number_device
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Controller with number_device {controller_data.number_device} already exists"
        )

    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(controller_data.type_device)
        device_status = EnumDeviceStatus(controller_data.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Create new controller
    new_controller = Controller(
        number_device=controller_data.number_device,
        group_device=controller_data.group_device,
        name_device=controller_data.name_device,
        type_device=device_type,
        version=controller_data.version,
        status=device_status,
        ip_address=controller_data.ip_address,
        ip_port=controller_data.ip_port
    )

    db.add(new_controller)
    db.commit()
    db.refresh(new_controller)

    controller_response = ControllerResponse(
        id=new_controller.id,
        number_device=new_controller.number_device,
        group_device=new_controller.group_device,
        name_device=new_controller.name_device,
        type_device=new_controller.type_device.value,
        version=new_controller.version,
        status=new_controller.status.value,
        ip_address=new_controller.ip_address,
        ip_port=new_controller.ip_port,
        created_at=new_controller.created_at,
        updated_at=new_controller.updated_at
    )

    return ApiResponse(
        success=True,
        message="Controller created successfully",
        data=controller_response
    )


@router.patch("/{controller_id}", response_model=ApiResponse[ControllerResponse])
async def update_controller(
    controller_id: int,
    controller_data: ControllerUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Update a controller (partial update)

    Args:
        controller_id: Controller ID
        controller_data: Controller update data (all fields optional)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated controller data

    Raises:
        HTTPException 404: If controller not found
        HTTPException 409: If number_device conflicts with existing controller
    """
    controller = db.query(Controller).filter(Controller.id == controller_id).first()

    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {controller_id} not found"
        )

    # Check for number_device conflict
    if controller_data.number_device is not None:
        existing = db.query(Controller).filter(
            Controller.number_device == controller_data.number_device,
            Controller.id != controller_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Controller with number_device {controller_data.number_device} already exists"
            )

    # Update fields if provided
    update_data = controller_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "type_device" and value is not None:
            try:
                value = EnumDeviceType(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid type_device value: {value}"
                )
        elif field == "status" and value is not None:
            try:
                value = EnumDeviceStatus(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status value: {value}"
                )

        setattr(controller, field, value)

    db.commit()
    db.refresh(controller)

    controller_response = ControllerResponse(
        id=controller.id,
        number_device=controller.number_device,
        group_device=controller.group_device,
        name_device=controller.name_device,
        type_device=controller.type_device.value,
        version=controller.version,
        status=controller.status.value,
        ip_address=controller.ip_address,
        ip_port=controller.ip_port,
        created_at=controller.created_at,
        updated_at=controller.updated_at
    )

    return ApiResponse(
        success=True,
        message="Controller updated successfully",
        data=controller_response
    )


@router.put("/{controller_id}", response_model=ApiResponse[ControllerResponse])
async def replace_controller(
    controller_id: int,
    controller_data: ControllerCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Replace a controller (full update - all fields required)

    Args:
        controller_id: Controller ID
        controller_data: Complete controller data (all fields required)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated controller data

    Raises:
        HTTPException 404: If controller not found
        HTTPException 409: If number_device conflicts with existing controller
    """
    controller = db.query(Controller).filter(Controller.id == controller_id).first()

    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {controller_id} not found"
        )

    # Check for number_device conflict
    if controller_data.number_device != controller.number_device:
        existing = db.query(Controller).filter(
            Controller.number_device == controller_data.number_device,
            Controller.id != controller_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Controller with number_device {controller_data.number_device} already exists"
            )

    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(controller_data.type_device)
        device_status = EnumDeviceStatus(controller_data.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Replace all fields (PUT = full replacement)
    controller.number_device = controller_data.number_device
    controller.group_device = controller_data.group_device
    controller.name_device = controller_data.name_device
    controller.type_device = device_type
    controller.version = controller_data.version
    controller.status = device_status
    controller.ip_address = controller_data.ip_address
    controller.ip_port = controller_data.ip_port

    db.commit()
    db.refresh(controller)

    controller_response = ControllerResponse(
        id=controller.id,
        number_device=controller.number_device,
        group_device=controller.group_device,
        name_device=controller.name_device,
        type_device=controller.type_device.value,
        version=controller.version,
        status=controller.status.value,
        ip_address=controller.ip_address,
        ip_port=controller.ip_port,
        created_at=controller.created_at,
        updated_at=controller.updated_at
    )

    return ApiResponse(
        success=True,
        message="Controller replaced successfully",
        data=controller_response
    )


@router.delete("/{controller_id}", response_model=ApiResponse[dict])
async def delete_controller(
    controller_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Delete a controller

    Args:
        controller_id: Controller ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with deletion confirmation

    Raises:
        HTTPException 404: If controller not found
    """
    controller = db.query(Controller).filter(Controller.id == controller_id).first()

    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {controller_id} not found"
        )

    db.delete(controller)
    db.commit()

    return ApiResponse(
        success=True,
        message="Controller deleted successfully",
        data={"id": controller_id}
    )
