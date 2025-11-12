"""
Camera API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType
from app.schemas.device import CameraCreate, CameraResponse, CameraUpdate
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[CameraResponse]])
async def get_cameras(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    group_device: Optional[int] = Query(None, description="Filter by group_device"),
    type_device: Optional[str] = Query(None, description="Filter by type_device"),
    status: Optional[str] = Query(None, description="Filter by status"),
    mode: Optional[str] = Query(None, description="Filter by camera mode"),
    category: Optional[str] = Query(None, description="Filter by camera category"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of cameras with pagination and filters

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        group_device: Filter by group_device
        type_device: Filter by type_device
        status: Filter by status
        mode: Filter by camera mode
        category: Filter by camera category
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with list of cameras and pagination metadata
    """
    # Build query
    query = db.query(Camera)

    # Apply filters
    if group_device is not None:
        query = query.filter(Camera.group_device == group_device)
    if type_device is not None:
        query = query.filter(Camera.type_device == type_device)
    if status is not None:
        query = query.filter(Camera.status == status)
    if mode is not None:
        query = query.filter(Camera.mode == mode)
    if category is not None:
        query = query.filter(Camera.category == category)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    cameras = query.offset(skip).limit(limit).all()

    # Convert to response format
    camera_responses = [
        CameraResponse(
            id=c.id,
            number_device=c.number_device,
            group_device=c.group_device,
            name_device=c.name_device,
            type_device=c.type_device.value,
            version=c.version,
            status=c.status.value,
            ip_address=c.ip_address,
            ip_port=c.ip_port,
            user_name=c.user_name,
            user_password=c.user_password,
            rtsp_uri=c.rtsp_uri,
            rtsp_port=c.rtsp_port,
            mode=c.mode.value,
            category=c.category.value,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in cameras
    ]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Cameras retrieved successfully",
        data=camera_responses,
        pagination=pagination
    )


@router.get("/{camera_id}", response_model=ApiResponse[CameraResponse])
async def get_camera(
    camera_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get a single camera by ID

    Args:
        camera_id: Camera ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with camera data

    Raises:
        HTTPException 404: If camera not found
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    camera_response = CameraResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device.value,
        version=camera.version,
        status=camera.status.value,
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        user_name=camera.user_name,
        user_password=camera.user_password,
        rtsp_uri=camera.rtsp_uri,
        rtsp_port=camera.rtsp_port,
        mode=camera.mode.value,
        category=camera.category.value,
        created_at=camera.created_at,
        updated_at=camera.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera retrieved successfully",
        data=camera_response
    )


@router.post("", response_model=ApiResponse[CameraResponse], status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Create a new camera

    Args:
        camera_data: Camera creation data
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with created camera data

    Raises:
        HTTPException 409: If camera with same number_device already exists
        HTTPException 422: If invalid enum value provided
    """
    # Check for duplicate number_device
    existing = db.query(Camera).filter(
        Camera.number_device == camera_data.number_device
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Camera with number_device {camera_data.number_device} already exists"
        )

    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(camera_data.type_device)
        device_status = EnumDeviceStatus(camera_data.status)
        camera_mode = EnumCameraMode(camera_data.mode)
        camera_category = EnumCameraType(camera_data.category)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Create new camera
    new_camera = Camera(
        number_device=camera_data.number_device,
        group_device=camera_data.group_device,
        name_device=camera_data.name_device,
        type_device=device_type,
        version=camera_data.version,
        status=device_status,
        ip_address=camera_data.ip_address,
        ip_port=camera_data.ip_port,
        user_name=camera_data.user_name,
        user_password=camera_data.user_password,
        rtsp_uri=camera_data.rtsp_uri,
        rtsp_port=camera_data.rtsp_port,
        mode=camera_mode,
        category=camera_category
    )

    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)

    camera_response = CameraResponse(
        id=new_camera.id,
        number_device=new_camera.number_device,
        group_device=new_camera.group_device,
        name_device=new_camera.name_device,
        type_device=new_camera.type_device.value,
        version=new_camera.version,
        status=new_camera.status.value,
        ip_address=new_camera.ip_address,
        ip_port=new_camera.ip_port,
        user_name=new_camera.user_name,
        user_password=new_camera.user_password,
        rtsp_uri=new_camera.rtsp_uri,
        rtsp_port=new_camera.rtsp_port,
        mode=new_camera.mode.value,
        category=new_camera.category.value,
        created_at=new_camera.created_at,
        updated_at=new_camera.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera created successfully",
        data=camera_response
    )


@router.patch("/{camera_id}", response_model=ApiResponse[CameraResponse])
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Update a camera (partial update)

    Args:
        camera_id: Camera ID
        camera_data: Camera update data (all fields optional)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated camera data

    Raises:
        HTTPException 404: If camera not found
        HTTPException 409: If number_device conflicts with existing camera
        HTTPException 422: If invalid enum value provided
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Check for number_device conflict
    if camera_data.number_device is not None:
        existing = db.query(Camera).filter(
            Camera.number_device == camera_data.number_device,
            Camera.id != camera_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Camera with number_device {camera_data.number_device} already exists"
            )

    # Update fields if provided
    update_data = camera_data.model_dump(exclude_unset=True)

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
        elif field == "mode" and value is not None:
            try:
                value = EnumCameraMode(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid mode value: {value}"
                )
        elif field == "category" and value is not None:
            try:
                value = EnumCameraType(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid category value: {value}"
                )

        setattr(camera, field, value)

    db.commit()
    db.refresh(camera)

    camera_response = CameraResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device.value,
        version=camera.version,
        status=camera.status.value,
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        user_name=camera.user_name,
        user_password=camera.user_password,
        rtsp_uri=camera.rtsp_uri,
        rtsp_port=camera.rtsp_port,
        mode=camera.mode.value,
        category=camera.category.value,
        created_at=camera.created_at,
        updated_at=camera.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera updated successfully",
        data=camera_response
    )


@router.put("/{camera_id}", response_model=ApiResponse[CameraResponse])
async def replace_camera(
    camera_id: int,
    camera_data: CameraCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Replace a camera (full update - all fields required)

    Args:
        camera_id: Camera ID
        camera_data: Complete camera data (all fields required)
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with updated camera data

    Raises:
        HTTPException 404: If camera not found
        HTTPException 409: If number_device conflicts with existing camera
        HTTPException 422: If invalid enum value provided
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Check for number_device conflict
    if camera_data.number_device != camera.number_device:
        existing = db.query(Camera).filter(
            Camera.number_device == camera_data.number_device,
            Camera.id != camera_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Camera with number_device {camera_data.number_device} already exists"
            )

    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(camera_data.type_device)
        device_status = EnumDeviceStatus(camera_data.status)
        camera_mode = EnumCameraMode(camera_data.mode)
        camera_category = EnumCameraType(camera_data.category)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Replace all fields (PUT = full replacement)
    camera.number_device = camera_data.number_device
    camera.group_device = camera_data.group_device
    camera.name_device = camera_data.name_device
    camera.type_device = device_type
    camera.version = camera_data.version
    camera.status = device_status
    camera.ip_address = camera_data.ip_address
    camera.ip_port = camera_data.ip_port
    camera.user_name = camera_data.user_name
    camera.user_password = camera_data.user_password
    camera.rtsp_uri = camera_data.rtsp_uri
    camera.rtsp_port = camera_data.rtsp_port
    camera.mode = camera_mode
    camera.category = camera_category

    db.commit()
    db.refresh(camera)

    camera_response = CameraResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device.value,
        version=camera.version,
        status=camera.status.value,
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        user_name=camera.user_name,
        user_password=camera.user_password,
        rtsp_uri=camera.rtsp_uri,
        rtsp_port=camera.rtsp_port,
        mode=camera.mode.value,
        category=camera.category.value,
        created_at=camera.created_at,
        updated_at=camera.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera replaced successfully",
        data=camera_response
    )


@router.delete("/{camera_id}", response_model=ApiResponse[dict])
async def delete_camera(
    camera_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Delete a camera

    Args:
        camera_id: Camera ID
        current_user: Current authenticated user (optional based on AUTH_MODE)
        db: Database session

    Returns:
        ApiResponse with deletion confirmation

    Raises:
        HTTPException 404: If camera not found
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    db.delete(camera)
    db.commit()

    return ApiResponse(
        success=True,
        message="Camera deleted successfully",
        data={"id": camera_id}
    )
