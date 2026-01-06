"""
Event schemas: DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent

PRD: PRD_Event_Device_Refactoring.md v1.1
- Response에 device (DeviceNestedResponse, Optional) 및 device_description 추가

PRD v2.7: Device Polymorphic Response
- device 필드: Sensor/Controller/Camera 타입에 따라 다른 스키마 반환
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Union, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.device import SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse


# Enum value constants for documentation
DEVICE_TYPE_VALUES = "NONE | Controller | Multi | Fence | Underground | Contact | PIR | IoController | Laser | Cable | IpCamera | SmartSensor | SmartSensor2 | SmartCompound | IpSpeaker | Radar | OpticalCable | Fence_Group"
DETECTION_TYPE_VALUES = "NONE | CABLE_CUTTING | CABLE_CONNECTED | PIR_SENSOR | THERMAL_SENSOR | VIBRATION_SENSOR | CONTACT_SENSOR | DISTANCE_SENSOR"
FAULT_TYPE_VALUES = "FAULT_CONTROLLER | FAULT_FENCE | FAULT_MULTI | FAULT_CABLE_CUTTING | FAULT_ETC"
TRUE_FALSE_VALUES = "True | False"
EVENT_TYPE_VALUES = "None | Intrusion | ContactOn | ContactOff | Connection | Action | Fault | WindyMode | Lowlight | DetectionMode | TrackingMode"


class DetectionEventCreate(BaseModel):
    """
    Schema for creating a new DetectionEvent

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - device_id: Device FK (기존 controller, sensor, type_device 대체)
    - group_event, sequence 필드 제거됨

    PRD v2.8: action_reported 필드 제거
    - 이벤트 생성 시 action_reported는 항상 "False"로 시작
    - ActionEvent 생성/삭제 시 시스템이 자동으로 관리
    """
    type_event: str = Field(..., example="Intrusion", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    device_id: int = Field(..., example=1, description="장치 ID (Device FK)")
    result: str = Field(..., example="PIR_SENSOR", description=f"탐지 결과 [{DETECTION_TYPE_VALUES}]")


class DetectionEventResponse(BaseModel):
    """
    Schema for DetectionEvent response

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - group_event 필드 제거됨
    - device: Polymorphic nested response (Optional, Device 삭제 시 null)
    - device_description: Device 정보 스냅샷

    PRD v1.3: device_id, sequence 필드 제거
    - device_id: device.id에 포함되어 중복
    - sequence: Request 전용 필드

    PRD v1.4: category_event 필드 제거
    - polymorphic inheritance 내부용 필드로 Response에서 불필요

    PRD v2.7: Device Polymorphic Response
    - Sensor → SensorNestedResponse (controller_id 포함)
    - Controller → ControllerNestedResponse (ip_address, ip_port 포함)
    - Camera → CameraNestedResponse (rtsp_uri, mode, category 등 포함)
    """
    id: int = Field(..., example=1, description="이벤트 ID")
    type_event: str = Field(..., example="Intrusion", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    action_reported: str = Field(..., example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    result: str = Field(..., example="PIR_SENSOR", description=f"탐지 결과 [{DETECTION_TYPE_VALUES}]")
    # PRD v2.7: device polymorphic nested response (타입에 따라 다른 스키마)
    device: Optional[Union["SensorNestedResponse", "ControllerNestedResponse", "CameraNestedResponse"]] = Field(None, description="장치 정보 (Polymorphic, Device 삭제 시 null)")
    device_description: Optional[str] = Field(None, description="장치 정보 스냅샷")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class DetectionEventUpdate(BaseModel):
    """
    Schema for updating a DetectionEvent (all fields optional for PATCH)

    PRD v2.1: group_event, controller, sensor, type_device, sequence 필드 제거됨
    - device_id는 수정 불가 (이벤트 생성 시에만 설정)
    """
    type_event: Optional[str] = Field(None, example="Intrusion", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    action_reported: Optional[str] = Field(None, example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    result: Optional[str] = Field(None, example="PIR_SENSOR", description=f"탐지 결과 [{DETECTION_TYPE_VALUES}]")


class MalfunctionEventCreate(BaseModel):
    """
    Schema for creating a new MalfunctionEvent

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - device_id: Device FK (기존 controller, sensor, type_device 대체)
    - group_event, sequence 필드 제거됨

    PRD v2.8: action_reported 필드 제거
    - 이벤트 생성 시 action_reported는 항상 "False"로 시작
    - ActionEvent 생성/삭제 시 시스템이 자동으로 관리
    """
    type_event: str = Field(..., example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    device_id: int = Field(..., example=1, description="장치 ID (Device FK)")
    reason: str = Field(..., example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    first_start: int = Field(..., example=0, description="첫 번째 구간 시작")
    first_end: int = Field(..., example=0, description="첫 번째 구간 종료")
    second_start: int = Field(..., example=0, description="두 번째 구간 시작")
    second_end: int = Field(..., example=0, description="두 번째 구간 종료")


class MalfunctionEventResponse(BaseModel):
    """
    Schema for MalfunctionEvent response

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - group_event 필드 제거됨
    - device: Polymorphic nested response (Optional, Device 삭제 시 null)
    - device_description: Device 정보 스냅샷

    PRD v1.3: device_id, sequence 필드 제거
    - device_id: device.id에 포함되어 중복
    - sequence: Request 전용 필드

    PRD v1.4: category_event 필드 제거
    - polymorphic inheritance 내부용 필드로 Response에서 불필요

    PRD v2.7: Device Polymorphic Response
    - Sensor → SensorNestedResponse (controller_id 포함)
    - Controller → ControllerNestedResponse (ip_address, ip_port 포함)
    - Camera → CameraNestedResponse (rtsp_uri, mode, category 등 포함)
    """
    id: int = Field(..., example=1, description="이벤트 ID")
    type_event: str = Field(..., example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    action_reported: str = Field(..., example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    reason: str = Field(..., example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    first_start: int = Field(..., example=0, description="첫 번째 구간 시작")
    first_end: int = Field(..., example=0, description="첫 번째 구간 종료")
    second_start: int = Field(..., example=0, description="두 번째 구간 시작")
    second_end: int = Field(..., example=0, description="두 번째 구간 종료")
    # PRD v2.7: device polymorphic nested response (타입에 따라 다른 스키마)
    device: Optional[Union["SensorNestedResponse", "ControllerNestedResponse", "CameraNestedResponse"]] = Field(None, description="장치 정보 (Polymorphic, Device 삭제 시 null)")
    device_description: Optional[str] = Field(None, description="장치 정보 스냅샷")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class MalfunctionEventUpdate(BaseModel):
    """
    Schema for updating a MalfunctionEvent (all fields optional for PATCH)

    PRD v2.1: group_event, controller, sensor, type_device, sequence 필드 제거됨
    - device_id는 수정 불가 (이벤트 생성 시에만 설정)
    """
    type_event: Optional[str] = Field(None, example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    action_reported: Optional[str] = Field(None, example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    reason: Optional[str] = Field(None, example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    first_start: Optional[int] = Field(None, example=0, description="첫 번째 구간 시작")
    first_end: Optional[int] = Field(None, example=0, description="첫 번째 구간 종료")
    second_start: Optional[int] = Field(None, example=0, description="두 번째 구간 시작")
    second_end: Optional[int] = Field(None, example=0, description="두 번째 구간 종료")


class ConnectionEventCreate(BaseModel):
    """
    Schema for creating a new ConnectionEvent

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - device_id: Device FK (기존 controller, sensor, type_device 대체)
    - group_event, sequence 필드 제거됨
    """
    type_event: str = Field(..., example="Connection", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    device_id: int = Field(..., example=1, description="장치 ID (Device FK)")


class ConnectionEventResponse(BaseModel):
    """
    Schema for ConnectionEvent response

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - group_event 필드 제거됨
    - device: Polymorphic nested response (Optional, Device 삭제 시 null)
    - device_description: Device 정보 스냅샷

    PRD v1.3: device_id, sequence 필드 제거
    - device_id: device.id에 포함되어 중복
    - sequence: Request 전용 필드

    PRD v1.4: category_event 필드 제거
    - polymorphic inheritance 내부용 필드로 Response에서 불필요

    PRD v2.7: Device Polymorphic Response
    - Sensor → SensorNestedResponse (controller_id 포함)
    - Controller → ControllerNestedResponse (ip_address, ip_port 포함)
    - Camera → CameraNestedResponse (rtsp_uri, mode, category 등 포함)
    """
    id: int = Field(..., example=1, description="이벤트 ID")
    type_event: str = Field(..., example="Connection", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    # PRD v2.7: device polymorphic nested response (타입에 따라 다른 스키마)
    device: Optional[Union["SensorNestedResponse", "ControllerNestedResponse", "CameraNestedResponse"]] = Field(None, description="장치 정보 (Polymorphic, Device 삭제 시 null)")
    device_description: Optional[str] = Field(None, description="장치 정보 스냅샷")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class ConnectionEventUpdate(BaseModel):
    """
    Schema for updating a ConnectionEvent (all fields optional for PATCH)

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - group_event, controller, sensor, type_device, sequence 필드 제거됨
    - device_id는 수정 불가 (이벤트 생성 시에만 설정)
    """
    type_event: Optional[str] = Field(None, example="Connection", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")


class ActionEventCreate(BaseModel):
    """
    Schema for creating a new ActionEvent

    PRD v1.5: from_type_event 필드 제거
    - from_event_id만으로 원본 이벤트 참조 (polymorphic relationship으로 타입 자동 확인)
    """
    type_event: str = Field(..., example="Action", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    content: str = Field(..., example="침입 확인 및 경비 출동", description="조치 내용")
    user: str = Field(..., example="operator1", description="조치자")
    from_event_id: int = Field(..., example=1, description="원본 이벤트 ID (events.id FK)")
    created_at: Optional[datetime] = Field(None, description="생성 일시 (미입력시 자동 생성)")


class ActionEventResponse(BaseModel):
    """Schema for ActionEvent response"""
    id: int = Field(..., example=1, description="이벤트 ID")
    type_event: str = Field(..., example="Action", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    content: str = Field(..., example="침입 확인 및 경비 출동", description="조치 내용")
    user: str = Field(..., example="operator1", description="조치자")
    from_event: Union['DetectionEventResponse', 'MalfunctionEventResponse', 'ConnectionEventResponse'] = Field(..., description="원본 이벤트 객체")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class ActionEventUpdate(BaseModel):
    """
    Schema for updating an ActionEvent (all fields optional for PATCH)

    PRD v1.5: from_type_event 필드 제거
    - from_event_id만으로 원본 이벤트 참조
    - from_event_id 변경 시 polymorphic relationship으로 타입 자동 확인
    """
    type_event: Optional[str] = Field(None, example="Action", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    content: Optional[str] = Field(None, example="침입 확인 및 경비 출동", description="조치 내용")
    user: Optional[str] = Field(None, example="operator1", description="조치자")
    from_event_id: Optional[int] = Field(None, example=1, description="원본 이벤트 ID (events.id FK)")
    created_at: Optional[datetime] = Field(None, description="생성 일시")


# Forward reference resolution for Nested Response schemas
# This must be done after all classes are defined
from app.schemas.device import DeviceNestedResponse, SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse

DetectionEventResponse.model_rebuild()
MalfunctionEventResponse.model_rebuild()
ConnectionEventResponse.model_rebuild()
