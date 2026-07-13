"""
Lamp API endpoints
PRD: PRD_Lamp_Device.md v1.1 - Section 5.1
URL Pattern: /api/devices/lamps (Device 하위 리소스)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import math

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async
from app.models.device import Lamp
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory, EnumConfigResourceType, EnumConfigActionType
from app.schemas.device import LampCreate, LampUpdate, LampResponse, DeviceGroupNestedResponse
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.services.config_log_service import log_config_change, get_identifier, get_changed_fields, model_to_dict

router = APIRouter()


async def _get_device_groups_nested(db: AsyncSession, device_id: int, category_device: EnumDeviceCategory = EnumDeviceCategory.LAMP) -> List[DeviceGroupNestedResponse]:
    """Get device groups for a lamp (PRD_DeviceGroup_Support_Completion.md)"""
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
    category_device: EnumDeviceCategory = EnumDeviceCategory.LAMP
):
    """Update device group mappings for a lamp (PRD_DeviceGroup_Support_Completion.md)"""
    await db.execute(
        delete(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == category_device
        )
    )

    for group_id in group_ids:
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


async def _lamp_to_response(lamp: Lamp, db: AsyncSession) -> LampResponse:
    """Convert Lamp model to LampResponse schema"""
    # PRD_DeviceGroup_Support_Completion.md: 깨진 코드 수정 → DeviceGroupMapping 직접 쿼리
    device_groups = await _get_device_groups_nested(db, lamp.id, EnumDeviceCategory.LAMP)

    return LampResponse(
        id=lamp.id,
        number_device=lamp.number_device,
        group_device=lamp.group_device,
        name_device=lamp.name_device,
        type_device=lamp.type_device.value if hasattr(lamp.type_device, 'value') else str(lamp.type_device),
        version=lamp.version,
        status=lamp.status.value if hasattr(lamp.status, 'value') else str(lamp.status),
        is_enable=lamp.is_enable if lamp.is_enable is not None else True,
        created_at=lamp.created_at,
        updated_at=lamp.updated_at,
        ip_address=lamp.ip_address,
        ip_port=lamp.ip_port,
        user_name=lamp.user_name,
        user_password=lamp.user_password,
        description=lamp.description,
        geolocation=lamp.geolocation,
        device_groups=device_groups
    )


@router.get("", response_model=ApiResponse[list[LampResponse]])
async def get_lamps(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    status: Optional[str] = Query(None, description="상태로 필터링 (EnumDeviceStatus)"),
    is_enable: Optional[bool] = Query(None, description="활성화 여부 필터링"),
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    경광등 목록 조회 (페이지네이션)

    경광등 목록을 페이지네이션하여 조회합니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **status**: 상태로 필터링 (선택)
    - **is_enable**: 활성화 여부 필터링 (선택)

    **Response**: 경광등 목록 및 페이지네이션 정보
    """
    # Build query
    stmt = select(Lamp)
    count_stmt = select(func.count()).select_from(Lamp)

    # Apply filters
    if status is not None:
        stmt = stmt.where(Lamp.status == status)
        count_stmt = count_stmt.where(Lamp.status == status)
    if is_enable is not None:
        stmt = stmt.where(Lamp.is_enable == is_enable)
        count_stmt = count_stmt.where(Lamp.is_enable == is_enable)

    # Get total count
    total = (await db.execute(count_stmt)).scalar()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get items with pagination (order by id for stable pagination)
    lamps = (await db.execute(
        stmt.order_by(Lamp.id).offset(skip).limit(limit)
    )).scalars().all()

    # Convert to response schema
    items = [await _lamp_to_response(lamp, db) for lamp in lamps]

    return ApiResponse(
        success=True,
        message="Lamp 목록 조회 성공",
        data=items,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages
        )
    )


@router.get("/{lamp_id}", response_model=ApiSingleResponse[LampResponse])
async def get_lamp(
    lamp_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    경광등 상세 조회

    - **lamp_id**: 조회할 경광등 ID

    **Response**: 경광등 상세 정보
    """
    lamp = (await db.execute(
        select(Lamp).where(Lamp.id == lamp_id)
    )).scalars().first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_id} not found"
        )

    return ApiSingleResponse(
        success=True,
        message="Lamp 조회 성공",
        data=await _lamp_to_response(lamp, db)
    )


@router.post("", response_model=ApiSingleResponse[LampResponse], status_code=status.HTTP_201_CREATED)
async def create_lamp(
    lamp_data: LampCreate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    경광등 생성

    새로운 경광등을 생성합니다.

    **Response**: 생성된 경광등 정보
    """
    # Parse type_device to enum
    try:
        type_device_enum = EnumDeviceType(lamp_data.type_device)
    except ValueError:
        type_device_enum = EnumDeviceType.Lamp

    # Parse status to enum
    try:
        status_enum = EnumDeviceStatus(lamp_data.status)
    except ValueError:
        status_enum = EnumDeviceStatus.ACTIVATED

    # Create new Lamp
    lamp = Lamp(
        category_device=EnumDeviceCategory.LAMP,
        number_device=lamp_data.number_device,
        group_device=lamp_data.group_device,
        name_device=lamp_data.name_device,
        type_device=type_device_enum,
        version=lamp_data.version,
        status=status_enum,
        is_enable=lamp_data.is_enable,
        ip_address=lamp_data.ip_address,
        ip_port=lamp_data.ip_port,
        user_name=lamp_data.user_name,
        user_password=lamp_data.user_password,
        description=lamp_data.description,
        geolocation=lamp_data.geolocation.model_dump() if lamp_data.geolocation else None
    )

    db.add(lamp)
    await db.commit()
    await db.refresh(lamp)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if lamp_data.group_ids is not None:
        await _update_device_group_mappings(db, lamp.id, lamp_data.group_ids, EnumDeviceCategory.LAMP)
        await db.commit()

    # Log config change (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.LAMP,
        resource_id=lamp.id,
        resource_name=f"Lamp-{lamp.id} ({lamp.name_device})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": lamp.id, "name_device": lamp.name_device},
        description="Lamp 생성"
    )

    return ApiSingleResponse(
        success=True,
        message="Lamp 생성 성공",
        data=await _lamp_to_response(lamp, db)
    )


@router.patch("/{lamp_id}", response_model=ApiSingleResponse[LampResponse])
async def patch_lamp(
    lamp_id: int,
    lamp_data: LampUpdate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    경광등 부분 수정 (PATCH)

    제공된 필드만 업데이트합니다.

    - **lamp_id**: 수정할 경광등 ID

    **Response**: 수정된 경광등 정보
    """
    lamp = (await db.execute(
        select(Lamp).where(Lamp.id == lamp_id)
    )).scalars().first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_id} not found"
        )

    # Store old data for logging
    old_data = model_to_dict(lamp)

    # Update provided fields
    update_data = lamp_data.model_dump(exclude_unset=True)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 분리 처리
    group_ids = update_data.pop("group_ids", None)

    for field, value in update_data.items():
        if field == "type_device" and value is not None:
            try:
                value = EnumDeviceType(value)
            except ValueError:
                pass
        elif field == "status" and value is not None:
            try:
                value = EnumDeviceStatus(value)
            except ValueError:
                pass
        elif field == "geolocation" and value is not None:
            value = value.model_dump() if hasattr(value, 'model_dump') else value
        setattr(lamp, field, value)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if group_ids is not None:
        await _update_device_group_mappings(db, lamp.id, group_ids, EnumDeviceCategory.LAMP)

    await db.commit()
    await db.refresh(lamp)

    # Log config change (PRD v1.2)
    after_state = model_to_dict(lamp)
    before_changes, after_changes = get_changed_fields(old_data, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.LAMP,
            resource_id=lamp.id,
            resource_name=f"Lamp-{lamp.id} ({lamp.name_device})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="Lamp 수정"
        )

    return ApiSingleResponse(
        success=True,
        message="Lamp 수정 성공",
        data=await _lamp_to_response(lamp, db)
    )


@router.put("/{lamp_id}", response_model=ApiSingleResponse[LampResponse])
async def put_lamp(
    lamp_id: int,
    lamp_data: LampCreate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    경광등 전체 수정 (PUT)

    모든 필드를 업데이트합니다.

    - **lamp_id**: 수정할 경광등 ID

    **Response**: 수정된 경광등 정보
    """
    lamp = (await db.execute(
        select(Lamp).where(Lamp.id == lamp_id)
    )).scalars().first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_id} not found"
        )

    # Store old data for logging
    old_data = model_to_dict(lamp)

    # Parse type_device to enum
    try:
        type_device_enum = EnumDeviceType(lamp_data.type_device)
    except ValueError:
        type_device_enum = EnumDeviceType.Lamp

    # Parse status to enum
    try:
        status_enum = EnumDeviceStatus(lamp_data.status)
    except ValueError:
        status_enum = EnumDeviceStatus.ACTIVATED

    # Update all fields
    lamp.number_device = lamp_data.number_device
    lamp.group_device = lamp_data.group_device
    lamp.name_device = lamp_data.name_device
    lamp.type_device = type_device_enum
    lamp.version = lamp_data.version
    lamp.status = status_enum
    lamp.is_enable = lamp_data.is_enable
    lamp.ip_address = lamp_data.ip_address
    lamp.ip_port = lamp_data.ip_port
    lamp.user_name = lamp_data.user_name
    lamp.user_password = lamp_data.user_password
    lamp.description = lamp_data.description
    lamp.geolocation = lamp_data.geolocation.model_dump() if lamp_data.geolocation else None

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if lamp_data.group_ids is not None:
        await _update_device_group_mappings(db, lamp.id, lamp_data.group_ids, EnumDeviceCategory.LAMP)

    await db.commit()
    await db.refresh(lamp)

    # Log config change (PRD v1.2)
    new_data = model_to_dict(lamp)
    before_changes, after_changes = get_changed_fields(old_data, new_data)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.LAMP,
            resource_id=lamp.id,
            resource_name=f"Lamp-{lamp.id} ({lamp.name_device})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="Lamp 전체 수정"
        )

    return ApiSingleResponse(
        success=True,
        message="Lamp 전체 수정 성공",
        data=await _lamp_to_response(lamp, db)
    )


@router.delete("/{lamp_id}", response_model=ApiSingleResponse[None])
async def delete_lamp(
    lamp_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    경광등 삭제

    - **lamp_id**: 삭제할 경광등 ID

    **Response**: 삭제 결과 메시지

    **Note**: EventMappingLamp의 lamp_id는 SET NULL로 처리됨
    """
    lamp = (await db.execute(
        select(Lamp).where(Lamp.id == lamp_id)
    )).scalars().first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_id} not found"
        )

    # Store info for logging (PRD v1.2)
    deleted_id = lamp.id
    deleted_identifier = {"id": lamp.id, "name_device": lamp.name_device}
    deleted_name = f"Lamp-{lamp.id} ({lamp.name_device})"

    # Delete associated device group mappings first (no FK cascade for polymorphic relation)
    await db.execute(
        delete(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == lamp_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.LAMP
        )
    )

    # Delete lamp (CASCADE will delete from devices table, SET NULL for event_mapping_lamps)
    await db.delete(lamp)
    await db.commit()

    # Log config change (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.LAMP,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="Lamp 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message=f"Lamp {lamp_id} 삭제 성공",
        data=None
    )
