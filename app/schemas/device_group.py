"""
DeviceGroup Schemas for Pydantic validation
PRD: PRD_Device_Structure_Refactoring.md - Section 3.1
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime


class DeviceGroupBase(BaseModel):
    """DeviceGroup 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=200, description="그룹 이름 (최대 200자)")
    description: Optional[str] = Field(None, max_length=500, description="그룹 설명 (최대 500자)")


class DeviceGroupCreate(DeviceGroupBase):
    """DeviceGroup 생성 스키마"""
    pass


class DeviceGroupUpdate(BaseModel):
    """DeviceGroup 수정 스키마 (부분 업데이트 지원)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="그룹 이름")
    description: Optional[str] = Field(None, max_length=500, description="그룹 설명")


class DeviceGroupResponse(BaseModel):
    """DeviceGroup 응답 스키마"""
    id: int = Field(..., description="그룹 ID")
    name: str = Field(..., description="그룹 이름")
    description: Optional[str] = Field(None, description="그룹 설명")
    device_count: int = Field(default=0, description="그룹 내 디바이스 수")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = {"from_attributes": True}


class DeviceSummaryBase(BaseModel):
    """디바이스 요약 정보 기본 스키마"""
    id: int = Field(..., description="디바이스 ID")
    number_device: int = Field(..., description="디바이스 번호")
    group_device: int = Field(..., description="디바이스 그룹 번호 (레거시)")
    name_device: str = Field(..., description="디바이스 이름")
    type_device: str = Field(..., description="디바이스 타입")
    version: Optional[str] = Field(None, description="디바이스 버전")
    status: str = Field(..., description="디바이스 상태")

    model_config = {"from_attributes": True}


class ControllerSummary(DeviceSummaryBase):
    """Controller 요약 정보 스키마"""
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., description="포트 번호")


class SensorSummary(DeviceSummaryBase):
    """Sensor 요약 정보 스키마"""
    controller_id: int = Field(..., description="연결된 Controller ID")


class CameraSummary(DeviceSummaryBase):
    """Camera 요약 정보 스키마 (전체 필드 포함)"""
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., description="HTTP 포트")
    user_name: Optional[str] = Field(None, description="접속 사용자명")
    user_password: Optional[str] = Field(None, description="접속 비밀번호")
    rtsp_uri: Optional[str] = Field(None, description="RTSP URI")
    rtsp_port: int = Field(..., description="RTSP 포트")
    mode: str = Field(..., description="카메라 모드")
    camera_category: str = Field(..., description="카메라 카테고리")
    is_record: bool = Field(..., description="녹화 여부")
    hardware_spec: Optional[dict] = Field(None, description="하드웨어 스펙 정보")
    geolocation: Optional[dict] = Field(None, description="좌표/위치 정보")


# Union type for polymorphic device summary
DeviceSummary = Union[ControllerSummary, SensorSummary, CameraSummary]


class DeviceGroupDetailResponse(DeviceGroupResponse):
    """DeviceGroup 상세 응답 스키마 (디바이스 목록 포함)"""
    devices: List[DeviceSummary] = Field(default_factory=list, description="소속 디바이스 목록")


class DeviceAssignRequest(BaseModel):
    """디바이스 할당 요청 스키마"""
    device_ids: List[int] = Field(..., min_length=1, description="할당할 디바이스 ID 목록")

    @field_validator('device_ids')
    @classmethod
    def validate_device_ids(cls, v):
        if not v:
            raise ValueError('device_ids must not be empty')
        return v


class DeviceAssignResponse(BaseModel):
    """디바이스 할당 응답 스키마"""
    group_id: int = Field(..., description="그룹 ID")
    assigned_device_ids: List[int] = Field(default_factory=list, description="할당 완료된 디바이스 ID 목록")
    skipped_device_ids: List[int] = Field(default_factory=list, description="건너뛴 디바이스 ID 목록 (이미 할당됨)")
    message: str = Field(..., description="결과 메시지")


class DeviceRemoveResponse(BaseModel):
    """디바이스 제거 응답 스키마"""
    group_id: int = Field(..., description="그룹 ID")
    device_id: int = Field(..., description="제거된 디바이스 ID")
    message: str = Field(..., description="결과 메시지")
