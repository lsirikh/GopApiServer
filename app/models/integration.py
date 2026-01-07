"""
Integration models: EventMapping, CameraEventMapping, CameraEventPreset
"""
from datetime import datetime as dt
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.config import settings
from app.utils.enums import EnumCategoryEvent


class EventMapping(Base):
    """
    EventMapping Model

    PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
    이벤트 매핑 설정을 저장합니다.
    DeviceGroup을 통해 어떤 장비 그룹에서 발생한 이벤트에
    어떤 카메라 프리셋을 실행할지 정의합니다.

    ※ group_event (VARCHAR) → device_group_id (FK)로 변경
    """
    __tablename__ = "event_mappings"

    id = Column(Integer, primary_key=True, index=True)
    name_event = Column(String(100), nullable=False, doc="이벤트 매핑 이름")

    # ===== 변경: group_event → device_group_id FK =====
    device_group_id = Column(
        Integer,
        ForeignKey('device_groups.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="장비 그룹 ID (DeviceGroup FK)"
    )

    category_event = Column(
        String(50),
        nullable=False,
        index=True,
        doc="이벤트 카테고리 (detection/malfunction/connection)"
    )
    description = Column(String(500), nullable=True, doc="설명")
    status = Column(Boolean, default=True, nullable=False, doc="활성화 상태")
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    # ===== Relationships =====
    device_group = relationship("DeviceGroup", back_populates="event_mappings", lazy="joined")

    # Camera Actions (PRD: PRD_CameraEventMapping_Refactoring.md v2.1)
    cameras = relationship(
        "EventMappingCamera",
        back_populates="event_mapping",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )


class CameraEventMapping(Base):
    """CameraEventMapping model for camera event integration settings"""
    __tablename__ = "camera_event_mappings"

    id = Column(Integer, primary_key=True, index=True)
    name_event = Column(String(200), nullable=False)
    group_event = Column(String(100), nullable=False, index=True)
    category_event = Column(SQLEnum(EnumCategoryEvent), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)

    # Relationship
    camera_presets = relationship("CameraEventPreset", back_populates="mapping", cascade="all, delete-orphan")


class CameraEventPreset(Base):
    """CameraEventPreset model for camera preset settings"""
    __tablename__ = "camera_event_presets"

    id = Column(Integer, primary_key=True, index=True)
    mapping_id = Column(Integer, ForeignKey("camera_event_mappings.id"), nullable=False, index=True)
    cam_id = Column(Integer, nullable=False)
    url_live = Column(String(500), nullable=True)      # Phase 28.4: Changed from rtsp_uri
    url_record = Column(String(500), nullable=True)    # Phase 28.4: Added for record stream
    category = Column(String(20), nullable=False)
    preset_id = Column(String(50), nullable=True)
    preset_time = Column(Integer, default=0, nullable=False)
    home_preset = Column(Integer, default=0, nullable=False)
    home_time = Column(Integer, default=0, nullable=False)

    # Relationship
    mapping = relationship("CameraEventMapping", back_populates="camera_presets")
