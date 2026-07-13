"""
Event Statistics API Tests

PRD: PRD_EventStatistics_Api.md v2.1
TDD: Red → Green → Refactor
"""
import pytest
from datetime import datetime, timedelta

from app.models.device import Controller, Sensor, Camera
from app.models.event import DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
from app.utils.enums import (
    EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory,
    EnumDetectionType, EnumFaultType, EnumEventCategory,
    EnumCameraMode, EnumCameraType,
)


def _create_controller(db, number=1, name="Test Controller"):
    c = Controller(
        number_device=number, group_device=1, name_device=name,
        type_device=EnumDeviceType.IoController, status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100", ip_port=8080,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _create_sensor(db, controller_id, number=1, name="Test Sensor"):
    s = Sensor(
        number_device=number, group_device=1, name_device=name,
        type_device=EnumDeviceType.Multi, status=EnumDeviceStatus.ACTIVATED,
        controller_id=controller_id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _create_camera(db, number=1, name="Test Camera"):
    c = Camera(
        number_device=number, group_device=1, name_device=name,
        type_device=EnumDeviceType.IpCamera, status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.200", ip_port=80,
        mode=EnumCameraMode.ONVIF, category=EnumCameraType.PTZ,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _create_detection(db, device_id, result=EnumDetectionType.PIR_SENSOR, created_at=None):
    evt = DetectionEvent(
        category_event=EnumEventCategory.DETECTION,
        type_event="Intrusion", device_id=device_id,
        action_reported="False", result=result,
    )
    if created_at:
        evt.created_at = created_at
        evt.updated_at = created_at
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def _create_malfunction(db, device_id, created_at=None):
    evt = MalfunctionEvent(
        category_event=EnumEventCategory.MALFUNCTION,
        type_event="Fault", device_id=device_id,
        action_reported="False", reason=EnumFaultType.FAULT_FENCE,
    )
    if created_at:
        evt.created_at = created_at
        evt.updated_at = created_at
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def _create_connection(db, device_id, created_at=None):
    evt = ConnectionEvent(
        category_event=EnumEventCategory.CONNECTION,
        type_event="Connection", device_id=device_id,
    )
    if created_at:
        evt.created_at = created_at
        evt.updated_at = created_at
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def _create_action(db, from_event_id, created_at=None):
    evt = ActionEvent(
        type_event="Action", content="Test action", user="tester",
        from_event_id=from_event_id,
    )
    if created_at:
        evt.created_at = created_at
        evt.updated_at = created_at
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


class TestEventStatisticsSchema:
    """Phase 1: Pydantic 스키마 직렬화 테스트"""

    def test_event_trend_item_serialization(self):
        """1.1 EventTrendItem 직렬화 확인"""
        from app.schemas.event_statistics import EventTrendItem

        item = EventTrendItem(
            time_bucket="2025-01-15 10",
            sensor_detection=3,
            camera_detection=1,
            malfunction=30,
            connection=0,
            action=2,
        )
        data = item.model_dump()
        assert data["time_bucket"] == "2025-01-15 10"
        assert data["sensor_detection"] == 3
        assert data["camera_detection"] == 1
        assert data["malfunction"] == 30
        assert data["connection"] == 0
        assert data["action"] == 2

    def test_event_trend_item_defaults(self):
        """1.1 EventTrendItem 기본값 확인"""
        from app.schemas.event_statistics import EventTrendItem

        item = EventTrendItem(time_bucket="2025-01-15 10")
        assert item.sensor_detection == 0
        assert item.camera_detection == 0
        assert item.malfunction == 0
        assert item.connection == 0
        assert item.action == 0

    def test_event_summary_response_serialization(self):
        """1.1 EventSummaryResponse 직렬화 확인"""
        from app.schemas.event_statistics import EventSummaryResponse, DailyAverages, ActiveDevices

        summary = EventSummaryResponse(
            start_date=datetime(2025, 1, 15),
            end_date=datetime(2025, 1, 22),
            days_in_range=7,
            total=275,
            sensor_detection=150,
            camera_detection=30,
            malfunction=45,
            connection=30,
            action=20,
            daily_averages=DailyAverages(
                sensor_detection=21.4,
                camera_detection=4.3,
                malfunction=6.4,
                connection=4.3,
                action=2.9,
            ),
            active_devices=ActiveDevices(sensors=25, cameras=15, controllers=5),
        )
        data = summary.model_dump()
        assert data["total"] == 275
        assert data["days_in_range"] == 7
        assert data["daily_averages"]["camera_detection"] == 4.3
        assert data["active_devices"]["cameras"] == 15

    def test_event_summary_response_defaults(self):
        """1.1 EventSummaryResponse 기본값 확인"""
        from app.schemas.event_statistics import EventSummaryResponse

        summary = EventSummaryResponse(
            start_date=datetime(2025, 1, 15),
            end_date=datetime(2025, 1, 16),
        )
        assert summary.total == 0
        assert summary.days_in_range == 1
        assert summary.daily_averages.sensor_detection == 0.0
        assert summary.active_devices.cameras == 0

    def test_event_dashboard_response_composition(self):
        """1.1 EventDashboardResponse 합성 확인"""
        from app.schemas.event_statistics import (
            EventDashboardResponse,
            EventSummaryResponse,
            EventTrendResponse,
            EventByDeviceResponse,
        )

        dashboard = EventDashboardResponse(
            summary=EventSummaryResponse(
                start_date=datetime(2025, 1, 15),
                end_date=datetime(2025, 1, 16),
            ),
            trend=EventTrendResponse(
                interval="hour",
                start_date=datetime(2025, 1, 15),
                end_date=datetime(2025, 1, 16),
            ),
            by_device=EventByDeviceResponse(
                start_date=datetime(2025, 1, 15),
                end_date=datetime(2025, 1, 16),
            ),
        )
        data = dashboard.model_dump()
        assert "summary" in data
        assert "trend" in data
        assert "by_device" in data
        assert data["trend"]["series"] == []
        assert data["by_device"]["controllers"] == []
        assert data["by_device"]["cameras"] == []


class TestSummaryApiBasic:
    """Phase 2: Summary API 기본 건수"""

    def test_summary_empty_returns_zeros(self, client):
        """2.1 이벤트 없으면 전부 0"""
        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-16T00:00:00",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["sensor_detection"] == 0
        assert data["camera_detection"] == 0
        assert data["malfunction"] == 0
        assert data["connection"] == 0
        assert data["action"] == 0

    def test_summary_sensor_camera_split(self, client, test_db):
        """2.3 sensor + camera detection 분리 집계 확인"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)
        camera = _create_camera(test_db)

        # 센서 탐지 3건
        for _ in range(3):
            _create_detection(test_db, sensor.id, EnumDetectionType.PIR_SENSOR)
        # 카메라 탐지 2건
        for _ in range(2):
            _create_detection(test_db, camera.id, EnumDetectionType.AI_DETECT)

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["sensor_detection"] == 3
        assert data["camera_detection"] == 2

    def test_summary_malfunction_connection_action(self, client, test_db):
        """2.5 malfunction, connection, action 각각 카운트 확인"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)

        det = _create_detection(test_db, sensor.id)
        _create_malfunction(test_db, sensor.id)
        _create_malfunction(test_db, sensor.id)
        _create_connection(test_db, sensor.id)
        _create_action(test_db, det.id)

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert data["malfunction"] == 2
        assert data["connection"] == 1
        assert data["action"] == 1

    def test_summary_total_equals_sum(self, client, test_db):
        """2.7 total = sensor + camera + malfunction + connection + action"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)
        camera = _create_camera(test_db)

        det = _create_detection(test_db, sensor.id, EnumDetectionType.PIR_SENSOR)
        _create_detection(test_db, camera.id, EnumDetectionType.AI_DETECT)
        _create_malfunction(test_db, sensor.id)
        _create_connection(test_db, sensor.id)
        _create_action(test_db, det.id)

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        expected_total = (
            data["sensor_detection"] + data["camera_detection"]
            + data["malfunction"] + data["connection"] + data["action"]
        )
        assert data["total"] == expected_total
        assert data["total"] == 5


class TestSummaryDerivedMetrics:
    """Phase 2B: Summary 파생 메트릭 (요약 카드)"""

    def test_days_in_range(self, client):
        """2B.1 days_in_range = (end - start).days, 최소 1"""
        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-22T00:00:00",
        })
        data = resp.json()["data"]
        assert data["days_in_range"] == 7

    def test_days_in_range_minimum_one(self, client):
        """2B.1 같은 날이면 days_in_range = 1"""
        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-15T23:59:59",
        })
        data = resp.json()["data"]
        assert data["days_in_range"] == 1

    def test_daily_averages(self, client, test_db):
        """2B.2 daily_averages = count / days_in_range"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)
        # 7건 생성
        for _ in range(7):
            _create_detection(test_db, sensor.id, EnumDetectionType.PIR_SENSOR)

        # 넓은 범위 (이벤트는 현재 시간으로 생성됨) → 7일 범위
        now = datetime.utcnow()
        start = now - timedelta(days=1)
        end = now + timedelta(days=6)

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        })
        data = resp.json()["data"]
        assert data["sensor_detection"] == 7
        assert data["days_in_range"] == 7
        assert data["daily_averages"]["sensor_detection"] == 1.0

    def test_active_devices_cameras(self, client, test_db):
        """2B.4 active_devices.cameras = DISTINCT 카메라 수"""
        cam1 = _create_camera(test_db, number=1, name="Camera 1")
        cam2 = _create_camera(test_db, number=2, name="Camera 2")
        cam3 = _create_camera(test_db, number=3, name="Camera 3")  # 이벤트 없음

        _create_detection(test_db, cam1.id, EnumDetectionType.AI_DETECT)
        _create_detection(test_db, cam1.id, EnumDetectionType.AI_DETECT)
        _create_detection(test_db, cam2.id, EnumDetectionType.AI_DETECT)

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert data["active_devices"]["cameras"] == 2  # cam3은 이벤트 없음

    def test_active_devices_sensors(self, client, test_db):
        """2B.5 active_devices.sensors = DISTINCT 센서 수"""
        controller = _create_controller(test_db)
        s1 = _create_sensor(test_db, controller.id, number=1, name="Sensor 1")
        s2 = _create_sensor(test_db, controller.id, number=2, name="Sensor 2")

        _create_detection(test_db, s1.id)
        _create_detection(test_db, s2.id)

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert data["active_devices"]["sensors"] == 2

    def test_active_devices_controllers(self, client, test_db):
        """2B.6 active_devices.controllers = DISTINCT 제어기 수"""
        c1 = _create_controller(test_db, number=1, name="Controller 1")
        c2 = _create_controller(test_db, number=2, name="Controller 2")
        s1 = _create_sensor(test_db, c1.id, number=1, name="Sensor 1")
        s2 = _create_sensor(test_db, c2.id, number=2, name="Sensor 2")

        _create_detection(test_db, s1.id)
        _create_detection(test_db, s2.id)

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert data["active_devices"]["controllers"] == 2


class TestTrendApi:
    """Phase 3: Trend API (라인 차트)"""

    def test_trend_empty_returns_empty_series(self, client):
        """3.1 이벤트 없으면 빈 series"""
        resp = client.get("/api/events/statistics/trend", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-16T00:00:00",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["interval"] == "hour"
        assert data["series"] == []

    def test_trend_hour_grouping(self, client, test_db):
        """3.3 hour 단위 그룹핑 → time_bucket 형식 'YYYY-MM-DD HH'"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)

        t1 = datetime(2025, 1, 15, 10, 0, 0)
        t2 = datetime(2025, 1, 15, 10, 30, 0)
        t3 = datetime(2025, 1, 15, 11, 0, 0)
        _create_detection(test_db, sensor.id, created_at=t1)
        _create_detection(test_db, sensor.id, created_at=t2)
        _create_detection(test_db, sensor.id, created_at=t3)

        resp = client.get("/api/events/statistics/trend", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-16T00:00:00",
            "interval": "hour",
        })
        data = resp.json()["data"]
        assert len(data["series"]) == 2  # 10시, 11시
        buckets = [s["time_bucket"] for s in data["series"]]
        assert "2025-01-15 10" in buckets
        assert "2025-01-15 11" in buckets
        # 10시에 2건
        hour_10 = next(s for s in data["series"] if s["time_bucket"] == "2025-01-15 10")
        assert hour_10["sensor_detection"] == 2

    def test_trend_day_grouping(self, client, test_db):
        """3.4 day 단위 그룹핑 → time_bucket 형식 'YYYY-MM-DD'"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)

        _create_detection(test_db, sensor.id, created_at=datetime(2025, 1, 15, 10, 0))
        _create_detection(test_db, sensor.id, created_at=datetime(2025, 1, 16, 14, 0))

        resp = client.get("/api/events/statistics/trend", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-17T00:00:00",
            "interval": "day",
        })
        data = resp.json()["data"]
        assert data["interval"] == "day"
        assert len(data["series"]) == 2
        buckets = [s["time_bucket"] for s in data["series"]]
        assert "2025-01-15" in buckets
        assert "2025-01-16" in buckets

    def test_trend_sensor_camera_split(self, client, test_db):
        """3.5 센서/카메라 분리 집계가 trend에도 반영"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)
        camera = _create_camera(test_db)

        t = datetime(2025, 1, 15, 10, 0, 0)
        _create_detection(test_db, sensor.id, EnumDetectionType.PIR_SENSOR, created_at=t)
        _create_detection(test_db, sensor.id, EnumDetectionType.PIR_SENSOR, created_at=t)
        _create_detection(test_db, camera.id, EnumDetectionType.AI_DETECT, created_at=t)

        resp = client.get("/api/events/statistics/trend", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-16T00:00:00",
        })
        data = resp.json()["data"]
        assert len(data["series"]) == 1
        bucket = data["series"][0]
        assert bucket["sensor_detection"] == 2
        assert bucket["camera_detection"] == 1


class TestByDeviceApi:
    """Phase 4: By-Device API (막대 그래프)"""

    def test_by_device_empty_returns_empty_arrays(self, client):
        """4.1 이벤트 없으면 빈 배열"""
        resp = client.get("/api/events/statistics/by-device", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-16T00:00:00",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["controllers"] == []
        assert data["cameras"] == []

    def test_by_device_controller_sensor_detection(self, client, test_db):
        """4.3 제어기 1개 + 센서 이벤트 → controllers에 집계"""
        c1 = _create_controller(test_db, number=1, name="Controller-A")
        s1 = _create_sensor(test_db, c1.id, number=1, name="Sensor-1")

        for _ in range(3):
            _create_detection(test_db, s1.id)

        resp = client.get("/api/events/statistics/by-device", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert len(data["controllers"]) == 1
        ctrl = data["controllers"][0]
        assert ctrl["controller_id"] == c1.id
        assert ctrl["controller_name"] == "Controller-A"
        assert ctrl["sensor_detection"] == 3

    def test_by_device_camera_detection(self, client, test_db):
        """4.4 카메라 이벤트 → cameras에 집계"""
        cam = _create_camera(test_db, number=10, name="AI-Camera-Front")

        for _ in range(5):
            _create_detection(test_db, cam.id, EnumDetectionType.AI_DETECT)

        resp = client.get("/api/events/statistics/by-device", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert len(data["cameras"]) == 1
        cam_data = data["cameras"][0]
        assert cam_data["camera_id"] == cam.id
        assert cam_data["camera_name"] == "AI-Camera-Front"
        assert cam_data["camera_detection"] == 5

    def test_by_device_controller_malfunction_connection(self, client, test_db):
        """4.5 제어기별 malfunction, connection 포함 확인"""
        c1 = _create_controller(test_db)
        s1 = _create_sensor(test_db, c1.id)

        _create_detection(test_db, s1.id)
        _create_malfunction(test_db, s1.id)
        _create_malfunction(test_db, s1.id)
        _create_connection(test_db, s1.id)

        resp = client.get("/api/events/statistics/by-device", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert len(data["controllers"]) == 1
        ctrl = data["controllers"][0]
        assert ctrl["sensor_detection"] == 1
        assert ctrl["malfunction"] == 2
        assert ctrl["connection"] == 1

    def test_by_device_controller_action_count(self, client, test_db):
        """4.6 제어기별 action 집계: 센서 탐지에 대한 조치 건수"""
        c1 = _create_controller(test_db, number=1, name="Controller-A")
        c2 = _create_controller(test_db, number=2, name="Controller-B")
        s1 = _create_sensor(test_db, c1.id, number=1, name="Sensor-1")
        s2 = _create_sensor(test_db, c2.id, number=2, name="Sensor-2")

        # c1 소속 센서의 탐지 → 조치 3건
        det1 = _create_detection(test_db, s1.id)
        det2 = _create_detection(test_db, s1.id)
        _create_action(test_db, det1.id)
        _create_action(test_db, det1.id)
        _create_action(test_db, det2.id)

        # c2 소속 센서의 탐지 → 조치 1건
        det3 = _create_detection(test_db, s2.id)
        _create_action(test_db, det3.id)

        resp = client.get("/api/events/statistics/by-device", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        data = resp.json()["data"]
        assert len(data["controllers"]) == 2

        ctrl_a = next(c for c in data["controllers"] if c["controller_name"] == "Controller-A")
        ctrl_b = next(c for c in data["controllers"] if c["controller_name"] == "Controller-B")
        assert ctrl_a["action"] == 3
        assert ctrl_b["action"] == 1


class TestEdgeCases:
    """Phase 6: 엣지 케이스"""

    def test_event_with_null_device_id_excluded(self, client, test_db):
        """6.1 device_id NULL인 이벤트 → 집계에서 제외 (에러 없음)"""
        from app.models.event import Event
        # device_id가 NULL인 detection 이벤트 (device 없이 생성)
        evt = DetectionEvent(
            category_event=EnumEventCategory.DETECTION,
            type_event="Intrusion", device_id=None,
            action_reported="False", result=EnumDetectionType.PIR_SENSOR,
        )
        test_db.add(evt)
        test_db.commit()

        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2030-01-01T00:00:00",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        # device_id NULL이면 Device JOIN에서 제외 → sensor/camera 0
        assert data["sensor_detection"] == 0
        assert data["camera_detection"] == 0

    def test_start_date_after_end_date_returns_empty(self, client):
        """6.2 start_date > end_date → 빈 결과 (에러 아님)"""
        resp = client.get("/api/events/statistics/summary", params={
            "start_date": "2025-01-16T00:00:00",
            "end_date": "2025-01-15T00:00:00",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0


class TestDashboardApi:
    """Phase 5: Dashboard API (통합)"""

    def test_dashboard_returns_all_sections(self, client, test_db):
        """5.1 summary + trend + by_device 모두 포함"""
        controller = _create_controller(test_db)
        sensor = _create_sensor(test_db, controller.id)
        camera = _create_camera(test_db)

        t = datetime(2025, 1, 15, 10, 0, 0)
        _create_detection(test_db, sensor.id, created_at=t)
        _create_detection(test_db, camera.id, EnumDetectionType.AI_DETECT, created_at=t)
        _create_malfunction(test_db, sensor.id, created_at=t)

        resp = client.get("/api/events/statistics/dashboard", params={
            "start_date": "2025-01-15T00:00:00",
            "end_date": "2025-01-16T00:00:00",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]

        # summary section
        assert "summary" in data
        assert data["summary"]["total"] == 3
        assert data["summary"]["sensor_detection"] == 1
        assert data["summary"]["camera_detection"] == 1
        assert data["summary"]["malfunction"] == 1

        # trend section
        assert "trend" in data
        assert data["trend"]["interval"] == "hour"
        assert len(data["trend"]["series"]) >= 1

        # by_device section
        assert "by_device" in data
        assert len(data["by_device"]["controllers"]) == 1
        assert len(data["by_device"]["cameras"]) == 1
