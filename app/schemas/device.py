"""
Device schemas: Controller, Sensor, Camera, Speaker

PRD: PRD_Device_Structure_Refactoring.md
- Section 2: Device Group N:N 관계
- Section 3: Camera 확장 필드 (HardwareSpec, Geolocation)
PRD: PRD_Speaker_Device.md - Section 5.1
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumDoorStatus

if TYPE_CHECKING:
    from app.schemas.device_group import DeviceGroupResponse


# ============================================================================
# Phase 1: Camera URLs JSONB Schema (PRD: PRD_Camera_Urls_JsonB.md)
# ============================================================================

class CameraUrls(BaseModel):
    """
    카메라 URL 통합 스키마 (JSONB) - 단순화 버전
    PRD: PRD_Camera_Urls_JsonB.md - Section 2.1

    유연한 딕셔너리 기반 구조로 다양한 URL 형식 지원:
    - homepage: {"url": "https://192.168.0.10/"}
    - onvif: {"device_service": "http://..."}
    - streams: {"rtsp": {"main": "rtsp://...", "sub": "rtsp://..."}, "webrtc": {"main": "https://..."}}
    - snapshot: {"ch1": "http://..."}

    extra="allow"로 벤더 특화 필드 지원

    Example:
    {
      "homepage": {"url": "https://192.168.0.10/"},
      "onvif": {"device_service": "http://192.168.0.10:8000/onvif/device_service"},
      "streams": {
        "rtsp": {"main": "rtsp://192.168.0.10:554/Streaming/Channels/101", "sub": "rtsp://192.168.0.10:554/Streaming/Channels/102"},
        "webrtc": {"main": "https://192.168.0.10/webrtc/main"}
      },
      "snapshot": {"ch1": "http://192.168.0.10/cgi-bin/snapshot.cgi"}
    }
    """
    homepage: Optional[dict] = Field(
        None,
        description="홈페이지 URL",
        json_schema_extra={"example": {"url": "https://192.168.0.10/"}}
    )
    onvif: Optional[dict] = Field(
        None,
        description="ONVIF 서비스 URL",
        json_schema_extra={"example": {"device_service": "http://192.168.0.10:8000/onvif/device_service"}}
    )
    streams: Optional[dict] = Field(
        None,
        description="스트림 URL (rtsp, webrtc 등)",
        json_schema_extra={"example": {
            "rtsp": {"main": "rtsp://192.168.0.10:554/Streaming/Channels/101", "sub": "rtsp://192.168.0.10:554/Streaming/Channels/102"},
            "webrtc": {"main": "https://192.168.0.10/webrtc/main"}
        }}
    )
    snapshot: Optional[dict] = Field(
        None,
        description="스냅샷 URL",
        json_schema_extra={"example": {"ch1": "http://192.168.0.10/cgi-bin/snapshot.cgi"}}
    )

    model_config = ConfigDict(from_attributes=True, extra="allow")


# ============================================================================
# Phase 3: Camera 확장 필드 Composite Types (PRD Section 3.2)
# ============================================================================

class HardwareSpec(BaseModel):
    """
    카메라 하드웨어 스펙 정보 (Composite Type)
    PRD Section 3.2.2
    """
    name: Optional[str] = Field(None, max_length=200, description="하드웨어 이름")
    location: Optional[str] = Field(None, max_length=500, description="설치 위치")
    manufacturer: Optional[str] = Field(None, max_length=200, description="제조사")
    model: Optional[str] = Field(None, max_length=200, description="모델명")
    hardware: Optional[str] = Field(None, max_length=200, description="하드웨어 정보")
    firmware: Optional[str] = Field(None, max_length=100, description="펌웨어 버전")
    device_id: Optional[str] = Field(None, max_length=200, description="장치 ID")
    mac_address: Optional[str] = Field(None, max_length=17, description="MAC 주소 (XX:XX:XX:XX:XX:XX)")
    onvif_version: Optional[str] = Field(None, max_length=50, description="ONVIF 버전")

    model_config = ConfigDict(from_attributes=True)


class Geolocation(BaseModel):
    """
    좌표 정보 (Composite Type)
    PRD Section 3.2.3
    """
    location: Optional[str] = Field(None, max_length=500, description="설치 위치 (예: GOP 1구역 전방 초소)")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="위도")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="경도")
    altitude: Optional[float] = Field(None, description="고도 (미터)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DeviceGroupNestedResponse: Event 응답에서 DeviceGroup 정보를 경량화하여 반환
# PRD: PRD_Event_Api_Refactoring.md v1.2 - Section 2.2.4
# ============================================================================

class DeviceGroupNestedResponse(BaseModel):
    """
    DeviceGroup 경량화 nested response 스키마

    Event/Device 응답에서 device.device_groups[]로 사용됩니다.
    EventMapping.device_group_id와 매칭하여 카메라 프리셋 실행에 사용됩니다.

    v2.4: Nested Response 규칙 적용
    포함 필드: id, name, description, device_count (4개 필드)
    제외 필드: created_at, updated_at (Nested 객체이므로)
    """
    id: int = Field(..., description="DeviceGroup ID (EventMapping FK)")
    name: str = Field(..., description="그룹 이름")
    description: Optional[str] = Field(None, description="그룹 설명")
    device_count: int = Field(default=0, description="소속 디바이스 수")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# DeviceNestedResponse: Event 응답에서 Device 정보를 nested로 반환하기 위한 스키마
# PRD: PRD_Event_Device_Refactoring.md - Section 3.2
# PRD: PRD_Event_Api_Refactoring.md v1.2 - device_groups 추가
# ============================================================================

class DeviceNestedResponse(BaseModel):
    """
    폴리모픽 Device nested response 스키마

    Event 응답에서 Device 정보를 nested 객체로 반환할 때 사용합니다.
    Device 타입(Controller, Sensor, Camera)에 따라 다른 필드가 포함됩니다.

    공통 필드:
        id, number_device, group_device, name_device, type_device, version, status, device_groups

    Controller 전용:
        ip_address, ip_port

    Sensor 전용:
        controller_id

    Camera 전용:
        ip_address, ip_port, urls, mode, category, is_record

    EventMapping 연동:
        device_groups[].id → EventMapping.device_group_id 매칭으로 카메라 프리셋 실행

    Breaking Change (v2.3):
    - rtsp_uri, rtsp_port 필드 제거
    - urls JSONB 필드로 통합 (CameraUrls 스키마)
    """
    # 공통 필드 (필수)
    id: int = Field(..., description="Device ID")
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장치 이름")
    type_device: str = Field(..., description="장치 타입")
    status: str = Field(..., description="장치 상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")

    # 공통 필드 (선택적) - PRD v1.2: nullable
    version: Optional[str] = Field(None, description="장치 버전")

    # Controller/Camera 공유 필드 (선택적)
    ip_address: Optional[str] = Field(None, description="IP 주소")
    ip_port: Optional[int] = Field(None, description="포트 번호")

    # Sensor 전용 필드 (선택적)
    controller_id: Optional[int] = Field(None, description="소속 컨트롤러 ID")

    # Camera 전용 필드 (선택적)
    mode: Optional[str] = Field(None, description="카메라 모드")
    category: Optional[str] = Field(None, description="카메라 카테고리")
    is_record: Optional[bool] = Field(None, description="녹화 활성화 여부")
    # PRD_Camera_Urls_JsonB.md: URLs JSONB 통합
    urls: Optional[CameraUrls] = Field(None, description="카메라 URL 정보 (JSONB)")

    # PRD v1.2: device_groups 추가 (EventMapping 연동 필수)
    device_groups: List[DeviceGroupNestedResponse] = Field(
        default=[],
        description="소속 DeviceGroup 목록 (EventMapping 연동 필수)"
    )

    model_config = ConfigDict(from_attributes=True)


class ControllerCreate(BaseModel):
    """
    컨트롤러 생성 스키마

    컨트롤러는 센서를 관리하는 상위 장치입니다.
    """
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(0, description="장치 그룹 번호 (Deprecated 예정, 레거시, 기본값: 0)")
    name_device: str = Field(..., max_length=200, description="장치 이름")
    type_device: str = Field(..., description="장치 타입 (Controller)")
    version: Optional[str] = Field(None, max_length=50, description="펌웨어/소프트웨어 버전")
    status: str = Field(..., description="상태 (ACTIVATED|DEACTIVATED|MAINTENANCE)")
    is_enable: bool = Field(True, description="장비 활성화 여부")
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., ge=1, le=65535, description="포트 번호")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    # Phase 5: group_ids 배열 지원 (N:N 관계)
    group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")


class ControllerResponse(BaseModel):
    """
    컨트롤러 응답 스키마

    컨트롤러 정보 및 소속 디바이스 그룹 목록을 포함합니다.
    """
    id: int = Field(..., description="컨트롤러 ID")
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장치 이름")
    type_device: str = Field(..., description="장치 타입")
    version: str = Field(..., description="버전")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., description="포트 번호")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")
    # v2.4: SensorNestedResponse 사용 (timestamp 제외, device_groups 포함)
    sensors: Optional[List['SensorNestedResponse']] = Field(None, description="소속 센서 목록 (include_sensors=true 시)")
    # v2.4: Nested Response 규칙 적용 - DeviceGroupNestedResponse 사용 (timestamp 제외)
    device_groups: List[DeviceGroupNestedResponse] = Field(default=[], description="소속 디바이스 그룹 목록 (N:N 관계)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ControllerNestedResponse: Sensor 조회 시 controller nested 반환용 스키마
# v2.5: Nested Response 규칙 적용
# ============================================================================

class ControllerNestedResponse(BaseModel):
    """
    컨트롤러 Nested response 스키마

    Sensor 조회 시 include_controller=true로 반환되는 컨트롤러 정보입니다.

    v2.5: Nested Response 규칙 적용
    - created_at, updated_at 제외 (Nested 객체이므로)
    - device_groups 포함 (DeviceGroupNestedResponse 사용)
    """
    id: int = Field(..., description="컨트롤러 ID")
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장치 이름")
    type_device: str = Field(..., description="장치 타입")
    version: Optional[str] = Field(None, description="버전")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., description="포트 번호")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    # v2.5: Nested Response 규칙 - device_groups 포함 (SensorNestedResponse와 일관성)
    device_groups: List[DeviceGroupNestedResponse] = Field(default=[], description="소속 디바이스 그룹 목록")

    model_config = ConfigDict(from_attributes=True)


class ControllerUpdate(BaseModel):
    """
    컨트롤러 수정 스키마 (PATCH)

    모든 필드가 선택적입니다. 제공된 필드만 업데이트됩니다.
    """
    number_device: Optional[int] = Field(None, description="장치 번호")
    group_device: Optional[int] = Field(None, description="장치 그룹 번호")
    name_device: Optional[str] = Field(None, description="장치 이름")
    type_device: Optional[str] = Field(None, description="장치 타입")
    version: Optional[str] = Field(None, description="버전")
    status: Optional[str] = Field(None, description="상태")
    is_enable: Optional[bool] = Field(None, description="장비 활성화 여부")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    ip_port: Optional[int] = Field(None, description="포트 번호")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    # Phase 5: group_ids 배열 지원 (N:N 관계)
    group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열")


class SensorCreate(BaseModel):
    """
    센서 생성 스키마

    센서는 컨트롤러에 종속된 감지 장치입니다.
    """
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(0, description="장치 그룹 번호 (Deprecated 예정, 레거시, 기본값: 0)")
    name_device: str = Field(..., max_length=200, description="장치 이름")
    type_device: str = Field(..., description="센서 타입 (Fence|Pir|Fod 등)")
    version: Optional[str] = Field(None, max_length=50, description="버전")
    status: str = Field(..., description="상태 (ACTIVATED|DEACTIVATED|MAINTENANCE)")
    is_enable: bool = Field(True, description="장비 활성화 여부")
    controller_id: int = Field(..., description="소속 컨트롤러 ID")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    # Phase 5: group_ids 배열 지원 (N:N 관계)
    group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")


class SensorResponse(BaseModel):
    """
    센서 응답 스키마

    센서 정보, 소속 컨트롤러 및 디바이스 그룹 목록을 포함합니다.
    """
    id: int = Field(..., description="센서 ID")
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장치 이름")
    type_device: str = Field(..., description="센서 타입")
    version: str = Field(..., description="버전")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    controller_id: int = Field(..., description="소속 컨트롤러 ID")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")
    # v2.5: Nested Response 규칙 적용 - ControllerNestedResponse 사용 (timestamp 제외)
    controller: Optional['ControllerNestedResponse'] = Field(None, description="소속 컨트롤러 정보 (include_controller=true 시)")
    # v2.4: Nested Response 규칙 적용 - DeviceGroupNestedResponse 사용 (timestamp 제외)
    device_groups: List[DeviceGroupNestedResponse] = Field(default=[], description="소속 디바이스 그룹 목록 (N:N 관계)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SensorNestedResponse: Controller 조회 시 sensors[] nested 반환용 스키마
# v2.4: Nested Response 규칙 적용
# ============================================================================

class SensorNestedResponse(BaseModel):
    """
    센서 Nested response 스키마

    Controller 조회 시 include_sensors=true로 반환되는 센서 정보입니다.

    v2.4: Nested Response 규칙 적용
    - created_at, updated_at 제외 (Nested 객체이므로)
    - device_groups 포함 (DeviceGroupNestedResponse 사용)
    """
    id: int = Field(..., description="센서 ID")
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장치 이름")
    type_device: str = Field(..., description="센서 타입")
    version: Optional[str] = Field(None, description="버전")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    controller_id: int = Field(..., description="소속 컨트롤러 ID")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    # v2.4: Nested에서 device_groups 포함 (timestamp 제외된 DeviceGroupNestedResponse 사용)
    device_groups: List[DeviceGroupNestedResponse] = Field(default=[], description="소속 디바이스 그룹 목록")

    model_config = ConfigDict(from_attributes=True)


class SensorUpdate(BaseModel):
    """
    센서 수정 스키마 (PATCH)

    모든 필드가 선택적입니다. 제공된 필드만 업데이트됩니다.
    """
    number_device: Optional[int] = Field(None, description="장치 번호")
    group_device: Optional[int] = Field(None, description="장치 그룹 번호")
    name_device: Optional[str] = Field(None, description="장치 이름")
    type_device: Optional[str] = Field(None, description="센서 타입")
    version: Optional[str] = Field(None, description="버전")
    status: Optional[str] = Field(None, description="상태")
    is_enable: Optional[bool] = Field(None, description="장비 활성화 여부")
    controller_id: Optional[int] = Field(None, description="소속 컨트롤러 ID")
    # PRD_Controller_Sensor_Geolocation.md: 위치 정보 추가
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    # Phase 5: group_ids 배열 지원 (N:N 관계)
    group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열")


class CameraCreate(BaseModel):
    """
    카메라 생성 스키마

    카메라는 영상 감시 장치로, HardwareSpec과 Geolocation 확장 필드를 지원합니다.
    PRD: PRD_Device_Structure_Refactoring.md Section 3.2
    PRD: PRD_Camera_Urls_JsonB.md (urls JSONB 통합)

    Breaking Change (v2.3):
    - rtsp_uri, rtsp_port 필드 제거
    - urls JSONB 필드로 통합 (CameraUrls 스키마)
    """
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(0, description="장치 그룹 번호 (Deprecated 예정, 레거시, 기본값: 0)")
    name_device: str = Field(..., max_length=200, description="장치 이름")
    type_device: str = Field(..., description="장치 타입 (IpCamera)")
    version: Optional[str] = Field(None, max_length=50, description="버전")
    status: str = Field(..., description="상태 (ACTIVATED|DEACTIVATED|MAINTENANCE)")
    is_enable: bool = Field(True, description="장비 활성화 여부")
    ip_address: str = Field(..., description="카메라 IP 주소")
    ip_port: int = Field(..., ge=1, le=65535, description="HTTP 포트")
    user_name: Optional[str] = Field(None, description="카메라 접속 사용자명 (PRD v1.2: nullable)")
    user_password: Optional[str] = Field(None, description="카메라 접속 비밀번호 (PRD v1.2: nullable)")
    mode: str = Field(..., description="카메라 모드 (NONE|ONVIF|RTSP)")
    category: str = Field(..., description="카메라 카테고리 (NONE|PTZ|FIXED|THERMAL)")
    # Phase 3: Camera 확장 필드 (PRD Section 3.2)
    is_record: bool = Field(False, description="녹화 활성화 여부")
    hardware_spec: Optional[HardwareSpec] = Field(None, description="하드웨어 스펙 정보 (JSON)")
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
    # PRD_Camera_Urls_JsonB.md: URLs JSONB 통합
    urls: Optional[CameraUrls] = Field(None, description="카메라 URL 정보 (JSONB)")
    # Phase 5: group_ids 배열 지원 (N:N 관계)
    group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")


class CameraResponse(BaseModel):
    """
    카메라 응답 스키마

    카메라 정보, 확장 필드(HardwareSpec, Geolocation) 및 디바이스 그룹 목록을 포함합니다.
    PRD: PRD_Device_Structure_Refactoring.md Section 3.2
    PRD: PRD_Camera_Urls_JsonB.md (urls JSONB 통합)

    Breaking Change (v2.3):
    - rtsp_uri, rtsp_port 필드 제거
    - urls JSONB 필드로 통합 (CameraUrls 스키마)
    """
    id: int = Field(..., description="카메라 ID")
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장치 이름")
    type_device: str = Field(..., description="장치 타입")
    version: str = Field(..., description="버전")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., description="HTTP 포트")
    user_name: Optional[str] = Field(None, description="접속 사용자명 (PRD v1.2: nullable)")
    user_password: Optional[str] = Field(None, description="접속 비밀번호 (PRD v1.2: nullable)")
    mode: str = Field(..., description="카메라 모드")
    category: str = Field(..., description="카메라 카테고리")
    # Phase 3: Camera 확장 필드 (PRD Section 3.2)
    is_record: bool = Field(False, description="녹화 활성화 여부")
    hardware_spec: Optional[HardwareSpec] = Field(None, description="하드웨어 스펙 정보")
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보")
    # PRD_Camera_Urls_JsonB.md: URLs JSONB 통합
    urls: Optional[CameraUrls] = Field(None, description="카메라 URL 정보 (JSONB)")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")
    # v2.4: Nested Response 규칙 적용 - DeviceGroupNestedResponse 사용 (timestamp 제외)
    device_groups: List[DeviceGroupNestedResponse] = Field(default=[], description="소속 디바이스 그룹 목록 (N:N 관계)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CameraWithPresetsResponse: Camera 단일 조회 시 presets 포함 응답
# PRD: PRD_API_Gap_Analysis.md (IMP-001, IMP-002)
# ============================================================================

class CameraWithPresetsResponse(CameraResponse):
    """
    카메라 + 프리셋 응답 스키마

    PRD: PRD_API_Gap_Analysis.md (IMP-001, IMP-002)
    Camera 단일 조회 시 include_presets=true, include_rois=true 파라미터 지원

    presets 필드는 CameraPresetNestedResponse 리스트로 반환됩니다.
    """
    presets: List = Field(
        default=[],
        description="카메라 프리셋 목록 (include_presets=true일 때 포함)"
    )


# ============================================================================
# CameraNestedResponse: Event 조회 시 device nested 반환용 스키마
# v2.7: Event의 device polymorphic response 지원
# ============================================================================

class CameraNestedResponse(BaseModel):
    """
    카메라 Nested response 스키마

    Event 조회 시 device가 Camera인 경우 반환되는 정보입니다.

    v2.7: Nested Response 규칙 적용
    - created_at, updated_at 제외 (Nested 객체이므로)
    - device_groups 포함 (DeviceGroupNestedResponse 사용)
    - user_name, user_password, hardware_spec, geolocation 제외 (민감정보/상세정보)

    Breaking Change (v2.3):
    - rtsp_uri, rtsp_port 필드 제거
    - urls JSONB 필드로 통합 (CameraUrls 스키마)
    """
    id: int = Field(..., description="카메라 ID")
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장치 이름")
    type_device: str = Field(..., description="장치 타입")
    version: Optional[str] = Field(None, description="버전")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., description="HTTP 포트")
    mode: str = Field(..., description="카메라 모드 (NONE|ONVIF|RTSP)")
    category: str = Field(..., description="카메라 카테고리 (NONE|PTZ|FIXED|THERMAL)")
    is_record: bool = Field(False, description="녹화 활성화 여부")
    # PRD_Camera_Urls_JsonB.md: URLs JSONB 통합
    urls: Optional[CameraUrls] = Field(None, description="카메라 URL 정보 (JSONB)")
    device_groups: List[DeviceGroupNestedResponse] = Field(default=[], description="소속 디바이스 그룹 목록")

    model_config = ConfigDict(from_attributes=True)


class CameraUpdate(BaseModel):
    """
    카메라 수정 스키마 (PATCH)

    모든 필드가 선택적입니다. 제공된 필드만 업데이트됩니다.
    확장 필드(hardware_spec, geolocation)도 부분 업데이트를 지원합니다.

    Breaking Change (v2.3):
    - rtsp_uri, rtsp_port 필드 제거
    - urls JSONB 필드로 통합 (CameraUrls 스키마)
    """
    number_device: Optional[int] = Field(None, description="장치 번호")
    group_device: Optional[int] = Field(None, description="장치 그룹 번호")
    name_device: Optional[str] = Field(None, description="장치 이름")
    type_device: Optional[str] = Field(None, description="장치 타입")
    version: Optional[str] = Field(None, description="버전")
    status: Optional[str] = Field(None, description="상태")
    is_enable: Optional[bool] = Field(None, description="장비 활성화 여부")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    ip_port: Optional[int] = Field(None, description="HTTP 포트")
    user_name: Optional[str] = Field(None, description="접속 사용자명")
    user_password: Optional[str] = Field(None, description="접속 비밀번호")
    mode: Optional[str] = Field(None, description="카메라 모드")
    category: Optional[str] = Field(None, description="카메라 카테고리")
    # Phase 3: Camera 확장 필드
    is_record: Optional[bool] = Field(None, description="녹화 활성화 여부")
    hardware_spec: Optional[HardwareSpec] = Field(None, description="하드웨어 스펙 정보")
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보")
    # PRD_Camera_Urls_JsonB.md: URLs JSONB 통합
    urls: Optional[CameraUrls] = Field(None, description="카메라 URL 정보 (JSONB)")
    # Phase 5: group_ids 배열 지원 (N:N 관계)
    group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열")


# ============================================================================
# Speaker Schemas (PRD: PRD_Speaker_Device.md - Section 5.1)
# ============================================================================

class ServerNestedResponse(BaseModel):
    """
    Server Nested Response for Speaker

    Speaker 응답에서 server 정보를 nested로 반환할 때 사용합니다.
    Timestamp 필드 제외 (Nested 객체 규칙)
    PRD: PRD_Speaker_Device.md Section 5.3
    """
    id: int = Field(..., description="서버 ID")
    category_id: int = Field(..., description="서버 카테고리 ID")
    name: str = Field(..., description="서버 이름")
    status: str = Field(..., description="서버 상태")
    ip_address: str = Field(..., description="서버 IP 주소")
    port: int = Field(..., description="서버 포트")
    hostname: Optional[str] = Field(None, description="호스트명")
    user_name: Optional[str] = Field(None, description="사용자명")
    user_password: Optional[str] = Field(None, description="비밀번호")
    cpu_usage: Optional[float] = Field(None, description="CPU 사용률")
    ram_usage: Optional[float] = Field(None, description="RAM 사용률")
    disk_usage: Optional[float] = Field(None, description="디스크 사용률")
    network_throughput: Optional[str] = Field(None, description="네트워크 처리량")

    model_config = ConfigDict(from_attributes=True)


class SpeakerCreate(BaseModel):
    """
    Schema for creating a new Speaker
    PRD: PRD_Speaker_Geolocation.md v1.0 - geolocation 필드 추가
    """
    # Device Base fields
    number_device: int = Field(..., description="단말 번호 (NATS device_no 통합)")
    group_device: int = Field(0, description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="표시명 (예: 'VCS_2401')")
    type_device: EnumDeviceType = Field(EnumDeviceType.IpSpeaker, description="장치 타입")
    version: Optional[str] = Field(None, description="버전")
    status: EnumDeviceStatus = Field(EnumDeviceStatus.ACTIVATED, description="상태")
    is_enable: bool = Field(True, description="장비 활성화 여부")

    # Speaker-specific fields
    speaker_type: EnumSpeakerType = Field(EnumSpeakerType.NORMAL, description="스피커 타입")
    server_id: Optional[int] = Field(None, description="방송서버 ID (FK)")
    description: Optional[str] = Field(None, description="설명")
    # PRD_Speaker_Geolocation.md v1.0: 위치 정보 JSONB
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")


class SpeakerUpdate(BaseModel):
    """
    Schema for updating a Speaker (PATCH - all fields optional)
    PRD: PRD_Speaker_Geolocation.md v1.0 - geolocation 필드 추가
    """
    # Device Base fields (Optional)
    number_device: Optional[int] = Field(None, description="단말 번호")
    group_device: Optional[int] = Field(None, description="장치 그룹 번호")
    name_device: Optional[str] = Field(None, description="표시명")
    version: Optional[str] = Field(None, description="버전")
    status: Optional[EnumDeviceStatus] = Field(None, description="상태")
    is_enable: Optional[bool] = Field(None, description="장비 활성화 여부")

    # Speaker-specific fields (Optional)
    speaker_type: Optional[EnumSpeakerType] = Field(None, description="스피커 타입")
    server_id: Optional[int] = Field(None, description="방송서버 ID")
    description: Optional[str] = Field(None, description="설명")
    # PRD_Speaker_Geolocation.md v1.0: 위치 정보 JSONB
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")


class SpeakerResponse(BaseModel):
    """
    Schema for Speaker response
    PRD: PRD_Speaker_Geolocation.md v1.0 - geolocation 필드 추가
    SPEC-6.1: category_device 제거 (polymorphic discriminator - API 노출 불필요)
    """
    # Device Base fields
    id: int = Field(..., description="Speaker ID")
    # category_device 제거: polymorphic discriminator로 내부 DB 구조용 (SPEC-6.1)
    number_device: int = Field(..., description="단말 번호 (NATS device_no)")
    group_device: int = Field(..., description="장치 그룹 번호")
    name_device: str = Field(..., description="표시명")
    type_device: str = Field(..., description="장치 타입")
    version: Optional[str] = Field(None, description="버전")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    # Speaker-specific fields
    speaker_type: str = Field(..., description="스피커 타입")
    description: Optional[str] = Field(None, description="설명")
    # PRD_Speaker_Geolocation.md v1.0: 위치 정보 JSONB
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")

    # Nested Server 정보 (server_id 대신 server 객체로 제공)
    server: Optional[ServerNestedResponse] = Field(None, description="연결된 서버 정보")

    model_config = ConfigDict(from_attributes=True)


class SpeakerNestedResponse(BaseModel):
    """
    Speaker Nested Response (Event 등에서 사용) - excludes timestamps
    PRD: PRD_Speaker_Geolocation.md v1.0 - geolocation 필드 추가
    """
    id: int = Field(..., description="Speaker ID")
    category_device: str = Field("speaker", description="디바이스 카테고리")
    number_device: int = Field(..., description="단말 번호 (NATS device_no)")
    name_device: str = Field(..., description="표시명")
    type_device: str = Field(..., description="장치 타입")
    status: str = Field(..., description="상태")
    is_enable: bool = Field(..., description="장비 활성화 여부")
    speaker_type: str = Field(..., description="스피커 타입")
    # PRD_Speaker_Geolocation.md v1.0: 위치 정보 JSONB
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Enclosure Schemas (PRD: PRD_Enclosure_Device.md v1.1)
# 함체관리장비 스키마 정의 - CS-3.2: device.py로 통합
# ============================================================================

# EnclosureDetailInfo 제거됨 (PRD_Enclosure_Metrics_Separation.md v1.0)
# 실시간 측정 데이터는 enclosure_metrics 테이블 및 EnclosureMetricCreate/Response 스키마로 분리됨


class EnclosureThresholdConfig(BaseModel):
    """
    함체 알람 임계값 설정 (JSONB)
    PRD: PRD_Enclosure_Device.md v1.1 - Section 3.3.3
    """
    temp_high: Optional[float] = Field(40.0, description="고온 경보 (°C)")
    temp_low: Optional[float] = Field(-10.0, description="저온 경보 (°C)")
    humidity_high: Optional[float] = Field(80.0, description="고습도 경보 (%)")
    current_high: Optional[float] = Field(10.0, description="과전류 경보 (A)")
    voltage_low: Optional[float] = Field(200.0, description="저전압 경보 (V)")
    vibration_high: Optional[int] = Field(70, description="진동 경보 레벨")

    model_config = ConfigDict(from_attributes=True)


class EnclosureCreate(BaseModel):
    """
    함체 생성 스키마
    PRD: PRD_Enclosure_Device.md v1.1 - Section 4.2
    PRD: PRD_API_Spec_Compliance.md v1.0 - SPEC-004 (is_enable 필드 추가)
    """
    # Device 기본 필드 (필수)
    number_device: int = Field(..., description="장비 번호")
    group_device: int = Field(0, description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., max_length=200, description="장비 이름")
    type_device: EnumDeviceType = Field(EnumDeviceType.IoController, description="장치 타입")
    version: Optional[str] = Field(None, max_length=50, description="버전")
    status: EnumDeviceStatus = Field(
        EnumDeviceStatus.ACTIVATED,
        description="장비 운영 상태 (ACTIVATED/DEACTIVATED/ERROR)"
    )
    is_enable: bool = Field(True, description="장비 활성화 여부")

    # Enclosure 전용 필드
    door_status: EnumDoorStatus = Field(
        EnumDoorStatus.CLOSED,
        description="도어 물리적 상태 (센서 감지): CLOSED/OPEN"
    )
    # detail_info 제거됨 → enclosure_metrics API 사용 (PRD_Enclosure_Metrics_Separation.md v1.0)
    geolocation: Optional[Geolocation] = Field(None, description="위치 정보")
    threshold_config: Optional[EnclosureThresholdConfig] = Field(None, description="알람 임계값")
    heater_enabled: bool = Field(False, description="히터 활성화")
    fan_enabled: bool = Field(False, description="팬 활성화")

    model_config = ConfigDict(from_attributes=True)


class EnclosureUpdate(BaseModel):
    """
    함체 수정 스키마 (PATCH)
    PRD: PRD_Enclosure_Device.md v1.1 - Section 4.2
    PRD: PRD_API_Spec_Compliance.md v1.0 - SPEC-004 (is_enable 필드 추가)

    모든 필드가 선택적입니다. 제공된 필드만 업데이트됩니다.
    """
    # Device 기본 필드 (선택적)
    number_device: Optional[int] = Field(None, description="장비 번호")
    group_device: Optional[int] = Field(None, description="장치 그룹 번호")
    name_device: Optional[str] = Field(None, max_length=200, description="장비 이름")
    version: Optional[str] = Field(None, max_length=50, description="버전")
    status: Optional[EnumDeviceStatus] = Field(
        None,
        description="장비 운영 상태 (ACTIVATED/DEACTIVATED/ERROR)"
    )
    is_enable: Optional[bool] = Field(None, description="장비 활성화 여부")

    # Enclosure 전용 필드 (선택적)
    door_status: Optional[EnumDoorStatus] = Field(
        None,
        description="도어 물리적 상태: CLOSED/OPEN"
    )
    # detail_info 제거됨 → enclosure_metrics API 사용 (PRD_Enclosure_Metrics_Separation.md v1.0)
    geolocation: Optional[Geolocation] = Field(None, description="위치 정보")
    threshold_config: Optional[EnclosureThresholdConfig] = Field(None, description="알람 임계값")
    heater_enabled: Optional[bool] = Field(None, description="히터 활성화")
    fan_enabled: Optional[bool] = Field(None, description="팬 활성화")

    model_config = ConfigDict(from_attributes=True)


class EnclosureResponse(BaseModel):
    """
    함체 응답 스키마
    PRD: PRD_Enclosure_Device.md v1.1 - Section 4.2
    PRD: PRD_API_Spec_Compliance.md v1.0 - SPEC-004 (is_enable 필드 추가)

    Device에서 상속받은 status와 Enclosure 고유의 door_status를 구분:
    - status: 장비 운영 상태 (EnumDeviceStatus: ACTIVATED/DEACTIVATED/ERROR)
    - door_status: 도어 물리적 상태 (EnumDoorStatus: CLOSED/OPEN)
    """
    # Device 기본 필드
    id: int = Field(..., description="Enclosure ID")
    number_device: int = Field(..., description="장비 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., description="장비 이름")
    type_device: str = Field(..., description="장치 타입")
    version: Optional[str] = Field(None, description="버전")
    status: EnumDeviceStatus = Field(
        ...,
        description="장비 운영 상태 (Device 상속): ACTIVATED/DEACTIVATED/ERROR"
    )
    is_enable: bool = Field(..., description="장비 활성화 여부")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    # Enclosure 전용 필드
    door_status: EnumDoorStatus = Field(
        ...,
        description="도어 물리적 상태 (센서 감지): CLOSED/OPEN"
    )
    # detail_info 제거됨 → enclosure_metrics API 사용 (PRD_Enclosure_Metrics_Separation.md v1.0)
    geolocation: Optional[Geolocation] = Field(None, description="위치 정보")
    threshold_config: Optional[EnclosureThresholdConfig] = Field(None, description="알람 임계값")
    heater_enabled: bool = Field(..., description="히터 활성화 상태")
    fan_enabled: bool = Field(..., description="팬 활성화 상태")

    model_config = ConfigDict(from_attributes=True)


class EnclosureControl(BaseModel):
    """
    히터/팬 제어 스키마
    PRD: PRD_Enclosure_Device.md v1.1 - Section 5.3.3

    POST /api/devices/enclosures/{id}/control 엔드포인트에서 사용
    """
    heater_enabled: Optional[bool] = Field(None, description="히터 활성화 (true/false)")
    fan_enabled: Optional[bool] = Field(None, description="팬 활성화 (true/false)")

    model_config = ConfigDict(from_attributes=True)


class EnclosureStatusUpdate(BaseModel):
    """
    도어 상태 업데이트 스키마
    PRD: PRD_Enclosure_Device.md v1.1 - Section 5.3.2
    PRD: PRD_Enclosure_Metrics_Separation.md v1.0 (detail_info 제거)

    PATCH /api/devices/enclosures/{id}/status 엔드포인트에서 사용
    Note: 환경 모니터링 데이터(temperature, humidity 등)는 POST /{id}/metrics API로 이동
    """
    # detail_info 제거됨 → POST /api/devices/enclosures/{id}/metrics 사용
    door_status: Optional[EnumDoorStatus] = Field(
        None,
        description="도어 물리적 상태 (센서 감지): CLOSED/OPEN"
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# EnclosureMetric Schemas (PRD: PRD_Enclosure_Metrics_Separation.md v1.0)
# 함체 환경 모니터링 메트릭 분리 저장 스키마
# ============================================================================

class EnclosureMetricCreate(BaseModel):
    """
    함체 메트릭 생성 스키마
    PRD: PRD_Enclosure_Metrics_Separation.md v1.0 - Section 3.3
    """
    temperature: Optional[float] = Field(None, description="온도 (°C)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="습도 (%)")
    current: Optional[float] = Field(None, ge=0, description="전류 (A)")
    voltage: Optional[float] = Field(None, ge=0, description="전압 (V)")
    vibration: Optional[int] = Field(None, ge=0, le=100, description="진동 레벨 (0-100)")
    ups_battery_level: Optional[int] = Field(None, ge=0, le=100, description="UPS 배터리 잔량 (%)")
    ups_charging: Optional[bool] = Field(None, description="UPS 충전 중 여부")
    detail: Optional[dict] = Field(None, description="추가 상세 정보 (JSONB)")

    model_config = ConfigDict(from_attributes=True)


class EnclosureMetricResponse(BaseModel):
    """
    함체 메트릭 응답 스키마
    PRD: PRD_Enclosure_Metrics_Separation.md v1.0 - Section 3.3
    """
    id: int = Field(..., description="메트릭 ID")
    enclosure_id: int = Field(..., description="함체 ID (FK)")
    temperature: Optional[float] = Field(None, description="온도 (°C)")
    humidity: Optional[float] = Field(None, description="습도 (%)")
    current: Optional[float] = Field(None, description="전류 (A)")
    voltage: Optional[float] = Field(None, description="전압 (V)")
    vibration: Optional[int] = Field(None, description="진동 레벨 (0-100)")
    ups_battery_level: Optional[int] = Field(None, description="UPS 배터리 잔량 (%)")
    ups_charging: Optional[bool] = Field(None, description="UPS 충전 중 여부")
    detail: Optional[dict] = Field(None, description="추가 상세 정보 (JSONB)")
    created_at: datetime = Field(..., description="생성 일시")

    model_config = ConfigDict(from_attributes=True)


class EnclosureMetricLatestResponse(BaseModel):
    """
    함체별 최신 메트릭 응답 스키마
    PRD: PRD_Enclosure_Metrics_Separation.md v1.0 - Section 3.3
    EM-1.4: 전체 조회용 응답 스키마
    """
    enclosure_id: int = Field(..., description="함체 ID")
    enclosure_name: str = Field(..., description="함체 이름")
    latest_metrics: Optional[EnclosureMetricResponse] = Field(None, description="최신 메트릭 정보")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Phase 5: Forward Reference Resolution
# DeviceGroupResponse를 import하고 model_rebuild() 호출하여 순환 참조 해결
# ============================================================================
def _rebuild_models():
    """Rebuild models to resolve forward references for DeviceGroupResponse"""
    from app.schemas.device_group import DeviceGroupResponse
    ControllerResponse.model_rebuild()
    SensorResponse.model_rebuild()
    CameraResponse.model_rebuild()
    SpeakerResponse.model_rebuild()

# 모듈 로드 시 자동으로 model_rebuild() 실행
_rebuild_models()
