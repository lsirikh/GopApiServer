"""
EnclosureMetric Tests

PRD: PRD_Enclosure_Metrics_Separation.md v1.0
TDD Approach: Red → Green → Refactor
"""

import pytest


class TestEnclosureMetricSchema:
    """Phase EM-1: EnclosureMetric Schema Tests"""

    def test_enclosure_metric_create_schema_exists(self):
        """EM-1.1: EnclosureMetricCreate 스키마 존재 확인"""
        from app.schemas.device import EnclosureMetricCreate

        assert EnclosureMetricCreate is not None

    def test_enclosure_metric_create_all_fields_optional(self):
        """EM-1.1: 모든 필드 Optional 검증 (collected_at 제거됨)"""
        from app.schemas.device import EnclosureMetricCreate

        # 모든 필드 없이 생성 가능
        metric = EnclosureMetricCreate()
        assert metric is not None

    def test_enclosure_metric_create_temperature_optional(self):
        """EM-1.1: temperature Optional 필드 검증"""
        from app.schemas.device import EnclosureMetricCreate

        # temperature 없이 생성 가능
        metric = EnclosureMetricCreate()
        assert metric.temperature is None

        # temperature 포함하여 생성 가능
        metric_with_temp = EnclosureMetricCreate(temperature=25.5)
        assert metric_with_temp.temperature == 25.5

    def test_enclosure_metric_create_humidity_optional(self):
        """EM-1.1: humidity Optional 필드 검증"""
        from app.schemas.device import EnclosureMetricCreate

        # humidity 없이 생성 가능
        metric = EnclosureMetricCreate()
        assert metric.humidity is None

        # humidity 포함하여 생성 가능
        metric_with_humidity = EnclosureMetricCreate(humidity=65.0)
        assert metric_with_humidity.humidity == 65.0

    def test_enclosure_metric_create_all_fields(self):
        """EM-1.1: 모든 필드 포함 테스트"""
        from app.schemas.device import EnclosureMetricCreate

        metric = EnclosureMetricCreate(
            temperature=25.5,
            humidity=65.0,
            current=5.2,
            voltage=220.0,
            vibration=15,
            ups_battery_level=85,
            ups_charging=True,
            detail={"source": "sensor_1"}
        )

        assert metric.temperature == 25.5
        assert metric.humidity == 65.0
        assert metric.current == 5.2
        assert metric.voltage == 220.0
        assert metric.vibration == 15
        assert metric.ups_battery_level == 85
        assert metric.ups_charging is True
        assert metric.detail == {"source": "sensor_1"}

    def test_enclosure_metric_response_has_id(self):
        """EM-1.2: EnclosureMetricResponse id 필드 존재"""
        from app.schemas.device import EnclosureMetricResponse

        assert hasattr(EnclosureMetricResponse, 'model_fields')
        assert 'id' in EnclosureMetricResponse.model_fields

    def test_enclosure_metric_response_has_enclosure_id(self):
        """EM-1.2: EnclosureMetricResponse enclosure_id 필드 존재"""
        from app.schemas.device import EnclosureMetricResponse

        assert 'enclosure_id' in EnclosureMetricResponse.model_fields

    def test_enclosure_metric_response_has_timestamps(self):
        """EM-1.2: EnclosureMetricResponse created_at 필드 존재 (collected_at 제거됨)"""
        from app.schemas.device import EnclosureMetricResponse

        assert 'created_at' in EnclosureMetricResponse.model_fields
        assert 'collected_at' not in EnclosureMetricResponse.model_fields

    def test_enclosure_metric_temperature_accepts_decimal(self):
        """EM-1.3: temperature Decimal(5,2) 형식 허용"""
        from app.schemas.device import EnclosureMetricCreate

        # 소수점 2자리 허용
        metric = EnclosureMetricCreate(temperature=25.55)
        assert metric.temperature == 25.55

        # 음수 온도도 허용
        metric_negative = EnclosureMetricCreate(temperature=-15.5)
        assert metric_negative.temperature == -15.5

    def test_enclosure_metric_ups_battery_level_range(self):
        """EM-1.3: ups_battery_level 0-100 범위 검증"""
        from app.schemas.device import EnclosureMetricCreate
        from pydantic import ValidationError

        # 정상 범위 (0)
        metric_0 = EnclosureMetricCreate(ups_battery_level=0)
        assert metric_0.ups_battery_level == 0

        # 정상 범위 (100)
        metric_100 = EnclosureMetricCreate(ups_battery_level=100)
        assert metric_100.ups_battery_level == 100

        # 범위 초과 (101) - ValidationError 발생
        with pytest.raises(ValidationError):
            EnclosureMetricCreate(ups_battery_level=101)

        # 범위 미만 (-1) - ValidationError 발생
        with pytest.raises(ValidationError):
            EnclosureMetricCreate(ups_battery_level=-1)


class TestEnclosureMetricModel:
    """Phase EM-2: EnclosureMetric Model Tests"""

    def test_enclosure_metric_model_exists(self):
        """EM-2.1: EnclosureMetric 모델 클래스 존재"""
        from app.models.device import EnclosureMetric

        assert EnclosureMetric is not None

    def test_enclosure_metric_has_enclosure_fk(self):
        """EM-2.1: enclosure_id FK 필드 존재"""
        from app.models.device import EnclosureMetric

        assert hasattr(EnclosureMetric, 'enclosure_id')

    def test_enclosure_metric_has_metric_fields(self):
        """EM-2.1: temperature, humidity 등 메트릭 필드 존재"""
        from app.models.device import EnclosureMetric

        assert hasattr(EnclosureMetric, 'temperature')
        assert hasattr(EnclosureMetric, 'humidity')
        assert hasattr(EnclosureMetric, 'current')
        assert hasattr(EnclosureMetric, 'voltage')
        assert hasattr(EnclosureMetric, 'vibration')
        assert hasattr(EnclosureMetric, 'ups_battery_level')
        assert hasattr(EnclosureMetric, 'ups_charging')

    def test_enclosure_metric_has_detail_jsonb(self):
        """EM-2.1: detail JSONB 필드 존재"""
        from app.models.device import EnclosureMetric

        assert hasattr(EnclosureMetric, 'detail')

    def test_enclosure_metric_has_timestamps(self):
        """EM-2.1: created_at 필드 존재 (collected_at 제거됨)"""
        from app.models.device import EnclosureMetric

        assert not hasattr(EnclosureMetric, 'collected_at')
        assert hasattr(EnclosureMetric, 'created_at')

    def test_enclosure_metric_fk_cascade_delete(self):
        """EM-2.1: CASCADE DELETE 동작 확인 (FK 설정 검증)"""
        from app.models.device import EnclosureMetric
        from sqlalchemy import inspect

        # enclosure_id 컬럼의 FK 설정 확인
        mapper = inspect(EnclosureMetric)
        enclosure_id_col = mapper.columns['enclosure_id']

        # FK가 존재하는지 확인
        assert len(enclosure_id_col.foreign_keys) > 0

        # FK의 ondelete 설정 확인
        fk = list(enclosure_id_col.foreign_keys)[0]
        assert fk.ondelete == "CASCADE"


class TestEnclosureMetricPost:
    """Phase EM-3: POST /api/devices/enclosures/{id}/metrics Tests"""

    def test_post_enclosure_metrics_success(self, client, db_session):
        """EM-3.1: POST 성공 - 201 Created"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime

        # Create an Enclosure first
        enclosure = Enclosure(
            number_device=1,
            group_device=0,
            name_device="Test Enclosure",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # POST metric
        response = client.post(
            f"/api/devices/enclosures/{enclosure.id}/metrics",
            json={
                "temperature": 25.5,
                "humidity": 65.0
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["temperature"] == "25.5"
        assert data["data"]["humidity"] == "65.0"

    def test_post_enclosure_metrics_enclosure_not_found(self, client):
        """EM-3.2: Enclosure 없는 경우 - 404 Not Found"""

        response = client.post(
            "/api/devices/enclosures/99999/metrics",
            json={
                "temperature": 25.5
            }
        )

        assert response.status_code == 404

    def test_post_enclosure_metrics_empty_body_ok(self, client, db_session):
        """EM-3.2: 빈 body도 허용 (모든 필드 Optional)"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure first
        enclosure = Enclosure(
            number_device=2,
            group_device=0,
            name_device="Test Enclosure 2",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # POST with empty body (all fields optional now)
        response = client.post(
            f"/api/devices/enclosures/{enclosure.id}/metrics",
            json={}
        )

        assert response.status_code == 201

    def test_post_enclosure_metrics_response_format(self, client, db_session):
        """EM-3.1: 응답 형식 검증 - GOP 표준"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=3,
            group_device=0,
            name_device="Test Enclosure 3",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # POST metric
        response = client.post(
            f"/api/devices/enclosures/{enclosure.id}/metrics",
            json={
                "temperature": 25.5
            }
        )

        assert response.status_code == 201
        data = response.json()

        # GOP 표준 응답 형식 검증
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "threshold_exceeded" in data

        # data 필드 검증
        assert "id" in data["data"]
        assert "enclosure_id" in data["data"]
        assert "collected_at" not in data["data"]  # collected_at 제거됨
        assert "created_at" in data["data"]

    def test_post_enclosure_metrics_returns_threshold_exceeded_empty(self, client, db_session):
        """EM-3.1: 정상 범위 시 threshold_exceeded 빈 배열"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure with threshold_config
        enclosure = Enclosure(
            number_device=4,
            group_device=0,
            name_device="Test Enclosure 4",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED,
            threshold_config={"temp_high": 50, "temp_low": -10}
        )
        db_session.add(enclosure)
        db_session.commit()

        # POST metric within normal range
        response = client.post(
            f"/api/devices/enclosures/{enclosure.id}/metrics",
            json={
                "temperature": 25.0  # Within normal range
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["threshold_exceeded"] == []

    def test_post_enclosure_metrics_threshold_exceeded_temperature(self, client, db_session):
        """EM-3.3: 온도 임계치 초과 시 threshold_exceeded 반환"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure with threshold_config
        enclosure = Enclosure(
            number_device=5,
            group_device=0,
            name_device="Test Enclosure 5",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED,
            threshold_config={"temp_high": 40, "temp_low": 0}
        )
        db_session.add(enclosure)
        db_session.commit()

        # POST metric exceeding high threshold
        response = client.post(
            f"/api/devices/enclosures/{enclosure.id}/metrics",
            json={
                "temperature": 45.0  # Exceeds temp_high (40)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["threshold_exceeded"]) > 0
        exceeded = data["threshold_exceeded"][0]
        assert exceeded["field"] == "temperature"
        assert exceeded["type"] == "HIGH"
        assert exceeded["value"] == 45.0
        assert exceeded["threshold"] == 40

    def test_post_enclosure_metrics_threshold_exceeded_humidity(self, client, db_session):
        """EM-3.3: 습도 임계치 초과 시 threshold_exceeded 반환"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure with threshold_config
        enclosure = Enclosure(
            number_device=6,
            group_device=0,
            name_device="Test Enclosure 6",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED,
            threshold_config={"humidity_high": 80}
        )
        db_session.add(enclosure)
        db_session.commit()

        # POST metric exceeding humidity threshold
        response = client.post(
            f"/api/devices/enclosures/{enclosure.id}/metrics",
            json={
                "humidity": 90.0  # Exceeds humidity_high (80)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["threshold_exceeded"]) > 0
        exceeded = data["threshold_exceeded"][0]
        assert exceeded["field"] == "humidity"
        assert exceeded["type"] == "HIGH"
        assert exceeded["value"] == 90.0
        assert exceeded["threshold"] == 80

    def test_post_enclosure_metrics_threshold_exceeded_multiple(self, client, db_session):
        """EM-3.3: 다중 임계치 초과 시 threshold_exceeded 다중 반환"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure with multiple thresholds
        enclosure = Enclosure(
            number_device=7,
            group_device=0,
            name_device="Test Enclosure 7",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED,
            threshold_config={
                "temp_high": 40,
                "humidity_high": 80
            }
        )
        db_session.add(enclosure)
        db_session.commit()

        # POST metric exceeding multiple thresholds
        response = client.post(
            f"/api/devices/enclosures/{enclosure.id}/metrics",
            json={
                "temperature": 50.0,  # Exceeds temp_high (40)
                "humidity": 95.0  # Exceeds humidity_high (80)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["threshold_exceeded"]) >= 2

        # Verify both thresholds are exceeded
        fields_exceeded = [e["field"] for e in data["threshold_exceeded"]]
        assert "temperature" in fields_exceeded
        assert "humidity" in fields_exceeded


class TestEnclosureMetricGet:
    """Phase EM-4: GET /api/devices/enclosures/{id}/metrics Tests"""

    def test_get_enclosure_metrics_list_success(self, client, db_session):
        """EM-4.1: GET 목록 조회 - 200 OK"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=10,
            group_device=0,
            name_device="Test Enclosure 10",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create metrics
        metric1 = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="25.0"
        )
        metric2 = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="26.0"
        )
        db_session.add_all([metric1, metric2])
        db_session.commit()

        # GET metrics
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_get_enclosure_metrics_list_empty(self, client, db_session):
        """EM-4.1: 빈 배열 반환"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure without metrics
        enclosure = Enclosure(
            number_device=11,
            group_device=0,
            name_device="Test Enclosure 11",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # GET metrics
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_get_enclosure_metrics_list_with_limit(self, client, db_session):
        """EM-4.1: limit 파라미터 동작"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=12,
            group_device=0,
            name_device="Test Enclosure 12",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create multiple metrics
        for i in range(5):
            metric = EnclosureMetric(
                enclosure_id=enclosure.id,
                temperature=str(20 + i)
            )
            db_session.add(metric)
        db_session.commit()

        # GET metrics with limit
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3

    def test_get_enclosure_metrics_list_enclosure_not_found(self, client):
        """EM-4.1: Enclosure 없는 경우 - 404"""
        response = client.get("/api/devices/enclosures/99999/metrics")
        assert response.status_code == 404

    def test_get_enclosure_metrics_latest_success(self, client, db_session):
        """EM-4.2: GET /api/devices/enclosures/{id}/metrics/latest - 200 OK"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime, timedelta
        import time

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=13,
            group_device=0,
            name_device="Test Enclosure 13",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create metrics with different created_at timestamps
        metric_old = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="20.0"
        )
        db_session.add(metric_old)
        db_session.commit()

        # Small delay to ensure different created_at
        time.sleep(0.01)

        metric_new = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="30.0"
        )
        db_session.add(metric_new)
        db_session.commit()

        # GET latest metric
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["temperature"] == "30.0"  # Most recent (created last)

    def test_get_enclosure_metrics_latest_no_metrics(self, client, db_session):
        """EM-4.2: 메트릭 없는 경우 - 404 Not Found"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure without metrics
        enclosure = Enclosure(
            number_device=14,
            group_device=0,
            name_device="Test Enclosure 14",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # GET latest metric
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics/latest")

        assert response.status_code == 404

    def test_get_enclosure_metrics_latest_enclosure_not_found(self, client):
        """EM-4.2: Enclosure 없는 경우 - 404"""
        response = client.get("/api/devices/enclosures/99999/metrics/latest")
        assert response.status_code == 404

    def test_get_enclosure_metrics_filter_start_time(self, client, db_session):
        """EM-4.3: start_time 필터 동작 (created_at 기준)"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime, timedelta

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=15,
            group_device=0,
            name_device="Test Enclosure 15",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create metrics with different created_at timestamps (manually set)
        now = datetime.now()
        old_time = now - timedelta(hours=2)
        recent_time = now - timedelta(minutes=30)

        metric_old = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="20.0"
        )
        metric_old.created_at = old_time

        metric_recent = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="25.0"
        )
        metric_recent.created_at = recent_time

        db_session.add_all([metric_old, metric_recent])
        db_session.commit()

        # Filter with start_time (should only return recent metric)
        start_filter = (now - timedelta(hours=1)).isoformat()
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics?start_time={start_filter}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["temperature"] == "25.0"

    def test_get_enclosure_metrics_filter_end_time(self, client, db_session):
        """EM-4.3: end_time 필터 동작 (created_at 기준)"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime, timedelta

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=16,
            group_device=0,
            name_device="Test Enclosure 16",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create metrics with different created_at timestamps (manually set)
        now = datetime.now()
        old_time = now - timedelta(hours=2)
        recent_time = now - timedelta(minutes=30)

        metric_old = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="20.0"
        )
        metric_old.created_at = old_time

        metric_recent = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="25.0"
        )
        metric_recent.created_at = recent_time

        db_session.add_all([metric_old, metric_recent])
        db_session.commit()

        # Filter with end_time (should only return old metric)
        end_filter = (now - timedelta(hours=1)).isoformat()
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics?end_time={end_filter}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["temperature"] == "20.0"

    def test_get_enclosure_metrics_filter_time_range(self, client, db_session):
        """EM-4.3: start_time + end_time 범위 필터 동작 (created_at 기준)"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime, timedelta

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=17,
            group_device=0,
            name_device="Test Enclosure 17",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create 3 metrics with different created_at timestamps (manually set)
        now = datetime.now()
        old_time = now - timedelta(hours=3)
        middle_time = now - timedelta(hours=1, minutes=30)
        recent_time = now - timedelta(minutes=30)

        metric_old = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="20.0"
        )
        metric_old.created_at = old_time

        metric_middle = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="22.0"
        )
        metric_middle.created_at = middle_time

        metric_recent = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="25.0"
        )
        metric_recent.created_at = recent_time

        db_session.add_all([metric_old, metric_middle, metric_recent])
        db_session.commit()

        # Filter with time range (should only return middle metric)
        start_filter = (now - timedelta(hours=2)).isoformat()
        end_filter = (now - timedelta(hours=1)).isoformat()
        response = client.get(
            f"/api/devices/enclosures/{enclosure.id}/metrics"
            f"?start_time={start_filter}&end_time={end_filter}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["temperature"] == "22.0"


class TestEnclosureMetricDelete:
    """Phase EM-5: DELETE /api/devices/enclosures/{id}/metrics Tests"""

    def test_delete_enclosure_metrics_success(self, client, db_session):
        """EM-5.1: DELETE 성공 - 200 OK"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=20,
            group_device=0,
            name_device="Test Enclosure 20",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create metrics
        for i in range(5):
            metric = EnclosureMetric(
                enclosure_id=enclosure.id,
                temperature=str(20 + i)
            )
            db_session.add(metric)
        db_session.commit()

        # DELETE metrics
        response = client.delete(f"/api/devices/enclosures/{enclosure.id}/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted_count"] == 5

    def test_delete_enclosure_metrics_enclosure_not_found(self, client):
        """EM-5.1: Enclosure 없는 경우 - 404"""
        response = client.delete("/api/devices/enclosures/99999/metrics")
        assert response.status_code == 404

    def test_delete_enclosure_metrics_before_date(self, client, db_session):
        """EM-5.1: before_date 파라미터 동작 (created_at 기준)"""
        from app.models.device import Enclosure, EnclosureMetric
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus
        from datetime import datetime, timedelta

        # Create an Enclosure
        enclosure = Enclosure(
            number_device=21,
            group_device=0,
            name_device="Test Enclosure 21",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        db_session.add(enclosure)
        db_session.commit()

        # Create old metrics with manually set created_at
        old_time = datetime.now() - timedelta(days=10)
        for i in range(3):
            metric = EnclosureMetric(
                enclosure_id=enclosure.id,
                temperature=str(20 + i)
            )
            metric.created_at = old_time
            db_session.add(metric)

        # Create recent metrics (auto created_at = now)
        for i in range(2):
            metric = EnclosureMetric(
                enclosure_id=enclosure.id,
                temperature=str(30 + i)
            )
            db_session.add(metric)
        db_session.commit()

        # DELETE only old metrics
        before_date = (datetime.now() - timedelta(days=5)).isoformat()
        response = client.delete(
            f"/api/devices/enclosures/{enclosure.id}/metrics?before_date={before_date}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["deleted_count"] == 3  # Only old metrics deleted

        # Verify recent metrics still exist
        response = client.get(f"/api/devices/enclosures/{enclosure.id}/metrics")
        assert len(response.json()["data"]) == 2  # Recent metrics remain


class TestEnclosureMetricLatestResponseSchema:
    """EM-1.4: EnclosureMetricLatestResponse 스키마 테스트"""

    def test_enclosure_metric_latest_response_schema_exists(self):
        """EnclosureMetricLatestResponse 스키마가 존재해야 함"""
        from app.schemas.device import EnclosureMetricLatestResponse

        assert EnclosureMetricLatestResponse is not None

    def test_enclosure_metric_latest_response_has_enclosure_id(self):
        """EnclosureMetricLatestResponse에 enclosure_id 필드가 있어야 함"""
        from app.schemas.device import EnclosureMetricLatestResponse

        fields = EnclosureMetricLatestResponse.model_fields.keys()
        assert 'enclosure_id' in fields

    def test_enclosure_metric_latest_response_has_enclosure_name(self):
        """EnclosureMetricLatestResponse에 enclosure_name 필드가 있어야 함"""
        from app.schemas.device import EnclosureMetricLatestResponse

        fields = EnclosureMetricLatestResponse.model_fields.keys()
        assert 'enclosure_name' in fields

    def test_enclosure_metric_latest_response_has_latest_metrics(self):
        """EnclosureMetricLatestResponse에 latest_metrics 필드가 있어야 함"""
        from app.schemas.device import EnclosureMetricLatestResponse

        fields = EnclosureMetricLatestResponse.model_fields.keys()
        assert 'latest_metrics' in fields

    def test_enclosure_metric_latest_response_latest_metrics_optional(self):
        """EnclosureMetricLatestResponse.latest_metrics가 Optional이어야 함"""
        from app.schemas.device import EnclosureMetricLatestResponse

        # latest_metrics 없이 생성 가능
        response = EnclosureMetricLatestResponse(
            enclosure_id=1,
            enclosure_name="Test Enclosure"
        )
        assert response.latest_metrics is None


class TestEnclosureMetricsListAPI:
    """EM-4.4: GET /api/enclosure-metrics 전체 조회 테스트"""

    def test_get_all_enclosure_metrics_endpoint_exists(self, client, test_db):
        """GET /api/enclosure-metrics 엔드포인트가 존재해야 함"""
        response = client.get("/api/enclosure-metrics")
        # Should not return 404 or 405
        assert response.status_code != 404
        assert response.status_code != 405

    def test_get_all_enclosure_metrics_returns_list(self, client, test_db, create_enclosure_with_metric):
        """GET /api/enclosure-metrics가 목록을 반환해야 함"""
        # Create test data
        enclosure, metric = create_enclosure_with_metric("Test Enclosure 1")

        response = client.get("/api/enclosure-metrics")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_all_enclosure_metrics_returns_enclosure_info(self, client, test_db, create_enclosure_with_metric):
        """GET /api/enclosure-metrics가 enclosure_id, enclosure_name을 포함해야 함"""
        enclosure, metric = create_enclosure_with_metric("Test Enclosure Alpha")

        response = client.get("/api/enclosure-metrics")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) > 0
        item = data["data"][0]
        assert "enclosure_id" in item
        assert "enclosure_name" in item
        assert item["enclosure_name"] == "Test Enclosure Alpha"

    def test_get_all_enclosure_metrics_returns_latest_metrics(self, client, test_db, create_enclosure_with_metric):
        """GET /api/enclosure-metrics가 latest_metrics를 포함해야 함"""
        enclosure, metric = create_enclosure_with_metric("Test Enclosure Beta")

        response = client.get("/api/enclosure-metrics")
        assert response.status_code == 200

        data = response.json()
        item = data["data"][0]
        assert "latest_metrics" in item
        assert item["latest_metrics"] is not None
        assert "temperature" in item["latest_metrics"]

    def test_get_all_enclosure_metrics_empty_enclosure(self, client, test_db):
        """메트릭이 없는 함체는 latest_metrics가 None이어야 함"""
        from app.models.device import Enclosure
        from app.models.device_group import DeviceGroup

        # Create enclosure without metrics
        group = DeviceGroup(name="Test Group")
        test_db.add(group)
        test_db.commit()

        enclosure = Enclosure(
            number_device=999,
            group_device=group.id,
            name_device="Empty Metrics Enclosure",
            type_device="IoController",
            status="ACTIVATED"
        )
        test_db.add(enclosure)
        test_db.commit()

        response = client.get("/api/enclosure-metrics")
        assert response.status_code == 200

        data = response.json()
        # Find our enclosure
        found = None
        for item in data["data"]:
            if item["enclosure_name"] == "Empty Metrics Enclosure":
                found = item
                break

        assert found is not None
        assert found["latest_metrics"] is None


@pytest.fixture
def create_enclosure_with_metric(test_db):
    """함체와 메트릭을 생성하는 픽스처"""
    def _create(name: str):
        from app.models.device import Enclosure, EnclosureMetric
        from app.models.device_group import DeviceGroup

        # Create or get group
        group = test_db.query(DeviceGroup).first()
        if not group:
            group = DeviceGroup(name="Test Group")
            test_db.add(group)
            test_db.commit()

        # Create enclosure
        enclosure = Enclosure(
            number_device=100 + test_db.query(Enclosure).count(),
            group_device=group.id,
            name_device=name,
            type_device="IoController",
            status="ACTIVATED"
        )
        test_db.add(enclosure)
        test_db.commit()
        test_db.refresh(enclosure)

        # Create metric
        metric = EnclosureMetric(
            enclosure_id=enclosure.id,
            temperature="25.5",
            humidity="45.0",
            current="2.5",
            voltage="220.0",
            vibration=10
        )
        test_db.add(metric)
        test_db.commit()
        test_db.refresh(metric)

        return enclosure, metric

    return _create
