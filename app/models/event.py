"""
Event models: DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent

PRD: PRD_Event_Device_Refactoring.md v1.1
- device_id FK with SET NULL on delete (Event 영속성 보장)
- device_description: Device 정보 스냅샷 (Device 삭제 후에도 유지)
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime as dt

from app.database import Base
from app.utils.enums import EnumDeviceType, EnumDetectionType, EnumFaultType, EnumTrueFalse
from app.config import settings


class DetectionEvent(Base):
    """
    Detection Event model for managing detection events

    PRD: PRD_Event_Device_Refactoring.md v1.1 적용
    - device_id: Device FK (SET NULL on delete - Event 영속성 보장)
    - device_description: Device 정보 스냅샷 (Device 삭제 후에도 참조 정보 유지)
    - Legacy fields (controller, sensor, type_device) 주석 처리 예정

    Attributes:
        id: Primary key
        group_event: Event group identifier
        type_event: Event type (always "Intrusion")
        device_id: Device FK (nullable, SET NULL on delete)
        device_description: Device info snapshot (auto-generated)
        sequence: Sequence number
        action_reported: Whether action was reported
        result: Detection result type (EnumDetectionType)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_event = Column(String(100), nullable=False, index=True)
    type_event = Column(String(50), nullable=False, default="Intrusion")

    # PRD v1.1: device_id FK with SET NULL (Event 영속성 보장)
    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,  # SET NULL 허용을 위해 nullable
        index=True
    )
    # PRD v1.1: device_description - Device 정보 스냅샷
    device_description = Column(String(500), nullable=True)

    # Legacy fields - 마이그레이션 후 제거 예정
    controller = Column(Integer, nullable=True, index=True)  # nullable로 변경
    sensor = Column(Integer, nullable=True, index=True)  # nullable로 변경
    type_device = Column(SQLEnum(EnumDeviceType), nullable=True)  # nullable로 변경

    sequence = Column(Integer, nullable=False)
    action_reported = Column(String(10), nullable=False, default="False")
    result = Column(SQLEnum(EnumDetectionType), nullable=False)
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    # Polymorphic Device relationship
    device = relationship("Device", foreign_keys=[device_id])

    def __repr__(self):
        return (
            f"<DetectionEvent(id={self.id}, device_id={self.device_id}, "
            f"group_event='{self.group_event}', result='{self.result.value}')>"
        )


class MalfunctionEvent(Base):
    """
    Malfunction Event model for managing device malfunction events

    PRD: PRD_Event_Device_Refactoring.md v1.1 적용
    - device_id: Device FK (SET NULL on delete - Event 영속성 보장)
    - device_description: Device 정보 스냅샷 (Device 삭제 후에도 참조 정보 유지)
    - Legacy fields (controller, sensor, type_device) 주석 처리 예정

    Attributes:
        id: Primary key
        group_event: Event group identifier
        type_event: Event type (always "Fault")
        device_id: Device FK (nullable, SET NULL on delete)
        device_description: Device info snapshot (auto-generated)
        sequence: Sequence number
        action_reported: Whether action was reported (EnumTrueFalse)
        reason: Malfunction reason type (EnumFaultType)
        first_start: First period start value
        first_end: First period end value
        second_start: Second period start value
        second_end: Second period end value
        created_at: Creation timestamp (replaces datetime)
        updated_at: Last update timestamp
    """
    __tablename__ = "malfunction_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_event = Column(String(100), nullable=False, index=True)
    type_event = Column(String(50), nullable=False, default="Fault")

    # PRD v1.1: device_id FK with SET NULL (Event 영속성 보장)
    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,  # SET NULL 허용을 위해 nullable
        index=True
    )
    # PRD v1.1: device_description - Device 정보 스냅샷
    device_description = Column(String(500), nullable=True)

    # Legacy fields - 마이그레이션 후 제거 예정
    controller = Column(Integer, nullable=True, index=True)  # nullable로 변경
    sensor = Column(Integer, nullable=True, index=True)  # nullable로 변경
    type_device = Column(SQLEnum(EnumDeviceType), nullable=True)  # nullable로 변경

    sequence = Column(Integer, nullable=False)
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    first_start = Column(Integer, nullable=False)
    first_end = Column(Integer, nullable=False)
    second_start = Column(Integer, nullable=False)
    second_end = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    # Polymorphic Device relationship
    device = relationship("Device", foreign_keys=[device_id])

    def __repr__(self):
        return (
            f"<MalfunctionEvent(id={self.id}, device_id={self.device_id}, "
            f"group_event='{self.group_event}', reason='{self.reason.value}')>"
        )


class ConnectionEvent(Base):
    """
    Connection Event model for managing device connection events

    PRD: PRD_Event_Device_Refactoring.md v1.1 적용
    - device_id: Device FK (SET NULL on delete - Event 영속성 보장)
    - device_description: Device 정보 스냅샷 (Device 삭제 후에도 참조 정보 유지)
    - Legacy fields (controller, sensor, type_device) 주석 처리 예정

    Attributes:
        id: Primary key
        group_event: Event group identifier
        type_event: Event type (always "Connection")
        device_id: Device FK (nullable, SET NULL on delete)
        device_description: Device info snapshot (auto-generated)
        sequence: Sequence number
        created_at: Creation timestamp (replaces datetime)
        updated_at: Last update timestamp
    """
    __tablename__ = "connection_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_event = Column(String(100), nullable=False, index=True)
    type_event = Column(String(50), nullable=False, default="Connection")

    # PRD v1.1: device_id FK with SET NULL (Event 영속성 보장)
    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,  # SET NULL 허용을 위해 nullable
        index=True
    )
    # PRD v1.1: device_description - Device 정보 스냅샷
    device_description = Column(String(500), nullable=True)

    # Legacy fields - 마이그레이션 후 제거 예정
    controller = Column(Integer, nullable=True, index=True)  # nullable로 변경
    sensor = Column(Integer, nullable=True, index=True)  # nullable로 변경
    type_device = Column(SQLEnum(EnumDeviceType), nullable=True)  # nullable로 변경

    sequence = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    # Polymorphic Device relationship
    device = relationship("Device", foreign_keys=[device_id])

    def __repr__(self):
        return (
            f"<ConnectionEvent(id={self.id}, device_id={self.device_id}, "
            f"group_event='{self.group_event}')>"
        )


class ActionEvent(Base):
    """
    Action Event model for managing user actions on events

    Attributes:
        id: Primary key
        type_event: Event type (always "Action")
        content: Action content description
        user: User who performed the action
        from_event: Referenced event ID
        from_type_event: Type of the referenced event ("Intrusion", "Fault", or "Connection")
        created_at: Creation timestamp (when action was taken)
        updated_at: Last update timestamp
    """
    __tablename__ = "action_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_event = Column(String(50), nullable=False, default="Action")
    content = Column(String(500), nullable=False)
    user = Column(String(100), nullable=False, index=True)
    from_event = Column(Integer, nullable=False, index=True)
    from_type_event = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    def __repr__(self):
        return (
            f"<ActionEvent(id={self.id}, user='{self.user}', "
            f"from_event={self.from_event}, from_type_event='{self.from_type_event}')>"
        )
