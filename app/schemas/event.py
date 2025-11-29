"""
Event schemas: DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Union, Literal


# Enum value constants for documentation
DEVICE_TYPE_VALUES = "NONE | Controller | Multi | Fence | Underground | Contact | PIR | IoController | Laser | Cable | IpCamera | SmartSensor | SmartSensor2 | SmartCompound | IpSpeaker | Radar | OpticalCable | Fence_Group"
DETECTION_TYPE_VALUES = "NONE | CABLE_CUTTING | CABLE_CONNECTED | PIR_SENSOR | THERMAL_SENSOR | VIBRATION_SENSOR | CONTACT_SENSOR | DISTANCE_SENSOR"
FAULT_TYPE_VALUES = "FAULT_CONTROLLER | FAULT_FENCE | FAULT_MULTI | FAULT_CABLE_CUTTING | FAULT_ETC"
TRUE_FALSE_VALUES = "True | False"
EVENT_TYPE_VALUES = "None | Intrusion | ContactOn | ContactOff | Connection | Action | Fault | WindyMode | Lowlight | DetectionMode | TrackingMode"


class DetectionEventCreate(BaseModel):
    """Schema for creating a new DetectionEvent"""
    group_event: str = Field(..., example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: str = Field(..., example="Intrusion", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: int = Field(..., example=1, description="컨트롤러 번호")
    sensor: int = Field(..., example=1, description="센서 번호")
    type_device: str = Field(..., example="Fence", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: int = Field(..., example=1, description="시퀀스 번호")
    action_reported: str = Field(..., example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    result: str = Field(..., example="PIR_SENSOR", description=f"탐지 결과 [{DETECTION_TYPE_VALUES}]")


class DetectionEventResponse(BaseModel):
    """Schema for DetectionEvent response"""
    id: int = Field(..., example=1, description="이벤트 ID")
    group_event: str = Field(..., example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: str = Field(..., example="Intrusion", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: int = Field(..., example=1, description="컨트롤러 번호")
    sensor: int = Field(..., example=1, description="센서 번호")
    type_device: str = Field(..., example="Fence", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: int = Field(..., example=1, description="시퀀스 번호")
    action_reported: str = Field(..., example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    result: str = Field(..., example="PIR_SENSOR", description=f"탐지 결과 [{DETECTION_TYPE_VALUES}]")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class DetectionEventUpdate(BaseModel):
    """Schema for updating a DetectionEvent (all fields optional for PATCH)"""
    group_event: Optional[str] = Field(None, example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: Optional[str] = Field(None, example="Intrusion", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: Optional[int] = Field(None, example=1, description="컨트롤러 번호")
    sensor: Optional[int] = Field(None, example=1, description="센서 번호")
    type_device: Optional[str] = Field(None, example="Fence", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: Optional[int] = Field(None, example=1, description="시퀀스 번호")
    action_reported: Optional[str] = Field(None, example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    result: Optional[str] = Field(None, example="PIR_SENSOR", description=f"탐지 결과 [{DETECTION_TYPE_VALUES}]")


class MalfunctionEventCreate(BaseModel):
    """Schema for creating a new MalfunctionEvent"""
    group_event: str = Field(..., example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: str = Field(..., example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: int = Field(..., example=1, description="컨트롤러 번호")
    sensor: int = Field(..., example=0, description="센서 번호 (컨트롤러 고장시 0)")
    type_device: str = Field(..., example="Controller", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: int = Field(..., example=1, description="시퀀스 번호")
    action_reported: str = Field(..., example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    reason: str = Field(..., example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    first_start: int = Field(..., example=0, description="첫 번째 구간 시작")
    first_end: int = Field(..., example=0, description="첫 번째 구간 종료")
    second_start: int = Field(..., example=0, description="두 번째 구간 시작")
    second_end: int = Field(..., example=0, description="두 번째 구간 종료")


class MalfunctionEventResponse(BaseModel):
    """Schema for MalfunctionEvent response"""
    id: int = Field(..., example=1, description="이벤트 ID")
    group_event: str = Field(..., example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: str = Field(..., example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: int = Field(..., example=1, description="컨트롤러 번호")
    sensor: int = Field(..., example=0, description="센서 번호 (컨트롤러 고장시 0)")
    type_device: str = Field(..., example="Controller", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: int = Field(..., example=1, description="시퀀스 번호")
    action_reported: str = Field(..., example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    reason: str = Field(..., example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    first_start: int = Field(..., example=0, description="첫 번째 구간 시작")
    first_end: int = Field(..., example=0, description="첫 번째 구간 종료")
    second_start: int = Field(..., example=0, description="두 번째 구간 시작")
    second_end: int = Field(..., example=0, description="두 번째 구간 종료")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class MalfunctionEventUpdate(BaseModel):
    """Schema for updating a MalfunctionEvent (all fields optional for PATCH)"""
    group_event: Optional[str] = Field(None, example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: Optional[str] = Field(None, example="Fault", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: Optional[int] = Field(None, example=1, description="컨트롤러 번호")
    sensor: Optional[int] = Field(None, example=0, description="센서 번호 (컨트롤러 고장시 0)")
    type_device: Optional[str] = Field(None, example="Controller", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: Optional[int] = Field(None, example=1, description="시퀀스 번호")
    action_reported: Optional[str] = Field(None, example="False", description=f"조치 보고 여부 [{TRUE_FALSE_VALUES}]")
    reason: Optional[str] = Field(None, example="FAULT_CONTROLLER", description=f"고장 원인 [{FAULT_TYPE_VALUES}]")
    first_start: Optional[int] = Field(None, example=0, description="첫 번째 구간 시작")
    first_end: Optional[int] = Field(None, example=0, description="첫 번째 구간 종료")
    second_start: Optional[int] = Field(None, example=0, description="두 번째 구간 시작")
    second_end: Optional[int] = Field(None, example=0, description="두 번째 구간 종료")


class ConnectionEventCreate(BaseModel):
    """Schema for creating a new ConnectionEvent"""
    group_event: str = Field(..., example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: str = Field(..., example="Connection", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: int = Field(..., example=1, description="컨트롤러 번호")
    sensor: int = Field(..., example=1, description="센서 번호")
    type_device: str = Field(..., example="Fence", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: int = Field(..., example=1, description="시퀀스 번호")


class ConnectionEventResponse(BaseModel):
    """Schema for ConnectionEvent response"""
    id: int = Field(..., example=1, description="이벤트 ID")
    group_event: str = Field(..., example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: str = Field(..., example="Connection", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: int = Field(..., example=1, description="컨트롤러 번호")
    sensor: int = Field(..., example=1, description="센서 번호")
    type_device: str = Field(..., example="Fence", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: int = Field(..., example=1, description="시퀀스 번호")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class ConnectionEventUpdate(BaseModel):
    """Schema for updating a ConnectionEvent (all fields optional for PATCH)"""
    group_event: Optional[str] = Field(None, example="GROUP_001", description="이벤트 그룹 식별자")
    type_event: Optional[str] = Field(None, example="Connection", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    controller: Optional[int] = Field(None, example=1, description="컨트롤러 번호")
    sensor: Optional[int] = Field(None, example=1, description="센서 번호")
    type_device: Optional[str] = Field(None, example="Fence", description=f"장치 유형 [{DEVICE_TYPE_VALUES}]")
    sequence: Optional[int] = Field(None, example=1, description="시퀀스 번호")


class ActionEventCreate(BaseModel):
    """Schema for creating a new ActionEvent"""
    type_event: str = Field(..., example="Action", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    content: str = Field(..., example="침입 확인 및 경비 출동", description="조치 내용")
    user: str = Field(..., example="operator1", description="조치자")
    from_event: int = Field(..., example=1, description="원본 이벤트 ID")
    from_type_event: str = Field(..., example="Intrusion", description="원본 이벤트 유형 [Intrusion | Fault | Connection]")
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
    """Schema for updating an ActionEvent (all fields optional for PATCH)"""
    type_event: Optional[str] = Field(None, example="Action", description=f"이벤트 유형 [{EVENT_TYPE_VALUES}]")
    content: Optional[str] = Field(None, example="침입 확인 및 경비 출동", description="조치 내용")
    user: Optional[str] = Field(None, example="operator1", description="조치자")
    from_event: Optional[int] = Field(None, example=1, description="원본 이벤트 ID")
    from_type_event: Optional[str] = Field(None, example="Intrusion", description="원본 이벤트 유형 [Intrusion | Fault | Connection]")
    created_at: Optional[datetime] = Field(None, description="생성 일시")
