"""
Event Statistics Pydantic Schemas

PRD: PRD_EventStatistics_Api.md v2.1
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ===== Trend (라인 차트) =====

class EventTrendItem(BaseModel):
    time_bucket: str = Field(..., description="집계 시간 구간 (예: '2025-01-15 10')")
    sensor_detection: int = Field(0, description="센서 탐지 건수")
    camera_detection: int = Field(0, description="카메라(AI) 탐지 건수")
    malfunction: int = Field(0, description="장애 이벤트 건수")
    connection: int = Field(0, description="연결 이벤트 건수")
    action: int = Field(0, description="조치 이벤트 건수")


class EventTrendResponse(BaseModel):
    interval: str = Field(..., description="집계 단위: hour/day")
    start_date: datetime
    end_date: datetime
    series: list[EventTrendItem] = Field(default_factory=list)


# ===== By Device (막대 그래프) =====

class ControllerStats(BaseModel):
    controller_id: int
    controller_name: Optional[str] = None
    controller_number: int
    sensor_detection: int = 0
    malfunction: int = 0
    connection: int = 0
    action: int = 0


class CameraStats(BaseModel):
    camera_id: int
    camera_name: Optional[str] = None
    camera_number: int
    camera_detection: int = 0


class EventByDeviceResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    controllers: list[ControllerStats] = Field(default_factory=list)
    cameras: list[CameraStats] = Field(default_factory=list)


# ===== Summary (원형 그래프 + 요약 카드) =====

class DailyAverages(BaseModel):
    sensor_detection: float = 0.0
    camera_detection: float = 0.0
    malfunction: float = 0.0
    connection: float = 0.0
    action: float = 0.0


class ActiveDevices(BaseModel):
    sensors: int = 0
    cameras: int = 0
    controllers: int = 0


class EventSummaryResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    days_in_range: int = Field(1, description="조회 기간 일수 (최소 1)")
    total: int = 0
    sensor_detection: int = 0
    camera_detection: int = 0
    malfunction: int = 0
    connection: int = 0
    action: int = 0
    daily_averages: DailyAverages = Field(default_factory=DailyAverages)
    active_devices: ActiveDevices = Field(default_factory=ActiveDevices)


# ===== Dashboard (통합) =====

class EventDashboardResponse(BaseModel):
    summary: EventSummaryResponse
    trend: EventTrendResponse
    by_device: EventByDeviceResponse
