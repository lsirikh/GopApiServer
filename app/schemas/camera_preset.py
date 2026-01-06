"""
Camera Preset, ROI, XyPoint schemas
PRD: docs/PRD_Camera_Preset_ROI.md
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============================================================
# XyPoint Schemas
# ============================================================

class XyPointBase(BaseModel):
    """Base schema for XyPoint"""
    x: float = Field(..., description="X coordinate (0.0 ~ 1.0 normalized or pixel)")
    y: float = Field(..., description="Y coordinate (0.0 ~ 1.0 normalized or pixel)")
    order: int = Field(..., description="Point order for drawing polygon")


class XyPointCreate(XyPointBase):
    """Schema for creating XyPoint"""
    pass


class XyPointResponse(XyPointBase):
    """Schema for XyPoint response (주체용 - timestamp 포함)"""
    id: int

    model_config = ConfigDict(from_attributes=True)


class XyPointNestedResponse(XyPointBase):
    """Schema for XyPoint nested response (v2.10: timestamp 제외)"""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ROI Schemas
# ============================================================

class ROIBase(BaseModel):
    """Base schema for ROI"""
    name: str = Field(..., max_length=100, description="ROI display name")
    resolution_width: float = Field(..., description="Reference resolution width")
    resolution_height: float = Field(..., description="Reference resolution height")
    is_enable: bool = Field(default=True, description="Whether ROI is active")


class ROICreate(ROIBase):
    """Schema for creating ROI"""
    points: Optional[List[XyPointCreate]] = Field(default=None, description="Polygon vertices")


class ROIUpdate(BaseModel):
    """Schema for updating ROI (PATCH)"""
    name: Optional[str] = Field(default=None, max_length=100)
    resolution_width: Optional[float] = None
    resolution_height: Optional[float] = None
    is_enable: Optional[bool] = None


class ROIResponse(ROIBase):
    """Schema for ROI response (list view) - 주체용"""
    id: int
    preset_id: int
    point_count: int = Field(default=0, description="Number of polygon vertices")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ROIListNestedResponse(ROIBase):
    """Schema for ROI list nested response (v2.10: Preset 내 nested 목록 - timestamp 제외)"""
    id: int
    preset_id: int
    point_count: int = Field(default=0, description="Number of polygon vertices")

    model_config = ConfigDict(from_attributes=True)


class ROIDetailResponse(ROIBase):
    """Schema for ROI detail response (with points) - 주체용"""
    id: int
    preset_id: int
    points: List[XyPointNestedResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ROINestedResponse(ROIBase):
    """Schema for ROI nested response (v2.10: Preset 내 nested - timestamp 제외)"""
    id: int
    preset_id: int
    points: List[XyPointNestedResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# CameraPreset Schemas
# ============================================================

class CameraPresetBase(BaseModel):
    """Base schema for CameraPreset"""
    preset_index: int = Field(..., description="Preset index within camera")
    preset_name: str = Field(..., max_length=100, description="Preset display name")
    touring_time: int = Field(default=10, description="Time to move from Home to preset (seconds)")


class CameraPresetCreate(CameraPresetBase):
    """Schema for creating CameraPreset"""
    pass


class CameraPresetUpdate(BaseModel):
    """Schema for updating CameraPreset (PATCH)"""
    preset_index: Optional[int] = None
    preset_name: Optional[str] = Field(default=None, max_length=100)
    touring_time: Optional[int] = None


class CameraPresetResponse(CameraPresetBase):
    """Schema for CameraPreset response (list view)"""
    id: int
    camera_id: int
    camera_name: str
    roi_count: int = Field(default=0, description="Number of ROIs in preset")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraPresetWithROIsResponse(CameraPresetResponse):
    """Schema for CameraPreset response with ROIs (include_rois=true)

    v2.10: Nested Response 규칙 적용 - rois에서 timestamp 제외
    """
    rois: List[ROIListNestedResponse] = Field(default_factory=list)


class CameraPresetDetailResponse(CameraPresetBase):
    """Schema for CameraPreset detail response (with ROIs and points)

    v2.10: Nested Response 규칙 적용 - rois에서 timestamp 제외
    """
    id: int
    camera_id: int
    camera_name: str
    rois: List[ROINestedResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
