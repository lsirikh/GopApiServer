"""
Sensor API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Sensor, Controller, EnumDeviceType, EnumDeviceStatus
from app.schemas.device import SensorCreate, SensorResponse, SensorUpdate
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[SensorResponse]])
async def get_sensors(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    group_device: Optional[int] = Query(None, description="Filter by group_device"),
    controller_id: Optional[int] = Query(None, description="Filter by controller_id"),
    type_device: Optional[str] = Query(None, description="Filter by type_device"),
    status: Optional[str] = Query(None, description="Filter by status"),
    include_controller: bool = Query(False, description="Include controller information"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of sensors with pagination and filters

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        group_device: Filter by group_device
        controller_id: Filter by controller_id
        type_device: Filter by type_device
        status: Filter by status
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of sensors and pagination metadata
    """
    # Build query
    query = db.query(Sensor)

    # Apply filters
    if group_device is not None:
        query = query.filter(Sensor.group_device == group_device)
    if controller_id is not None:
        query = query.filter(Sensor.controller_id == controller_id)
    if type_device is not None:
        query = query.filter(Sensor.type_device == type_device)
    if status is not None:
        query = query.filter(Sensor.status == status)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    sensors = query.offset(skip).limit(limit).all()

    # Convert to response format
    sensor_responses = []
    for s in sensors:
        sensor_data = {
            "id": s.id,
            "number_device": s.number_device,
            "group_device": s.group_device,
            "name_device": s.name_device,
            "type_device": s.type_device.value,
            "version": s.version,
            "status": s.status.value,
            "controller_id": s.controller_id,
            "created_at": s.created_at,
            "updated_at": s.updated_at
        }

        # Include controller info if requested
        if include_controller and s.controller:
            from app.schemas.device import ControllerResponse
            sensor_data["controller"] = ControllerResponse(
                id=s.controller.id,
                number_device=s.controller.number_device,
                group_device=s.controller.group_device,
                name_device=s.controller.name_device,
                type_device=s.controller.type_device.value,
                version=s.controller.version,
                status=s.controller.status.value,
                ip_address=s.controller.ip_address,
                ip_port=s.controller.ip_port,
                created_at=s.controller.created_at,
                updated_at=s.controller.updated_at
            )

        sensor_responses.append(SensorResponse(**sensor_data))

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Sensors retrieved successfully",
        data=sensor_responses,
        pagination=pagination
    )


@router.get("/{sensor_id}", response_model=ApiResponse[SensorResponse])
async def get_sensor(
    sensor_id: int,
    include_controller: bool = Query(False, description="Include controller information"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get a single sensor by ID

    Args:
        sensor_id: Sensor ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with sensor data

    Raises:
        HTTPException 404: If sensor not found
    """
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    sensor_data = {
        "id": sensor.id,
        "number_device": sensor.number_device,
        "group_device": sensor.group_device,
        "name_device": sensor.name_device,
        "type_device": sensor.type_device.value,
        "version": sensor.version,
        "status": sensor.status.value,
        "controller_id": sensor.controller_id,
        "created_at": sensor.created_at,
        "updated_at": sensor.updated_at
    }

    # Include controller info if requested
    if include_controller and sensor.controller:
        from app.schemas.device import ControllerResponse
        sensor_data["controller"] = ControllerResponse(
            id=sensor.controller.id,
            number_device=sensor.controller.number_device,
            group_device=sensor.controller.group_device,
            name_device=sensor.controller.name_device,
            type_device=sensor.controller.type_device.value,
            version=sensor.controller.version,
            status=sensor.controller.status.value,
            ip_address=sensor.controller.ip_address,
            ip_port=sensor.controller.ip_port,
            created_at=sensor.controller.created_at,
            updated_at=sensor.controller.updated_at
        )

    sensor_response = SensorResponse(**sensor_data)

    return ApiResponse(
        success=True,
        message="Sensor retrieved successfully",
        data=sensor_response
    )


@router.post("", response_model=ApiResponse[SensorResponse], status_code=status.HTTP_201_CREATED)
async def create_sensor(
    sensor_data: SensorCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Create a new sensor

    Args:
        sensor_data: Sensor creation data
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created sensor data

    Raises:
        HTTPException 404: If controller not found
        HTTPException 409: If sensor with same number_device already exists
    """
    # Validate controller exists
    controller = db.query(Controller).filter(Controller.id == sensor_data.controller_id).first()
    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {sensor_data.controller_id} not found"
        )

    # Check for duplicate number_device
    existing = db.query(Sensor).filter(
        Sensor.number_device == sensor_data.number_device
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sensor with number_device {sensor_data.number_device} already exists"
        )

    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(sensor_data.type_device)
        device_status = EnumDeviceStatus(sensor_data.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Create new sensor
    new_sensor = Sensor(
        number_device=sensor_data.number_device,
        group_device=sensor_data.group_device,
        name_device=sensor_data.name_device,
        type_device=device_type,
        version=sensor_data.version,
        status=device_status,
        controller_id=sensor_data.controller_id
    )

    db.add(new_sensor)
    db.commit()
    db.refresh(new_sensor)

    sensor_response = SensorResponse(
        id=new_sensor.id,
        number_device=new_sensor.number_device,
        group_device=new_sensor.group_device,
        name_device=new_sensor.name_device,
        type_device=new_sensor.type_device.value,
        version=new_sensor.version,
        status=new_sensor.status.value,
        controller_id=new_sensor.controller_id,
        created_at=new_sensor.created_at,
        updated_at=new_sensor.updated_at
    )

    return ApiResponse(
        success=True,
        message="Sensor created successfully",
        data=sensor_response
    )


@router.patch("/{sensor_id}", response_model=ApiResponse[SensorResponse])
async def update_sensor(
    sensor_id: int,
    sensor_data: SensorUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Update a sensor (partial update)

    Args:
        sensor_id: Sensor ID
        sensor_data: Sensor update data (all fields optional)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated sensor data

    Raises:
        HTTPException 404: If sensor not found or controller not found
        HTTPException 409: If number_device conflicts with existing sensor
    """
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    # Check for number_device conflict
    if sensor_data.number_device is not None:
        existing = db.query(Sensor).filter(
            Sensor.number_device == sensor_data.number_device,
            Sensor.id != sensor_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Sensor with number_device {sensor_data.number_device} already exists"
            )

    # Validate controller exists if updating controller_id
    if sensor_data.controller_id is not None:
        controller = db.query(Controller).filter(Controller.id == sensor_data.controller_id).first()
        if not controller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Controller with id {sensor_data.controller_id} not found"
            )

    # Update fields if provided
    update_data = sensor_data.model_dump(exclude_unset=True)

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

        setattr(sensor, field, value)

    db.commit()
    db.refresh(sensor)

    sensor_response = SensorResponse(
        id=sensor.id,
        number_device=sensor.number_device,
        group_device=sensor.group_device,
        name_device=sensor.name_device,
        type_device=sensor.type_device.value,
        version=sensor.version,
        status=sensor.status.value,
        controller_id=sensor.controller_id,
        created_at=sensor.created_at,
        updated_at=sensor.updated_at
    )

    return ApiResponse(
        success=True,
        message="Sensor updated successfully",
        data=sensor_response
    )


@router.put("/{sensor_id}", response_model=ApiResponse[SensorResponse])
async def replace_sensor(
    sensor_id: int,
    sensor_data: SensorCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Replace a sensor (full update - all fields required)

    Args:
        sensor_id: Sensor ID
        sensor_data: Complete sensor data (all fields required)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated sensor data

    Raises:
        HTTPException 404: If sensor not found or controller not found
        HTTPException 409: If number_device conflicts with existing sensor
    """
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    # Check for number_device conflict
    if sensor_data.number_device != sensor.number_device:
        existing = db.query(Sensor).filter(
            Sensor.number_device == sensor_data.number_device,
            Sensor.id != sensor_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Sensor with number_device {sensor_data.number_device} already exists"
            )

    # Validate controller exists
    controller = db.query(Controller).filter(Controller.id == sensor_data.controller_id).first()
    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {sensor_data.controller_id} not found"
        )

    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(sensor_data.type_device)
        device_status = EnumDeviceStatus(sensor_data.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Replace all fields (PUT = full replacement)
    sensor.number_device = sensor_data.number_device
    sensor.group_device = sensor_data.group_device
    sensor.name_device = sensor_data.name_device
    sensor.type_device = device_type
    sensor.version = sensor_data.version
    sensor.status = device_status
    sensor.controller_id = sensor_data.controller_id

    db.commit()
    db.refresh(sensor)

    sensor_response = SensorResponse(
        id=sensor.id,
        number_device=sensor.number_device,
        group_device=sensor.group_device,
        name_device=sensor.name_device,
        type_device=sensor.type_device.value,
        version=sensor.version,
        status=sensor.status.value,
        controller_id=sensor.controller_id,
        created_at=sensor.created_at,
        updated_at=sensor.updated_at
    )

    return ApiResponse(
        success=True,
        message="Sensor replaced successfully",
        data=sensor_response
    )


@router.delete("/{sensor_id}", response_model=ApiResponse[dict])
async def delete_sensor(
    sensor_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Delete a sensor

    Args:
        sensor_id: Sensor ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with deletion confirmation

    Raises:
        HTTPException 404: If sensor not found
    """
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    db.delete(sensor)
    db.commit()

    return ApiResponse(
        success=True,
        message="Sensor deleted successfully",
        data={"id": sensor_id}
    )
