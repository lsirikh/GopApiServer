"""
System Event model
Based on PRD_System_Event.md Section 3
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity


class SystemEvent(Base):
    """
    System Event model (시스템 이벤트)

    Attributes:
        id: Primary key
        server_id: Foreign key to Server (SET NULL - 서버 삭제 시에도 이벤트 보존)
        server_description: 서버 설명 (server_id가 SET NULL되어도 기록 유지)
        type_event: 이벤트 유형 (EnumSystemEventType)
        severity: 심각도 (EnumSystemEventSeverity)
        title: 이벤트 제목
        message: 이벤트 메시지
        detail: 추가 상세 정보 (JSONB)
        source: 이벤트 발생 소스 (PRD 3.2)
        is_acknowledged: 확인 여부
        acknowledged_by: 확인자
        acknowledged_at: 확인 시간
        created_at: 생성 시간
        updated_at: 수정 시간 (PRD 3.2)
        server: Relationship to Server

    PRD Reference: PRD_System_Event.md Section 3
    """
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    server_id = Column(
        Integer,
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    server_description = Column(String(200), nullable=True)  # 서버 삭제 후에도 기록 유지

    # 이벤트 유형 및 심각도
    type_event = Column(
        SQLEnum(EnumSystemEventType),
        nullable=False,
        index=True
    )
    severity = Column(
        SQLEnum(EnumSystemEventSeverity),
        nullable=False,
        default=EnumSystemEventSeverity.INFO,
        index=True
    )

    # 이벤트 내용
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=True)
    detail = Column(JSON, nullable=True)  # 추가 상세 정보
    source = Column(String(100), nullable=True)  # 이벤트 발생 소스 (PRD 3.2)

    # 확인(Acknowledge) 관련
    is_acknowledged = Column(Boolean, nullable=False, default=False, index=True)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz).replace(tzinfo=None),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz).replace(tzinfo=None),
        onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None),
        nullable=True
    )  # PRD 3.2: 수정 시간

    # Relationship to server (SET NULL)
    server = relationship("Server", back_populates="system_events")

    def __repr__(self):
        return (
            f"<SystemEvent(id={self.id}, type_event='{self.type_event.value}', "
            f"severity='{self.severity.value}', server_id={self.server_id}, "
            f"is_acknowledged={self.is_acknowledged})>"
        )
