"""
Device Setting Schemas
PRD: PRD_Device_Setting.md Section 4
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import (
    EnumOperationMode, EnumWindyMode,
    EnumWeatherMode, EnumCameraVideoMode, EnumOnOff,
    EnumDayNightMode, EnumPalette,
    EnumFocusMode, EnumIrisMode,
)


def _nullable_palette_schema(schema: dict) -> None:
    """Replace anyOf with inline enum for Swagger UI dropdown compatibility."""
    schema.pop("anyOf", None)
    schema["enum"] = [e.value for e in EnumPalette] + [None]


# ============================================================
# ProxySetting Schemas
# ============================================================

class ProxySettingCreate(BaseModel):
    """Schema for replacing ProxySetting via PUT (all fields required)"""
    operation_mode: EnumOperationMode = Field(..., description="운용 모드")
    windy_mode: EnumWindyMode = Field(..., description="풍량 모드")


class ProxySettingUpdate(BaseModel):
    """Schema for updating ProxySetting (all fields optional for PATCH)"""
    operation_mode: Optional[EnumOperationMode] = Field(None, description="운용 모드")
    windy_mode: Optional[EnumWindyMode] = Field(None, description="풍량 모드")


class ProxySettingResponse(BaseModel):
    """Schema for ProxySetting response"""
    id: int = Field(..., description="설정 ID")
    server_id: int = Field(..., description="서버 ID")
    operation_mode: EnumOperationMode = Field(..., description="운용 모드")
    windy_mode: EnumWindyMode = Field(..., description="풍량 모드")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# CameraSetting Schemas
# ============================================================

class CameraSettingCreate(BaseModel):
    """Schema for replacing CameraSetting via PUT (all fields required except palette)"""
    weather_mode: EnumWeatherMode = Field(..., description="악천후 모드")
    camera_mode: EnumCameraVideoMode = Field(..., description="카메라 영상 모드")
    heater: EnumOnOff = Field(..., description="열선 상태")
    fan: EnumOnOff = Field(..., description="냉각팬 상태")
    headlight: EnumOnOff = Field(..., description="전조등 상태")
    day_night_mode: EnumDayNightMode = Field(..., description="주/야간 모드")
    focus_mode: EnumFocusMode = Field(..., description="초점 모드")
    iris_mode: EnumIrisMode = Field(..., description="조리개 모드")
    pan_tilt_speed: int = Field(..., ge=0, le=100, description="팬/틸트 속도 (0-100)")
    zoom_speed: int = Field(..., ge=0, le=100, description="줌 속도 (0-100)")
    palette: Optional[EnumPalette] = Field(None, description="열화상 팔레트 (nullable)", json_schema_extra=_nullable_palette_schema)


class CameraSettingUpdate(BaseModel):
    """Schema for updating CameraSetting (all fields optional for PATCH)"""
    weather_mode: Optional[EnumWeatherMode] = Field(None, description="악천후 모드")
    camera_mode: Optional[EnumCameraVideoMode] = Field(None, description="카메라 영상 모드")
    heater: Optional[EnumOnOff] = Field(None, description="열선 상태")
    fan: Optional[EnumOnOff] = Field(None, description="냉각팬 상태")
    headlight: Optional[EnumOnOff] = Field(None, description="전조등 상태")
    day_night_mode: Optional[EnumDayNightMode] = Field(None, description="주/야간 모드")
    focus_mode: Optional[EnumFocusMode] = Field(None, description="초점 모드")
    iris_mode: Optional[EnumIrisMode] = Field(None, description="조리개 모드")
    pan_tilt_speed: Optional[int] = Field(None, ge=0, le=100, description="팬/틸트 속도 (0-100)")
    zoom_speed: Optional[int] = Field(None, ge=0, le=100, description="줌 속도 (0-100)")
    palette: Optional[EnumPalette] = Field(None, description="열화상 팔레트", json_schema_extra=_nullable_palette_schema)


class CameraSettingResponse(BaseModel):
    """Schema for CameraSetting response"""
    id: int = Field(..., description="설정 ID")
    camera_id: int = Field(..., description="카메라 ID")
    weather_mode: EnumWeatherMode = Field(..., description="악천후 모드")
    camera_mode: EnumCameraVideoMode = Field(..., description="카메라 영상 모드")
    heater: EnumOnOff = Field(..., description="열선 상태")
    fan: EnumOnOff = Field(..., description="냉각팬 상태")
    headlight: EnumOnOff = Field(..., description="전조등 상태")
    day_night_mode: EnumDayNightMode = Field(..., description="주/야간 모드")
    focus_mode: EnumFocusMode = Field(..., description="초점 모드")
    iris_mode: EnumIrisMode = Field(..., description="조리개 모드")
    pan_tilt_speed: int = Field(..., description="팬/틸트 속도 (0-100)")
    zoom_speed: int = Field(..., description="줌 속도 (0-100)")
    palette: Optional[EnumPalette] = Field(None, description="열화상 팔레트 (열화상 카메라만, nullable)", json_schema_extra=_nullable_palette_schema)
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)
