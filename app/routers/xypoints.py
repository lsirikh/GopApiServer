"""
XyPoint API endpoints
PRD: docs/PRD_Camera_Preset_ROI.md
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.camera_preset import ROI, XyPoint
from app.schemas.camera_preset import XyPointCreate, XyPointResponse
from app.schemas.common import ApiResponse, PaginationMeta
from pydantic import BaseModel, Field


class XyPointBulkUpdate(BaseModel):
    """Schema for bulk updating points"""
    points: List[XyPointCreate] = Field(..., min_length=3, description="Minimum 3 points for polygon")


router = APIRouter(tags=["XyPoints"])


@router.get("/{roi_id}/points")
async def get_points(
    roi_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=100, description="Max items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get list of XyPoints for a specific ROI, ordered by order field
    """
    # Check if ROI exists
    roi = db.query(ROI).filter(ROI.id == roi_id).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Query points ordered by order field
    query = db.query(XyPoint).filter(XyPoint.roi_id == roi_id).order_by(XyPoint.order)
    total = query.count()

    # Pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1
    points = query.offset(skip).limit(limit).all()

    # Build response items
    items = [
        {
            "id": point.id,
            "roi_id": point.roi_id,
            "x": point.x,
            "y": point.y,
            "order": point.order,
            "created_at": point.created_at.isoformat(),
            "updated_at": point.updated_at.isoformat()
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


@router.post("/{roi_id}/points", status_code=status.HTTP_201_CREATED)
async def create_point(
    roi_id: int,
    point_data: XyPointCreate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Create a new XyPoint
    """
    # Check if ROI exists
    roi = db.query(ROI).filter(ROI.id == roi_id).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Check for duplicate order
    existing = db.query(XyPoint).filter(
        XyPoint.roi_id == roi_id,
        XyPoint.order == point_data.order
    ).first()
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
    db.commit()
    db.refresh(point)

    return ApiResponse(
        success=True,
        message="XyPoint created successfully",
        data={
            "id": point.id,
            "roi_id": point.roi_id,
            "x": point.x,
            "y": point.y,
            "order": point.order,
            "created_at": point.created_at.isoformat(),
            "updated_at": point.updated_at.isoformat()
        }
    )


@router.put("/{roi_id}/points")
async def replace_points(
    roi_id: int,
    bulk_data: XyPointBulkUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Replace all points for an ROI (bulk update)
    """
    # Check if ROI exists
    roi = db.query(ROI).filter(ROI.id == roi_id).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Delete existing points
    db.query(XyPoint).filter(XyPoint.roi_id == roi_id).delete()

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

    db.commit()

    # Refresh all points
    for point in new_points:
        db.refresh(point)

    # Build response
    points_data = [
        {
            "id": point.id,
            "roi_id": point.roi_id,
            "x": point.x,
            "y": point.y,
            "order": point.order,
            "created_at": point.created_at.isoformat(),
            "updated_at": point.updated_at.isoformat()
        }
        for point in new_points
    ]

    return ApiResponse(
        success=True,
        message="XyPoints replaced successfully",
        data={
            "roi_id": roi_id,
            "points": points_data,
            "total": len(points_data)
        }
    )


@router.delete("/{roi_id}/points/{point_id}")
async def delete_point(
    roi_id: int,
    point_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Delete a specific XyPoint
    """
    # Check if ROI exists
    roi = db.query(ROI).filter(ROI.id == roi_id).first()
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ROI with id {roi_id} not found"
        )

    # Get point
    point = db.query(XyPoint).filter(
        XyPoint.id == point_id,
        XyPoint.roi_id == roi_id
    ).first()
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point with id {point_id} not found"
        )

    # Delete point
    db.delete(point)
    db.commit()

    return ApiResponse(
        success=True,
        message="XyPoint deleted successfully",
        data=None
    )
