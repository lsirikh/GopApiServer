"""
XyPoint API endpoints
PRD: docs/PRD_Camera_Preset_ROI.md
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
import math

from app.dependencies import get_async_db
from app.utils.datetime import to_display
from app.routers.auth import get_current_account_user_optional_async
from app.models.camera_preset import ROI, XyPoint
from app.schemas.camera_preset import XyPointCreate, XyPointResponse, XyPointListData, XyPointListItem, XyPointBulkReplaceData
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from pydantic import BaseModel, Field
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change_async


class XyPointBulkUpdate(BaseModel):
    """Schema for bulk updating points"""
    points: List[XyPointCreate] = Field(..., min_length=3, description="Minimum 3 points for polygon")


router = APIRouter()


@router.get("/{roi_id}/points", response_model=ApiResponse[XyPointListData])
async def get_points(
    roi_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=100, description="Max items per page"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Get list of XyPoints for a specific ROI, ordered by order field
    """
    # Check if ROI exists
    roi = (await db.execute(select(ROI).where(ROI.id == roi_id))).scalars().first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Count total
    count_stmt = select(func.count()).select_from(XyPoint).where(XyPoint.roi_id == roi_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    # Pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    points_stmt = (
        select(XyPoint)
        .where(XyPoint.roi_id == roi_id)
        .order_by(XyPoint.id)
        .offset(skip)
        .limit(limit)
    )
    points = (await db.execute(points_stmt)).scalars().all()

    # Build response items
    items = [
        {
            "id": point.id,
            "roi_id": point.roi_id,
            "x": point.x,
            "y": point.y,
            "order": point.order,
            "created_at": to_display(point.created_at).isoformat(),
            "updated_at": to_display(point.updated_at).isoformat()
        }
        for point in points
    ]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="XyPoints retrieved successfully",
        data={
            "items": items,
            "total": total
        },
        pagination=pagination
    )


@router.post("/{roi_id}/points", status_code=status.HTTP_201_CREATED, response_model=ApiSingleResponse[XyPointListItem])
async def create_point(
    roi_id: int,
    point_data: XyPointCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Create a new XyPoint
    """
    # Check if ROI exists
    roi = (await db.execute(select(ROI).where(ROI.id == roi_id))).scalars().first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Check for duplicate order
    existing_stmt = select(XyPoint).where(
        XyPoint.roi_id == roi_id,
        XyPoint.order == point_data.order
    )
    existing = (await db.execute(existing_stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Point with order {point_data.order} already exists for this ROI"
        )

    # Create point
    point = XyPoint(
        roi_id=roi_id,
        x=point_data.x,
        y=point_data.y,
        order=point_data.order
    )
    db.add(point)
    await db.commit()
    await db.refresh(point)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.XY_POINT,
        resource_id=point.id,
        resource_name=f"XyPoint-{point.id} (order: {point.order})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": point.id, "order": point.order},
        description="XyPoint 생성"
    )

    return ApiSingleResponse(
        success=True,
        message="XyPoint created successfully",
        data={
            "id": point.id,
            "roi_id": point.roi_id,
            "x": point.x,
            "y": point.y,
            "order": point.order,
            "created_at": to_display(point.created_at).isoformat(),
            "updated_at": to_display(point.updated_at).isoformat()
        }
    )


@router.put("/{roi_id}/points", response_model=ApiSingleResponse[XyPointBulkReplaceData])
async def replace_points(
    roi_id: int,
    bulk_data: XyPointBulkUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Replace all points for an ROI (bulk update)
    """
    # Check if ROI exists
    roi = (await db.execute(select(ROI).where(ROI.id == roi_id))).scalars().first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Delete existing points
    await db.execute(delete(XyPoint).where(XyPoint.roi_id == roi_id))

    # Create new points
    new_points = []
    for point_data in bulk_data.points:
        point = XyPoint(
            roi_id=roi_id,
            x=point_data.x,
            y=point_data.y,
            order=point_data.order
        )
        db.add(point)
        new_points.append(point)

    await db.commit()

    # Refresh all points
    for point in new_points:
        await db.refresh(point)

    # Build response
    points_data = [
        {
            "id": point.id,
            "roi_id": point.roi_id,
            "x": point.x,
            "y": point.y,
            "order": point.order,
            "created_at": to_display(point.created_at).isoformat(),
            "updated_at": to_display(point.updated_at).isoformat()
        }
        for point in new_points
    ]

    return ApiSingleResponse(
        success=True,
        message="XyPoints replaced successfully",
        data={
            "roi_id": roi_id,
            "points": points_data,
            "total": len(points_data)
        }
    )


@router.delete("/{roi_id}/points/{point_id}", response_model=ApiSingleResponse[None])
async def delete_point(
    roi_id: int,
    point_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_account_user_optional_async)
):
    """
    Delete a specific XyPoint
    """
    # Check if ROI exists
    roi = (await db.execute(select(ROI).where(ROI.id == roi_id))).scalars().first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Get point
    point_stmt = select(XyPoint).where(
        XyPoint.id == point_id,
        XyPoint.roi_id == roi_id
    )
    point = (await db.execute(point_stmt)).scalars().first()
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point with id {point_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = point.id
    deleted_identifier = {"id": point.id, "order": point.order}
    deleted_name = f"XyPoint-{point.id} (order: {point.order})"

    # Delete point
    await db.delete(point)
    await db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.XY_POINT,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="XyPoint 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message="XyPoint deleted successfully",
        data=None
    )
