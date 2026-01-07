"""
EventMappingCamera Model

PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 7

이벤트 매핑에 연동된 카메라 설정을 저장합니다.
EventMapping을 Base Node로 사용하여 다양한 Action 타입 중 Camera Action을 정의합니다.
"""
from datetime import datetime as dt
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.config import settings


class EventMappingCamera(Base):
    """
    이벤트 매핑 카메라 연동 설정

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
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz),
                        onupdate=lambda: dt.now(settings.tz), nullable=False)

    # Relationships
    event_mapping = relationship("EventMapping", back_populates="cameras")
    camera = relationship("Camera", foreign_keys=[camera_id])
    target_preset = relationship("CameraPreset", foreign_keys=[target_preset_id])
    home_preset = relationship("CameraPreset", foreign_keys=[home_preset_id])
