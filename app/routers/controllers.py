"""
Controller API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Controller, Sensor, EnumDeviceType, EnumDeviceStatus
from app.schemas.device import ControllerCreate, ControllerResponse, ControllerUpdate, SensorResponse
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[ControllerResponse]])
async def get_controllers(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    group_device: Optional[int] = Query(None, description="장치 그룹으로 필터링"),
    status: Optional[str] = Query(None, description="상태로 필터링 (EnumDeviceStatus)"),
    include_sensors: bool = Query(False, description="센서 정보 포함 여부 (기본값: false)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    제어기 목록 조회 (페이지네이션)

    제어기 목록을 페이지네이션하여 조회합니다.
    그룹 및 상태로 필터링할 수 있습니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **group_device**: 장치 그룹으로 필터링 (선택)
    - **status**: 상태로 필터링 (선택)
    - **include_sensors**: 센서 정보 포함 여부 (기본값: false)

    **Response**: 제어기 목록 및 페이지네이션 정보
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
    controller_responses = []
    for c in controllers:
        controller_response = ControllerResponse(
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

        # Include sensors if requested
        if include_sensors:
            sensors = db.query(Sensor).filter(Sensor.controller_id == c.id).all()
            sensor_responses = [
                SensorResponse(
                    id=s.id,
                    number_device=s.number_device,
                    group_device=s.group_device,
                    name_device=s.name_device,
                    type_device=s.type_device.value,
                    version=s.version,
                    status=s.status.value,
                    controller_id=s.controller_id,
                    created_at=s.created_at,
                    updated_at=s.updated_at
                )
                for s in sensors
            ]
            controller_response.sensors = sensor_responses

        controller_responses.append(controller_response)

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
    include_sensors: bool = Query(False, description="센서 정보 포함 여부 (기본값: false)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    제어기 단건 조회

    ID로 제어기 정보를 조회합니다.

    - **controller_id**: 제어기 ID (Path Parameter)
    - **include_sensors**: 센서 정보 포함 여부 (기본값: false)

    **Response**: 제어기 상세 정보

    **Error**:
    - 404: 제어기를 찾을 수 없음
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

    # Include sensors if requested
    if include_sensors:
        sensors = db.query(Sensor).filter(Sensor.controller_id == controller.id).all()
        sensor_responses = [
            SensorResponse(
                id=s.id,
                number_device=s.number_device,
                group_device=s.group_device,
                name_device=s.name_device,
                type_device=s.type_device.value,
                version=s.version,
                status=s.status.value,
                controller_id=s.controller_id,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in sensors
        ]
        controller_response.sensors = sensor_responses

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
    제어기 생성

    새로운 제어기를 생성합니다.
    number_device는 유니크하므로 중복될 수 없습니다.

    **Request Body**:
    - **number_device**: 장치 번호 (필수, 유니크)
    - **group_device**: 장치 그룹 (필수)
    - **name_device**: 장치 이름 (필수)
    - **type_device**: 장치 타입 EnumDeviceType (필수)
    - **version**: 버전 (선택)
    - **status**: 상태 EnumDeviceStatus (필수)
    - **ip_address**: IP 주소 (필수)
    - **ip_port**: IP 포트 (필수)

    **Response**: 생성된 제어기 정보

    **Error**:
    - 409: 동일한 number_device가 이미 존재함
    - 422: 잘못된 Enum 값
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
    제어기 부분 수정 (PATCH)

    제어기의 일부 필드만 수정합니다.
    제공된 필드만 업데이트되며, 나머지는 유지됩니다.

    - **controller_id**: 제어기 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **number_device**: 장치 번호 (유니크)
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 타입 EnumDeviceType
    - **version**: 버전
    - **status**: 상태 EnumDeviceStatus
    - **ip_address**: IP 주소
    - **ip_port**: IP 포트

    **Response**: 수정된 제어기 정보

    **Error**:
    - 404: 제어기를 찾을 수 없음
    - 409: 변경하려는 number_device가 이미 존재함
    - 422: 잘못된 Enum 값
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
    제어기 전체 수정 (PUT)

    제어기의 모든 필드를 교체합니다.
    모든 필드가 필수입니다.

    - **controller_id**: 제어기 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **number_device**: 장치 번호 (유니크)
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 타입 EnumDeviceType
    - **version**: 버전
    - **status**: 상태 EnumDeviceStatus
    - **ip_address**: IP 주소
    - **ip_port**: IP 포트

    **Response**: 수정된 제어기 정보

    **Error**:
    - 404: 제어기를 찾을 수 없음
    - 409: 변경하려는 number_device가 이미 존재함
    - 422: 잘못된 Enum 값
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
    제어기 삭제

    제어기를 삭제합니다.

    - **controller_id**: 제어기 ID (Path Parameter)

    **Response**: 삭제된 제어기 ID

    **Error**:
    - 404: 제어기를 찾을 수 없음
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
