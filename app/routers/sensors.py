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
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    group_device: Optional[int] = Query(None, description="장치 그룹으로 필터링"),
    controller_id: Optional[int] = Query(None, description="컨트롤러 ID로 필터링"),
    type_device: Optional[str] = Query(None, description="장치 유형으로 필터링"),
    status: Optional[str] = Query(None, description="상태로 필터링"),
    include_controller: bool = Query(False, description="컨트롤러 정보 포함 여부"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    센서 목록 조회 (페이지네이션)

    센서 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **group_device**: 장치 그룹으로 필터링
    - **controller_id**: 컨트롤러 ID로 필터링
    - **type_device**: 장치 유형으로 필터링
    - **status**: 상태로 필터링
    - **include_controller**: 컨트롤러 정보 포함 여부

    **Response**: 센서 목록 및 페이지네이션 정보
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
    include_controller: bool = Query(False, description="컨트롤러 정보 포함 여부"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    센서 단건 조회

    특정 센서의 상세 정보를 조회합니다.

    **파라미터**:
    - **sensor_id**: 센서 ID (Path Parameter)
    - **include_controller**: 컨트롤러 정보 포함 여부

    **Response**: 센서 상세 정보

    **Error**:
    - 404: 센서를 찾을 수 없음
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
    센서 생성

    새로운 센서를 생성합니다.

    **Request Body**:
    - **number_device**: 장치 번호 (필수, 고유값)
    - **group_device**: 장치 그룹 (필수)
    - **name_device**: 장치 이름 (필수)
    - **type_device**: 장치 유형 (필수)
    - **version**: 버전 (필수)
    - **status**: 상태 (필수)
    - **controller_id**: 연결된 컨트롤러 ID (필수)

    **Response**: 생성된 센서 정보

    **Error**:
    - 404: 컨트롤러를 찾을 수 없음
    - 409: 동일한 number_device를 가진 센서가 이미 존재함
    - 422: 유효하지 않은 enum 값
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
    센서 부분 수정 (PATCH)

    센서의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **sensor_id**: 센서 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **number_device**: 장치 번호
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 유형
    - **version**: 버전
    - **status**: 상태
    - **controller_id**: 연결된 컨트롤러 ID

    **Response**: 수정된 센서 정보

    **Error**:
    - 404: 센서 또는 컨트롤러를 찾을 수 없음
    - 409: 동일한 number_device를 가진 다른 센서가 존재함
    - 422: 유효하지 않은 enum 값
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
    센서 전체 수정 (PUT)

    센서의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **sensor_id**: 센서 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **number_device**: 장치 번호
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 유형
    - **version**: 버전
    - **status**: 상태
    - **controller_id**: 연결된 컨트롤러 ID

    **Response**: 수정된 센서 정보

    **Error**:
    - 404: 센서 또는 컨트롤러를 찾을 수 없음
    - 409: 동일한 number_device를 가진 다른 센서가 존재함
    - 422: 유효하지 않은 enum 값
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
    센서 삭제

    특정 센서를 삭제합니다.

    **파라미터**:
    - **sensor_id**: 센서 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 센서를 찾을 수 없음
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
