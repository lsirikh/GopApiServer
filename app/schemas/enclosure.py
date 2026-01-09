"""
Enclosure Device Schemas
PRD: PRD_Enclosure_Device.md v1.1

함체관리장비 스키마 정의:
- EnclosureDetailInfo: 환경 모니터링 데이터 (JSONB)
- EnclosureThresholdConfig: 알람 임계값 설정 (JSONB)
- EnclosureCreate/Update/Response: CRUD 스키마
- EnclosureControl: 히터/팬 제어 스키마
- EnclosureStatusUpdate: 환경 데이터 업데이트 스키마
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

from app.utils.enums import EnumDoorStatus, EnumDeviceStatus, EnumDeviceType
from app.schemas.device import Geolocation


class EnclosureDetailInfo(BaseModel):
    """
    함체 환경 모니터링 데이터 (JSONB)
    PRD: PRD_Enclosure_Device.md v1.1 - Section 3.3.1
    """
    temperature: Optional[float] = Field(None, description="온도 (°C)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="습도 (%)")
    current: Optional[float] = Field(None, ge=0, description="전류 (A)")
    voltage: Optional[float] = Field(None, ge=0, description="전압 (V)")
    vibration: Optional[int] = Field(None, ge=0, le=100, description="진동 레벨 (0-100)")
    ups_battery_level: Optional[int] = Field(None, ge=0, le=100, description="UPS 배터리 잔량 (%)")
    ups_charging: Optional[bool] = Field(None, description="UPS 충전 중 여부")
    last_updated: Optional[datetime] = Field(None, description="마지막 업데이트 시각")

    model_config = ConfigDict(from_attributes=True)


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

    # Enclosure 전용 필드
    door_status: EnumDoorStatus = Field(
        EnumDoorStatus.CLOSED,
        description="도어 물리적 상태 (센서 감지): CLOSED/OPEN"
    )
    detail_info: Optional[EnclosureDetailInfo] = Field(None, description="환경 모니터링 데이터")
    geolocation: Optional[Geolocation] = Field(None, description="위치 정보")
    threshold_config: Optional[EnclosureThresholdConfig] = Field(None, description="알람 임계값")
    heater_enabled: bool = Field(False, description="히터 활성화")
    fan_enabled: bool = Field(False, description="팬 활성화")

    model_config = ConfigDict(from_attributes=True)


class EnclosureUpdate(BaseModel):
    """
    함체 수정 스키마 (PATCH)
    PRD: PRD_Enclosure_Device.md v1.1 - Section 4.2

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

    # Enclosure 전용 필드 (선택적)
    door_status: Optional[EnumDoorStatus] = Field(
        None,
        description="도어 물리적 상태: CLOSED/OPEN"
    )
    detail_info: Optional[EnclosureDetailInfo] = Field(None, description="환경 모니터링 데이터")
    geolocation: Optional[Geolocation] = Field(None, description="위치 정보")
    threshold_config: Optional[EnclosureThresholdConfig] = Field(None, description="알람 임계값")
    heater_enabled: Optional[bool] = Field(None, description="히터 활성화")
    fan_enabled: Optional[bool] = Field(None, description="팬 활성화")

    model_config = ConfigDict(from_attributes=True)


class EnclosureResponse(BaseModel):
    """
    함체 응답 스키마
    PRD: PRD_Enclosure_Device.md v1.1 - Section 4.2

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
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    # Enclosure 전용 필드
    door_status: EnumDoorStatus = Field(
        ...,
        description="도어 물리적 상태 (센서 감지): CLOSED/OPEN"
    )
    detail_info: Optional[EnclosureDetailInfo] = Field(None, description="환경 모니터링 데이터")
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
    환경 데이터 업데이트 스키마
    PRD: PRD_Enclosure_Device.md v1.1 - Section 5.3.2

    PATCH /api/devices/enclosures/{id}/status 엔드포인트에서 사용
    """
    detail_info: Optional[EnclosureDetailInfo] = Field(
        None,
        description="환경 모니터링 데이터 (temperature, humidity, current, voltage, vibration)"
    )
    door_status: Optional[EnumDoorStatus] = Field(
        None,
        description="도어 물리적 상태 (센서 감지): CLOSED/OPEN"
    )

    model_config = ConfigDict(from_attributes=True)
