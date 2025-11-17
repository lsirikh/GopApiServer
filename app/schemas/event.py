"""
Event schemas: DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Union


class DetectionEventCreate(BaseModel):
    """Schema for creating a new DetectionEvent"""
    group_event: str
    type_event: str  # Always "Intrusion"
    controller: int
    sensor: int
    type_device: str  # EnumDeviceType value as string
    sequence: int
    action_reported: str  # EnumTrueFalse value as string
    result: str  # EnumDetectionType value as string
    datetime: datetime


class DetectionEventResponse(BaseModel):
    """Schema for DetectionEvent response (excludes message_type)"""
    id: int
    group_event: str
    type_event: str  # Always "Intrusion"
    controller: int
    sensor: int
    type_device: str  # EnumDeviceType value as string
    sequence: int
    action_reported: str  # EnumTrueFalse value as string
    result: str  # EnumDetectionType value as string
    datetime: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DetectionEventUpdate(BaseModel):
    """Schema for updating a DetectionEvent (all fields optional for PATCH)"""
    group_event: Optional[str] = None
    type_event: Optional[str] = None  # Always "Intrusion"
    controller: Optional[int] = None
    sensor: Optional[int] = None
    type_device: Optional[str] = None  # EnumDeviceType value as string
    sequence: Optional[int] = None
    action_reported: Optional[str] = None  # EnumTrueFalse value as string
    result: Optional[str] = None  # EnumDetectionType value as string
    datetime: Optional[datetime] = None


class MalfunctionEventCreate(BaseModel):
    """Schema for creating a new MalfunctionEvent"""
    group_event: str
    type_event: str  # Always "Fault"
    controller: int
    sensor: int  # 0 if controller fault
    type_device: str  # EnumDeviceType value as string
    sequence: int
    action_reported: str  # EnumTrueFalse value as string
    reason: str  # EnumFaultType value as string
    first_start: int
    first_end: int
    second_start: int
    second_end: int
    datetime: datetime


class MalfunctionEventResponse(BaseModel):
    """Schema for MalfunctionEvent response (excludes message_type)"""
    id: int
    group_event: str
    type_event: str  # Always "Fault"
    controller: int
    sensor: int  # 0 if controller fault
    type_device: str  # EnumDeviceType value as string
    sequence: int
    action_reported: str  # EnumTrueFalse value as string
    reason: str  # EnumFaultType value as string
    first_start: int
    first_end: int
    second_start: int
    second_end: int
    datetime: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MalfunctionEventUpdate(BaseModel):
    """Schema for updating a MalfunctionEvent (all fields optional for PATCH)"""
    group_event: Optional[str] = None
    type_event: Optional[str] = None  # Always "Fault"
    controller: Optional[int] = None
    sensor: Optional[int] = None  # 0 if controller fault
    type_device: Optional[str] = None  # EnumDeviceType value as string
    sequence: Optional[int] = None
    action_reported: Optional[str] = None  # EnumTrueFalse value as string
    reason: Optional[str] = None  # EnumFaultType value as string
    first_start: Optional[int] = None
    first_end: Optional[int] = None
    second_start: Optional[int] = None
    second_end: Optional[int] = None
    datetime: Optional[datetime] = None


class ConnectionEventCreate(BaseModel):
    """Schema for creating a new ConnectionEvent"""
    group_event: str
    type_event: str  # Always "Connection"
    controller: int
    sensor: int
    type_device: str  # EnumDeviceType value as string
    sequence: int
    datetime: datetime


class ConnectionEventResponse(BaseModel):
    """Schema for ConnectionEvent response (excludes message_type)"""
    id: int
    group_event: str
    type_event: str  # Always "Connection"
    controller: int
    sensor: int
    type_device: str  # EnumDeviceType value as string
    sequence: int
    datetime: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConnectionEventUpdate(BaseModel):
    """Schema for updating a ConnectionEvent (all fields optional for PATCH)"""
    group_event: Optional[str] = None
    type_event: Optional[str] = None  # Always "Connection"
    controller: Optional[int] = None
    sensor: Optional[int] = None
    type_device: Optional[str] = None  # EnumDeviceType value as string
    sequence: Optional[int] = None
    datetime: Optional[datetime] = None


class ActionEventCreate(BaseModel):
    """
    Schema for creating a new ActionEvent

    An action event represents a user action taken in response to a source event.
    It uses polymorphic reference to link to detection, malfunction, or connection events.

    Attributes:
        type_event: Event type (always "Action")
        content: Description of the action taken
        user: Username of the person who performed the action
        from_event: ID of the source event being referenced
        from_type_event: Type of source event ("Intrusion", "Fault", or "Connection")
        datetime: Timestamp when the action was taken
    """
    type_event: str  # Always "Action"
    content: str
    user: str
    from_event: int
    from_type_event: str  # "Intrusion", "Fault", or "Connection"
    datetime: datetime


class ActionEventResponse(BaseModel):
    """
    Schema for ActionEvent response

    Response includes the full nested source event object, not just the ID.
    The `from_event` field contains a complete DetectionEventResponse,
    MalfunctionEventResponse, or ConnectionEventResponse object.

    Attributes:
        id: Action event ID
        type_event: Event type (always "Action")
        content: Description of the action taken
        user: Username of the person who performed the action
        from_event: Nested source event object (Detection/Malfunction/Connection)
        datetime: Timestamp when the action was taken
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    id: int
    type_event: str  # Always "Action"
    content: str
    user: str
    from_event: Union['DetectionEventResponse', 'MalfunctionEventResponse', 'ConnectionEventResponse']  # Nested event object
    datetime: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionEventUpdate(BaseModel):
    """Schema for updating an ActionEvent (all fields optional for PATCH)"""
    type_event: Optional[str] = None  # Always "Action"
    content: Optional[str] = None
    user: Optional[str] = None
    from_event: Optional[int] = None
    from_type_event: Optional[str] = None  # "Intrusion", "Fault", or "Connection"
    datetime: Optional[datetime] = None
