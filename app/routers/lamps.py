"""
Lamp API endpoints
PRD: PRD_Lamp_Device.md v1.1 - Section 5.1
URL Pattern: /api/devices/lamps (Device 하위 리소스)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Lamp
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory, EnumConfigResourceType, EnumConfigActionType
from app.schemas.device import LampCreate, LampUpdate, LampResponse, DeviceGroupNestedResponse
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.services.config_log_service import log_config_change, get_identifier, get_changed_fields, model_to_dict

router = APIRouter(tags=["Lamps"])


def _lamp_to_response(lamp: Lamp, db: Session) -> LampResponse:
    """Convert Lamp model to LampResponse schema"""
    # Build DeviceGroupNestedResponse list
    device_groups = []
    if hasattr(lamp, 'group_mappings') and lamp.group_mappings:
        for mapping in lamp.group_mappings:
            group = mapping.device_group
            if group:
                device_groups.append(DeviceGroupNestedResponse(
                    id=group.id,
                    name=group.name,
                    description=group.description,
                    device_count=group.device_mappings.count() if hasattr(group, 'device_mappings') else 0
                ))

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
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    query = db.query(Lamp)

    # Apply filters
    if status is not None:
        query = query.filter(Lamp.status == status)
    if is_enable is not None:
        query = query.filter(Lamp.is_enable == is_enable)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get items with pagination
    lamps = query.offset(skip).limit(limit).all()

    # Convert to response schema
    items = [_lamp_to_response(lamp, db) for lamp in lamps]

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
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    경광등 상세 조회

    - **lamp_id**: 조회할 경광등 ID

    **Response**: 경광등 상세 정보
    """
    lamp = db.query(Lamp).filter(Lamp.id == lamp_id).first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_id} not found"
        )

    return ApiSingleResponse(
        success=True,
        message="Lamp 조회 성공",
        data=_lamp_to_response(lamp, db)
    )


@router.post("", response_model=ApiSingleResponse[LampResponse], status_code=status.HTTP_201_CREATED)
async def create_lamp(
    lamp_data: LampCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    db.commit()
    db.refresh(lamp)

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
        data=_lamp_to_response(lamp, db)
    )


@router.patch("/{lamp_id}", response_model=ApiSingleResponse[LampResponse])
async def patch_lamp(
    lamp_id: int,
    lamp_data: LampUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    경광등 부분 수정 (PATCH)

    제공된 필드만 업데이트합니다.

    - **lamp_id**: 수정할 경광등 ID

    **Response**: 수정된 경광등 정보
    """
    lamp = db.query(Lamp).filter(Lamp.id == lamp_id).first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_id} not found"
        )

    # Store old data for logging
    old_data = model_to_dict(lamp)

    # Update provided fields
    update_data = lamp_data.model_dump(exclude_unset=True)
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

    db.commit()
    db.refresh(lamp)

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
        data=_lamp_to_response(lamp, db)
    )


@router.put("/{lamp_id}", response_model=ApiSingleResponse[LampResponse])
async def put_lamp(
    lamp_id: int,
    lamp_data: LampCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    경광등 전체 수정 (PUT)

    모든 필드를 업데이트합니다.

    - **lamp_id**: 수정할 경광등 ID

    **Response**: 수정된 경광등 정보
    """
    lamp = db.query(Lamp).filter(Lamp.id == lamp_id).first()
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

    db.commit()
    db.refresh(lamp)

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
        data=_lamp_to_response(lamp, db)
    )


@router.delete("/{lamp_id}", response_model=ApiSingleResponse[dict])
async def delete_lamp(
    lamp_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    경광등 삭제

    - **lamp_id**: 삭제할 경광등 ID

    **Response**: 삭제 결과 메시지

    **Note**: EventMappingLamp의 lamp_id는 SET NULL로 처리됨
    """
    lamp = db.query(Lamp).filter(Lamp.id == lamp_id).first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_id} not found"
        )

    # Store info for logging (PRD v1.2)
    deleted_id = lamp.id
    deleted_identifier = {"id": lamp.id, "name_device": lamp.name_device}
    deleted_name = f"Lamp-{lamp.id} ({lamp.name_device})"

    # Delete lamp (CASCADE will delete from devices table, SET NULL for event_mapping_lamps)
    db.delete(lamp)
    db.commit()

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
        message="Lamp 삭제 성공",
        data={"id": lamp_id, "deleted": True}
    )
