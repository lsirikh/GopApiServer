"""
Integration schemas: EventMapping, EventMappingCamera, EventMappingSpeaker, EventMappingLamp

PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
PRD: PRD_CameraEventMapping_Refactoring.md v2.1
PRD: PRD_CategoryEvent_Refactoring.md v1.1
PRD: PRD_Lamp_Device.md v1.1 - EventMappingLamp
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from app.schemas.common import KSTDatetime
from typing import Optional, List

from app.schemas.device import (
    CameraUrls,
    HardwareSpec,
    Geolocation,
    DeviceGroupNestedResponse
)
from app.utils.enums import (
    EnumMappingEventCategory, EnumDeviceType, EnumDeviceStatus,
    EnumCameraMode, EnumCameraType, EnumSpeakerType,
    EnumLampColor, EnumBuzzerSound, EnumLightMode,
)


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
    name_event: str = Field(..., description="이벤트 매핑 이름")
    device_group_id: Optional[int] = Field(None, description="연결된 DeviceGroup ID (FK)")
    category_event_mapping: EnumMappingEventCategory = Field(..., description="이벤트 매핑 카테고리")
    description: Optional[str] = Field(None, description="이벤트 매핑 설명")
    status: bool = Field(True, description="활성화 상태")


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
    created_at: KSTDatetime
    updated_at: KSTDatetime

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
    type_device: EnumDeviceType
    version: Optional[str] = None
    status: EnumDeviceStatus
    is_enable: bool = True
    ip_address: str
    ip_port: int
    mode: EnumCameraMode
    category: EnumCameraType
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
    created_at: KSTDatetime
    updated_at: KSTDatetime

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
    스피커 Nested 응답 - Full Property (timestamp 제외)

    PRD: PRD_EventMappingSpeaker.md v1.0
    PRD: PRD_Speaker_Geolocation.md v1.0
    """
    # Device 공통 필드
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: EnumDeviceType
    version: Optional[str] = None
    status: EnumDeviceStatus
    is_enable: bool = True

    # Speaker 고유 필드
    speaker_type: EnumSpeakerType
    server_id: Optional[int] = None
    description: Optional[str] = None
    geolocation: Optional[Geolocation] = None

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
    created_at: KSTDatetime
    updated_at: KSTDatetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# EventMappingLamp Schemas
# PRD: PRD_Lamp_Device.md v1.1
# ============================================

class EventMappingNestedResponse(BaseModel):
    """
    EventMapping Nested 응답 - EventMappingLamp용 (timestamp 제외)

    PRD: PRD_Lamp_Device.md v1.1 - Section 4.2.4
    """
    id: int
    name_event: str = Field(..., description="이벤트 매핑 이름")
    category_event_mapping: EnumMappingEventCategory = Field(..., description="이벤트 매핑 카테고리")

    model_config = ConfigDict(from_attributes=True)


class LampNestedResponseIntegration(BaseModel):
    """
    경광등 Nested 응답 - Full Property (timestamp 제외)

    PRD: PRD_Lamp_Device.md v1.1 - Section 4.2.4

    Nested Response 규칙 적용:
    - created_at, updated_at 제외 (Nested 객체이므로)
    - user_password 제외 (민감 정보)
    """
    id: int = Field(..., description="Lamp ID", json_schema_extra={"example": 501})
    number_device: int = Field(..., description="장비 번호", json_schema_extra={"example": 5001})
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)", json_schema_extra={"example": 0})
    name_device: str = Field(..., description="장비 이름", json_schema_extra={"example": "Lamp-A-1"})
    type_device: EnumDeviceType = Field(..., description="장치 타입", json_schema_extra={"example": "Lamp"})
    version: Optional[str] = Field(None, description="펌웨어 버전", json_schema_extra={"example": "v1.0.0"})
    status: EnumDeviceStatus = Field(..., description="장비 운영 상태", json_schema_extra={"example": "ACTIVATED"})
    is_enable: bool = Field(True, description="장비 활성화 여부", json_schema_extra={"example": True})
    ip_address: str = Field(..., description="IP 주소", json_schema_extra={"example": "192.168.1.109"})
    ip_port: int = Field(..., description="포트 번호", json_schema_extra={"example": 80})
    user_name: Optional[str] = Field(None, description="접속 사용자명", json_schema_extra={"example": "admin"})
    description: Optional[str] = Field(None, description="설명", json_schema_extra={"example": "GOP 1구역 전방 경광등"})
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보")

    model_config = ConfigDict(from_attributes=True)


class EventMappingLampCreate(BaseModel):
    """
    경광등 연동 생성 스키마

    PRD: PRD_Lamp_Device.md v1.1 - Section 4.2.2
    """
    event_mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    lamp_id: int = Field(..., description="대상 경광등 ID", json_schema_extra={"example": 501})
    color: str = Field("Red", description="경광등 색상 (EnumLampColor)", json_schema_extra={"example": "Red"})
    buzzer_time: int = Field(5, ge=0, description="부저 작동 시간 (초)", json_schema_extra={"example": 5})
    buzzer_sound: str = Field("PI-PI-PI", description="부저 소리 패턴 (EnumBuzzerSound)", json_schema_extra={"example": "PI-PI-PI"})
    light_mode: str = Field("steady", description="점등 모드 (EnumLightMode)", json_schema_extra={"example": "steady"})
    is_enable: bool = Field(True, description="활성화 여부", json_schema_extra={"example": True})
    priority: int = Field(1, ge=1, description="우선순위 (낮을수록 높음)", json_schema_extra={"example": 1})


class EventMappingLampUpdate(BaseModel):
    """
    경광등 연동 수정 스키마 (PATCH)

    PRD: PRD_Lamp_Device.md v1.1 - Section 4.2.2

    모든 필드가 선택적입니다. 제공된 필드만 업데이트됩니다.
    """
    lamp_id: Optional[int] = Field(None, description="대상 경광등 ID", json_schema_extra={"example": 502})
    color: Optional[str] = Field(None, description="경광등 색상 (EnumLampColor)", json_schema_extra={"example": "Orange"})
    buzzer_time: Optional[int] = Field(None, ge=0, description="부저 작동 시간 (초)", json_schema_extra={"example": 10})
    buzzer_sound: Optional[str] = Field(None, description="부저 소리 패턴 (EnumBuzzerSound)", json_schema_extra={"example": "Emergency"})
    light_mode: Optional[str] = Field(None, description="점등 모드 (EnumLightMode)", json_schema_extra={"example": "blinking"})
    is_enable: Optional[bool] = Field(None, description="활성화 여부", json_schema_extra={"example": False})
    priority: Optional[int] = Field(None, ge=1, description="우선순위", json_schema_extra={"example": 2})


class EventMappingLampReplace(BaseModel):
    """
    경광등 연동 전체 수정 스키마 (PUT)

    PRD: PRD_Lamp_Device.md v1.1 - Section 4.2.2
    """
    event_mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    lamp_id: int = Field(..., description="대상 경광등 ID", json_schema_extra={"example": 503})
    color: str = Field(..., description="경광등 색상 (EnumLampColor)", json_schema_extra={"example": "Green"})
    buzzer_time: int = Field(..., ge=0, description="부저 작동 시간 (초)", json_schema_extra={"example": 3})
    buzzer_sound: str = Field(..., description="부저 소리 패턴 (EnumBuzzerSound)", json_schema_extra={"example": "Ambulance"})
    light_mode: str = Field(..., description="점등 모드 (EnumLightMode)", json_schema_extra={"example": "steady"})
    is_enable: bool = Field(..., description="활성화 여부", json_schema_extra={"example": True})
    priority: int = Field(..., ge=1, description="우선순위", json_schema_extra={"example": 1})


class EventMappingLampResponse(BaseModel):
    """
    경광등 연동 응답 스키마 (주체용 - timestamp 포함, Nested)

    PRD: PRD_Lamp_Device.md v1.1 - Section 4.2.3

    Nested Response 포함:
    - event_mapping: EventMappingNestedResponse (id, name_event, category_event_mapping)
    - lamp: LampNestedResponseIntegration (Full Property, timestamp 제외)
    """
    id: int = Field(..., description="EventMappingLamp ID", json_schema_extra={"example": 1})
    event_mapping: EventMappingNestedResponse = Field(..., description="연결된 EventMapping 정보")
    lamp: Optional[LampNestedResponseIntegration] = Field(None, description="연결된 경광등 정보 (삭제 시 null)")
    color: EnumLampColor = Field(..., description="경광등 색상", json_schema_extra={"example": "Red"})
    buzzer_time: int = Field(..., description="부저 작동 시간 (초)", json_schema_extra={"example": 5})
    buzzer_sound: EnumBuzzerSound = Field(..., description="부저 소리 패턴", json_schema_extra={"example": "PI-PI-PI"})
    light_mode: EnumLightMode = Field(..., description="점등 모드", json_schema_extra={"example": "steady"})
    is_enable: bool = Field(..., description="활성화 여부", json_schema_extra={"example": True})
    priority: int = Field(..., description="우선순위", json_schema_extra={"example": 1})
    created_at: KSTDatetime = Field(..., description="생성 일시")
    updated_at: KSTDatetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# EventMapping Bulk Schemas (PRD_EventMapping_BulkOperations.md §4.2~4.5)
# ============================================
class EventMappingCameraBulkCreateRequest(BaseModel):
    """
    카메라 연동 벌크 생성 요청 스키마

    PRD: PRD_EventMapping_BulkOperations.md §4.2
    - 단건 EventMappingCameraCreate 재사용 (per-row 부가 필드 보존)
    - 1~100건 처리 (DeviceGroup device_ids와 동일 상한)
    """
    items: List[EventMappingCameraCreate] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="일괄 생성할 Camera 연동 리스트 (1~100)",
        json_schema_extra={"example": [
            {"camera_id": 101, "target_preset_id": 201, "delay_time": 5, "is_enable": True},
            {"camera_id": 102, "target_preset_id": 202, "delay_time": 3, "is_enable": True},
        ]},
    )

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError('items must not be empty')
        return v


class EventMappingCameraBulkCreateFailure(BaseModel):
    """
    카메라 연동 벌크 생성 실패 row 상세

    PRD: PRD_EventMapping_BulkOperations.md §4.3
    """
    index: int = Field(..., description="요청 items 내 0-based 인덱스", json_schema_extra={"example": 2})
    item: EventMappingCameraCreate = Field(..., description="실패한 원본 입력 row")
    error: str = Field(
        ...,
        description="실패 사유 (예: 'Camera 11 not found')",
        json_schema_extra={"example": "Camera 11 not found"},
    )


class EventMappingCameraBulkCreateResponse(BaseModel):
    """
    카메라 연동 벌크 생성 응답 스키마 (부분 성공 시맨틱)

    PRD: PRD_EventMapping_BulkOperations.md §4.3
    - HTTP 200 + failed_items 분리 반환 (best-effort)
    """
    mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    created_ids: List[int] = Field(
        default_factory=list,
        description="생성된 EventMappingCamera row PK 목록",
        json_schema_extra={"example": [301, 302]},
    )
    failed_items: List[EventMappingCameraBulkCreateFailure] = Field(
        default_factory=list,
        description="실패 row 상세 (index, item, error)",
    )
    skipped_config_ids: List[int] = Field(
        default_factory=list,
        description="(envelope 일관성용 빈 리스트 — 등록 시 분류 없음)",
        json_schema_extra={"example": []},
    )
    not_found_config_ids: List[int] = Field(
        default_factory=list,
        description="(envelope 일관성용 빈 리스트 — 등록 시 분류 없음)",
        json_schema_extra={"example": []},
    )
    message: str = Field(
        ...,
        description="결과 요약 메시지",
        json_schema_extra={"example": "2개 카메라 연동 생성 완료, 1개 실패"},
    )


class EventMappingCameraBulkUnassignRequest(BaseModel):
    """
    카메라 연동 벌크 해제 요청 스키마

    PRD: PRD_EventMapping_BulkOperations.md §4.4
    - DeviceGroup DeviceUnassignRequest와 동일 패턴 (config_ids: List[int], 1~100)
    """
    config_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="해제할 EventMappingCamera row PK 목록 (1~100, 중복 자동 제거)",
        json_schema_extra={"example": [301, 302, 303, 999]},
    )

    @field_validator('config_ids')
    @classmethod
    def validate_config_ids(cls, v):
        if not v:
            raise ValueError('config_ids must not be empty')
        return v


class EventMappingCameraBulkUnassignResponse(BaseModel):
    """
    카메라 연동 벌크 해제 응답 스키마 (멱등성 3-way 분류)

    PRD: PRD_EventMapping_BulkOperations.md §4.5
    - DeviceGroup DeviceBulkRemoveResponse 3-way 미러
    """
    mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    removed_config_ids: List[int] = Field(
        default_factory=list,
        description="실제 삭제된 EventMappingCamera row PK",
        json_schema_extra={"example": [301, 302]},
    )
    skipped_config_ids: List[int] = Field(
        default_factory=list,
        description="row는 존재하나 mapping_id 불일치 (멱등)",
        json_schema_extra={"example": [303]},
    )
    not_found_config_ids: List[int] = Field(
        default_factory=list,
        description="row 자체가 DB에 존재하지 않음",
        json_schema_extra={"example": [999]},
    )
    message: str = Field(
        ...,
        description="결과 요약 메시지",
        json_schema_extra={"example": "2개 카메라 연동 해제 완료, 1개 건너뜀, 1개 없음"},
    )


# ============================================
# EventMappingSpeaker Bulk Schemas
# PRD: PRD_EventMapping_BulkOperations.md §4.2~4.5
# ============================================

class EventMappingSpeakerBulkCreateRequest(BaseModel):
    """
    스피커 연동 벌크 생성 요청 스키마

    PRD: PRD_EventMapping_BulkOperations.md §4.2
    - 단건 EventMappingSpeakerCreate 재사용 (file_group_id/repeat_count per-row 보존)
    """
    items: List[EventMappingSpeakerCreate] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="일괄 생성할 Speaker 연동 리스트 (1~100)",
        json_schema_extra={"example": [
            {"speaker_id": 401, "file_group_id": 11, "repeat_count": 3, "is_enable": True},
            {"speaker_id": 402, "file_group_id": 12, "repeat_count": 1, "is_enable": True},
        ]},
    )

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError('items must not be empty')
        return v


class EventMappingSpeakerBulkCreateFailure(BaseModel):
    """
    스피커 연동 벌크 생성 실패 row 상세

    PRD: PRD_EventMapping_BulkOperations.md §4.3
    """
    index: int = Field(..., description="요청 items 내 0-based 인덱스", json_schema_extra={"example": 1})
    item: EventMappingSpeakerCreate = Field(..., description="실패한 원본 입력 row")
    error: str = Field(
        ...,
        description="실패 사유 (예: 'Speaker 999 not found')",
        json_schema_extra={"example": "Speaker 999 not found"},
    )


class EventMappingSpeakerBulkCreateResponse(BaseModel):
    """
    스피커 연동 벌크 생성 응답 스키마 (부분 성공 시맨틱)

    PRD: PRD_EventMapping_BulkOperations.md §4.3
    """
    mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    created_ids: List[int] = Field(
        default_factory=list,
        description="생성된 EventMappingSpeaker row PK 목록",
        json_schema_extra={"example": [501, 502]},
    )
    failed_items: List[EventMappingSpeakerBulkCreateFailure] = Field(
        default_factory=list,
        description="실패 row 상세 (index, item, error)",
    )
    skipped_config_ids: List[int] = Field(
        default_factory=list,
        description="(envelope 일관성용 빈 리스트 — 등록 시 분류 없음)",
        json_schema_extra={"example": []},
    )
    not_found_config_ids: List[int] = Field(
        default_factory=list,
        description="(envelope 일관성용 빈 리스트 — 등록 시 분류 없음)",
        json_schema_extra={"example": []},
    )
    message: str = Field(
        ...,
        description="결과 요약 메시지",
        json_schema_extra={"example": "2개 스피커 연동 생성 완료, 1개 실패"},
    )


class EventMappingSpeakerBulkUnassignRequest(BaseModel):
    """
    스피커 연동 벌크 해제 요청 스키마

    PRD: PRD_EventMapping_BulkOperations.md §4.4
    """
    config_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="해제할 EventMappingSpeaker row PK 목록 (1~100, 중복 자동 제거)",
        json_schema_extra={"example": [501, 502, 503, 999]},
    )

    @field_validator('config_ids')
    @classmethod
    def validate_config_ids(cls, v):
        if not v:
            raise ValueError('config_ids must not be empty')
        return v


class EventMappingSpeakerBulkUnassignResponse(BaseModel):
    """
    스피커 연동 벌크 해제 응답 스키마 (멱등성 3-way 분류)

    PRD: PRD_EventMapping_BulkOperations.md §4.5
    """
    mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    removed_config_ids: List[int] = Field(
        default_factory=list,
        description="실제 삭제된 EventMappingSpeaker row PK",
        json_schema_extra={"example": [501, 502]},
    )
    skipped_config_ids: List[int] = Field(
        default_factory=list,
        description="row는 존재하나 mapping_id 불일치 (멱등)",
        json_schema_extra={"example": [503]},
    )
    not_found_config_ids: List[int] = Field(
        default_factory=list,
        description="row 자체가 DB에 존재하지 않음",
        json_schema_extra={"example": [999]},
    )
    message: str = Field(
        ...,
        description="결과 요약 메시지",
        json_schema_extra={"example": "2개 스피커 연동 해제 완료, 1개 건너뜀, 1개 없음"},
    )


# ============================================
# EventMappingLamp Bulk Schemas
# PRD: PRD_EventMapping_BulkOperations.md §4.2~4.5
# ============================================

class EventMappingLampBulkCreateRequest(BaseModel):
    """
    경광등 연동 벌크 생성 요청 스키마

    PRD: PRD_EventMapping_BulkOperations.md §4.2
    - 단건 EventMappingLampCreate 재사용 (color/buzzer_time/buzzer_sound/light_mode per-row 보존)

    NOTE: 단건 EventMappingLampCreate가 event_mapping_id를 포함하지만
          벌크 엔드포인트는 path parameter {mapping_id}를 신뢰원으로 사용한다 (라우터에서 무시/덮어쓰기).
    """
    items: List[EventMappingLampCreate] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="일괄 생성할 Lamp 연동 리스트 (1~100)",
        json_schema_extra={"example": [
            {
                "event_mapping_id": 10, "lamp_id": 501,
                "color": "Red", "buzzer_time": 5, "buzzer_sound": "PI-PI-PI",
                "light_mode": "steady", "is_enable": True, "priority": 1,
            },
            {
                "event_mapping_id": 10, "lamp_id": 502,
                "color": "Orange", "buzzer_time": 10, "buzzer_sound": "Emergency",
                "light_mode": "blinking", "is_enable": True, "priority": 2,
            },
        ]},
    )

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError('items must not be empty')
        return v


class EventMappingLampBulkCreateFailure(BaseModel):
    """
    경광등 연동 벌크 생성 실패 row 상세

    PRD: PRD_EventMapping_BulkOperations.md §4.3
    """
    index: int = Field(..., description="요청 items 내 0-based 인덱스", json_schema_extra={"example": 0})
    item: EventMappingLampCreate = Field(..., description="실패한 원본 입력 row")
    error: str = Field(
        ...,
        description="실패 사유 (예: 'Lamp 999 not found')",
        json_schema_extra={"example": "Lamp 999 not found"},
    )


class EventMappingLampBulkCreateResponse(BaseModel):
    """
    경광등 연동 벌크 생성 응답 스키마 (부분 성공 시맨틱)

    PRD: PRD_EventMapping_BulkOperations.md §4.3
    """
    mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    created_ids: List[int] = Field(
        default_factory=list,
        description="생성된 EventMappingLamp row PK 목록",
        json_schema_extra={"example": [701, 702]},
    )
    failed_items: List[EventMappingLampBulkCreateFailure] = Field(
        default_factory=list,
        description="실패 row 상세 (index, item, error)",
    )
    skipped_config_ids: List[int] = Field(
        default_factory=list,
        description="(envelope 일관성용 빈 리스트 — 등록 시 분류 없음)",
        json_schema_extra={"example": []},
    )
    not_found_config_ids: List[int] = Field(
        default_factory=list,
        description="(envelope 일관성용 빈 리스트 — 등록 시 분류 없음)",
        json_schema_extra={"example": []},
    )
    message: str = Field(
        ...,
        description="결과 요약 메시지",
        json_schema_extra={"example": "2개 경광등 연동 생성 완료, 1개 실패"},
    )


class EventMappingLampBulkUnassignRequest(BaseModel):
    """
    경광등 연동 벌크 해제 요청 스키마

    PRD: PRD_EventMapping_BulkOperations.md §4.4
    """
    config_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="해제할 EventMappingLamp row PK 목록 (1~100, 중복 자동 제거)",
        json_schema_extra={"example": [701, 702, 703, 999]},
    )

    @field_validator('config_ids')
    @classmethod
    def validate_config_ids(cls, v):
        if not v:
            raise ValueError('config_ids must not be empty')
        return v


class EventMappingLampBulkUnassignResponse(BaseModel):
    """
    경광등 연동 벌크 해제 응답 스키마 (멱등성 3-way 분류)

    PRD: PRD_EventMapping_BulkOperations.md §4.5
    """
    mapping_id: int = Field(..., description="EventMapping ID", json_schema_extra={"example": 10})
    removed_config_ids: List[int] = Field(
        default_factory=list,
        description="실제 삭제된 EventMappingLamp row PK",
        json_schema_extra={"example": [701, 702]},
    )
    skipped_config_ids: List[int] = Field(
        default_factory=list,
        description="row는 존재하나 mapping_id 불일치 (멱등)",
        json_schema_extra={"example": [703]},
    )
    not_found_config_ids: List[int] = Field(
        default_factory=list,
        description="row 자체가 DB에 존재하지 않음",
        json_schema_extra={"example": [999]},
    )
    message: str = Field(
        ...,
        description="결과 요약 메시지",
        json_schema_extra={"example": "2개 경광등 연동 해제 완료, 1개 건너뜀, 1개 없음"},
    )
