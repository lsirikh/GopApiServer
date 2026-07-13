"""
Camera Preset, ROI, XyPoint models
PRD: docs/PRD_Camera_Preset_ROI.md

Hierarchical structure:
- Camera 1:N CameraPreset (CASCADE DELETE)
- CameraPreset 1:N ROI (CASCADE DELETE)
- ROI 1:N XyPoint (CASCADE DELETE)
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings


class CameraPreset(Base):
    """
    Camera Preset model for PTZ camera positions.

    Attributes:
        id: Primary key
        camera_id: FK to cameras table
        camera_name: Camera name (auto-filled, for reference)
        preset_index: Preset index within camera (unique per camera)
        preset_name: Preset display name
        touring_time: Time to move from Home to this preset (seconds)
        is_restricted_zone: 감시금지구역 플래그 (v4.6 신규)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "camera_presets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    camera_name = Column(String(200), nullable=False)
    preset_index = Column(Integer, nullable=False)
    preset_name = Column(String(100), nullable=False)
    touring_time = Column(Integer, nullable=False, default=10)
    # v4.6 — 감시금지구역 플래그 (차장 결재 2026-06-19 단순화)
    is_restricted_zone = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="감시금지구역 표시 — true 시 매니저 측에서 통일 처리 (RTSP/녹화/이벤트/화면 모두 차단)"
    )
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Unique constraint: camera_id + preset_index
    __table_args__ = (
        UniqueConstraint('camera_id', 'preset_index', name='uq_preset_camera_index'),
    )

    # Relationships
    camera = relationship("Camera", back_populates="presets", foreign_keys=[camera_id])
    rois = relationship("ROI", back_populates="preset", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<CameraPreset(id={self.id}, camera_id={self.camera_id}, preset_name='{self.preset_name}')>"


class ROI(Base):
    """
    ROI (Region of Interest) model for defining surveillance areas.

    Attributes:
        id: Primary key
        preset_id: FK to camera_presets table
        name: ROI display name
        resolution_width: Reference resolution width
        resolution_height: Reference resolution height
        is_enable: Whether ROI is active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "rois"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    preset_id = Column(Integer, ForeignKey("camera_presets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    resolution_width = Column(Float, nullable=False)
    resolution_height = Column(Float, nullable=False)
    is_enable = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Relationships
    preset = relationship("CameraPreset", back_populates="rois")
    points = relationship("XyPoint", back_populates="roi", cascade="all, delete-orphan", lazy="dynamic", order_by="XyPoint.order")

    def __repr__(self):
        return f"<ROI(id={self.id}, preset_id={self.preset_id}, name='{self.name}')>"


class XyPoint(Base):
    """
    XyPoint model for polygon vertices of ROI.

    Attributes:
        id: Primary key
        roi_id: FK to rois table
        x: X coordinate (0.0 ~ 1.0 normalized or pixel)
        y: Y coordinate (0.0 ~ 1.0 normalized or pixel)
        order: Point order for drawing polygon
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "xy_points"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    roi_id = Column(Integer, ForeignKey("rois.id", ondelete="CASCADE"), nullable=False, index=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Unique constraint: roi_id + order
    __table_args__ = (
        UniqueConstraint('roi_id', 'order', name='uq_xypoint_roi_order'),
    )

    # Relationships
    roi = relationship("ROI", back_populates="points")

    def __repr__(self):
        return f"<XyPoint(id={self.id}, roi_id={self.roi_id}, x={self.x}, y={self.y}, order={self.order})>"
