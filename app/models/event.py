"""
Event models: DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime as dt
import enum

from app.database import Base
from app.utils.enums import EnumDeviceType


class EnumTrueFalse(str, enum.Enum):
    """True/False enumeration"""
    FALSE = "False"
    TRUE = "True"


class EnumDetectionType(str, enum.Enum):
    """Detection type enumeration"""
    NONE = "NONE"
    CABLE_CUTTING = "CABLE_CUTTING"
    CABLE_CONNECTED = "CABLE_CONNECTED"
    PIR_SENSOR = "PIR_SENSOR"
    THERMAL_SENSOR = "THERMAL_SENSOR"
    VIBRATION_SENSOR = "VIBRATION_SENSOR"
    CONTACT_SENSOR = "CONTACT_SENSOR"
    DISTANCE_SENSOR = "DISTANCE_SENSOR"


class EnumFaultType(str, enum.Enum):
    """Fault type enumeration"""
    FAULT_CONTROLLER = "FAULT_CONTROLLER"
    FAULT_FENCE = "FAULT_FENCE"
    FAULT_MULTI = "FAULT_MULTI"
    FAULT_CABLE_CUTTING = "FAULT_CABLE_CUTTING"
    FAULT_ETC = "FAULT_ETC"


class DetectionEvent(Base):
    """
    Detection Event model for managing detection events

    Attributes:
        id: Primary key
        message_type: Message type identifier (internal use)
        group_event: Event group identifier
        type_event: Event type (always "Intrusion")
        controller: Controller number
        sensor: Sensor number
        type_device: Device type (EnumDeviceType)
        sequence: Sequence number
        action_reported: Whether action was reported (EnumTrueFalse)
        result: Detection result type (EnumDetectionType)
        datetime: Event occurrence datetime
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_event = Column(String(100), nullable=False, index=True)
    type_event = Column(String(50), nullable=False, default="Intrusion")
    controller = Column(Integer, nullable=False, index=True)
    sensor = Column(Integer, nullable=False, index=True)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    sequence = Column(Integer, nullable=False)
    action_reported = Column(SQLEnum(EnumTrueFalse), nullable=False)
    result = Column(SQLEnum(EnumDetectionType), nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=dt.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<DetectionEvent(id={self.id}, controller={self.controller}, "
            f"sensor={self.sensor}, group_event='{self.group_event}', "
            f"action_reported='{self.action_reported.value}', result='{self.result.value}')>"
        )


class MalfunctionEvent(Base):
    """
    Malfunction Event model for managing device malfunction events

    Attributes:
        id: Primary key
        message_type: Message type identifier (internal use)
        group_event: Event group identifier
        type_event: Event type (always "Fault")
        controller: Controller number
        sensor: Sensor number (0 if controller fault)
        type_device: Device type (EnumDeviceType)
        sequence: Sequence number
        action_reported: Whether action was reported (EnumTrueFalse)
        reason: Malfunction reason type (EnumFaultType)
        first_start: First period start value
        first_end: First period end value
        second_start: Second period start value
        second_end: Second period end value
        datetime: Event occurrence datetime
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "malfunction_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_event = Column(String(100), nullable=False, index=True)
    type_event = Column(String(50), nullable=False, default="Fault")
    controller = Column(Integer, nullable=False, index=True)
    sensor = Column(Integer, nullable=False, index=True)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    sequence = Column(Integer, nullable=False)
    action_reported = Column(SQLEnum(EnumTrueFalse), nullable=False)
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    first_start = Column(Integer, nullable=False)
    first_end = Column(Integer, nullable=False)
    second_start = Column(Integer, nullable=False)
    second_end = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=dt.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<MalfunctionEvent(id={self.id}, controller={self.controller}, "
            f"sensor={self.sensor}, group_event='{self.group_event}', "
            f"action_reported='{self.action_reported.value}', reason='{self.reason.value}')>"
        )


class ConnectionEvent(Base):
    """
    Connection Event model for managing device connection events

    Attributes:
        id: Primary key
        message_type: Message type identifier (internal use)
        group_event: Event group identifier
        type_event: Event type (always "Connection")
        controller: Controller number
        sensor: Sensor number
        type_device: Device type (EnumDeviceType)
        sequence: Sequence number
        datetime: Event occurrence datetime
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "connection_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_event = Column(String(100), nullable=False, index=True)
    type_event = Column(String(50), nullable=False, default="Connection")
    controller = Column(Integer, nullable=False, index=True)
    sensor = Column(Integer, nullable=False, index=True)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    sequence = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=dt.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<ConnectionEvent(id={self.id}, controller={self.controller}, "
            f"sensor={self.sensor}, group_event='{self.group_event}')>"
        )


class ActionEvent(Base):
    """
    Action Event model for managing user actions on events

    Attributes:
        id: Primary key
        type_event: Event type (always "Action")
        content: Action content description
        user: User who performed the action
        from_event_id: Referenced event ID (polymorphic)
        from_event_type: Referenced event type (detection/malfunction/connection)
        datetime: Event occurrence datetime
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "action_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_event = Column(String(50), nullable=False, default="Action")
    content = Column(String(500), nullable=False)
    user = Column(String(100), nullable=False, index=True)
    from_event_id = Column(Integer, nullable=False, index=True)
    from_event_type = Column(String(50), nullable=False, index=True)
    datetime = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=dt.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<ActionEvent(id={self.id}, user='{self.user}', "
            f"from_event_type='{self.from_event_type}', from_event_id={self.from_event_id})>"
        )
