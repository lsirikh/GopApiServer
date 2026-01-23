"""
DeviceGroup Schemas for Pydantic validation
PRD: PRD_Device_Structure_Refactoring.md - Section 3.1
PRD: PRD_Camera_Urls_JsonB.md v1.0 - Camera urls JSONB 통합
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas.device import CameraUrls


class DeviceGroupBase(BaseModel):
    """DeviceGroup 기본 스키마"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="그룹 이름 (최대 200자)",
        json_schema_extra={"example": "GOP 3구역"}
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="그룹 설명 (최대 500자)",
        json_schema_extra={"example": "GOP 3구역 장비 그룹"}
    )


class DeviceGroupCreate(DeviceGroupBase):
    """DeviceGroup 생성 스키마"""
    pass


class DeviceGroupUpdate(BaseModel):
    """DeviceGroup 수정 스키마 (부분 업데이트 지원)"""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="그룹 이름",
        json_schema_extra={"example": "GOP 3구역"}
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="그룹 설명",
        json_schema_extra={"example": "GOP 3구역 장비 그룹 - 수정됨"}
    )


class DeviceGroupResponse(BaseModel):
    """DeviceGroup 응답 스키마"""
    id: int = Field(..., description="그룹 ID", json_schema_extra={"example": 1})
    name: str = Field(..., description="그룹 이름", json_schema_extra={"example": "GOP 1구역"})
    description: Optional[str] = Field(
        None,
        description="그룹 설명",
        json_schema_extra={"example": "GOP 1구역 장비 그룹"}
    )
    device_count: int = Field(
        default=0,
        description="그룹 내 디바이스 수",
        json_schema_extra={"example": 5}
    )
    created_at: datetime = Field(
        ...,
        description="생성 일시",
        json_schema_extra={"example": "2025-01-01T00:00:00.000Z"}
    )
    updated_at: datetime = Field(
        ...,
        description="수정 일시",
        json_schema_extra={"example": "2025-01-01T00:00:00.000Z"}
    )

    model_config = {"from_attributes": True}


class DeviceSummaryBase(BaseModel):
    """디바이스 요약 정보 기본 스키마"""
    id: int = Field(..., description="디바이스 ID", json_schema_extra={"example": 1})
    number_device: int = Field(..., description="디바이스 번호", json_schema_extra={"example": 1})
    group_device: int = Field(
        ...,
        description="디바이스 그룹 번호 (레거시)",
        json_schema_extra={"example": 1}
    )
    name_device: str = Field(
        ...,
        description="디바이스 이름",
        json_schema_extra={"example": "Controller-A"}
    )
    type_device: str = Field(
        ...,
        description="디바이스 타입",
        json_schema_extra={"example": "IoController"}
    )
    version: Optional[str] = Field(
        None,
        description="디바이스 버전",
        json_schema_extra={"example": "v2.1.0"}
    )
    status: str = Field(
        ...,
        description="디바이스 상태",
        json_schema_extra={"example": "ACTIVATED"}
    )
    is_enable: bool = Field(
        ...,
        description="장비 활성화 여부",
        json_schema_extra={"example": True}
    )

    model_config = {"from_attributes": True}


class ControllerSummary(DeviceSummaryBase):
    """Controller 요약 정보 스키마

    GOP_Restful_Api_연동설계.md 5.6.2절 기준
    """
    # Override base fields with Controller-specific examples
    id: int = Field(..., description="디바이스 ID", json_schema_extra={"example": 1})
    name_device: str = Field(..., description="디바이스 이름", json_schema_extra={"example": "Controller-A"})
    type_device: str = Field(..., description="디바이스 타입", json_schema_extra={"example": "Controller"})
    version: Optional[str] = Field(None, description="디바이스 버전", json_schema_extra={"example": "v2.1.0"})

    # Controller-specific fields
    ip_address: str = Field(
        ...,
        description="IP 주소",
        json_schema_extra={"example": "192.168.1.100"}
    )
    ip_port: int = Field(..., description="포트 번호", json_schema_extra={"example": 8001})
    geolocation: Optional[dict] = Field(
        None,
        description="좌표/위치 정보",
        json_schema_extra={"example": {"location": "GOP 1구역 컨트롤러", "latitude": 38.1234, "longitude": 127.5678}}
    )


class SensorSummary(DeviceSummaryBase):
    """Sensor 요약 정보 스키마

    GOP_Restful_Api_연동설계.md 5.6.2절 기준
    """
    # Override base fields with Sensor-specific examples
    id: int = Field(..., description="디바이스 ID", json_schema_extra={"example": 101})
    name_device: str = Field(..., description="디바이스 이름", json_schema_extra={"example": "Sensor-A-1"})
    type_device: str = Field(..., description="디바이스 타입", json_schema_extra={"example": "Multi"})
    version: Optional[str] = Field(None, description="디바이스 버전", json_schema_extra={"example": "v1.5.0"})

    # Sensor-specific fields
    controller_id: int = Field(
        ...,
        description="연결된 Controller ID",
        json_schema_extra={"example": 1}
    )
    geolocation: Optional[dict] = Field(
        None,
        description="좌표/위치 정보",
        json_schema_extra={"example": {"location": "GOP 1구역 센서", "latitude": 38.1234, "longitude": 127.5678}}
    )


class CameraSummary(DeviceSummaryBase):
    """
    Camera 요약 정보 스키마 (전체 필드 포함)

    PRD: PRD_Camera_Urls_JsonB.md v1.0
    - rtsp_uri, rtsp_port 필드 제거
    - urls JSONB 필드 추가

    GOP_Restful_Api_연동설계.md 5.6.2절 기준
    """
    # Override base fields with Camera-specific examples
    id: int = Field(..., description="디바이스 ID", json_schema_extra={"example": 201})
    name_device: str = Field(..., description="디바이스 이름", json_schema_extra={"example": "Camera-A-1"})
    type_device: str = Field(..., description="디바이스 타입", json_schema_extra={"example": "IpCamera"})
    version: Optional[str] = Field(None, description="디바이스 버전", json_schema_extra={"example": "v1.0.0"})

    # Camera-specific fields
    ip_address: str = Field(
        ...,
        description="IP 주소",
        json_schema_extra={"example": "192.168.1.200"}
    )
    ip_port: int = Field(..., description="HTTP 포트", json_schema_extra={"example": 80})
    user_name: Optional[str] = Field(
        None,
        description="접속 사용자명",
        json_schema_extra={"example": "admin"}
    )
    user_password: Optional[str] = Field(
        None,
        description="접속 비밀번호",
        json_schema_extra={"example": "admin1234"}
    )
    # PRD_Camera_Urls_JsonB.md: urls JSONB 통합 (rtsp_uri/rtsp_port 제거)
    urls: Optional["CameraUrls"] = Field(
        None,
        description="카메라 URL 정보 (JSONB)",
        json_schema_extra={"example": {"streams": {"rtsp": {"main": "rtsp://192.168.1.200:554/stream1"}}}}
    )
    mode: str = Field(..., description="카메라 모드", json_schema_extra={"example": "RTSP"})
    camera_category: str = Field(
        ...,
        description="카메라 카테고리",
        json_schema_extra={"example": "PTZ"}
    )
    is_record: bool = Field(..., description="녹화 여부", json_schema_extra={"example": True})
    hardware_spec: Optional[dict] = Field(
        None,
        description="하드웨어 스펙 정보",
        json_schema_extra={"example": {"manufacturer": "Samsung", "model": "SNP-6320H", "firmware": "2.20.01"}}
    )
    geolocation: Optional[dict] = Field(
        None,
        description="좌표/위치 정보",
        json_schema_extra={"example": {"location": "GOP 1구역 전방 초소", "latitude": 38.1234, "longitude": 127.5678}}
    )


class SpeakerSummary(DeviceSummaryBase):
    """Speaker 요약 정보 스키마

    GOP_Restful_Api_연동설계.md 5.6.2절 기준
    PRD: PRD_Speaker_Device.md, PRD_Speaker_Geolocation.md v1.0
    """
    # Override base fields with Speaker-specific examples
    id: int = Field(..., description="디바이스 ID", json_schema_extra={"example": 301})
    name_device: str = Field(..., description="디바이스 이름", json_schema_extra={"example": "VCS_2401"})
    type_device: str = Field(..., description="디바이스 타입", json_schema_extra={"example": "IpSpeaker"})
    version: Optional[str] = Field(None, description="디바이스 버전", json_schema_extra={"example": "v1.0.0"})

    # Speaker-specific fields
    speaker_type: str = Field(
        ...,
        description="스피커 타입 (EnumSpeakerType)",
        json_schema_extra={"example": "NORMAL"}
    )
    server_id: Optional[int] = Field(
        None,
        description="방송서버 ID (FK)",
        json_schema_extra={"example": 1}
    )
    description: Optional[str] = Field(
        None,
        description="설명",
        json_schema_extra={"example": "1구역 스피커"}
    )
    geolocation: Optional[dict] = Field(
        None,
        description="좌표/위치 정보",
        json_schema_extra={"example": {"location": "GOP 1구역 스피커", "latitude": 38.1234, "longitude": 127.5678}}
    )


class EnclosureSummary(DeviceSummaryBase):
    """Enclosure 요약 정보 스키마

    GOP_Restful_Api_연동설계.md 5.6.2절 기준
    PRD: PRD_Enclosure_Device.md v1.1
    """
    # Override base fields with Enclosure-specific examples
    id: int = Field(..., description="디바이스 ID", json_schema_extra={"example": 401})
    name_device: str = Field(..., description="디바이스 이름", json_schema_extra={"example": "Enclosure-A-1"})
    type_device: str = Field(..., description="디바이스 타입", json_schema_extra={"example": "Enclosure"})
    version: Optional[str] = Field(None, description="디바이스 버전", json_schema_extra={"example": "v1.0.0"})

    # Enclosure-specific fields
    door_status: str = Field(
        ...,
        description="도어 물리적 상태 (EnumDoorStatus)",
        json_schema_extra={"example": "CLOSED"}
    )
    heater_enabled: bool = Field(
        ...,
        description="히터 활성화 상태",
        json_schema_extra={"example": False}
    )
    fan_enabled: bool = Field(
        ...,
        description="팬 활성화 상태",
        json_schema_extra={"example": False}
    )
    threshold_config: Optional[dict] = Field(
        None,
        description="알람 임계값 설정",
        json_schema_extra={"example": {"temperature": {"warning": 40, "critical": 50}}}
    )
    geolocation: Optional[dict] = Field(
        None,
        description="좌표/위치 정보",
        json_schema_extra={"example": {"location": "GOP 1구역 함체", "latitude": 38.1234, "longitude": 127.5678}}
    )


# Union type for polymorphic device summary
DeviceSummary = Union[ControllerSummary, SensorSummary, CameraSummary, SpeakerSummary, EnclosureSummary]


class DeviceGroupDetailResponse(DeviceGroupResponse):
    """DeviceGroup 상세 응답 스키마 (디바이스 목록 포함)"""
    devices: List[DeviceSummary] = Field(default_factory=list, description="소속 디바이스 목록")


class DeviceAssignRequest(BaseModel):
    """디바이스 할당 요청 스키마"""
    device_ids: List[int] = Field(
        ...,
        min_length=1,
        description="할당할 디바이스 ID 목록",
        json_schema_extra={"example": [1, 101, 201]}
    )

    @field_validator('device_ids')
    @classmethod
    def validate_device_ids(cls, v):
        if not v:
            raise ValueError('device_ids must not be empty')
        return v


class DeviceAssignResponse(BaseModel):
    """디바이스 할당 응답 스키마"""
    group_id: int = Field(..., description="그룹 ID", json_schema_extra={"example": 1})
    assigned_device_ids: List[int] = Field(
        default_factory=list,
        description="할당 완료된 디바이스 ID 목록",
        json_schema_extra={"example": [1, 101]}
    )
    skipped_device_ids: List[int] = Field(
        default_factory=list,
        description="건너뛴 디바이스 ID 목록 (이미 할당됨)",
        json_schema_extra={"example": [201]}
    )
    message: str = Field(
        ...,
        description="결과 메시지",
        json_schema_extra={"example": "2 devices assigned, 1 skipped (already in group)"}
    )


class DeviceRemoveResponse(BaseModel):
    """디바이스 제거 응답 스키마"""
    group_id: int = Field(..., description="그룹 ID", json_schema_extra={"example": 1})
    device_id: int = Field(..., description="제거된 디바이스 ID", json_schema_extra={"example": 101})
    message: str = Field(
        ...,
        description="결과 메시지",
        json_schema_extra={"example": "디바이스 그룹에서 제거 성공"}
    )


# Forward reference resolution for CameraUrls
# This must be done after all classes are defined
from app.schemas.device import CameraUrls

CameraSummary.model_rebuild()
