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
)


# ============================================================
# ProxySetting Schemas
# ============================================================

class ProxySettingUpdate(BaseModel):
    """Schema for updating ProxySetting (all fields optional for PATCH)"""
    operation_mode: Optional[EnumOperationMode] = Field(None, description="운용 모드")
    windy_mode: Optional[EnumWindyMode] = Field(None, description="풍량 모드")


class ProxySettingResponse(BaseModel):
    """Schema for ProxySetting response"""
    id: int = Field(..., description="설정 ID")
    server_id: int = Field(..., description="서버 ID")
    operation_mode: str = Field(..., description="운용 모드 (NORMAL/REGISTER)")
    windy_mode: str = Field(..., description="풍량 모드 (wind0~wind3)")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# CameraSetting Schemas
# ============================================================

class CameraSettingUpdate(BaseModel):
    """Schema for updating CameraSetting (all fields optional for PATCH)"""
    weather_mode: Optional[EnumWeatherMode] = Field(None, description="악천후 모드")
    camera_mode: Optional[EnumCameraVideoMode] = Field(None, description="카메라 영상 모드")
    heater: Optional[EnumOnOff] = Field(None, description="열선 상태")
    fan: Optional[EnumOnOff] = Field(None, description="냉각팬 상태")
    headlight: Optional[EnumOnOff] = Field(None, description="전조등 상태")
    day_night_mode: Optional[EnumDayNightMode] = Field(None, description="주/야간 모드")
    pan_tilt_speed: Optional[int] = Field(None, ge=0, le=100, description="팬/틸트 속도 (0-100)")
    zoom_speed: Optional[int] = Field(None, ge=0, le=100, description="줌 속도 (0-100)")
    palette: Optional[EnumPalette] = Field(None, description="열화상 팔레트")


class CameraSettingResponse(BaseModel):
    """Schema for CameraSetting response"""
    id: int = Field(..., description="설정 ID")
    camera_id: int = Field(..., description="카메라 ID")
    weather_mode: str = Field(..., description="악천후 모드")
    camera_mode: str = Field(..., description="카메라 영상 모드")
    heater: str = Field(..., description="열선 상태 (on/off)")
    fan: str = Field(..., description="냉각팬 상태 (on/off)")
    headlight: str = Field(..., description="전조등 상태 (on/off)")
    day_night_mode: str = Field(..., description="주/야간 모드 (AUTO/DAY/NIGHT)")
    pan_tilt_speed: int = Field(..., description="팬/틸트 속도 (0-100)")
    zoom_speed: int = Field(..., description="줌 속도 (0-100)")
    palette: Optional[str] = Field(None, description="열화상 팔레트 (열화상 카메라만)")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)
