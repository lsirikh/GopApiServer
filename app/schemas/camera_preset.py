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


class XyPointResponse(BaseModel):
    """Schema for XyPoint response (주체용 - timestamp 포함)

    문서 순서대로 필드 정의
    """
    id: int
    x: float = Field(..., description="X coordinate (0.0 ~ 1.0 normalized or pixel)")
    y: float = Field(..., description="Y coordinate (0.0 ~ 1.0 normalized or pixel)")
    order: int = Field(..., description="Point order for drawing polygon")

    model_config = ConfigDict(from_attributes=True)


class XyPointNestedResponse(BaseModel):
    """Schema for XyPoint nested response (v2.10: timestamp 제외)

    문서 순서대로 필드 정의
    """
    id: int
    x: float = Field(..., description="X coordinate (0.0 ~ 1.0 normalized or pixel)")
    y: float = Field(..., description="Y coordinate (0.0 ~ 1.0 normalized or pixel)")
    order: int = Field(..., description="Point order for drawing polygon")

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
    points: List[XyPointCreate] = Field(..., min_length=3, description="Polygon vertices (minimum 3 points for polygon)")


class ROIUpdate(BaseModel):
    """Schema for updating ROI (PATCH)"""
    name: Optional[str] = Field(default=None, max_length=100)
    resolution_width: Optional[float] = None
    resolution_height: Optional[float] = None
    is_enable: Optional[bool] = None


class ROIResponse(BaseModel):
    """Schema for ROI response (list view) - 주체용

    문서 순서대로 필드 정의
    """
    id: int
    preset_id: int
    name: str = Field(..., max_length=100, description="ROI display name")
    resolution_width: float = Field(..., description="Reference resolution width")
    resolution_height: float = Field(..., description="Reference resolution height")
    is_enable: bool = Field(default=True, description="Whether ROI is active")
    point_count: int = Field(default=0, description="Number of polygon vertices")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ROIListNestedResponse(BaseModel):
    """Schema for ROI list nested response (v2.10: Preset 내 nested 목록 - timestamp 제외)

    문서 순서대로 필드 정의
    """
    id: int
    name: str = Field(..., max_length=100, description="ROI display name")
    resolution_width: float = Field(..., description="Reference resolution width")
    resolution_height: float = Field(..., description="Reference resolution height")
    is_enable: bool = Field(default=True, description="Whether ROI is active")
    point_count: int = Field(default=0, description="Number of polygon vertices")

    model_config = ConfigDict(from_attributes=True)


class ROIDetailResponse(BaseModel):
    """Schema for ROI detail response (with points) - 주체용

    문서 순서대로 필드 정의
    """
    id: int
    preset_id: int
    name: str = Field(..., max_length=100, description="ROI display name")
    resolution_width: float = Field(..., description="Reference resolution width")
    resolution_height: float = Field(..., description="Reference resolution height")
    is_enable: bool = Field(default=True, description="Whether ROI is active")
    points: List[XyPointNestedResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ROINestedResponse(BaseModel):
    """Schema for ROI nested response (v2.10: Preset 내 nested - timestamp 제외)

    문서 순서대로 필드 정의
    """
    id: int
    preset_id: int
    name: str = Field(..., max_length=100, description="ROI display name")
    resolution_width: float = Field(..., description="Reference resolution width")
    resolution_height: float = Field(..., description="Reference resolution height")
    is_enable: bool = Field(default=True, description="Whether ROI is active")
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


class CameraPresetResponse(BaseModel):
    """Schema for CameraPreset response (list view)

    문서 순서대로 필드 정의
    """
    id: int
    camera_id: int
    camera_name: str
    preset_index: int = Field(..., description="Preset index within camera")
    preset_name: str = Field(..., max_length=100, description="Preset display name")
    touring_time: int = Field(default=10, description="Time to move from Home to preset (seconds)")
    roi_count: int = Field(default=0, description="Number of ROIs in preset")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraPresetWithROIsResponse(CameraPresetResponse):
    """Schema for CameraPreset response with ROIs (include_rois=true)

    v2.10: Nested Response 규칙 적용 - rois에서 timestamp 제외
    """
    rois: List[ROIListNestedResponse] = Field(default_factory=list)


class CameraPresetNestedResponse(CameraPresetBase):
    """Schema for CameraPreset nested response (Camera내 nested - timestamp 제외)

    PRD: PRD_API_Gap_Analysis.md (IMP-001, IMP-002)
    Camera 단일 조회 시 include_presets=true 응답에 사용

    v2.11: Nested Response 규칙 적용
    - created_at, updated_at 제외 (Nested 객체이므로)
    - rois는 선택적 (include_rois=true일 때만 포함)
    """
    id: int
    camera_id: int
    roi_count: int = Field(default=0, description="Number of ROIs in preset")
    rois: List[ROIListNestedResponse] = Field(default_factory=list, description="ROIs (include_rois=true일 때만 포함)")

    model_config = ConfigDict(from_attributes=True)


class CameraPresetDetailResponse(BaseModel):
    """Schema for CameraPreset detail response (with ROIs and points)

    v2.10: Nested Response 규칙 적용 - rois에서 timestamp 제외
    문서 순서대로 필드 정의
    """
    id: int
    camera_id: int
    camera_name: str
    preset_index: int = Field(..., description="Preset index within camera")
    preset_name: str = Field(..., max_length=100, description="Preset display name")
    touring_time: int = Field(default=10, description="Time to move from Home to preset (seconds)")
    rois: List[ROINestedResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# List Response Schemas (for Swagger documentation)
# ============================================================

class ROIListNestedResponseWithPoints(BaseModel):
    """Schema for ROI nested response with points (include_points=true)

    문서 순서대로 필드 정의
    """
    id: int
    preset_id: int
    name: str = Field(..., max_length=100, description="ROI display name")
    resolution_width: float = Field(..., description="Reference resolution width")
    resolution_height: float = Field(..., description="Reference resolution height")
    is_enable: bool = Field(default=True, description="Whether ROI is active")
    point_count: int = Field(default=0, description="Number of polygon vertices")
    points: List[XyPointNestedResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraPresetListItem(BaseModel):
    """Schema for CameraPreset list item (문서 순서대로 필드 정의)"""
    id: int
    camera_id: int
    camera_name: str
    preset_index: int = Field(..., description="Preset index within camera")
    preset_name: str = Field(..., max_length=100, description="Preset display name")
    touring_time: int = Field(default=10, description="Time to move from Home to preset (seconds)")
    roi_count: int = Field(default=0, description="Number of ROIs in preset")
    created_at: datetime
    updated_at: datetime
    rois: Optional[List[ROIListNestedResponse]] = Field(default=None, description="ROIs (include_rois=true일 때만 포함)")

    model_config = ConfigDict(from_attributes=True)


class CameraPresetListData(BaseModel):
    """Data structure for CameraPreset list response"""
    items: List[CameraPresetListItem]
    total: int


class ROIListItem(BaseModel):
    """Schema for ROI list item (문서 순서대로 필드 정의)"""
    id: int
    preset_id: int
    name: str = Field(..., max_length=100, description="ROI display name")
    resolution_width: float = Field(..., description="Reference resolution width")
    resolution_height: float = Field(..., description="Reference resolution height")
    is_enable: bool = Field(default=True, description="Whether ROI is active")
    point_count: int = Field(default=0, description="Number of polygon vertices")
    created_at: datetime
    updated_at: datetime
    points: Optional[List[XyPointNestedResponse]] = Field(default=None, description="Points (include_points=true일 때만 포함)")

    model_config = ConfigDict(from_attributes=True)


class ROIListData(BaseModel):
    """Data structure for ROI list response"""
    items: List[ROIListItem]
    total: int


class XyPointListItem(BaseModel):
    """Schema for XyPoint list item"""
    id: int
    roi_id: int
    x: float
    y: float
    order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class XyPointListData(BaseModel):
    """Data structure for XyPoint list response"""
    items: List[XyPointListItem]
    total: int


class XyPointBulkReplaceData(BaseModel):
    """Data structure for XyPoint bulk replace response"""
    roi_id: int
    points: List[XyPointListItem]
    total: int
