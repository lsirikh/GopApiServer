"""
Speaker schemas: SpeakerCreate, SpeakerUpdate, SpeakerResponse
PRD: PRD_Speaker_Device.md - Section 5.1
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType
from app.schemas.server import ServerNestedResponse


class SpeakerCreate(BaseModel):
    """Schema for creating a new Speaker"""
    # Device Base fields
    number_device: int  # 단말 번호 (NATS device_no 통합)
    group_device: int = 0
    name_device: str  # 표시명 (예: "VCS_2401")
    type_device: EnumDeviceType = EnumDeviceType.IpSpeaker
    version: Optional[str] = None
    status: EnumDeviceStatus = EnumDeviceStatus.ACTIVATED

    # Speaker-specific fields
    speaker_type: EnumSpeakerType = EnumSpeakerType.NORMAL
    server_id: Optional[int] = None  # 방송서버 ID (FK)
    description: Optional[str] = None


class SpeakerUpdate(BaseModel):
    """Schema for updating a Speaker (PATCH - all fields optional)"""
    # Device Base fields (Optional)
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    version: Optional[str] = None
    status: Optional[EnumDeviceStatus] = None

    # Speaker-specific fields (Optional)
    speaker_type: Optional[EnumSpeakerType] = None
    server_id: Optional[int] = None
    description: Optional[str] = None


class SpeakerResponse(BaseModel):
    """Schema for Speaker response"""
    # Device Base fields
    id: int
    category_device: str = "speaker"
    number_device: int  # 단말 번호 (NATS device_no)
    group_device: int
    name_device: str
    type_device: str
    version: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Speaker-specific fields
    speaker_type: str
    description: Optional[str] = None

    # Nested Server 정보 (server_id 대신 server 객체로 제공)
    server: Optional[ServerNestedResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SpeakerNestedResponse(BaseModel):
    """Speaker Nested Response (Event 등에서 사용) - excludes timestamps"""
    id: int
    category_device: str = "speaker"
    number_device: int  # 단말 번호 (NATS device_no)
    name_device: str
    type_device: str
    status: str
    speaker_type: str

    model_config = ConfigDict(from_attributes=True)
