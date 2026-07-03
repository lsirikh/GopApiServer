"""
Sensor API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
import math

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async, require_perm_optional_async
from app.models.device import Sensor, Controller, EnumDeviceType, EnumDeviceStatus
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceCategory, EnumConfigResourceType, EnumConfigActionType
from app.schemas.device import SensorCreate, SensorResponse, SensorUpdate, DeviceGroupNestedResponse, Geolocation
from app.schemas.device_group import DeviceGroupResponse
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.services.config_log_service import log_config_change_async, get_identifier, get_changed_fields, model_to_dict

router = APIRouter(tags=["Sensors"])


async def _get_device_groups_nested(db: AsyncSession, device_id: int, category_device: EnumDeviceCategory = EnumDeviceCategory.SENSOR) -> List[DeviceGroupNestedResponse]:
    """Get device groups for a sensor (v2.4: timestamp 제외)"""
    mappings = (await db.execute(
        select(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == category_device
        )
    )).scalars().all()

    if not mappings:
        return []

    group_ids = [m.group_id for m in mappings]
    groups = (await db.execute(
        select(DeviceGroup).where(DeviceGroup.id.in_(group_ids))
    )).scalars().all()

    result: List[DeviceGroupNestedResponse] = []
    for g in groups:
        device_count = (await db.execute(
            select(func.count()).select_from(DeviceGroupMapping).where(
                DeviceGroupMapping.group_id == g.id
            )
        )).scalar()
        result.append(
            DeviceGroupNestedResponse(
                id=g.id,
                name=g.name,
                description=g.description,
                device_count=device_count
            )
        )
    return result


async def _update_device_group_mappings(
    db: AsyncSession,
    device_id: int,
    group_ids: List[int],
    category_device: EnumDeviceCategory = EnumDeviceCategory.SENSOR
):
    """Update device group mappings for a sensor"""
    # Remove existing mappings
    await db.execute(
        delete(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == category_device
        )
    )

    # Create new mappings
    for group_id in group_ids:
        # Verify group exists
        group = (await db.execute(
            select(DeviceGroup).where(DeviceGroup.id == group_id)
        )).scalars().first()
        if group:
            mapping = DeviceGroupMapping(
                device_id=device_id,
                category_device=category_device,
                group_id=group_id
            )
            db.add(mapping)


async def _sensor_to_response(sensor: Sensor, db: AsyncSession, include_controller: bool = False) -> SensorResponse:
    """Convert Sensor model to SensorResponse schema with device_groups"""
    # v2.4: Nested Response 규칙 적용 - device_groups에서 timestamp 제외
    device_groups = await _get_device_groups_nested(db, sensor.id, EnumDeviceCategory.SENSOR)

    # PRD_Controller_Sensor_Geolocation.md: Convert geolocation dict to Geolocation schema
    geolocation = None
    if sensor.geolocation:
        geolocation = Geolocation(**sensor.geolocation)

    sensor_data = {
        "id": sensor.id,
        "number_device": sensor.number_device,
        "group_device": sensor.group_device,
        "name_device": sensor.name_device,
        "type_device": sensor.type_device.value,
        "version": sensor.version,
        "status": sensor.status.value,
        "is_enable": sensor.is_enable,
        "controller_id": sensor.controller_id,
        "geolocation": geolocation,
        "created_at": sensor.created_at,
        "updated_at": sensor.updated_at,
        "device_groups": device_groups
    }

    # Include controller info if requested
    # v2.5: Nested Response 규칙 적용 - ControllerNestedResponse 사용 (timestamp 제외, device_groups 포함)
    if include_controller and sensor.controller:
        from app.schemas.device import ControllerNestedResponse
        # Controller의 device_groups 조회 (Nested 규칙: timestamp 제외)
        controller_device_groups = await _get_device_groups_nested(db, sensor.controller.id, EnumDeviceCategory.CONTROLLER)
        # Controller geolocation 변환
        controller_geolocation = None
        if sensor.controller.geolocation:
            controller_geolocation = Geolocation(**sensor.controller.geolocation)
        sensor_data["controller"] = ControllerNestedResponse(
            id=sensor.controller.id,
            number_device=sensor.controller.number_device,
            group_device=sensor.controller.group_device,
            name_device=sensor.controller.name_device,
            type_device=sensor.controller.type_device.value,
            version=sensor.controller.version,
            status=sensor.controller.status.value,
            is_enable=sensor.controller.is_enable,
            ip_address=sensor.controller.ip_address,
            ip_port=sensor.controller.ip_port,
            geolocation=controller_geolocation,
            device_groups=controller_device_groups
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
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
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
    stmt = select(Sensor)
    count_stmt = select(func.count()).select_from(Sensor)

    # v6.0 P7: async lazy load 함정 회피 — include_controller 시 controller 관계 미리 로드
    if include_controller:
        stmt = stmt.options(selectinload(Sensor.controller))

    # Apply filters
    if group_device is not None:
        stmt = stmt.where(Sensor.group_device == group_device)
        count_stmt = count_stmt.where(Sensor.group_device == group_device)
    if group_id is not None:
        # N:N filtering via DeviceGroupMapping junction table
        subquery = select(DeviceGroupMapping.device_id).where(
            DeviceGroupMapping.group_id == group_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.SENSOR
        )
        stmt = stmt.where(Sensor.id.in_(subquery))
        count_stmt = count_stmt.where(Sensor.id.in_(subquery))
    if controller_id is not None:
        stmt = stmt.where(Sensor.controller_id == controller_id)
        count_stmt = count_stmt.where(Sensor.controller_id == controller_id)
    if type_device is not None:
        stmt = stmt.where(Sensor.type_device == type_device)
        count_stmt = count_stmt.where(Sensor.type_device == type_device)
    if status is not None:
        stmt = stmt.where(Sensor.status == status)
        count_stmt = count_stmt.where(Sensor.status == status)

    # Get total count
    total = (await db.execute(count_stmt)).scalar()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by id for stable pagination)
    sensors = (await db.execute(
        stmt.order_by(Sensor.id).offset(skip).limit(limit)
    )).scalars().all()

    # Convert to response format using helper function
    sensor_responses = [
        await _sensor_to_response(s, db, include_controller)
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


@router.get("/{sensor_id}", response_model=ApiSingleResponse[SensorResponse])
async def get_sensor(
    sensor_id: int,
    include_controller: bool = Query(False, description="컨트롤러 정보 포함 여부"),
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
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
    stmt = select(Sensor).where(Sensor.id == sensor_id)
    # v6.0 P7: async lazy load 함정 회피 — include_controller 시 controller 관계 미리 로드
    if include_controller:
        stmt = stmt.options(selectinload(Sensor.controller))
    sensor = (await db.execute(stmt)).scalars().first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    sensor_response = await _sensor_to_response(sensor, db, include_controller)

    return ApiSingleResponse(
        success=True,
        message="Sensor retrieved successfully",
        data=sensor_response
    )


@router.post("", response_model=ApiSingleResponse[SensorResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm_optional_async("devices", "edit"))])
async def create_sensor(
    sensor_data: SensorCreate,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    센서 생성

    새로운 센서를 생성합니다.

    **Request Body**:
    - **number_device**: 장치 번호 (필수)
    - **group_device**: 장치 그룹 (필수)
    - **name_device**: 장치 이름 (필수)
    - **type_device**: 장치 유형 (필수)
    - **version**: 버전 (필수)
    - **status**: 상태 (필수)
    - **controller_id**: 연결된 컨트롤러 ID (필수)

    **Response**: 생성된 센서 정보

    **Error**:
    - 404: 컨트롤러를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    # Validate controller exists
    controller = (await db.execute(
        select(Controller).where(Controller.id == sensor_data.controller_id)
    )).scalars().first()
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

    # Create new sensor
    new_sensor = Sensor(
        number_device=sensor_data.number_device,
        group_device=sensor_data.group_device,
        name_device=sensor_data.name_device,
        type_device=device_type,
        version=sensor_data.version,
        status=device_status,
        is_enable=sensor_data.is_enable,
        controller_id=sensor_data.controller_id,
        geolocation=sensor_data.geolocation.model_dump() if sensor_data.geolocation else None
    )

    db.add(new_sensor)
    await db.commit()
    await db.refresh(new_sensor)

    # Handle group_ids if provided (N:N relationship)
    if sensor_data.group_ids is not None:
        await _update_device_group_mappings(db, new_sensor.id, sensor_data.group_ids, "sensor")
        await db.commit()

    # ConfigChangeLog: CREATED 로깅 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SENSOR,
        resource_id=new_sensor.id,
        resource_name=f"Sensor-{new_sensor.id} ({new_sensor.name_device})",
        action=EnumConfigActionType.CREATED,
        after_state=get_identifier(new_sensor),
        description="Sensor 생성"
    )

    sensor_response = await _sensor_to_response(new_sensor, db)

    return ApiSingleResponse(
        success=True,
        message="Sensor created successfully",
        data=sensor_response
    )


@router.patch("/{sensor_id}", response_model=ApiSingleResponse[SensorResponse], dependencies=[Depends(require_perm_optional_async("devices", "edit"))])
async def update_sensor(
    sensor_id: int,
    sensor_data: SensorUpdate,
    include_controller: bool = Query(default=False, description="컨트롤러 정보 포함 여부"),
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    센서 부분 수정 (PATCH)

    센서의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **sensor_id**: 센서 ID (Path Parameter)
    - **include_controller**: 컨트롤러 정보 포함 여부

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
    - 422: 유효하지 않은 enum 값
    """
    stmt = select(Sensor).where(Sensor.id == sensor_id)
    # v6.0 P7: async lazy load 함정 회피 — include_controller 시 controller 관계 미리 로드
    if include_controller:
        stmt = stmt.options(selectinload(Sensor.controller))
    sensor = (await db.execute(stmt)).scalars().first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    # ConfigChangeLog: 변경 전 상태 캡처
    before_state = model_to_dict(sensor)

    # Validate controller exists if updating controller_id
    if sensor_data.controller_id is not None:
        controller = (await db.execute(
            select(Controller).where(Controller.id == sensor_data.controller_id)
        )).scalars().first()
        if not controller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Controller with id {sensor_data.controller_id} not found"
            )

    # Update fields if provided
    update_data = sensor_data.model_dump(exclude_unset=True)

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

        setattr(sensor, field, value)

    # Update geolocation if provided
    if geolocation_data is not None:
        sensor.geolocation = geolocation_data

    # Update group mappings if group_ids was provided
    if group_ids is not None:
        await _update_device_group_mappings(db, sensor.id, group_ids, "sensor")

    await db.commit()
    await db.refresh(sensor)

    # ConfigChangeLog: UPDATED 로깅 (PRD v1.2 - 변경된 필드만 저장)
    after_state = model_to_dict(sensor)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        await log_config_change_async(
            db=db,
            resource_type=EnumConfigResourceType.SENSOR,
            resource_id=sensor.id,
            resource_name=f"Sensor-{sensor.id} ({sensor.name_device})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="Sensor 수정"
        )

    sensor_response = await _sensor_to_response(sensor, db, include_controller)

    return ApiSingleResponse(
        success=True,
        message="Sensor updated successfully",
        data=sensor_response
    )


@router.put("/{sensor_id}", response_model=ApiSingleResponse[SensorResponse], dependencies=[Depends(require_perm_optional_async("devices", "edit"))])
async def replace_sensor(
    sensor_id: int,
    sensor_data: SensorCreate,
    include_controller: bool = Query(default=False, description="컨트롤러 정보 포함 여부"),
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    센서 전체 수정 (PUT)

    센서의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **sensor_id**: 센서 ID (Path Parameter)
    - **include_controller**: 컨트롤러 정보 포함 여부

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
    - 422: 유효하지 않은 enum 값
    """
    stmt = select(Sensor).where(Sensor.id == sensor_id)
    # v6.0 P7: async lazy load 함정 회피 — include_controller 시 controller 관계 미리 로드
    if include_controller:
        stmt = stmt.options(selectinload(Sensor.controller))
    sensor = (await db.execute(stmt)).scalars().first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    # Validate controller exists
    controller = (await db.execute(
        select(Controller).where(Controller.id == sensor_data.controller_id)
    )).scalars().first()
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
    sensor.is_enable = sensor_data.is_enable
    sensor.controller_id = sensor_data.controller_id
    sensor.geolocation = sensor_data.geolocation.model_dump() if sensor_data.geolocation else None

    # Handle group_ids if provided (N:N relationship)
    if sensor_data.group_ids is not None:
        await _update_device_group_mappings(db, sensor.id, sensor_data.group_ids, "sensor")

    await db.commit()
    await db.refresh(sensor)

    sensor_response = await _sensor_to_response(sensor, db, include_controller)

    return ApiSingleResponse(
        success=True,
        message="Sensor replaced successfully",
        data=sensor_response
    )


@router.delete("/{sensor_id}", response_model=ApiSingleResponse[None], dependencies=[Depends(require_perm_optional_async("devices", "delete"))])
async def delete_sensor(
    sensor_id: int,
    current_user = Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
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
    sensor = (await db.execute(
        select(Sensor).where(Sensor.id == sensor_id)
    )).scalars().first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found"
        )

    # ConfigChangeLog: 삭제 전 식별 정보 캡처
    deleted_identifier = get_identifier(sensor)
    resource_name = f"Sensor-{sensor.id} ({sensor.name_device})"

    # Delete associated device group mappings first (no FK cascade for polymorphic relation)
    await db.execute(
        delete(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == sensor_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.SENSOR
        )
    )

    await db.delete(sensor)
    await db.commit()

    # ConfigChangeLog: DELETED 로깅 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SENSOR,
        resource_id=sensor_id,
        resource_name=resource_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="Sensor 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message="Sensor deleted successfully",
        data=None
    )
