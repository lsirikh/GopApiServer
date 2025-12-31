"""
Sensor API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Sensor, Controller, EnumDeviceType, EnumDeviceStatus
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceCategory
from app.schemas.device import SensorCreate, SensorResponse, SensorUpdate
from app.schemas.device_group import DeviceGroupResponse
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=["Sensors"])


def _get_device_groups(db: Session, device_id: int, category_device: EnumDeviceCategory = EnumDeviceCategory.SENSOR) -> List[DeviceGroupResponse]:
    """Get device groups for a sensor"""
    mappings = db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == category_device
    ).all()

    if not mappings:
        return []

    group_ids = [m.group_id for m in mappings]
    groups = db.query(DeviceGroup).filter(DeviceGroup.id.in_(group_ids)).all()

    return [
        DeviceGroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            device_count=db.query(DeviceGroupMapping).filter(
                DeviceGroupMapping.group_id == g.id
            ).count(),
            created_at=g.created_at,
            updated_at=g.updated_at
        )
        for g in groups
    ]


def _update_device_group_mappings(
    db: Session,
    device_id: int,
    group_ids: List[int],
    category_device: EnumDeviceCategory = EnumDeviceCategory.SENSOR
):
    """Update device group mappings for a sensor"""
    # Remove existing mappings
    db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == category_device
    ).delete()

    # Create new mappings
    for group_id in group_ids:
        # Verify group exists
        group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
        if group:
            mapping = DeviceGroupMapping(
                device_id=device_id,
                category_device=category_device,
                group_id=group_id
            )
            db.add(mapping)


def _sensor_to_response(sensor: Sensor, db: Session, include_controller: bool = False) -> SensorResponse:
    """Convert Sensor model to SensorResponse schema with device_groups"""
    device_groups = _get_device_groups(db, sensor.id, "sensor")

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
        "updated_at": sensor.updated_at,
        "device_groups": device_groups
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

    return SensorResponse(**sensor_data)


@router.get("", response_model=ApiResponse[list[SensorResponse]])
async def get_sensors(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    group_device: Optional[int] = Query(None, description="장치 그룹으로 필터링 (레거시 1:1)"),
    group_id: Optional[int] = Query(None, description="DeviceGroup ID로 필터링 (N:N 관계)"),
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
    - **group_device**: 장치 그룹으로 필터링 - 레거시 1:1 관계
    - **group_id**: DeviceGroup ID로 필터링 - N:N 관계
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
    if group_id is not None:
        # N:N filtering via DeviceGroupMapping junction table
        subquery = db.query(DeviceGroupMapping.device_id).filter(
            DeviceGroupMapping.group_id == group_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.SENSOR
        ).subquery()
        query = query.filter(Sensor.id.in_(subquery))
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

    # Convert to response format using helper function
    sensor_responses = [
        _sensor_to_response(s, db, include_controller)
        for s in sensors
    ]

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

    sensor_response = _sensor_to_response(sensor, db, include_controller)

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

    # Handle group_ids if provided (N:N relationship)
    if sensor_data.group_ids is not None:
        _update_device_group_mappings(db, new_sensor.id, sensor_data.group_ids, "sensor")
        db.commit()

    sensor_response = _sensor_to_response(new_sensor, db)

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

    # Handle group_ids separately (N:N relationship)
    group_ids = update_data.pop("group_ids", None)

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

    # Update group mappings if group_ids was provided
    if group_ids is not None:
        _update_device_group_mappings(db, sensor.id, group_ids, "sensor")

    db.commit()
    db.refresh(sensor)

    sensor_response = _sensor_to_response(sensor, db)

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

    # Handle group_ids if provided (N:N relationship)
    if sensor_data.group_ids is not None:
        _update_device_group_mappings(db, sensor.id, sensor_data.group_ids, "sensor")

    db.commit()
    db.refresh(sensor)

    sensor_response = _sensor_to_response(sensor, db)

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

    # Delete associated device group mappings first (no FK cascade for polymorphic relation)
    db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == sensor_id,
        DeviceGroupMapping.category_device == EnumDeviceCategory.SENSOR
    ).delete()

    db.delete(sensor)
    db.commit()

    return ApiResponse(
        success=True,
        message="Sensor deleted successfully",
        data={"id": sensor_id}
    )
