"""
Controller API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Controller, Sensor, EnumDeviceType, EnumDeviceStatus
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceCategory
from app.schemas.device import ControllerCreate, ControllerResponse, ControllerUpdate, SensorNestedResponse, DeviceGroupNestedResponse, Geolocation
from app.schemas.device_group import DeviceGroupResponse
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=["Controllers"])


def _get_device_groups(db: Session, device_id: int, category_device: EnumDeviceCategory = EnumDeviceCategory.CONTROLLER) -> List[DeviceGroupResponse]:
    """Get device groups for a controller (주체용 - timestamp 포함)"""
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


def _get_device_groups_nested(db: Session, device_id: int, category_device: EnumDeviceCategory) -> List[DeviceGroupNestedResponse]:
    """Get device groups for nested response (v2.4: timestamp 제외)"""
    mappings = db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == category_device
    ).all()

    if not mappings:
        return []

    group_ids = [m.group_id for m in mappings]
    groups = db.query(DeviceGroup).filter(DeviceGroup.id.in_(group_ids)).all()

    return [
        DeviceGroupNestedResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            device_count=db.query(DeviceGroupMapping).filter(
                DeviceGroupMapping.group_id == g.id
            ).count()
        )
        for g in groups
    ]


def _update_device_group_mappings(
    db: Session,
    device_id: int,
    group_ids: List[int],
    category_device: EnumDeviceCategory = EnumDeviceCategory.CONTROLLER
):
    """Update device group mappings for a controller"""
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


def _controller_to_response(controller: Controller, db: Session, include_sensors: bool = False) -> ControllerResponse:
    """Convert Controller model to ControllerResponse schema with device_groups"""
    # v2.4: Nested Response 규칙 적용 - device_groups에서 timestamp 제외
    device_groups = _get_device_groups_nested(db, controller.id, EnumDeviceCategory.CONTROLLER)

    # PRD_Controller_Sensor_Geolocation.md: Convert geolocation dict to Geolocation schema
    geolocation = None
    if controller.geolocation:
        geolocation = Geolocation(**controller.geolocation)

    response = ControllerResponse(
        id=controller.id,
        number_device=controller.number_device,
        group_device=controller.group_device,
        name_device=controller.name_device,
        type_device=controller.type_device.value,
        version=controller.version,
        status=controller.status.value,
        is_enable=controller.is_enable,
        ip_address=controller.ip_address,
        ip_port=controller.ip_port,
        geolocation=geolocation,
        created_at=controller.created_at,
        updated_at=controller.updated_at,
        device_groups=device_groups
    )

    if include_sensors:
        sensors = db.query(Sensor).filter(Sensor.controller_id == controller.id).all()
        # v2.4: SensorNestedResponse 사용 (timestamp 제외, device_groups 포함)
        sensor_responses = [
            SensorNestedResponse(
                id=s.id,
                number_device=s.number_device,
                group_device=s.group_device,
                name_device=s.name_device,
                type_device=s.type_device.value,
                version=s.version,
                status=s.status.value,
                is_enable=s.is_enable,
                controller_id=s.controller_id,
                geolocation=Geolocation(**s.geolocation) if s.geolocation else None,
                device_groups=_get_device_groups_nested(db, s.id, EnumDeviceCategory.SENSOR)
            )
            for s in sensors
        ]
        response.sensors = sensor_responses

    return response


@router.get("", response_model=ApiResponse[list[ControllerResponse]])
async def get_controllers(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    group_device: Optional[int] = Query(None, description="장치 그룹으로 필터링 (레거시 1:1)"),
    group_id: Optional[int] = Query(None, description="DeviceGroup ID로 필터링 (N:N 관계)"),
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
    - **group_device**: 장치 그룹으로 필터링 - 레거시 1:1 관계 (선택)
    - **group_id**: DeviceGroup ID로 필터링 - N:N 관계 (선택)
    - **status**: 상태로 필터링 (선택)
    - **include_sensors**: 센서 정보 포함 여부 (기본값: false)

    **Response**: 제어기 목록 및 페이지네이션 정보
    """
    # Build query
    query = db.query(Controller)

    # Apply filters
    if group_device is not None:
        query = query.filter(Controller.group_device == group_device)
    if group_id is not None:
        # N:N filtering via DeviceGroupMapping junction table
        subquery = db.query(DeviceGroupMapping.device_id).filter(
            DeviceGroupMapping.group_id == group_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER
        ).subquery()
        query = query.filter(Controller.id.in_(subquery))
    if status is not None:
        query = query.filter(Controller.status == status)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    controllers = query.offset(skip).limit(limit).all()

    # Convert to response format using helper function
    controller_responses = [
        _controller_to_response(c, db, include_sensors)
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

    controller_response = _controller_to_response(controller, db, include_sensors)

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

    **Request Body**:
    - **number_device**: 장치 번호 (필수)
    - **group_device**: 장치 그룹 (필수)
    - **name_device**: 장치 이름 (필수)
    - **type_device**: 장치 타입 EnumDeviceType (필수)
    - **version**: 버전 (선택)
    - **status**: 상태 EnumDeviceStatus (필수)
    - **ip_address**: IP 주소 (필수)
    - **ip_port**: IP 포트 (필수)

    **Response**: 생성된 제어기 정보

    **Error**:
    - 422: 잘못된 Enum 값
    """
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
        is_enable=controller_data.is_enable,
        ip_address=controller_data.ip_address,
        ip_port=controller_data.ip_port,
        geolocation=controller_data.geolocation.model_dump() if controller_data.geolocation else None
    )

    db.add(new_controller)
    db.commit()
    db.refresh(new_controller)

    # Handle group_ids if provided (N:N relationship)
    if controller_data.group_ids is not None:
        _update_device_group_mappings(db, new_controller.id, controller_data.group_ids, "controller")
        db.commit()

    controller_response = _controller_to_response(new_controller, db)

    return ApiResponse(
        success=True,
        message="Controller created successfully",
        data=controller_response
    )


@router.patch("/{controller_id}", response_model=ApiResponse[ControllerResponse])
async def update_controller(
    controller_id: int,
    controller_data: ControllerUpdate,
    include_sensors: bool = Query(default=False, description="센서 목록 포함 여부"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    제어기 부분 수정 (PATCH)

    제어기의 일부 필드만 수정합니다.
    제공된 필드만 업데이트되며, 나머지는 유지됩니다.

    - **controller_id**: 제어기 ID (Path Parameter)
    - **include_sensors**: 센서 목록 포함 여부

    **Request Body** (모든 필드 선택):
    - **number_device**: 장치 번호
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
    - 422: 잘못된 Enum 값
    """
    controller = db.query(Controller).filter(Controller.id == controller_id).first()

    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {controller_id} not found"
        )

    # Update fields if provided
    update_data = controller_data.model_dump(exclude_unset=True)

    # Handle group_ids separately (N:N relationship)
    group_ids = update_data.pop("group_ids", None)

    # Handle geolocation separately (Pydantic model -> dict)
    geolocation_data = update_data.pop("geolocation", None)

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

    # Update geolocation if provided
    if geolocation_data is not None:
        controller.geolocation = geolocation_data

    # Update group mappings if group_ids was provided
    if group_ids is not None:
        _update_device_group_mappings(db, controller.id, group_ids, "controller")

    db.commit()
    db.refresh(controller)

    controller_response = _controller_to_response(controller, db, include_sensors)

    return ApiResponse(
        success=True,
        message="Controller updated successfully",
        data=controller_response
    )


@router.put("/{controller_id}", response_model=ApiResponse[ControllerResponse])
async def replace_controller(
    controller_id: int,
    controller_data: ControllerCreate,
    include_sensors: bool = Query(default=False, description="센서 목록 포함 여부"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    제어기 전체 수정 (PUT)

    제어기의 모든 필드를 교체합니다.
    모든 필드가 필수입니다.

    - **controller_id**: 제어기 ID (Path Parameter)
    - **include_sensors**: 센서 목록 포함 여부

    **Request Body** (모든 필드 필수):
    - **number_device**: 장치 번호
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
    - 422: 잘못된 Enum 값
    """
    controller = db.query(Controller).filter(Controller.id == controller_id).first()

    if not controller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Controller with id {controller_id} not found"
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
    controller.is_enable = controller_data.is_enable
    controller.ip_address = controller_data.ip_address
    controller.ip_port = controller_data.ip_port
    controller.geolocation = controller_data.geolocation.model_dump() if controller_data.geolocation else None

    # Handle group_ids if provided (N:N relationship)
    if controller_data.group_ids is not None:
        _update_device_group_mappings(db, controller.id, controller_data.group_ids, "controller")

    db.commit()
    db.refresh(controller)

    controller_response = _controller_to_response(controller, db, include_sensors)

    return ApiResponse(
        success=True,
        message="Controller replaced successfully",
        data=controller_response
    )


@router.delete("/{controller_id}", response_model=ApiResponse[None])
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

    # Delete associated device group mappings first (no FK cascade for polymorphic relation)
    db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == controller_id,
        DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER
    ).delete()

    db.delete(controller)
    db.commit()

    return ApiResponse(
        success=True,
        message="Controller deleted successfully",
        data=None
    )
