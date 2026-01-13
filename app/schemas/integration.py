"""
Integration schemas: EventMapping, EventMappingCamera

PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
PRD: PRD_CameraEventMapping_Refactoring.md v2.1
PRD: PRD_CategoryEvent_Refactoring.md v1.1
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List

from app.schemas.device import (
    CameraUrls,
    HardwareSpec,
    Geolocation,
    DeviceGroupNestedResponse
)
from app.utils.enums import EnumMappingEventCategory


# ============================================
# EventMapping Schemas
# ============================================

class EventMappingCreate(BaseModel):
    """
    Schema for creating a new EventMapping

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    PRD: PRD_CategoryEvent_Refactoring.md v1.1
    - group_event 필드 제거됨
    - device_group_id: DeviceGroup FK
    - category_event → category_event_mapping 변경
    """
    name_event: str
    device_group_id: Optional[int] = None
    category_event_mapping: EnumMappingEventCategory
    description: Optional[str] = None
    status: bool = True


class EventMappingResponse(BaseModel):
    """
    Schema for EventMapping response

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    PRD: PRD_CategoryEvent_Refactoring.md v1.1
    - group_event 필드 제거됨
    - device_group_id: DeviceGroup FK
    - category_event → category_event_mapping 변경
    """
    id: int
    name_event: str
    device_group_id: Optional[int] = None
    category_event_mapping: EnumMappingEventCategory
    description: Optional[str]
    status: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventMappingUpdate(BaseModel):
    """
    Schema for updating an EventMapping (all fields optional for PATCH)

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    PRD: PRD_CategoryEvent_Refactoring.md v1.1
    - group_event 필드 제거됨
    - category_event → category_event_mapping 변경
    """
    name_event: Optional[str] = None
    device_group_id: Optional[int] = None
    category_event_mapping: Optional[EnumMappingEventCategory] = None
    description: Optional[str] = None
    status: Optional[bool] = None


# ============================================
# EventMappingCamera Nested Response Schemas
# ============================================

class CameraNestedResponseIntegration(BaseModel):
    """
    카메라 Nested 응답 - Full Property (timestamp 제외)

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.1
    PRD: PRD_Camera_Urls_JsonB.md
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


# ============================================
# EventMappingCamera Create/Update Schemas
# ============================================

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

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.3
    """
    camera_id: Optional[int] = None
    target_preset_id: Optional[int] = None
    home_preset_id: Optional[int] = None
    delay_time: Optional[int] = Field(None, ge=0)
    is_enable: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


# ============================================
# EventMappingCamera Response Schemas
# ============================================

class EventMappingCameraResponse(BaseModel):
    """
    카메라 연동 응답 스키마 (주체용 - timestamp 포함)

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.1
    """
    id: int
    event_mapping_id: int
    camera: Optional[CameraNestedResponseIntegration] = None
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
    """
    id: int
    camera: Optional[CameraNestedResponseIntegration] = None
    target_preset: Optional[PresetNestedResponse] = None
    home_preset: Optional[PresetNestedResponse] = None
    delay_time: int
    is_enable: bool
    priority: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EventMappingCameraListResponse(BaseModel):
    """
    카메라 연동 목록 응답 스키마

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5.2.1
    """
    items: List[EventMappingCameraResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================
# EventMappingSpeaker Create/Update Schemas
# ============================================

class EventMappingSpeakerCreate(BaseModel):
    """
    스피커 연동 생성 스키마

    PRD: PRD_EventMappingSpeaker.md v1.0
    """
    speaker_id: int = Field(..., description="대상 스피커 ID")
    file_group_id: Optional[int] = Field(None, description="방송 파일 그룹 ID")
    repeat_count: int = Field(1, ge=1, description="방송 반복 횟수")
    is_enable: bool = Field(True, description="활성화 여부")
    priority: Optional[int] = Field(None, ge=0, description="실행 우선순위 (Optional)")


class EventMappingSpeakerUpdate(BaseModel):
    """
    스피커 연동 수정 스키마 (PATCH)

    PRD: PRD_EventMappingSpeaker.md v1.0
    """
    speaker_id: Optional[int] = None
    file_group_id: Optional[int] = None
    repeat_count: Optional[int] = Field(None, ge=1)
    is_enable: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


class EventMappingSpeakerReplace(BaseModel):
    """
    스피커 연동 전체 수정 스키마 (PUT)

    PRD: PRD_EventMappingSpeaker.md v1.0
    """
    speaker_id: int = Field(..., description="대상 스피커 ID")
    file_group_id: Optional[int] = Field(None, description="방송 파일 그룹 ID")
    repeat_count: int = Field(..., ge=1, description="방송 반복 횟수")
    is_enable: bool = Field(..., description="활성화 여부")
    priority: Optional[int] = Field(None, ge=0, description="실행 우선순위 (Optional)")


# ============================================
# EventMappingSpeaker Nested Response Schemas
# ============================================

class SpeakerNestedResponseIntegration(BaseModel):
    """
    스피커 Nested 응답 - EventMappingSpeaker용 (timestamp 제외)

    PRD: PRD_EventMappingSpeaker.md v1.0
    """
    id: int
    number_device: int
    name_device: str
    type_device: str
    status: str
    speaker_type: str

    model_config = ConfigDict(from_attributes=True)


class FileGroupNestedResponse(BaseModel):
    """
    파일그룹 Nested 응답 - EventMappingSpeaker용 (timestamp 제외)

    PRD: PRD_EventMappingSpeaker.md v1.0
    """
    id: int
    server_id: int
    group_id: int
    group_name: str
    files: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# EventMappingSpeaker Response Schemas
# ============================================

class EventMappingSpeakerResponse(BaseModel):
    """
    스피커 연동 응답 스키마 (주체용 - timestamp 포함)

    PRD: PRD_EventMappingSpeaker.md v1.0
    """
    id: int
    event_mapping_id: int
    speaker: Optional[SpeakerNestedResponseIntegration] = None
    file_group: Optional[FileGroupNestedResponse] = None
    repeat_count: int
    is_enable: bool
    priority: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
