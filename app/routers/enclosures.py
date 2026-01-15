"""
Enclosure API endpoints
PRD: PRD_Enclosure_Device.md v1.1 - Section 5.1
URL Pattern: /api/devices/enclosures (Device 하위 리소스)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Enclosure
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
from app.schemas.device import (
    EnclosureCreate,
    EnclosureUpdate,
    EnclosureResponse,
    EnclosureControl,
    EnclosureStatusUpdate,
    EnclosureThresholdConfig,
    Geolocation
)
# EnclosureDetailInfo 제거됨 (PRD_Enclosure_Metrics_Separation.md v1.0)
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=["Enclosures"])


def _enclosure_to_response(enclosure: Enclosure) -> EnclosureResponse:
    """Convert Enclosure model to EnclosureResponse schema"""
    # Convert JSONB to Pydantic schemas
    # detail_info 제거됨 → enclosure_metrics API 사용 (PRD_Enclosure_Metrics_Separation.md v1.0)

    geolocation = None
    if enclosure.geolocation:
        geolocation = Geolocation(**enclosure.geolocation)

    threshold_config = None
    if enclosure.threshold_config:
        threshold_config = EnclosureThresholdConfig(**enclosure.threshold_config)

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
        updated_at=enclosure.updated_at
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

    # Get paginated results
    enclosures = query.offset(skip).limit(limit).all()

    # Convert to response format
    enclosure_responses = [_enclosure_to_response(e) for e in enclosures]

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


@router.get("/{enclosure_id}", response_model=ApiResponse[EnclosureResponse])
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

    enclosure_response = _enclosure_to_response(enclosure)

    return ApiResponse(
        success=True,
        message="Enclosure retrieved successfully",
        data=enclosure_response
    )


@router.post("", response_model=ApiResponse[EnclosureResponse], status_code=status.HTTP_201_CREATED)
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

    enclosure_response = _enclosure_to_response(new_enclosure)

    return ApiResponse(
        success=True,
        message="Enclosure created successfully",
        data=enclosure_response
    )


@router.patch("/{enclosure_id}", response_model=ApiResponse[EnclosureResponse])
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

    # Update fields if provided
    update_data = enclosure_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        # Handle nested Pydantic models (JSONB fields)
        if field in ['geolocation', 'threshold_config'] and value is not None:
            setattr(enclosure, field, value if isinstance(value, dict) else value.model_dump(mode='json'))
        else:
            setattr(enclosure, field, value)

    db.commit()
    db.refresh(enclosure)

    enclosure_response = _enclosure_to_response(enclosure)

    return ApiResponse(
        success=True,
        message="Enclosure updated successfully",
        data=enclosure_response
    )


@router.put("/{enclosure_id}", response_model=ApiResponse[EnclosureResponse])
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

    db.commit()
    db.refresh(enclosure)

    enclosure_response = _enclosure_to_response(enclosure)

    return ApiResponse(
        success=True,
        message="Enclosure replaced successfully",
        data=enclosure_response
    )


@router.delete("/{enclosure_id}", response_model=ApiResponse[None])
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

    db.delete(enclosure)
    db.commit()

    return ApiResponse(
        success=True,
        message="Enclosure deleted successfully",
        data=None
    )


# ============================================================================
# Phase 5: 특수 엔드포인트
# ============================================================================

@router.patch("/{enclosure_id}/status", response_model=ApiResponse[EnclosureResponse])
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

    # Update door_status if provided
    if status_data.door_status is not None:
        enclosure.door_status = status_data.door_status

    db.commit()
    db.refresh(enclosure)

    enclosure_response = _enclosure_to_response(enclosure)

    return ApiResponse(
        success=True,
        message="Enclosure status updated successfully",
        data=enclosure_response
    )


@router.post("/{enclosure_id}/control", response_model=ApiResponse[EnclosureResponse])
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

    enclosure_response = _enclosure_to_response(enclosure)

    return ApiResponse(
        success=True,
        message="Enclosure control updated successfully",
        data=enclosure_response
    )
