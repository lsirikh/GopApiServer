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
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    group_device: Optional[int] = Query(None, description="장치 그룹으로 필터링"),
    type_device: Optional[str] = Query(None, description="장치 유형으로 필터링"),
    status: Optional[str] = Query(None, description="상태로 필터링"),
    mode: Optional[str] = Query(None, description="카메라 모드로 필터링"),
    category: Optional[str] = Query(None, description="카메라 카테고리로 필터링"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 목록 조회 (페이지네이션)

    카메라 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **group_device**: 장치 그룹으로 필터링
    - **type_device**: 장치 유형으로 필터링
    - **status**: 상태로 필터링
    - **mode**: 카메라 모드로 필터링
    - **category**: 카메라 카테고리로 필터링

    **Response**: 카메라 목록 및 페이지네이션 정보
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
    카메라 단건 조회

    특정 카메라의 상세 정보를 조회합니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)

    **Response**: 카메라 상세 정보

    **Error**:
    - 404: 카메라를 찾을 수 없음
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
    카메라 생성

    새로운 카메라를 생성합니다.

    **Request Body**:
    - **number_device**: 장치 번호 (필수, 고유값)
    - **group_device**: 장치 그룹 (필수)
    - **name_device**: 장치 이름 (필수)
    - **type_device**: 장치 유형 (필수)
    - **version**: 버전 (필수)
    - **status**: 상태 (필수)
    - **ip_address**: IP 주소 (필수)
    - **ip_port**: IP 포트 (필수)
    - **user_name**: 사용자 이름 (필수)
    - **user_password**: 사용자 비밀번호 (필수)
    - **rtsp_uri**: RTSP URI (필수)
    - **rtsp_port**: RTSP 포트 (필수)
    - **mode**: 카메라 모드 (필수)
    - **category**: 카메라 카테고리 (필수)

    **Response**: 생성된 카메라 정보

    **Error**:
    - 409: 동일한 number_device를 가진 카메라가 이미 존재함
    - 422: 유효하지 않은 enum 값
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
    카메라 부분 수정 (PATCH)

    카메라의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **number_device**: 장치 번호
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 유형
    - **version**: 버전
    - **status**: 상태
    - **ip_address**: IP 주소
    - **ip_port**: IP 포트
    - **user_name**: 사용자 이름
    - **user_password**: 사용자 비밀번호
    - **rtsp_uri**: RTSP URI
    - **rtsp_port**: RTSP 포트
    - **mode**: 카메라 모드
    - **category**: 카메라 카테고리

    **Response**: 수정된 카메라 정보

    **Error**:
    - 404: 카메라를 찾을 수 없음
    - 409: 동일한 number_device를 가진 다른 카메라가 존재함
    - 422: 유효하지 않은 enum 값
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
    카메라 전체 수정 (PUT)

    카메라의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **number_device**: 장치 번호
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 유형
    - **version**: 버전
    - **status**: 상태
    - **ip_address**: IP 주소
    - **ip_port**: IP 포트
    - **user_name**: 사용자 이름
    - **user_password**: 사용자 비밀번호
    - **rtsp_uri**: RTSP URI
    - **rtsp_port**: RTSP 포트
    - **mode**: 카메라 모드
    - **category**: 카메라 카테고리

    **Response**: 수정된 카메라 정보

    **Error**:
    - 404: 카메라를 찾을 수 없음
    - 409: 동일한 number_device를 가진 다른 카메라가 존재함
    - 422: 유효하지 않은 enum 값
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
    카메라 삭제

    특정 카메라를 삭제합니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 카메라를 찾을 수 없음
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
