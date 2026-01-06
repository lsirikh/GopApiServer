"""
Event models: Event (Base), DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent

PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
- Event Joined Table Inheritance: events (Base) → detection_events, malfunction_events, connection_events
- device_id FK with SET NULL on delete (Event 영속성 보장)
- device_description: Device 정보 스냅샷 (Device 삭제 후에도 유지)
- group_event 필드 제거됨
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime as dt

from app.database import Base
from app.utils.enums import EnumDeviceType, EnumDetectionType, EnumFaultType, EnumTrueFalse
from app.config import settings


class Event(Base):
    """
    Event Base Model - Polymorphic Parent (Joined Table Inheritance)

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    모든 이벤트 타입(Detection, Malfunction, Connection)의 부모 클래스입니다.
    Joined Table Inheritance 패턴을 사용하여 공통 필드를 통합 관리합니다.

    Discriminator: category_event
    - "detection": DetectionEvent 클래스
    - "malfunction": MalfunctionEvent 클래스
    - "connection": ConnectionEvent 클래스

    ※ group_event 필드 제거됨 - DeviceGroup은 device_id를 통해 조회
    """
    __tablename__ = "events"

    # ===== Primary Key =====
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ===== Polymorphic Discriminator =====
    category_event = Column(
        String(50),
        nullable=False,
        index=True,
        doc="이벤트 분류 (detection/malfunction/connection)"
    )

    # ===== Common Fields =====
    type_event = Column(
        String(50),
        nullable=False,
        doc="이벤트 타입명 (Intrusion/Fault/Connection)"
    )

    # ===== Device FK (SET NULL on delete) =====
    device_id = Column(
        Integer,
        ForeignKey('devices.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="장비 ID (삭제 시 NULL 유지)"
    )

    device_description = Column(
        String(500),
        nullable=True,
        doc="장비 정보 스냅샷 (자동 동기화)"
    )

    # PRD v2.7: sequence 필드 제거됨 (Request/Response 모두에서 사용하지 않음)
    # DB 호환성을 위해 nullable로 유지 (레거시 데이터 보존)
    sequence = Column(Integer, nullable=True, doc="시퀀스 번호 (Deprecated - PRD v2.7)")

    # ===== Timestamps =====
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    # ===== Relationships =====
    device = relationship("Device", foreign_keys=[device_id])
    actions = relationship(
        "ActionEvent",
        back_populates="source_event",
        foreign_keys="ActionEvent.from_event_id",
        doc="이 이벤트에 대한 조치 목록"
    )

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_on": category_event,
        "polymorphic_identity": "event"
    }

    def __repr__(self):
        return (
            f"<Event(id={self.id}, category_event='{self.category_event}', "
            f"device_id={self.device_id})>"
        )


class DetectionEvent(Event):
    """
    DetectionEvent Model - Inherits from Event (Joined Table Inheritance)

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    침입 탐지 이벤트입니다.
    Event의 모든 필드를 상속받고, 추가로 탐지 결과 정보를 가집니다.

    Polymorphic Identity: "detection"

    ※ group_event 필드 제거됨
    """
    __tablename__ = "detection_events"

    # ===== Primary Key (FK to events) =====
    id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
        doc="이벤트 ID (events.id 참조)"
    )

    # ===== Detection-Specific Fields =====
    action_reported = Column(
        String(10),
        nullable=False,
        default="False",
        doc="조치 보고 여부"
    )

    result = Column(
        SQLEnum(EnumDetectionType),
        nullable=False,
        doc="탐지 결과 (THERMAL_SENSOR, PIR_SENSOR 등)"
    )

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "detection"
    }

    def __repr__(self):
        return (
            f"<DetectionEvent(id={self.id}, device_id={self.device_id}, "
            f"result='{self.result.value if self.result else None}')>"
        )


class MalfunctionEvent(Event):
    """
    MalfunctionEvent Model - Inherits from Event (Joined Table Inheritance)

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    장비 오동작 이벤트입니다.
    Event의 모든 필드를 상속받고, 추가로 오동작 정보를 가집니다.

    Polymorphic Identity: "malfunction"

    ※ group_event 필드 제거됨
    """
    __tablename__ = "malfunction_events"

    # ===== Primary Key (FK to events) =====
    id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
        doc="이벤트 ID (events.id 참조)"
    )

    # ===== Malfunction-Specific Fields =====
    action_reported = Column(String(10), nullable=False, default="False", doc="조치 보고 여부")
    reason = Column(SQLEnum(EnumFaultType), nullable=False, doc="오동작 원인")
    first_start = Column(Integer, nullable=False)
    first_end = Column(Integer, nullable=False)
    second_start = Column(Integer, nullable=False)
    second_end = Column(Integer, nullable=False)

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "malfunction"
    }

    def __repr__(self):
        return (
            f"<MalfunctionEvent(id={self.id}, device_id={self.device_id}, "
            f"reason='{self.reason.value if self.reason else None}')>"
        )


class ConnectionEvent(Event):
    """
    ConnectionEvent Model - Inherits from Event (Joined Table Inheritance)

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    장비 연결 이벤트입니다.
    Event의 모든 필드만 사용하고, 추가 전용 필드는 없습니다.

    Polymorphic Identity: "connection"

    ※ group_event 필드 제거됨
    """
    __tablename__ = "connection_events"

    # ===== Primary Key (FK to events) =====
    id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
        doc="이벤트 ID (events.id 참조)"
    )

    # 추가 전용 필드 없음 (Base 필드만 사용)

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "connection"
    }

    def __repr__(self):
        return (
            f"<ConnectionEvent(id={self.id}, device_id={self.device_id})>"
        )


class ActionEvent(Base):
    """
    ActionEvent Model

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    이벤트에 대한 사용자 조치를 저장합니다.
    from_event_id로 BaseEvent(events 테이블)를 단일 FK 참조합니다.

    FK 참조:
    - from_event_id → events.id (Polymorphic - 실제 타입은 Detection/Malfunction/Connection)
    - ON DELETE SET NULL: 원본 이벤트 삭제 시 ActionEvent 유지
    """
    __tablename__ = "action_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ===== 단일 FK로 BaseEvent 참조 (Polymorphic) =====
    from_event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="원본 이벤트 ID (events.id 참조)"
    )

    type_event = Column(String(50), nullable=False, default="Action")
    content = Column(String(500), nullable=False, doc="조치 내용")
    user = Column(String(100), nullable=False, index=True, doc="조치한 사용자")

    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    # ===== Relationship =====
    source_event = relationship(
        "Event",
        back_populates="actions",
        foreign_keys=[from_event_id],
        doc="원본 이벤트 (Polymorphic - Detection/Malfunction/Connection)"
    )

    @property
    def source_event_type(self) -> str:
        """원본 이벤트 타입 반환 (하위 호환용)"""
        if self.source_event:
            return self.source_event.type_event  # "Intrusion", "Fault", "Connection"
        return None

    def __repr__(self):
        return (
            f"<ActionEvent(id={self.id}, user='{self.user}', "
            f"from_event_id={self.from_event_id})>"
        )
