"""
Integration models: EventMapping, EventMappingCamera, EventMappingSpeaker, EventMappingLamp

PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
PRD: PRD_CameraEventMapping_Refactoring.md v2.1
PRD: PRD_Lamp_Device.md v1.1 - EventMappingLamp
"""
from datetime import datetime as dt
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.config import settings
from app.utils.enums import EnumMappingEventCategory, EnumLampColor, EnumBuzzerSound, EnumLightMode


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

    # PRD: PRD_CategoryEvent_Refactoring.md - 필드명 변경 및 Enum 타입 적용
    category_event_mapping = Column(
        SQLEnum(EnumMappingEventCategory),
        nullable=False,
        index=True,
        doc="이벤트 매핑 카테고리 (센서 조합 타입)"
    )
    description = Column(String(500), nullable=True, doc="설명")
    status = Column(Boolean, default=True, nullable=False, doc="활성화 상태")
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None), onupdate=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)

    # ===== Relationships =====
    device_group = relationship("DeviceGroup", back_populates="event_mappings", lazy="joined")

    # Camera Actions (PRD: PRD_CameraEventMapping_Refactoring.md v2.1)
    cameras = relationship(
        "EventMappingCamera",
        back_populates="event_mapping",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Speaker Actions (PRD: PRD_EventMappingSpeaker.md v1.0)
    speakers = relationship(
        "EventMappingSpeaker",
        back_populates="event_mapping",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Lamp Actions (PRD: PRD_Lamp_Device.md v1.1)
    lamps = relationship(
        "EventMappingLamp",
        back_populates="event_mapping",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )


class EventMappingCamera(Base):
    """
    이벤트 매핑 카메라 연동 설정

    PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 7

    EventMapping에서 특정 이벤트 발생 시 실행할 카메라 동작을 정의합니다.
    touring_time은 target_preset.touring_time에서 참조합니다.

    FK Behavior:
    - event_mapping_id: CASCADE DELETE (EventMapping 삭제 시 함께 삭제)
    - camera_id: SET NULL (Camera 삭제 시 NULL로 설정)
    - target_preset_id: SET NULL (CameraPreset 삭제 시 NULL로 설정)
    - home_preset_id: SET NULL (CameraPreset 삭제 시 NULL로 설정)
    """
    __tablename__ = "event_mapping_cameras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # FK: EventMapping (CASCADE DELETE)
    event_mapping_id = Column(
        Integer,
        ForeignKey("event_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # FK: Camera (SET NULL - 카메라 삭제 시 연결만 해제)
    camera_id = Column(
        Integer,
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # FK: 이동 대상 프리셋 (SET NULL)
    # touring_time은 이 preset에서 참조
    target_preset_id = Column(
        Integer,
        ForeignKey("camera_presets.id", ondelete="SET NULL"),
        nullable=True
    )

    # FK: 홈 복귀 프리셋 (SET NULL)
    home_preset_id = Column(
        Integer,
        ForeignKey("camera_presets.id", ondelete="SET NULL"),
        nullable=True
    )

    # target_preset 도착 후 대기 시간 (홈 복귀 전 대기)
    delay_time = Column(Integer, nullable=False, default=0)

    # 상태 및 우선순위
    is_enable = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=True, default=None)  # Optional

    # 타임스탬프
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None),
                        onupdate=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Relationships
    event_mapping = relationship("EventMapping", back_populates="cameras")
    camera = relationship("Camera", foreign_keys=[camera_id])
    target_preset = relationship("CameraPreset", foreign_keys=[target_preset_id])
    home_preset = relationship("CameraPreset", foreign_keys=[home_preset_id])


class EventMappingSpeaker(Base):
    """
    이벤트 매핑 스피커 연동 설정

    PRD: PRD_EventMappingSpeaker.md v1.0

    EventMapping에서 특정 이벤트 발생 시 실행할 스피커 방송을 정의합니다.

    FK Behavior:
    - event_mapping_id: CASCADE DELETE (EventMapping 삭제 시 함께 삭제)
    - speaker_id: SET NULL (Speaker 삭제 시 NULL로 설정)
    - file_group_id: SET NULL (FileGroup 삭제 시 NULL로 설정)
    """
    __tablename__ = "event_mapping_speakers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # FK: EventMapping (CASCADE DELETE)
    event_mapping_id = Column(
        Integer,
        ForeignKey("event_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # FK: Speaker (SET NULL - 스피커 삭제 시 연결만 해제)
    speaker_id = Column(
        Integer,
        ForeignKey("speakers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # FK: FileGroup (SET NULL - 파일그룹 삭제 시 연결만 해제)
    file_group_id = Column(
        Integer,
        ForeignKey("file_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 방송 반복 횟수 (기본값: 1)
    repeat_count = Column(Integer, nullable=False, default=1)

    # 상태 및 우선순위
    is_enable = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=True, default=None)

    # 타임스탬프
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None),
                        onupdate=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Relationships
    event_mapping = relationship("EventMapping", back_populates="speakers")
    speaker = relationship("Speaker", foreign_keys=[speaker_id])
    file_group = relationship("FileGroup", foreign_keys=[file_group_id])


class EventMappingLamp(Base):
    """
    이벤트 매핑 경광등 연동 설정

    PRD: PRD_Lamp_Device.md v1.1 - Section 3.2

    EventMapping에서 특정 이벤트 발생 시 실행할 경광등 동작을 정의합니다.

    FK Behavior:
    - event_mapping_id: CASCADE DELETE (EventMapping 삭제 시 함께 삭제)
    - lamp_id: SET NULL (Lamp 삭제 시 NULL로 설정, 매핑 유지)

    Default Values:
    - color: Red (EnumLampColor)
    - buzzer_time: 5 (초)
    - buzzer_sound: PI-PI-PI (EnumBuzzerSound)
    - light_mode: steady (EnumLightMode)
    - is_enable: True
    - priority: 1
    """
    __tablename__ = "event_mapping_lamps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # FK: EventMapping (CASCADE DELETE)
    event_mapping_id = Column(
        Integer,
        ForeignKey("event_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # FK: Lamp (SET NULL - 경광등 삭제 시 연결만 해제)
    lamp_id = Column(
        Integer,
        ForeignKey("lamps.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 경광등 설정
    color = Column(
        SQLEnum(EnumLampColor),
        nullable=False,
        default=EnumLampColor.RED,
        comment="경광등 색상"
    )
    buzzer_time = Column(
        Integer,
        nullable=False,
        default=5,
        comment="부저 작동 시간 (초)"
    )
    buzzer_sound = Column(
        SQLEnum(EnumBuzzerSound),
        nullable=False,
        default=EnumBuzzerSound.PI_PI_PI,
        comment="부저 소리 패턴"
    )
    light_mode = Column(
        SQLEnum(EnumLightMode),
        nullable=False,
        default=EnumLightMode.STEADY,
        comment="점등 모드"
    )

    # 상태 및 우선순위
    is_enable = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=1)

    # 타임스탬프
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz).replace(tzinfo=None),
                        onupdate=lambda: dt.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Unique constraint: 동일 EventMapping에 동일 Lamp는 1번만 매핑 가능
    __table_args__ = (
        UniqueConstraint('event_mapping_id', 'lamp_id', name='uq_event_mapping_lamp'),
    )

    # Relationships
    event_mapping = relationship("EventMapping", back_populates="lamps")
    lamp = relationship("Lamp", back_populates="event_mapping_lamps", foreign_keys=[lamp_id])
