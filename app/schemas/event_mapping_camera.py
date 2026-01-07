"""
EventMappingCamera Schemas

PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 6

이벤트 매핑 카메라 연동 설정을 위한 Pydantic 스키마입니다.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.device import (
    CameraUrls,
    HardwareSpec,
    Geolocation,
    DeviceGroupNestedResponse
)


# ============================================================
# Nested Response Schemas (Full Property, timestamp 제외)
# PRD: Nested Response 규칙
# ============================================================

class CameraNestedResponse(BaseModel):
    """
    카메라 Nested 응답 - Full Property (timestamp 제외)

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.1
    PRD: PRD_Camera_Urls_JsonB.md
    - rtsp_uri, rtsp_port 제거
    - urls JSONB 필드로 통합
    """
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: Optional[str] = None
    status: str
    ip_address: str
    ip_port: int
    mode: str
    category: str
    is_record: bool = False
    hardware_spec: Optional[HardwareSpec] = None
    geolocation: Optional[Geolocation] = None
    urls: Optional[CameraUrls] = None
    device_groups: List[DeviceGroupNestedResponse] = Field(default=[])

    model_config = ConfigDict(from_attributes=True)


class PresetNestedResponse(BaseModel):
    """
    프리셋 Nested 응답 - Full Property (timestamp 제외)

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.1
    """
    id: int
    camera_id: int
    camera_name: str
    preset_index: int
    preset_name: str
    touring_time: int = 0

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Create/Update Schemas
# ============================================================

class EventMappingCameraCreate(BaseModel):
    """
    카메라 연동 생성 스키마

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.2
    """
    camera_id: int = Field(..., description="대상 카메라 ID")
    target_preset_id: Optional[int] = Field(None, description="이벤트 발생 시 이동할 프리셋 ID")
    home_preset_id: Optional[int] = Field(None, description="홈 복귀 프리셋 ID")
    delay_time: int = Field(0, ge=0, description="target_preset 도착 후 대기 시간 (초)")
    is_enable: bool = Field(True, description="활성화 여부")
    priority: Optional[int] = Field(None, ge=0, description="실행 우선순위 (Optional)")


class EventMappingCameraUpdate(BaseModel):
    """
    카메라 연동 수정 스키마 (PATCH)

    모든 필드가 Optional이므로 부분 업데이트 가능
    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.3
    """
    camera_id: Optional[int] = None
    target_preset_id: Optional[int] = None
    home_preset_id: Optional[int] = None
    delay_time: Optional[int] = Field(None, ge=0)
    is_enable: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


# ============================================================
# Response Schemas
# ============================================================

class EventMappingCameraResponse(BaseModel):
    """
    카메라 연동 응답 스키마 (주체용 - timestamp 포함)

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.1
    Nested Response 규칙:
    - 주체(EventMappingCamera): created_at, updated_at 포함
    - Nested 객체(camera, target_preset, home_preset): Full Property, timestamp 제외
    """
    id: int
    event_mapping_id: int
    camera: Optional[CameraNestedResponse] = None
    target_preset: Optional[PresetNestedResponse] = None
    home_preset: Optional[PresetNestedResponse] = None
    delay_time: int
    is_enable: bool
    priority: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventMappingCameraNestedResponse(BaseModel):
    """
    카메라 연동 Nested 응답 (EventMapping 내 nested용 - timestamp 제외)

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 6.1
    EventMapping 내부에서 nested로 사용될 때 timestamp 제외
    """
    id: int
    camera: Optional[CameraNestedResponse] = None
    target_preset: Optional[PresetNestedResponse] = None
    home_preset: Optional[PresetNestedResponse] = None
    delay_time: int
    is_enable: bool
    priority: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# List Response Schema
# ============================================================

class EventMappingCameraListResponse(BaseModel):
    """
    카메라 연동 목록 응답 스키마

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.1
    """
    items: List[EventMappingCameraResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
