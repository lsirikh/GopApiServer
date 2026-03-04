"""
Event Statistics API endpoints

PRD: PRD_EventStatistics_Api.md v2.1
이벤트 통계 집계 API — 대시보드 차트용 경량 응답
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, case, literal_column, union_all, literal
from datetime import datetime
from collections import defaultdict

from app.dependencies import get_db
from app.models.event import Event, DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
from app.models.device import Device, Sensor, Controller, Camera
from app.utils.enums import EnumDeviceCategory, EnumEventCategory
from app.schemas.event_statistics import (
    EventSummaryResponse,
    EventTrendResponse,
    EventTrendItem,
    EventByDeviceResponse,
    EventDashboardResponse,
    ControllerStats,
    CameraStats,
    DailyAverages,
    ActiveDevices,
)
from app.schemas.common import ApiSingleResponse


router = APIRouter()


def _count_detections_by_device_category(db: Session, category: EnumDeviceCategory, start_date, end_date) -> int:
    """DetectionEvent를 Device category_device 기준으로 카운트"""
    return db.query(func.count(DetectionEvent.id)).join(
        Device, Event.device_id == Device.id
    ).filter(
        Device.category_device == category,
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).scalar() or 0


@router.get(
    "/summary",
    response_model=ApiSingleResponse[EventSummaryResponse],
    summary="이벤트 타입별 건수 요약 (원형 그래프 + 요약 카드)",
)
def get_event_summary(
    start_date: datetime = Query(..., description="조회 시작 시간 (ISO 8601)"),
    end_date: datetime = Query(..., description="조회 종료 시간 (ISO 8601)"),
    db: Session = Depends(get_db),
):
    # 1. 기본 건수 집계
    sensor_count = _count_detections_by_device_category(db, EnumDeviceCategory.SENSOR, start_date, end_date)
    camera_count = _count_detections_by_device_category(db, EnumDeviceCategory.CAMERA, start_date, end_date)

    malfunction_count = db.query(func.count(MalfunctionEvent.id)).filter(
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).scalar() or 0

    connection_count = db.query(func.count(ConnectionEvent.id)).filter(
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).scalar() or 0

    action_count = db.query(func.count(ActionEvent.id)).filter(
        ActionEvent.created_at >= start_date,
        ActionEvent.created_at <= end_date,
    ).scalar() or 0

    total = sensor_count + camera_count + malfunction_count + connection_count + action_count

    # 2. 파생 메트릭
    days = max((end_date - start_date).days, 1)

    daily_averages = DailyAverages(
        sensor_detection=round(sensor_count / days, 1),
        camera_detection=round(camera_count / days, 1),
        malfunction=round(malfunction_count / days, 1),
        connection=round(connection_count / days, 1),
        action=round(action_count / days, 1),
    )

    # 3. Active devices
    active_sensors = db.query(func.count(func.distinct(Event.device_id))).join(
        Device, Event.device_id == Device.id
    ).filter(
        Device.category_device == EnumDeviceCategory.SENSOR,
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).scalar() or 0

    active_cameras = db.query(func.count(func.distinct(Event.device_id))).join(
        Device, Event.device_id == Device.id
    ).filter(
        Device.category_device == EnumDeviceCategory.CAMERA,
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).scalar() or 0

    active_controllers = db.query(func.count(func.distinct(Sensor.controller_id))).join(
        Event, Event.device_id == Sensor.id
    ).filter(
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).scalar() or 0

    return ApiSingleResponse(
        message="Event summary statistics retrieved",
        data=EventSummaryResponse(
            start_date=start_date,
            end_date=end_date,
            days_in_range=days,
            total=total,
            sensor_detection=sensor_count,
            camera_detection=camera_count,
            malfunction=malfunction_count,
            connection=connection_count,
            action=action_count,
            daily_averages=daily_averages,
            active_devices=ActiveDevices(
                sensors=active_sensors,
                cameras=active_cameras,
                controllers=active_controllers,
            ),
        ),
    )


def _time_bucket_expr(col, interval: str, db: Session):
    """DB 방언에 따른 시간 버킷 SQL 표현식 반환 (SQLite: strftime, PostgreSQL: to_char)"""
    dialect = db.bind.dialect.name
    if dialect == "postgresql":
        fmt = "YYYY-MM-DD" if interval == "day" else "YYYY-MM-DD HH24"
        return func.to_char(col, fmt)
    else:
        fmt = "%Y-%m-%d" if interval == "day" else "%Y-%m-%d %H"
        return func.strftime(fmt, col)


def _build_trend_series(db: Session, start_date, end_date, interval: str) -> list[EventTrendItem]:
    """시간대별 이벤트 건수 집계"""
    time_fn = _time_bucket_expr(Event.created_at, interval, db)

    # Detection (sensor/camera 분리)
    det_rows = db.query(
        time_fn.label("bucket"),
        Device.category_device,
        func.count(DetectionEvent.id).label("cnt"),
    ).join(
        Device, Event.device_id == Device.id
    ).filter(
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).group_by("bucket", Device.category_device).all()

    # Malfunction
    mal_rows = db.query(
        _time_bucket_expr(Event.created_at, interval, db).label("bucket"),
        func.count(MalfunctionEvent.id).label("cnt"),
    ).filter(
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).group_by("bucket").all()

    # Connection
    con_rows = db.query(
        _time_bucket_expr(Event.created_at, interval, db).label("bucket"),
        func.count(ConnectionEvent.id).label("cnt"),
    ).filter(
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).group_by("bucket").all()

    # Action (별도 테이블)
    act_rows = db.query(
        _time_bucket_expr(ActionEvent.created_at, interval, db).label("bucket"),
        func.count(ActionEvent.id).label("cnt"),
    ).filter(
        ActionEvent.created_at >= start_date,
        ActionEvent.created_at <= end_date,
    ).group_by("bucket").all()

    # 합산
    buckets = defaultdict(lambda: {"sensor_detection": 0, "camera_detection": 0, "malfunction": 0, "connection": 0, "action": 0})

    for row in det_rows:
        cat = row.category_device
        key = "camera_detection" if cat == EnumDeviceCategory.CAMERA else "sensor_detection"
        buckets[row.bucket][key] += row.cnt

    for row in mal_rows:
        buckets[row.bucket]["malfunction"] += row.cnt
    for row in con_rows:
        buckets[row.bucket]["connection"] += row.cnt
    for row in act_rows:
        buckets[row.bucket]["action"] += row.cnt

    series = []
    for bucket_key in sorted(buckets.keys()):
        vals = buckets[bucket_key]
        series.append(EventTrendItem(time_bucket=bucket_key, **vals))

    return series


@router.get(
    "/by-device",
    response_model=ApiSingleResponse[EventByDeviceResponse],
    summary="제어기별/카메라별 이벤트 건수 (막대 그래프)",
)
def get_event_by_device(
    start_date: datetime = Query(..., description="조회 시작 시간 (ISO 8601)"),
    end_date: datetime = Query(..., description="조회 종료 시간 (ISO 8601)"),
    db: Session = Depends(get_db),
):
    # Part 1: 제어기별 센서 이벤트 집계
    # Sensor, Controller 모두 Device JTI 상속 → devices 테이블 충돌 방지용 alias
    CtrlAlias = aliased(Controller, flat=True)
    ctrl_rows = db.query(
        Sensor.controller_id,
        CtrlAlias.name_device.label("controller_name"),
        CtrlAlias.number_device.label("controller_number"),
        func.sum(case((Event.category_event == EnumEventCategory.DETECTION, 1), else_=0)).label("sensor_detection"),
        func.sum(case((Event.category_event == EnumEventCategory.MALFUNCTION, 1), else_=0)).label("malfunction"),
        func.sum(case((Event.category_event == EnumEventCategory.CONNECTION, 1), else_=0)).label("connection"),
    ).select_from(Event).join(
        Sensor, Event.device_id == Sensor.id
    ).join(
        CtrlAlias, Sensor.controller_id == CtrlAlias.id
    ).filter(
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).group_by(Sensor.controller_id, CtrlAlias.name_device, CtrlAlias.number_device).all()

    # Part 1b: 제어기별 action 집계
    # ActionEvent.from_event_id → Event.device_id → Sensor.controller_id
    action_rows = db.query(
        Sensor.controller_id,
        func.count(ActionEvent.id).label("action_count"),
    ).select_from(ActionEvent).join(
        Event, ActionEvent.from_event_id == Event.id
    ).join(
        Sensor, Event.device_id == Sensor.id
    ).filter(
        ActionEvent.created_at >= start_date,
        ActionEvent.created_at <= end_date,
    ).group_by(Sensor.controller_id).all()

    action_by_ctrl = {row.controller_id: row.action_count for row in action_rows}

    controllers = [
        ControllerStats(
            controller_id=row.controller_id,
            controller_name=row.controller_name,
            controller_number=row.controller_number,
            sensor_detection=row.sensor_detection,
            malfunction=row.malfunction,
            connection=row.connection,
            action=action_by_ctrl.get(row.controller_id, 0),
        )
        for row in ctrl_rows
    ]

    # Part 2: 카메라별 AI 탐지 집계
    cam_rows = db.query(
        Device.id.label("camera_id"),
        Device.name_device.label("camera_name"),
        Device.number_device.label("camera_number"),
        func.count(DetectionEvent.id).label("camera_detection"),
    ).join(
        Device, Event.device_id == Device.id
    ).filter(
        Device.category_device == EnumDeviceCategory.CAMERA,
        Event.created_at >= start_date,
        Event.created_at <= end_date,
    ).group_by(Device.id, Device.name_device, Device.number_device).all()

    cameras = [
        CameraStats(
            camera_id=row.camera_id,
            camera_name=row.camera_name,
            camera_number=row.camera_number,
            camera_detection=row.camera_detection,
        )
        for row in cam_rows
    ]

    return ApiSingleResponse(
        message="Event statistics by device retrieved",
        data=EventByDeviceResponse(
            start_date=start_date,
            end_date=end_date,
            controllers=controllers,
            cameras=cameras,
        ),
    )


@router.get(
    "/trend",
    response_model=ApiSingleResponse[EventTrendResponse],
    summary="이벤트 시간대별 건수 추이 (라인 차트)",
)
def get_event_trend(
    start_date: datetime = Query(..., description="조회 시작 시간 (ISO 8601)"),
    end_date: datetime = Query(..., description="조회 종료 시간 (ISO 8601)"),
    interval: str = Query("hour", description="집계 단위: hour/day"),
    db: Session = Depends(get_db),
):
    series = _build_trend_series(db, start_date, end_date, interval)

    return ApiSingleResponse(
        message="Event trend statistics retrieved",
        data=EventTrendResponse(
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            series=series,
        ),
    )


@router.get(
    "/dashboard",
    response_model=ApiSingleResponse[EventDashboardResponse],
    summary="대시보드 통합 통계 (summary + trend + by-device)",
)
def get_event_dashboard(
    start_date: datetime = Query(..., description="조회 시작 시간 (ISO 8601)"),
    end_date: datetime = Query(..., description="조회 종료 시간 (ISO 8601)"),
    interval: str = Query("hour", description="집계 단위: hour/day"),
    db: Session = Depends(get_db),
):
    summary_resp = get_event_summary(start_date, end_date, db)
    trend_resp = get_event_trend(start_date, end_date, interval, db)
    by_device_resp = get_event_by_device(start_date, end_date, db)

    return ApiSingleResponse(
        message="Event dashboard statistics retrieved",
        data=EventDashboardResponse(
            summary=summary_resp.data,
            trend=trend_resp.data,
            by_device=by_device_resp.data,
        ),
    )
