"""
ROI API endpoints
PRD: docs/PRD_Camera_Preset_ROI.md
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.camera_preset import CameraPreset, ROI, XyPoint
from app.schemas.camera_preset import (
    ROICreate,
    ROIResponse,
    ROIDetailResponse,
    ROIUpdate
)
from app.schemas.common import ApiResponse, PaginationMeta
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change, get_identifier, get_changed_fields, model_to_dict

router = APIRouter(tags=["ROIs"])


@router.get("/{preset_id}/rois")
async def get_rois(
    preset_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Max items per page"),
    include_points: bool = Query(False, description="Include points in response"),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get list of ROIs for a specific preset
    """
    # Check if preset exists
    preset = db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Query ROIs
    query = db.query(ROI).filter(ROI.preset_id == preset_id)
    total = query.count()

    # Pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1
    rois = query.offset(skip).limit(limit).all()

    # Build response items
    items = []
    for roi in rois:
        point_count = roi.points.count()
        item = {
            "id": roi.id,
            "preset_id": roi.preset_id,
            "name": roi.name,
            "resolution_width": roi.resolution_width,
            "resolution_height": roi.resolution_height,
            "is_enable": roi.is_enable,
            "point_count": point_count,
            "created_at": roi.created_at.isoformat(),
            "updated_at": roi.updated_at.isoformat()
        }

        # Include points if requested
        if include_points:
            item["points"] = [
                {
                    "id": point.id,
                    "x": point.x,
                    "y": point.y,
                    "order": point.order
                }
                for point in roi.points.order_by(XyPoint.order).all()
            ]

        items.append(item)

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="ROIs retrieved successfully",
        data={
            "items": items,
            "total": total
        },
        pagination=pagination
    )


@router.get("/{preset_id}/rois/{roi_id}")
async def get_roi(
    preset_id: int,
    roi_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get a specific ROI with points
    """
    # Check if preset exists
    preset = db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Get ROI
    roi = db.query(ROI).filter(
        ROI.id == roi_id,
        ROI.preset_id == preset_id
    ).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Build points data
    points_data = [
        {
            "id": point.id,
            "x": point.x,
            "y": point.y,
            "order": point.order
        }
        for point in roi.points.all()
    ]

    return ApiResponse(
        success=True,
        message="ROI retrieved successfully",
        data={
            "id": roi.id,
            "preset_id": roi.preset_id,
            "name": roi.name,
            "resolution_width": roi.resolution_width,
            "resolution_height": roi.resolution_height,
            "is_enable": roi.is_enable,
            "points": points_data,
            "created_at": roi.created_at.isoformat(),
            "updated_at": roi.updated_at.isoformat()
        }
    )


@router.post("/{preset_id}/rois", status_code=status.HTTP_201_CREATED)
async def create_roi(
    preset_id: int,
    roi_data: ROICreate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Create a new ROI
    """
    # Check if preset exists
    preset = db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Create ROI
    roi = ROI(
        preset_id=preset_id,
        name=roi_data.name,
        resolution_width=roi_data.resolution_width,
        resolution_height=roi_data.resolution_height,
        is_enable=roi_data.is_enable if roi_data.is_enable is not None else True
    )
    db.add(roi)
    db.commit()
    db.refresh(roi)

    # Create points if provided
    if roi_data.points:
        for point_data in roi_data.points:
            point = XyPoint(
                roi_id=roi.id,
                x=point_data.x,
                y=point_data.y,
                order=point_data.order
            )
            db.add(point)
        db.commit()
        db.refresh(roi)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.ROI,
        resource_id=roi.id,
        resource_name=f"ROI-{roi.id} ({roi.name})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": roi.id, "name": roi.name},
        description="ROI 생성"
    )

    point_count = roi.points.count()

    return ApiResponse(
        success=True,
        message="ROI created successfully",
        data={
            "id": roi.id,
            "preset_id": roi.preset_id,
            "name": roi.name,
            "resolution_width": roi.resolution_width,
            "resolution_height": roi.resolution_height,
            "is_enable": roi.is_enable,
            "point_count": point_count,
            "created_at": roi.created_at.isoformat(),
            "updated_at": roi.updated_at.isoformat()
        }
    )


@router.patch("/{preset_id}/rois/{roi_id}")
async def update_roi(
    preset_id: int,
    roi_id: int,
    roi_data: ROIUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Partially update an ROI
    """
    # Check if preset exists
    preset = db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Get ROI
    roi = db.query(ROI).filter(
        ROI.id == roi_id,
        ROI.preset_id == preset_id
    ).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(roi)

    # Update fields
    update_data = roi_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(roi, field, value)

    db.commit()
    db.refresh(roi)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(roi)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.ROI,
            resource_id=roi.id,
            resource_name=f"ROI-{roi.id} ({roi.name})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="ROI 수정"
        )

    return ApiResponse(
        success=True,
        message="ROI updated successfully",
        data={
            "id": roi.id,
            "preset_id": roi.preset_id,
            "name": roi.name,
            "resolution_width": roi.resolution_width,
            "resolution_height": roi.resolution_height,
            "is_enable": roi.is_enable,
            "point_count": roi.points.count(),
            "created_at": roi.created_at.isoformat(),
            "updated_at": roi.updated_at.isoformat()
        }
    )


@router.put("/{preset_id}/rois/{roi_id}")
async def replace_roi(
    preset_id: int,
    roi_id: int,
    roi_data: ROICreate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Replace an ROI completely
    """
    # Check if preset exists
    preset = db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Get ROI
    roi = db.query(ROI).filter(
        ROI.id == roi_id,
        ROI.preset_id == preset_id
    ).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Replace all fields
    roi.name = roi_data.name
    roi.resolution_width = roi_data.resolution_width
    roi.resolution_height = roi_data.resolution_height
    roi.is_enable = roi_data.is_enable if roi_data.is_enable is not None else True

    db.commit()
    db.refresh(roi)

    return ApiResponse(
        success=True,
        message="ROI replaced successfully",
        data={
            "id": roi.id,
            "preset_id": roi.preset_id,
            "name": roi.name,
            "resolution_width": roi.resolution_width,
            "resolution_height": roi.resolution_height,
            "is_enable": roi.is_enable,
            "point_count": roi.points.count(),
            "created_at": roi.created_at.isoformat(),
            "updated_at": roi.updated_at.isoformat()
        }
    )


@router.delete("/{preset_id}/rois/{roi_id}")
async def delete_roi(
    preset_id: int,
    roi_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Delete an ROI and its points (cascade)
    """
    # Check if preset exists
    preset = db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset with id {preset_id} not found"
        )

    # Get ROI
    roi = db.query(ROI).filter(
        ROI.id == roi_id,
        ROI.preset_id == preset_id
    ).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = roi.id
    deleted_identifier = {"id": roi.id, "name": roi.name}
    deleted_name = f"ROI-{roi.id} ({roi.name})"

    # Delete ROI (cascade will delete XyPoints)
    db.delete(roi)
    db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.ROI,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="ROI 삭제"
    )

    return ApiResponse(
        success=True,
        message="ROI deleted successfully",
        data=None
    )
