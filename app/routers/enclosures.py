"""
Enclosure API endpoints
PRD: PRD_Enclosure_Device.md v1.1 - Section 5.1
URL Pattern: /api/devices/enclosures (Device 하위 리소스)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Enclosure
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus, EnumDeviceCategory, EnumConfigResourceType, EnumConfigActionType
from app.schemas.device import (
    EnclosureCreate,
    EnclosureUpdate,
    EnclosureResponse,
    EnclosureControl,
    EnclosureStatusUpdate,
    EnclosureThresholdConfig,
    Geolocation,
    DeviceGroupNestedResponse
)
# EnclosureDetailInfo 제거됨 (PRD_Enclosure_Metrics_Separation.md v1.0)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.services.config_log_service import log_config_change, get_identifier, get_changed_fields, model_to_dict

router = APIRouter(tags=["Enclosures"])


def _get_device_groups_nested(db: Session, device_id: int, category_device: EnumDeviceCategory = EnumDeviceCategory.ENCLOSURE) -> List[DeviceGroupNestedResponse]:
    """Get device groups for an enclosure (PRD_DeviceGroup_Support_Completion.md)"""
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
    category_device: EnumDeviceCategory = EnumDeviceCategory.ENCLOSURE
):
    """Update device group mappings for an enclosure (PRD_DeviceGroup_Support_Completion.md)"""
    db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == category_device
    ).delete()

    for group_id in group_ids:
        group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
        if group:
            mapping = DeviceGroupMapping(
                device_id=device_id,
                category_device=category_device,
                group_id=group_id
            )
            db.add(mapping)


def _enclosure_to_response(enclosure: Enclosure, db: Session) -> EnclosureResponse:
    """Convert Enclosure model to EnclosureResponse schema"""
    # Convert JSONB to Pydantic schemas
    # detail_info 제거됨 → enclosure_metrics API 사용 (PRD_Enclosure_Metrics_Separation.md v1.0)

    geolocation = None
    if enclosure.geolocation:
        geolocation = Geolocation(**enclosure.geolocation)

    threshold_config = None
    if enclosure.threshold_config:
        threshold_config = EnclosureThresholdConfig(**enclosure.threshold_config)

    # PRD_DeviceGroup_Support_Completion.md: device_groups 조회
    device_groups = _get_device_groups_nested(db, enclosure.id, EnumDeviceCategory.ENCLOSURE)

    return EnclosureResponse(
        id=enclosure.id,
        number_device=enclosure.number_device,
        group_device=enclosure.group_device,
        name_device=enclosure.name_device,
        type_device=enclosure.type_device.value if hasattr(enclosure.type_device, 'value') else str(enclosure.type_device),
        version=enclosure.version,
        status=enclosure.status,
        is_enable=enclosure.is_enable,
        door_status=enclosure.door_status,
        geolocation=geolocation,
        threshold_config=threshold_config,
        heater_enabled=enclosure.heater_enabled,
        fan_enabled=enclosure.fan_enabled,
        created_at=enclosure.created_at,
        updated_at=enclosure.updated_at,
        device_groups=device_groups
    )


@router.get("", response_model=ApiResponse[list[EnclosureResponse]])
async def get_enclosures(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    door_status: Optional[str] = Query(None, description="도어 상태 필터 (CLOSED/OPEN)"),
    status: Optional[str] = Query(None, description="장비 상태 필터 (ACTIVATED/DEACTIVATED/ERROR)"),
    name_device: Optional[str] = Query(None, description="장비명 검색"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 목록 조회 (페이지네이션)

    함체 목록을 페이지네이션하여 조회합니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **door_status**: 도어 물리적 상태 필터 (CLOSED/OPEN)
    - **status**: 장비 운영 상태 필터 (ACTIVATED/DEACTIVATED/ERROR)
    - **name_device**: 장비명 검색

    **Response**: 함체 목록 및 페이지네이션 정보
    """
    # Build query
    query = db.query(Enclosure)

    # Apply filters
    if door_status is not None:
        query = query.filter(Enclosure.door_status == door_status)
    if status is not None:
        query = query.filter(Enclosure.status == status)
    if name_device is not None:
        query = query.filter(Enclosure.name_device.contains(name_device))

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by id for stable pagination)
    enclosures = query.order_by(Enclosure.id).offset(skip).limit(limit).all()

    # Convert to response format
    enclosure_responses = [_enclosure_to_response(e, db) for e in enclosures]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Enclosures retrieved successfully",
        data=enclosure_responses,
        pagination=pagination
    )


@router.get("/{enclosure_id}", response_model=ApiSingleResponse[EnclosureResponse])
async def get_enclosure(
    enclosure_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 단건 조회

    ID로 함체 정보를 조회합니다.

    - **enclosure_id**: 함체 ID (Path Parameter)

    **Response**: 함체 상세 정보 (status: 장비 운영 상태, door_status: 도어 물리적 상태)

    **Error**:
    - 404: 함체를 찾을 수 없음
    """
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()

    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    enclosure_response = _enclosure_to_response(enclosure, db)

    return ApiSingleResponse(
        success=True,
        message="Enclosure retrieved successfully",
        data=enclosure_response
    )


@router.post("", response_model=ApiSingleResponse[EnclosureResponse], status_code=status.HTTP_201_CREATED)
async def create_enclosure(
    enclosure_data: EnclosureCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 생성

    새로운 함체를 생성합니다.

    **Request Body**:
    - **number_device**: 장비 번호 (필수)
    - **name_device**: 장비 이름 (필수)
    - **group_device**: 장치 그룹 번호 (레거시)
    - **status**: 장비 운영 상태 (ACTIVATED/DEACTIVATED/ERROR)
    - **door_status**: 도어 물리적 상태 (CLOSED/OPEN)
    - **geolocation**: 위치 정보 (JSONB)
    - **threshold_config**: 알람 임계값 (JSONB)
    - **heater_enabled**: 히터 활성화
    - **fan_enabled**: 팬 활성화

    **Response**: 생성된 함체 정보
    """
    # Create new enclosure
    new_enclosure = Enclosure(
        number_device=enclosure_data.number_device,
        group_device=enclosure_data.group_device,
        name_device=enclosure_data.name_device,
        type_device=enclosure_data.type_device,
        version=enclosure_data.version,
        status=enclosure_data.status,
        is_enable=enclosure_data.is_enable,
        door_status=enclosure_data.door_status,
        geolocation=enclosure_data.geolocation.model_dump(mode='json') if enclosure_data.geolocation else None,
        threshold_config=enclosure_data.threshold_config.model_dump(mode='json') if enclosure_data.threshold_config else None,
        heater_enabled=enclosure_data.heater_enabled,
        fan_enabled=enclosure_data.fan_enabled
    )

    db.add(new_enclosure)
    db.commit()
    db.refresh(new_enclosure)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if enclosure_data.group_ids is not None:
        _update_device_group_mappings(db, new_enclosure.id, enclosure_data.group_ids, EnumDeviceCategory.ENCLOSURE)
        db.commit()

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.ENCLOSURE,
        resource_id=new_enclosure.id,
        resource_name=f"Enclosure-{new_enclosure.id} ({new_enclosure.name_device})",
        action=EnumConfigActionType.CREATED,
        after_state=get_identifier(new_enclosure),
        description="Enclosure 생성"
    )

    enclosure_response = _enclosure_to_response(new_enclosure, db)

    return ApiSingleResponse(
        success=True,
        message="Enclosure created successfully",
        data=enclosure_response
    )


@router.patch("/{enclosure_id}", response_model=ApiSingleResponse[EnclosureResponse])
async def update_enclosure(
    enclosure_id: int,
    enclosure_data: EnclosureUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 부분 수정 (PATCH)

    함체의 일부 필드만 수정합니다.

    - **enclosure_id**: 함체 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **name_device**: 장비 이름
    - **status**: 장비 운영 상태 (ACTIVATED/DEACTIVATED/ERROR)
    - **door_status**: 도어 물리적 상태 (CLOSED/OPEN)
    - **geolocation**: 위치 정보
    - **threshold_config**: 알람 임계값
    - **heater_enabled**: 히터 활성화
    - **fan_enabled**: 팬 활성화

    **Response**: 수정된 함체 정보

    **Error**:
    - 404: 함체를 찾을 수 없음
    """
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()

    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(enclosure)

    # Update fields if provided
    update_data = enclosure_data.model_dump(exclude_unset=True)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 분리 처리
    group_ids = update_data.pop("group_ids", None)

    for field, value in update_data.items():
        # Handle nested Pydantic models (JSONB fields)
        if field in ['geolocation', 'threshold_config'] and value is not None:
            setattr(enclosure, field, value if isinstance(value, dict) else value.model_dump(mode='json'))
        else:
            setattr(enclosure, field, value)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if group_ids is not None:
        _update_device_group_mappings(db, enclosure.id, group_ids, EnumDeviceCategory.ENCLOSURE)

    db.commit()
    db.refresh(enclosure)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(enclosure)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.ENCLOSURE,
            resource_id=enclosure.id,
            resource_name=f"Enclosure-{enclosure.id} ({enclosure.name_device})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="Enclosure 수정"
        )

    enclosure_response = _enclosure_to_response(enclosure, db)

    return ApiSingleResponse(
        success=True,
        message="Enclosure updated successfully",
        data=enclosure_response
    )


@router.put("/{enclosure_id}", response_model=ApiSingleResponse[EnclosureResponse])
async def replace_enclosure(
    enclosure_id: int,
    enclosure_data: EnclosureCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 전체 수정 (PUT)

    함체의 모든 필드를 교체합니다.

    - **enclosure_id**: 함체 ID (Path Parameter)

    **Request Body** (필수 필드):
    - **number_device**: 장비 번호
    - **name_device**: 장비 이름

    **Response**: 수정된 함체 정보

    **Error**:
    - 404: 함체를 찾을 수 없음
    """
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()

    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # Replace all fields
    enclosure.number_device = enclosure_data.number_device
    enclosure.group_device = enclosure_data.group_device
    enclosure.name_device = enclosure_data.name_device
    enclosure.type_device = enclosure_data.type_device
    enclosure.version = enclosure_data.version
    enclosure.status = enclosure_data.status
    enclosure.is_enable = enclosure_data.is_enable
    enclosure.door_status = enclosure_data.door_status
    enclosure.geolocation = enclosure_data.geolocation.model_dump(mode='json') if enclosure_data.geolocation else None
    enclosure.threshold_config = enclosure_data.threshold_config.model_dump(mode='json') if enclosure_data.threshold_config else None
    enclosure.heater_enabled = enclosure_data.heater_enabled
    enclosure.fan_enabled = enclosure_data.fan_enabled

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if enclosure_data.group_ids is not None:
        _update_device_group_mappings(db, enclosure.id, enclosure_data.group_ids, EnumDeviceCategory.ENCLOSURE)

    db.commit()
    db.refresh(enclosure)

    enclosure_response = _enclosure_to_response(enclosure, db)

    return ApiSingleResponse(
        success=True,
        message="Enclosure replaced successfully",
        data=enclosure_response
    )


@router.delete("/{enclosure_id}", response_model=ApiSingleResponse[None])
async def delete_enclosure(
    enclosure_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 삭제

    함체를 삭제합니다. Device 레코드도 CASCADE로 함께 삭제됩니다.

    - **enclosure_id**: 함체 ID (Path Parameter)

    **Response**: 삭제된 함체 ID

    **Error**:
    - 404: 함체를 찾을 수 없음
    """
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()

    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = enclosure.id
    deleted_identifier = get_identifier(enclosure)
    deleted_name = f"Enclosure-{enclosure.id} ({enclosure.name_device})"

    db.delete(enclosure)
    db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.ENCLOSURE,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="Enclosure 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message="Enclosure deleted successfully",
        data=None
    )


# ============================================================================
# Phase 5: 특수 엔드포인트
# ============================================================================

@router.patch("/{enclosure_id}/status", response_model=ApiSingleResponse[EnclosureResponse])
async def update_enclosure_status(
    enclosure_id: int,
    status_data: EnclosureStatusUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 도어 상태 업데이트

    함체의 도어 상태를 업데이트합니다.
    외부 장비(센서)에서 주기적으로 호출하는 엔드포인트입니다.

    PRD: PRD_Enclosure_Device.md v1.1 - Section 5.3.2
    Note: 환경 모니터링 데이터는 enclosure_metrics API 사용 (PRD_Enclosure_Metrics_Separation.md v1.0)

    - **enclosure_id**: 함체 ID (Path Parameter)

    **Request Body**:
    - **door_status**: 도어 물리적 상태 (CLOSED/OPEN)

    **Response**: 업데이트된 함체 정보

    **Error**:
    - 404: 함체를 찾을 수 없음
    """
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()

    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # ConfigChangeLog: 상태 변경 전 캡처 (PRD v1.2)
    old_door_status = enclosure.door_status

    # Update door_status if provided
    if status_data.door_status is not None:
        enclosure.door_status = status_data.door_status

    db.commit()
    db.refresh(enclosure)

    # ConfigChangeLog: STATUS_CHANGED 로그 기록 (PRD v1.2)
    if old_door_status != enclosure.door_status:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.ENCLOSURE,
            resource_id=enclosure.id,
            resource_name=f"Enclosure-{enclosure.id} ({enclosure.name_device})",
            action=EnumConfigActionType.STATUS_CHANGED,
            before_state={"door_status": old_door_status.value if hasattr(old_door_status, 'value') else old_door_status},
            after_state={"door_status": enclosure.door_status.value if hasattr(enclosure.door_status, 'value') else enclosure.door_status},
            description=f"Enclosure 상태 변경: {old_door_status} → {enclosure.door_status}"
        )

    enclosure_response = _enclosure_to_response(enclosure, db)

    return ApiSingleResponse(
        success=True,
        message="Enclosure status updated successfully",
        data=enclosure_response
    )


@router.post("/{enclosure_id}/control", response_model=ApiSingleResponse[EnclosureResponse])
async def control_enclosure(
    enclosure_id: int,
    control_data: EnclosureControl,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    함체 히터/팬 제어

    함체의 히터 및 팬을 제어합니다.

    PRD: PRD_Enclosure_Device.md v1.1 - Section 5.3.3

    - **enclosure_id**: 함체 ID (Path Parameter)

    **Request Body**:
    - **heater_enabled**: 히터 활성화 (true/false)
    - **fan_enabled**: 팬 활성화 (true/false)

    **Response**: 제어된 함체 정보

    **Error**:
    - 404: 함체를 찾을 수 없음
    """
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()

    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # Update control fields if provided
    if control_data.heater_enabled is not None:
        enclosure.heater_enabled = control_data.heater_enabled

    if control_data.fan_enabled is not None:
        enclosure.fan_enabled = control_data.fan_enabled

    db.commit()
    db.refresh(enclosure)

    enclosure_response = _enclosure_to_response(enclosure, db)

    return ApiSingleResponse(
        success=True,
        message="Enclosure control updated successfully",
        data=enclosure_response
    )
