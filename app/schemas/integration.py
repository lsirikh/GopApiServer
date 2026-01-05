"""
Integration schemas: EventMapping, CameraEventMapping, CameraEventPreset
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


# ============================================
# Phase 28: CameraUrls Schema
# ============================================

class CameraUrls(BaseModel):
    """Schema for camera URL configuration (live/record streams)"""
    live: Optional[str] = None
    record: Optional[str] = None


class EventMappingCreate(BaseModel):
    """
    Schema for creating a new EventMapping

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - group_event 필드 제거됨
    - device_group_id: DeviceGroup FK
    """
    name_event: str
    device_group_id: Optional[int] = None
    category_event: str
    description: Optional[str] = None
    status: bool = True


class EventMappingResponse(BaseModel):
    """
    Schema for EventMapping response

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - group_event 필드 제거됨
    - device_group_id: DeviceGroup FK
    """
    id: int
    name_event: str
    device_group_id: Optional[int] = None
    category_event: str
    description: Optional[str]
    status: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventMappingUpdate(BaseModel):
    """
    Schema for updating an EventMapping (all fields optional for PATCH)

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - group_event 필드 제거됨
    """
    name_event: Optional[str] = None
    device_group_id: Optional[int] = None
    category_event: Optional[str] = None
    description: Optional[str] = None
    status: Optional[bool] = None


# ============================================
# CameraEventMapping and CameraEventPreset Schemas
# ============================================

class CameraEventPresetCreate(BaseModel):
    """Schema for creating a new CameraEventPreset"""
    cam_id: int
    urls: Optional[CameraUrls] = None  # Phase 28: Changed from rtsp_uri
    category: str
    preset_id: Optional[str] = None
    preset_time: int = 0
    home_preset: int = 0
    home_time: int = 0


class CameraEventPresetResponse(BaseModel):
    """Schema for CameraEventPreset response"""
    id: int
    cam_id: int
    urls: Optional[CameraUrls] = None  # Phase 28: Changed from rtsp_uri
    category: str
    preset_id: Optional[str]
    preset_time: int
    home_preset: int
    home_time: int

    model_config = ConfigDict(from_attributes=True)


class CameraEventMappingCreate(BaseModel):
    """Schema for creating a new CameraEventMapping"""
    name_event: str
    group_event: str
    category_event: str
    description: Optional[str] = None
    status: bool = True
    camera_presets: List[CameraEventPresetCreate] = []


class CameraEventMappingResponse(BaseModel):
    """Schema for CameraEventMapping response"""
    id: int
    name_event: str
    group_event: str
    category_event: str
    description: Optional[str]
    status: bool
    camera_presets: List[CameraEventPresetResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraEventMappingUpdate(BaseModel):
    """Schema for updating a CameraEventMapping (all fields optional for PATCH)"""
    name_event: Optional[str] = None
    group_event: Optional[str] = None
    category_event: Optional[str] = None
    description: Optional[str] = None
    status: Optional[bool] = None
    camera_presets: Optional[List[CameraEventPresetCreate]] = None
