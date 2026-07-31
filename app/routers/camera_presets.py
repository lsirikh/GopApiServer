"""
Camera Preset API endpoints
PRD: docs/PRD_Camera_Preset_ROI.md
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import math

from app.dependencies import get_async_db
from app.utils.datetime import to_display
from app.routers.auth import get_current_account_user_optional_async
from app.models.device import Camera
from app.models.camera_preset import CameraPreset, ROI, XyPoint
from app.schemas.camera_preset import (
    CameraPresetCreate,
    CameraPresetResponse,
    CameraPresetDetailResponse,
    CameraPresetUpdate,
    CameraPresetWithROIsResponse,
    CameraPresetListData
)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change, get_identifier, get_changed_fields, model_to_dict

router = APIRouter()


@router.get("/{camera_id}/presets", response_model=ApiResponse[CameraPresetListData])
async def get_camera_presets(
    camera_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Max items per page"),
    include_rois: bool = Query(False, description="Include ROIs in response"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Get list of camera presets for a specific camera
    """
    # Check if camera exists
    camera = (await db.execute(select(Camera).where(Camera.id == camera_id))).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Query presets
    total = (await db.execute(
        select(func.count()).select_from(CameraPreset).where(CameraPreset.camera_id == camera_id)
    )).scalar() or 0

    # Pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1
    presets = (await db.execute(
        select(CameraPreset)
        .where(CameraPreset.camera_id == camera_id)
        .order_by(CameraPreset.id)
        .offset(skip)
        .limit(limit)
    )).scalars().all()

    # Build response items
    items = []
    for preset in presets:
        roi_count = (await db.execute(
            select(func.count()).select_from(ROI).where(ROI.preset_id == preset.id)
        )).scalar() or 0
        item = {
            "id": preset.id,
            "camera_id": preset.camera_id,
            "camera_name": preset.camera_name,
            "preset_index": preset.preset_index,
            "preset_name": preset.preset_name,
            "touring_time": preset.touring_time,
            "roi_count": roi_count,
            "created_at": to_display(preset.created_at).isoformat(),
            "updated_at": to_display(preset.updated_at).isoformat()
        }
        if include_rois:
            rois_list = (await db.execute(
                select(ROI).where(ROI.preset_id == preset.id)
            )).scalars().all()
            rois_data = []
            for roi in rois_list:
                point_count = (await db.execute(
                    select(func.count()).select_from(XyPoint).where(XyPoint.roi_id == roi.id)
                )).scalar() or 0
                rois_data.append({
                    "id": roi.id,
                    "name": roi.name,
                    "resolution_width": roi.resolution_width,
                    "resolution_height": roi.resolution_height,
                    "is_enable": roi.is_enable,
                    "point_count": point_count
                })
            item["rois"] = rois_data
        items.append(item)

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Camera presets retrieved successfully",
        data={
            "items": items,
            "total": total
        },
        pagination=pagination
    )


@router.get("/{camera_id}/presets/{preset_id}", response_model=ApiSingleResponse[CameraPresetDetailResponse])
async def get_camera_preset(
    camera_id: int,
    preset_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Get a specific camera preset with ROIs and points
    """
    # Check if camera exists
    camera = (await db.execute(select(Camera).where(Camera.id == camera_id))).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Get preset
    preset = (await db.execute(
        select(CameraPreset).where(
            CameraPreset.id == preset_id,
            CameraPreset.camera_id == camera_id
        )
    )).scalars().first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Build ROIs with points (v2.10: Nested Response - timestamp 제외)
    rois_list = (await db.execute(
        select(ROI).where(ROI.preset_id == preset.id)
    )).scalars().all()
    rois_data = []
    for roi in rois_list:
        points_list = (await db.execute(
            select(XyPoint).where(XyPoint.roi_id == roi.id).order_by(XyPoint.order)
        )).scalars().all()
        points_data = [
            {
                "id": point.id,
                "x": point.x,
                "y": point.y,
                "order": point.order
            }
            for point in points_list
        ]
        rois_data.append({
            "id": roi.id,
            "preset_id": roi.preset_id,
            "name": roi.name,
            "resolution_width": roi.resolution_width,
            "resolution_height": roi.resolution_height,
            "is_enable": roi.is_enable,
            "points": points_data
        })

    return ApiSingleResponse(
        success=True,
        message="Camera preset retrieved successfully",
        data={
            "id": preset.id,
            "camera_id": preset.camera_id,
            "camera_name": preset.camera_name,
            "preset_index": preset.preset_index,
            "preset_name": preset.preset_name,
            "touring_time": preset.touring_time,
            "rois": rois_data,
            "created_at": to_display(preset.created_at).isoformat(),
            "updated_at": to_display(preset.updated_at).isoformat()
        }
    )


@router.post("/{camera_id}/presets", status_code=status.HTTP_201_CREATED, response_model=ApiSingleResponse[CameraPresetResponse])
async def create_camera_preset(
    camera_id: int,
    preset_data: CameraPresetCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Create a new camera preset
    """
    # Check if camera exists
    camera = (await db.execute(select(Camera).where(Camera.id == camera_id))).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Check for duplicate preset_index
    existing = (await db.execute(
        select(CameraPreset).where(
            CameraPreset.camera_id == camera_id,
            CameraPreset.preset_index == preset_data.preset_index
        )
    )).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Preset with index {preset_data.preset_index} already exists for this camera"
        )

    # Create preset
    preset = CameraPreset(
        camera_id=camera_id,
        camera_name=camera.name_device,
        preset_index=preset_data.preset_index,
        preset_name=preset_data.preset_name,
        touring_time=preset_data.touring_time
    )
    db.add(preset)
    await db.commit()
    await db.refresh(preset)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.CAMERA_PRESET,
        resource_id=preset.id,
        resource_name=f"CameraPreset-{preset.id} ({preset.preset_name})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": preset.id, "name": preset.preset_name},
        description="CameraPreset 생성"
    )

    return ApiSingleResponse(
        success=True,
        message="Camera preset created successfully",
        data={
            "id": preset.id,
            "camera_id": preset.camera_id,
            "camera_name": preset.camera_name,
            "preset_index": preset.preset_index,
            "preset_name": preset.preset_name,
            "touring_time": preset.touring_time,
            "roi_count": 0,
            "created_at": to_display(preset.created_at).isoformat(),
            "updated_at": to_display(preset.updated_at).isoformat()
        }
    )


@router.patch("/{camera_id}/presets/{preset_id}", response_model=ApiSingleResponse[CameraPresetResponse])
async def update_camera_preset(
    camera_id: int,
    preset_id: int,
    preset_data: CameraPresetUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Partially update a camera preset
    """
    # Check if camera exists
    camera = (await db.execute(select(Camera).where(Camera.id == camera_id))).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Get preset
    preset = (await db.execute(
        select(CameraPreset).where(
            CameraPreset.id == preset_id,
            CameraPreset.camera_id == camera_id
        )
    )).scalars().first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Check for duplicate preset_index if changing
    if preset_data.preset_index is not None and preset_data.preset_index != preset.preset_index:
        existing = (await db.execute(
            select(CameraPreset).where(
                CameraPreset.camera_id == camera_id,
                CameraPreset.preset_index == preset_data.preset_index,
                CameraPreset.id != preset_id
            )
        )).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Preset with index {preset_data.preset_index} already exists for this camera"
            )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(preset)

    # Update fields
    update_data = preset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preset, field, value)

    await db.commit()
    await db.refresh(preset)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(preset)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.CAMERA_PRESET,
            resource_id=preset.id,
            resource_name=f"CameraPreset-{preset.id} ({preset.preset_name})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="CameraPreset 수정"
        )

    roi_count = (await db.execute(
        select(func.count()).select_from(ROI).where(ROI.preset_id == preset.id)
    )).scalar() or 0

    return ApiSingleResponse(
        success=True,
        message="Camera preset updated successfully",
        data={
            "id": preset.id,
            "camera_id": preset.camera_id,
            "camera_name": preset.camera_name,
            "preset_index": preset.preset_index,
            "preset_name": preset.preset_name,
            "touring_time": preset.touring_time,
            "roi_count": roi_count,
            "created_at": to_display(preset.created_at).isoformat(),
            "updated_at": to_display(preset.updated_at).isoformat()
        }
    )


@router.put("/{camera_id}/presets/{preset_id}", response_model=ApiSingleResponse[CameraPresetResponse])
async def replace_camera_preset(
    camera_id: int,
    preset_id: int,
    preset_data: CameraPresetCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Replace a camera preset completely
    """
    # Check if camera exists
    camera = (await db.execute(select(Camera).where(Camera.id == camera_id))).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Get preset
    preset = (await db.execute(
        select(CameraPreset).where(
            CameraPreset.id == preset_id,
            CameraPreset.camera_id == camera_id
        )
    )).scalars().first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Check for duplicate preset_index if changing
    if preset_data.preset_index != preset.preset_index:
        existing = (await db.execute(
            select(CameraPreset).where(
                CameraPreset.camera_id == camera_id,
                CameraPreset.preset_index == preset_data.preset_index,
                CameraPreset.id != preset_id
            )
        )).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Preset with index {preset_data.preset_index} already exists for this camera"
            )

    # Replace all fields
    preset.preset_index = preset_data.preset_index
    preset.preset_name = preset_data.preset_name
    preset.touring_time = preset_data.touring_time

    await db.commit()
    await db.refresh(preset)

    roi_count = (await db.execute(
        select(func.count()).select_from(ROI).where(ROI.preset_id == preset.id)
    )).scalar() or 0

    return ApiSingleResponse(
        success=True,
        message="Camera preset replaced successfully",
        data={
            "id": preset.id,
            "camera_id": preset.camera_id,
            "camera_name": preset.camera_name,
            "preset_index": preset.preset_index,
            "preset_name": preset.preset_name,
            "touring_time": preset.touring_time,
            "roi_count": roi_count,
            "created_at": to_display(preset.created_at).isoformat(),
            "updated_at": to_display(preset.updated_at).isoformat()
        }
    )


@router.delete("/{camera_id}/presets/{preset_id}", response_model=ApiSingleResponse[None])
async def delete_camera_preset(
    camera_id: int,
    preset_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Delete a camera preset and its ROIs/points (cascade)
    """
    # Check if camera exists
    camera = (await db.execute(select(Camera).where(Camera.id == camera_id))).scalars().first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Get preset
    preset = (await db.execute(
        select(CameraPreset).where(
            CameraPreset.id == preset_id,
            CameraPreset.camera_id == camera_id
        )
    )).scalars().first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = preset.id
    deleted_identifier = {"id": preset.id, "name": preset.preset_name}
    deleted_name = f"CameraPreset-{preset.id} ({preset.preset_name})"

    # Delete preset (cascade will delete ROIs and XyPoints)
    await db.delete(preset)
    await db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.CAMERA_PRESET,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="CameraPreset 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message="Camera preset deleted successfully",
        data=None
    )
