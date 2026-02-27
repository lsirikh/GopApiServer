"""
Device Setting Models
PRD: PRD_Device_Setting.md Section 3

ProxySetting: Server 1:1 운용 설정
CameraSetting: Camera 1:1 기능 설정
"""
from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base
from app.config import settings
from app.utils.enums import (
    EnumOperationMode, EnumWindyMode,
    EnumWeatherMode, EnumCameraVideoMode, EnumOnOff,
    EnumDayNightMode, EnumPalette,
    EnumFocusMode, EnumIrisMode, EnumTrackingStatus,
)


class ProxySetting(Base):
    __tablename__ = "proxy_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    operation_mode = Column(SAEnum(EnumOperationMode), nullable=False, default=EnumOperationMode.NORMAL)
    windy_mode = Column(SAEnum(EnumWindyMode), nullable=False, default=EnumWindyMode.WIND0)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    server = relationship("Server", backref="proxy_setting", uselist=False)


class CameraSetting(Base):
    __tablename__ = "camera_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    weather_mode = Column(SAEnum(EnumWeatherMode), nullable=False, default=EnumWeatherMode.NORMAL)
    camera_mode = Column(SAEnum(EnumCameraVideoMode), nullable=False, default=EnumCameraVideoMode.NORMAL)
    heater = Column(SAEnum(EnumOnOff), nullable=False, default=EnumOnOff.OFF)
    fan = Column(SAEnum(EnumOnOff), nullable=False, default=EnumOnOff.OFF)
    headlight = Column(SAEnum(EnumOnOff), nullable=False, default=EnumOnOff.OFF)
    day_night_mode = Column(SAEnum(EnumDayNightMode), nullable=False, default=EnumDayNightMode.AUTO)
    focus_mode = Column(SAEnum(EnumFocusMode), nullable=False, default=EnumFocusMode.AUTO)
    iris_mode = Column(SAEnum(EnumIrisMode), nullable=False, default=EnumIrisMode.AUTO)
    tracking = Column(SAEnum(EnumTrackingStatus), nullable=False, default=EnumTrackingStatus.IDLE)
    palette = Column(SAEnum(EnumPalette), nullable=True, default=None)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    camera = relationship("Camera", back_populates="setting", uselist=False)
