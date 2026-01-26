"""
Event schemas: DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent

PRD: PRD_Event_Device_Refactoring.md v1.1
- Response에 device (DeviceNestedResponse, Optional) 및 device_description 추가

PRD v2.7: Device Polymorphic Response
- device 필드: Sensor/Controller/Camera 타입에 따라 다른 스키마 반환
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Union, Literal, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.device import SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse


# Enum value constants for documentation
DEVICE_TYPE_VALUES = "NONE | Controller | Multi | Fence | Underground | Contact | PIR | IoController | Laser | Cable | IpCamera | SmartSensor | SmartSensor2 | SmartCompound | IpSpeaker | Radar | OpticalCable | Fence_Group"
DETECTION_TYPE_VALUES = "NONE | CABLE_CUTTING | CABLE_CONNECTED | PIR_SENSOR | THERMAL_SENSOR | VIBRATION_SENSOR | CONTACT_SENSOR | DISTANCE_SENSOR"
FAULT_TYPE_VALUES = "FAULT_CONTROLLER | FAULT_FENCE | FAULT_MULTI | FAULT_CABLE_CUTTING | FAULT_ETC"
TRUE_FALSE_VALUES = "True | False"
EVENT_TYPE_VALUES = "None | Intrusion | ContactOn | ContactOff | Connection | Action | Fault | WindyMode | Lowlight | DetectionMode | TrackingMode"


# ===== Event Detail JSONB Schemas (PRD_Event_Detail_JsonB.md v1.0) =====

class DetectionDetailObject(BaseModel):
    """AI 탐지 객체 정보"""
    label: str = Field(..., description="객체 레이블 (person, vehicle 등)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0.0~1.0)")
    bbox: List[int] = Field(..., min_length=4, max_length=4, description="바운딩 박스 [x, y, width, height]")


class DetectionDetail(BaseModel):
    """Detection Event 확장 정보 (PRD_Event_Detail_JsonB.md v1.0)"""
    result: Optional[str] = Field(None, description="탐지 결과")
    signal: Optional[int] = Field(None, description="탐지 신호 크기")
    thumbnail: str = Field(..., description="썸네일 HTTP URL (카메라 연동 시 필수)")
    objects: Optional[List[DetectionDetailObject]] = Field(None, description="탐지 객체 목록")
    model: Optional[str] = Field(None, description="AI 모델명")
    inference_ms: Optional[int] = Field(None, description="추론 시간 (ms)")


class MalfunctionDetail(BaseModel):
    """
    Malfunction Event 확장 정보 (2선 케이블 제어기 시스템용)

    PRD_Event_Field_Normalization.md v1.0:
    - reason: 별도 컬럼으로 분리 (이 스키마에서 제거됨)
    - 케이블 위치 정보만 detail에 저장
    """
    first_start: Optional[int] = Field(None, description="첫 번째 케이블 끊어진 위치 시작점")
    first_end: Optional[int] = Field(None, description="첫 번째 케이블 끊어진 위치 끝점")
    second_start: Optional[int] = Field(None, description="두 번째 케이블 끊어진 위치 시작점")
    second_end: Optional[int] = Field(None, description="두 번째 케이블 끊어진 위치 끝점")


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
    # PRD_Event_Detail_JsonB.md v1.0: 탐지 상세 정보
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="탐지 상세 정보 (썸네일, AI 객체 등)",
        json_schema_extra={
            "example": {
                "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
                "signal": 1500,
                "objects": [
                    {"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}
                ],
                "model": "yolov8n",
                "inference_ms": 45
            }
        }
    )


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
    # PRD_Event_Detail_JsonB.md v1.0: 탐지 상세 정보
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="탐지 상세 정보 (썸네일, AI 객체 등)",
        json_schema_extra={
            "example": {
                "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
                "signal": 1500,
                "objects": [
                    {"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}
                ],
                "model": "yolov8n",
                "inference_ms": 45
            }
        }
    )
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
    # PRD_Event_Detail_JsonB.md v1.0: 탐지 상세 정보
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="탐지 상세 정보 (썸네일, AI 객체 등)",
        json_schema_extra={
            "example": {
                "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
                "signal": 1500,
                "objects": [
                    {"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}
                ],
                "model": "yolov8n",
                "inference_ms": 45
            }
        }
    )


class MalfunctionEventCreate(BaseModel):
    """
    Schema for creating a new MalfunctionEvent

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    - device_id: Device FK (기존 controller, sensor, type_device 대체)
    - group_event, sequence 필드 제거됨

    PRD v2.8: action_reported 필드 제거
    - 이벤트 생성 시 action_reported는 항상 "False"로 시작
    - ActionEvent 생성/삭제 시 시스템이 자동으로 관리

    PRD_Event_Field_Normalization.md v1.0:
    - reason: 별도 필드 유지
    - first_start/end, second_start/end: detail JSONB로 이동
    """
    type_event: str = Field(..., example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    device_id: int = Field(..., example=1, description="장치 ID (Device FK)")
    reason: str = Field(..., example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    # PRD_Event_Field_Normalization.md v1.0: 케이블 위치 정보는 detail에 포함
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="오동작 상세 정보 (케이블 위치: first_start, first_end, second_start, second_end)",
        json_schema_extra={
            "example": {
                "first_start": 5,
                "first_end": 5,
                "second_start": 0,
                "second_end": 0
            }
        }
    )


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

    PRD_Event_Field_Normalization.md v1.0:
    - reason: 별도 필드 유지
    - first_start/end, second_start/end: detail JSONB로 이동
    """
    id: int = Field(..., example=1, description="이벤트 ID")
    type_event: str = Field(..., example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    action_reported: str = Field(..., example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    reason: str = Field(..., example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    # PRD v2.7: device polymorphic nested response (타입에 따라 다른 스키마)
    device: Optional[Union["SensorNestedResponse", "ControllerNestedResponse", "CameraNestedResponse"]] = Field(None, description="장치 정보 (Polymorphic, Device 삭제 시 null)")
    device_description: Optional[str] = Field(None, description="장치 정보 스냅샷")
    # PRD_Event_Field_Normalization.md v1.0: 케이블 위치 정보는 detail에 포함
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="오동작 상세 정보 (케이블 위치: first_start, first_end, second_start, second_end)",
        json_schema_extra={
            "example": {
                "first_start": 5,
                "first_end": 5,
                "second_start": 0,
                "second_end": 0
            }
        }
    )
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class MalfunctionEventUpdate(BaseModel):
    """
    Schema for updating a MalfunctionEvent (all fields optional for PATCH)

    PRD v2.1: group_event, controller, sensor, type_device, sequence 필드 제거됨
    - device_id는 수정 불가 (이벤트 생성 시에만 설정)

    PRD_Event_Field_Normalization.md v1.0:
    - reason: 별도 필드 유지
    - first_start/end, second_start/end: detail JSONB로 이동
    """
    type_event: Optional[str] = Field(None, example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    action_reported: Optional[str] = Field(None, example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    reason: Optional[str] = Field(None, example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    # PRD_Event_Field_Normalization.md v1.0: 케이블 위치 정보는 detail에 포함
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="오동작 상세 정보 (케이블 위치: first_start, first_end, second_start, second_end)",
        json_schema_extra={
            "example": {
                "first_start": 5,
                "first_end": 5,
                "second_start": 0,
                "second_end": 0
            }
        }
    )


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
