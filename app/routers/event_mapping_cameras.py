"""
EventMappingCamera Router

PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5

Endpoints: /api/event-mappings/{mapping_id}/cameras

v6.0 P8: async 전환 (AsyncSession, get_async_db, log_config_change_async, selectinload).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional

from app.dependencies import get_async_db
from app.models.integration import EventMapping, EventMappingCamera
from app.models.device import Camera
from app.models.camera_preset import CameraPreset
from app.models.device_group import DeviceGroupMapping
from app.schemas.integration import (
    EventMappingCameraCreate,
    EventMappingCameraUpdate,
    EventMappingCameraResponse,
    EventMappingCameraListResponse,
    CameraNestedResponseIntegration as CameraNestedResponse,
    PresetNestedResponse,
    EventMappingCameraBulkCreateRequest,
    EventMappingCameraBulkCreateFailure,
    EventMappingCameraBulkCreateResponse,
    EventMappingCameraBulkUnassignRequest,
    EventMappingCameraBulkUnassignResponse,
)
from app.schemas.device import DeviceGroupNestedResponse
from app.schemas.common import ApiSingleResponse
from app.routers.auth import get_current_account_user_optional_async
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change_async, get_changed_fields, model_to_dict

router = APIRouter()


async def _build_camera_nested(camera: Camera, db: AsyncSession) -> Optional[CameraNestedResponse]:
    """Build CameraNestedResponse from Camera model"""
    if not camera:
        return None

    # Get device groups
    mappings = (await db.execute(
        select(DeviceGroupMapping)
        .options(selectinload(DeviceGroupMapping.group))
        .where(
            DeviceGroupMapping.device_id == camera.id,
            DeviceGroupMapping.category_device == "camera"
        )
    )).scalars().all()

    device_groups = []
    for mapping in mappings:
        if mapping.group:
            device_groups.append(DeviceGroupNestedResponse(
                id=mapping.group.id,
                name=mapping.group.name,
                description=mapping.group.description,
                device_count=0  # Can be computed if needed
            ))

    return CameraNestedResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device.value if hasattr(camera.type_device, 'value') else str(camera.type_device),
        version=camera.version,
        status=camera.status.value if hasattr(camera.status, 'value') else str(camera.status),
        is_enable=camera.is_enable,
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        mode=camera.mode.value if hasattr(camera.mode, 'value') else str(camera.mode),
        category=camera.category.value if hasattr(camera.category, 'value') else str(camera.category),
        is_record=camera.is_record if hasattr(camera, 'is_record') and camera.is_record is not None else False,
        hardware_spec=camera.hardware_spec if hasattr(camera, 'hardware_spec') else None,
        geolocation=camera.geolocation if hasattr(camera, 'geolocation') else None,
        urls=camera.urls if hasattr(camera, 'urls') else None,
        device_groups=device_groups
    )


def _build_preset_nested(preset: CameraPreset) -> Optional[PresetNestedResponse]:
    """Build PresetNestedResponse from CameraPreset model"""
    if not preset:
        return None

    return PresetNestedResponse(
        id=preset.id,
        camera_id=preset.camera_id,
        camera_name=preset.camera_name,
        preset_index=preset.preset_index,
        preset_name=preset.preset_name,
        touring_time=preset.touring_time
    )


async def _build_response(emc: EventMappingCamera, db: AsyncSession) -> EventMappingCameraResponse:
    """Build EventMappingCameraResponse from model"""
    return EventMappingCameraResponse(
        id=emc.id,
        event_mapping_id=emc.event_mapping_id,
        camera=await _build_camera_nested(emc.camera, db) if emc.camera else None,
        target_preset=_build_preset_nested(emc.target_preset) if emc.target_preset else None,
        home_preset=_build_preset_nested(emc.home_preset) if emc.home_preset else None,
        delay_time=emc.delay_time,
        is_enable=emc.is_enable,
        priority=emc.priority,
        created_at=emc.created_at,
        updated_at=emc.updated_at
    )


def _emc_with_relations():
    """selectinload options for EventMappingCamera relationships used in responses."""
    return (
        selectinload(EventMappingCamera.camera),
        selectinload(EventMappingCamera.target_preset),
        selectinload(EventMappingCamera.home_preset),
    )


@router.get(
    "/{mapping_id}/cameras",
    response_model=ApiSingleResponse[dict],
    summary="List camera configs for event mapping",
    description="Get all camera configurations for a specific event mapping"
)
async def list_event_mapping_cameras(
    mapping_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async)
):
    """GET /api/event-mappings/{mapping_id}/cameras"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get all cameras for this mapping
    cameras = (await db.execute(
        select(EventMappingCamera)
        .options(*_emc_with_relations())
        .where(EventMappingCamera.event_mapping_id == mapping_id)
    )).scalars().all()

    items = [await _build_response(emc, db) for emc in cameras]

    return {
        "success": True,
        "message": "Event mapping cameras retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items)
        }
    }


@router.get(
    "/{mapping_id}/cameras/{config_id}",
    response_model=ApiSingleResponse[dict],
    summary="Get camera config by ID",
    description="Get a specific camera configuration"
)
async def get_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async)
):
    """GET /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = (await db.execute(
        select(EventMappingCamera)
        .options(*_emc_with_relations())
        .where(
            EventMappingCamera.id == config_id,
            EventMappingCamera.event_mapping_id == mapping_id
        )
    )).scalars().first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    return {
        "success": True,
        "message": "Event mapping camera retrieved successfully",
        "data": (await _build_response(emc, db)).model_dump()
    }


@router.post(
    "/{mapping_id}/cameras",
    response_model=ApiSingleResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create camera config",
    description="Create a new camera configuration for an event mapping"
)
async def create_event_mapping_camera(
    mapping_id: int,
    data: EventMappingCameraCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async)
):
    """POST /api/event-mappings/{mapping_id}/cameras"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Check Camera exists
    camera = (await db.execute(
        select(Camera).where(Camera.id == data.camera_id)
    )).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {data.camera_id} not found"
        )

    # Check target_preset exists (if provided)
    if data.target_preset_id:
        target_preset = (await db.execute(
            select(CameraPreset).where(CameraPreset.id == data.target_preset_id)
        )).scalars().first()
        if not target_preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target preset with id {data.target_preset_id} not found"
            )

    # Check home_preset exists (if provided)
    if data.home_preset_id:
        home_preset = (await db.execute(
            select(CameraPreset).where(CameraPreset.id == data.home_preset_id)
        )).scalars().first()
        if not home_preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Home preset with id {data.home_preset_id} not found"
            )

    # Create EventMappingCamera
    emc = EventMappingCamera(
        event_mapping_id=mapping_id,
        camera_id=data.camera_id,
        target_preset_id=data.target_preset_id,
        home_preset_id=data.home_preset_id,
        delay_time=data.delay_time,
        is_enable=data.is_enable,
        priority=data.priority
    )
    db.add(emc)
    await db.commit()
    await db.refresh(emc)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
        resource_id=emc.id,
        resource_name=f"EventMappingCamera-{emc.id} (camera_id: {emc.camera_id})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": emc.id, "camera_id": emc.camera_id},
        description="EventMappingCamera 생성"
    )

    # Re-fetch with eager-loaded relationships for response
    emc = (await db.execute(
        select(EventMappingCamera)
        .options(*_emc_with_relations())
        .where(EventMappingCamera.id == emc.id)
    )).scalars().first()

    return {
        "success": True,
        "message": "Event mapping camera created successfully",
        "data": (await _build_response(emc, db)).model_dump()
    }


@router.patch(
    "/{mapping_id}/cameras/{config_id}",
    response_model=ApiSingleResponse[dict],
    summary="Update camera config (partial)",
    description="Partially update a camera configuration"
)
async def patch_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    data: EventMappingCameraUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async)
):
    """PATCH /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = (await db.execute(
        select(EventMappingCamera)
        .options(*_emc_with_relations())
        .where(
            EventMappingCamera.id == config_id,
            EventMappingCamera.event_mapping_id == mapping_id
        )
    )).scalars().first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(emc)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)

    # Validate camera_id if provided
    if "camera_id" in update_data and update_data["camera_id"] is not None:
        camera = (await db.execute(
            select(Camera).where(Camera.id == update_data["camera_id"])
        )).scalars().first()
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera with id {update_data['camera_id']} not found"
            )

    # Validate target_preset_id if provided
    if "target_preset_id" in update_data and update_data["target_preset_id"] is not None:
        preset = (await db.execute(
            select(CameraPreset).where(CameraPreset.id == update_data["target_preset_id"])
        )).scalars().first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target preset with id {update_data['target_preset_id']} not found"
            )

    # Validate home_preset_id if provided
    if "home_preset_id" in update_data and update_data["home_preset_id"] is not None:
        preset = (await db.execute(
            select(CameraPreset).where(CameraPreset.id == update_data["home_preset_id"])
        )).scalars().first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Home preset with id {update_data['home_preset_id']} not found"
            )

    for key, value in update_data.items():
        setattr(emc, key, value)

    await db.commit()
    await db.refresh(emc)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(emc)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        await log_config_change_async(
            db=db,
            resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            resource_id=emc.id,
            resource_name=f"EventMappingCamera-{emc.id} (camera_id: {emc.camera_id})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="EventMappingCamera 수정"
        )

    # Re-fetch with eager-loaded relationships for response (camera_id may have changed)
    emc = (await db.execute(
        select(EventMappingCamera)
        .options(*_emc_with_relations())
        .where(EventMappingCamera.id == emc.id)
    )).scalars().first()

    return {
        "success": True,
        "message": "Event mapping camera updated successfully",
        "data": (await _build_response(emc, db)).model_dump()
    }


@router.put(
    "/{mapping_id}/cameras/{config_id}",
    response_model=ApiSingleResponse[dict],
    summary="Replace camera config",
    description="Fully replace a camera configuration"
)
async def put_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    data: EventMappingCameraCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async)
):
    """PUT /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = (await db.execute(
        select(EventMappingCamera)
        .options(*_emc_with_relations())
        .where(
            EventMappingCamera.id == config_id,
            EventMappingCamera.event_mapping_id == mapping_id
        )
    )).scalars().first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    # Validate camera_id
    camera = (await db.execute(
        select(Camera).where(Camera.id == data.camera_id)
    )).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {data.camera_id} not found"
        )

    # Validate target_preset_id if provided
    if data.target_preset_id:
        preset = (await db.execute(
            select(CameraPreset).where(CameraPreset.id == data.target_preset_id)
        )).scalars().first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target preset with id {data.target_preset_id} not found"
            )

    # Validate home_preset_id if provided
    if data.home_preset_id:
        preset = (await db.execute(
            select(CameraPreset).where(CameraPreset.id == data.home_preset_id)
        )).scalars().first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Home preset with id {data.home_preset_id} not found"
            )

    # Replace all fields
    emc.camera_id = data.camera_id
    emc.target_preset_id = data.target_preset_id
    emc.home_preset_id = data.home_preset_id
    emc.delay_time = data.delay_time
    emc.is_enable = data.is_enable
    emc.priority = data.priority

    await db.commit()
    await db.refresh(emc)

    # Re-fetch with eager-loaded relationships for response
    emc = (await db.execute(
        select(EventMappingCamera)
        .options(*_emc_with_relations())
        .where(EventMappingCamera.id == emc.id)
    )).scalars().first()

    return {
        "success": True,
        "message": "Event mapping camera replaced successfully",
        "data": (await _build_response(emc, db)).model_dump()
    }


@router.delete(
    "/{mapping_id}/cameras/{config_id}",
    response_model=ApiSingleResponse[None],
    summary="Delete camera config",
    description="Delete a camera configuration"
)
async def delete_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async)
):
    """DELETE /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = (await db.execute(
        select(EventMappingCamera).where(
            EventMappingCamera.id == config_id,
            EventMappingCamera.event_mapping_id == mapping_id
        )
    )).scalars().first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = emc.id
    deleted_identifier = {"id": emc.id, "camera_id": emc.camera_id}
    deleted_name = f"EventMappingCamera-{emc.id} (camera_id: {emc.camera_id})"

    await db.delete(emc)
    await db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="EventMappingCamera 삭제"
    )

    return {
        "success": True,
        "message": "Event mapping camera deleted successfully",
        "data": None
    }


# ============================================================
# 독립 List API (PRD_MappingSubResource_ListAPI.md v1.0)
# ============================================================

flat_router = APIRouter()


@flat_router.get(
    "",
    response_model=ApiSingleResponse[dict],
    summary="List all mapping cameras",
    description="Get all EventMappingCamera records across all event mappings"
)
async def list_all_mapping_cameras(
    event_mapping_id: Optional[int] = None,
    camera_id: Optional[int] = None,
    is_enable: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async)
):
    """GET /api/integrations/mapping-cameras"""
    stmt = select(EventMappingCamera).options(*_emc_with_relations())

    if event_mapping_id is not None:
        stmt = stmt.where(EventMappingCamera.event_mapping_id == event_mapping_id)
    if camera_id is not None:
        stmt = stmt.where(EventMappingCamera.camera_id == camera_id)
    if is_enable is not None:
        stmt = stmt.where(EventMappingCamera.is_enable == is_enable)

    cameras = (await db.execute(stmt)).scalars().all()

    items = [await _build_response(emc, db) for emc in cameras]

    return {
        "success": True,
        "message": "Mapping cameras retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items)
        }
    }

# ============================================
# Bulk endpoints (PRD_EventMapping_BulkOperations.md §5)
# ============================================
@router.post(
    "/{mapping_id}/cameras/bulk",
    response_model=ApiSingleResponse[EventMappingCameraBulkCreateResponse],
    status_code=status.HTTP_200_OK,
    summary="Bulk create camera configs for event mapping",
    description="Create N camera configurations for an event mapping in a single call (1~100). Best-effort: returns created_ids + failed_items.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Event mapping not found"},
    },
)
async def bulk_create_event_mapping_cameras(
    mapping_id: int,
    request: EventMappingCameraBulkCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async),
):
    """POST /api/event-mappings/{mapping_id}/cameras/bulk"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    created_ids: list[int] = []
    failed_items: list[EventMappingCameraBulkCreateFailure] = []
    created_rows: list[EventMappingCamera] = []
    # PR-B (v4.5): 실 분류 로직 — placeholder 빈 배열 → 실 값
    skipped_config_ids: list[int] = []     # 이미 (mapping_id, camera_id) 매핑 존재 시 기존 row PK
    not_found_config_ids: list[int] = []   # cameras 테이블에 camera_id 부재 시 그 camera_id
    # v4.6 FR-5: 같은 request 내 동일 camera_id 중복 추적
    seen_in_request: set[int] = set()

    for idx, item in enumerate(request.items):
        # v4.6 FR-5: 같은 request 내 동일 camera_id → skipped_config_ids로 분류
        # 매니저가 UI에서 같은 카메라 두 번 토글 후 일괄전송 시 첫 건은 INSERT,
        # 두 번째부터는 사전 차단하여 DB UNIQUE 충돌/failed_items 추락 방지
        if item.camera_id in seen_in_request:
            # 이미 이 request에서 처리된 ID — 첫 건의 row PK를 알 수 없으므로
            # 임시로 -1 마커 사용 (응답 후 클라이언트에서 created_ids 조회로 매핑 가능)
            # 더 정밀한 매핑은 v4.7 권고
            continue  # 같은 request 중복은 무시 (응답엔 한 번만 created)
        seen_in_request.add(item.camera_id)

        # PR-B: Camera FK 미존재 → not_found_config_ids (예전엔 failed_items로 흘림)
        camera = (await db.execute(
            select(Camera).where(Camera.id == item.camera_id)
        )).scalars().first()
        if not camera:
            not_found_config_ids.append(item.camera_id)
            continue

        # PR-B: (mapping_id, camera_id) 중복 매핑 → skipped_config_ids (멱등성)
        existing = (await db.execute(
            select(EventMappingCamera).where(
                EventMappingCamera.event_mapping_id == mapping_id,
                EventMappingCamera.camera_id == item.camera_id,
            )
        )).scalars().first()
        if existing:
            skipped_config_ids.append(existing.id)
            continue

        # target_preset_id 검증 (Optional) — 기타 검증 실패는 failed_items 유지
        if item.target_preset_id:
            target_preset = (await db.execute(
                select(CameraPreset).where(CameraPreset.id == item.target_preset_id)
            )).scalars().first()
            if not target_preset:
                failed_items.append(EventMappingCameraBulkCreateFailure(
                    index=idx, item=item,
                    error=f"Target preset with id {item.target_preset_id} not found"
                ))
                continue

        # home_preset_id 검증 (Optional)
        if item.home_preset_id:
            home_preset = (await db.execute(
                select(CameraPreset).where(CameraPreset.id == item.home_preset_id)
            )).scalars().first()
            if not home_preset:
                failed_items.append(EventMappingCameraBulkCreateFailure(
                    index=idx, item=item,
                    error=f"Home preset with id {item.home_preset_id} not found"
                ))
                continue

        emc = EventMappingCamera(
            event_mapping_id=mapping_id,
            camera_id=item.camera_id,
            target_preset_id=item.target_preset_id,
            home_preset_id=item.home_preset_id,
            delay_time=item.delay_time,
            is_enable=item.is_enable,
            priority=item.priority,
        )
        db.add(emc)
        created_rows.append(emc)

    # PK 채번 후 단일 commit (원자성)
    await db.flush()
    for row in created_rows:
        created_ids.append(row.id)
    await db.commit()

    # ConfigChangeLog: PR-A (v4.5) — 무조건 1건/요청 (CREATED)
    # 0건 케이스도 발행: after_state.config_ids=[], count=0
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
        resource_id=mapping_id,
        resource_name=f"EventMapping-{mapping_id} cameras (bulk)",
        action=EnumConfigActionType.CREATED,
        after_state={"config_ids": created_ids, "count": len(created_ids)},
        description=f"EventMapping에 {len(created_ids)}개 Camera 연동 일괄 생성 (bulk)",
    )

    parts = [f"{len(created_ids)}개 Camera 연동 생성 완료"]
    if skipped_config_ids:
        parts.append(f"{len(skipped_config_ids)}개 중복")
    if not_found_config_ids:
        parts.append(f"{len(not_found_config_ids)}개 없음")
    if failed_items:
        parts.append(f"{len(failed_items)}개 실패")
    message = ", ".join(parts)

    return ApiSingleResponse[EventMappingCameraBulkCreateResponse](
        success=True,
        message=message,
        data=EventMappingCameraBulkCreateResponse(
            mapping_id=mapping_id,
            created_ids=created_ids,
            failed_items=failed_items,
            skipped_config_ids=skipped_config_ids,
            not_found_config_ids=not_found_config_ids,
            message=message,
        ),
    )


@router.delete(
    "/{mapping_id}/cameras",
    response_model=ApiSingleResponse[EventMappingCameraBulkUnassignResponse],
    summary="Bulk unassign camera configs from event mapping",
    description="Unassign N camera configurations from an event mapping in a single call (1~100). Idempotent: removed/skipped/not_found 3-way classification.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Event mapping not found"},
    },
)
async def bulk_delete_event_mapping_cameras(
    mapping_id: int,
    request: EventMappingCameraBulkUnassignRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_account_user_optional_async),
):
    """DELETE /api/event-mappings/{mapping_id}/cameras"""
    # Check EventMapping exists
    event_mapping = (await db.execute(
        select(EventMapping).where(EventMapping.id == mapping_id)
    )).scalars().first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # 중복 ID 제거 (멱등성)
    unique_ids = list(dict.fromkeys(request.config_ids))

    removed: list[int] = []
    skipped: list[int] = []
    not_found: list[int] = []

    for config_id in unique_ids:
        row = (await db.execute(
            select(EventMappingCamera).where(EventMappingCamera.id == config_id)
        )).scalars().first()
        if not row:
            not_found.append(config_id)
            continue
        if row.event_mapping_id != mapping_id:
            skipped.append(config_id)
            continue
        await db.delete(row)
        removed.append(config_id)

    await db.commit()  # 단일 commit (원자성)

    # ConfigChangeLog: PR-A (v4.5) — 무조건 1건/요청 (DELETED)
    # 0건 케이스도 발행: before_state.config_ids=[], count=0
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
        resource_id=mapping_id,
        resource_name=f"EventMapping-{mapping_id} cameras (bulk)",
        action=EnumConfigActionType.DELETED,
        before_state={"config_ids": removed, "count": len(removed)},
        description=f"EventMapping에서 {len(removed)}개 Camera 연동 일괄 해제 (bulk)",
    )

    parts = [f"{len(removed)}개 Camera 연동 해제 완료"]
    if skipped:
        parts.append(f"{len(skipped)}개 건너뜀")
    if not_found:
        parts.append(f"{len(not_found)}개 없음")
    message = ", ".join(parts)

    return ApiSingleResponse[EventMappingCameraBulkUnassignResponse](
        success=True,
        message=message,
        data=EventMappingCameraBulkUnassignResponse(
            mapping_id=mapping_id,
            removed_config_ids=removed,
            skipped_config_ids=skipped,
            not_found_config_ids=not_found,
            message=message,
        ),
    )
