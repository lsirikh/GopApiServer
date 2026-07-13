"""
Test: 이벤트 기반 장비 상태 자동 변경
PRD: PRD_Malfunction_Device_Status.md v1.1

Phase 1: Malfunction → ERROR
Phase 2: Detection → ACTIVATED
Phase 3: Action → ACTIVATED (원본 장비)
Phase 4: 통합 시나리오
"""
import pytest
from fastapi.testclient import TestClient

from app.models.device import Sensor, Controller
from app.models.event import MalfunctionEvent, DetectionEvent, ActionEvent
from app.utils.enums import EnumDeviceType, EnumDeviceStatus


@pytest.fixture
def activated_sensor(test_db):
    """ACTIVATED 상태의 테스트 센서 생성"""
    ctrl = Controller(
        number_device=1, group_device=1, name_device="Ctrl",
        type_device=EnumDeviceType.Controller,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="10.0.0.1", ip_port=8080,
    )
    test_db.add(ctrl)
    test_db.flush()

    sensor = Sensor(
        number_device=1, group_device=1, name_device="Sensor-A",
        type_device=EnumDeviceType.Fence,
        status=EnumDeviceStatus.ACTIVATED,
        controller_id=ctrl.id,
    )
    test_db.add(sensor)
    test_db.commit()
    test_db.refresh(sensor)
    return sensor


class TestMalfunctionSetsDeviceError:
    """Phase 1: POST /api/events/malfunctions → Device.status = ERROR"""

    def test_activated_device_becomes_error_on_malfunction(self, client: TestClient, test_db, activated_sensor):
        """1.1 ACTIVATED 장비에 장애 POST → ERROR"""
        assert activated_sensor.status == EnumDeviceStatus.ACTIVATED

        response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": activated_sensor.id,
            "reason": "FAULT_FENCE",
        })
        assert response.status_code == 201

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ERROR

    def test_deactivated_device_becomes_error_on_malfunction(self, client: TestClient, test_db, activated_sensor):
        """1.2 DEACTIVATED 장비에 장애 POST → ERROR"""
        activated_sensor.status = EnumDeviceStatus.DEACTIVATED
        test_db.commit()

        response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": activated_sensor.id,
            "reason": "FAULT_FENCE",
        })
        assert response.status_code == 201

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ERROR

    def test_already_error_device_stays_error_on_malfunction(self, client: TestClient, test_db, activated_sensor):
        """1.3 이미 ERROR 장비에 장애 POST → ERROR 유지, 이벤트 정상 생성"""
        activated_sensor.status = EnumDeviceStatus.ERROR
        test_db.commit()

        response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": activated_sensor.id,
            "reason": "FAULT_FENCE",
        })
        assert response.status_code == 201

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ERROR

    def test_malfunction_response_shows_error_status(self, client: TestClient, test_db, activated_sensor):
        """1.4 응답 device.status == 'ERROR'"""
        response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": activated_sensor.id,
            "reason": "FAULT_FENCE",
        })
        assert response.status_code == 201

        data = response.json()["data"]
        assert data["device"]["status"] == "ERROR"


class TestDetectionSetsDeviceActivated:
    """Phase 2: POST /api/events/detections → Device.status = ACTIVATED"""

    def test_error_device_becomes_activated_on_detection(self, client: TestClient, test_db, activated_sensor):
        """2.1 ERROR 장비에 탐지 POST → ACTIVATED"""
        activated_sensor.status = EnumDeviceStatus.ERROR
        test_db.commit()

        response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": activated_sensor.id,
            "result": "PIR_SENSOR",
        })
        assert response.status_code == 201

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ACTIVATED

    def test_deactivated_device_becomes_activated_on_detection(self, client: TestClient, test_db, activated_sensor):
        """2.2 DEACTIVATED 장비에 탐지 POST → ACTIVATED"""
        activated_sensor.status = EnumDeviceStatus.DEACTIVATED
        test_db.commit()

        response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": activated_sensor.id,
            "result": "PIR_SENSOR",
        })
        assert response.status_code == 201

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ACTIVATED

    def test_already_activated_device_stays_activated_on_detection(self, client: TestClient, test_db, activated_sensor):
        """2.3 이미 ACTIVATED 장비에 탐지 POST → ACTIVATED 유지"""
        response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": activated_sensor.id,
            "result": "PIR_SENSOR",
        })
        assert response.status_code == 201

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ACTIVATED

    def test_detection_response_shows_activated_status(self, client: TestClient, test_db, activated_sensor):
        """2.4 ERROR → 탐지 POST → 응답 device.status == 'ACTIVATED'"""
        activated_sensor.status = EnumDeviceStatus.ERROR
        test_db.commit()

        response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": activated_sensor.id,
            "result": "PIR_SENSOR",
        })
        assert response.status_code == 201

        data = response.json()["data"]
        assert data["device"]["status"] == "ACTIVATED"


class TestActionSetsDeviceActivated:
    """Phase 3: POST /api/events/actions → 원본 이벤트의 Device.status = ACTIVATED"""

    def test_action_on_malfunction_restores_device_to_activated(self, client: TestClient, test_db, activated_sensor):
        """3.1 ERROR 장비의 장애이벤트에 조치 POST → 원본 Device.status == ACTIVATED"""
        # 장애 이벤트 생성 → 장비 ERROR
        mal_resp = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": activated_sensor.id,
            "reason": "FAULT_FENCE",
        })
        assert mal_resp.status_code == 201
        mal_id = mal_resp.json()["data"]["id"]

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ERROR

        # 조치 이벤트 생성 → 장비 ACTIVATED 복구
        action_resp = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "장애 조치 완료",
            "user": "operator1",
            "from_event_id": mal_id,
        })
        assert action_resp.status_code == 201

        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ACTIVATED


    def test_action_on_event_without_device_id_no_status_change(self, client: TestClient, test_db, activated_sensor):
        """3.2 원본 이벤트에 device_id 없는 경우 → 상태 변경 없이 ActionEvent 정상 생성"""
        # device_id=None인 이벤트를 직접 DB에 생성 (장비 삭제 후 SET NULL 시나리오)
        orphan_event = MalfunctionEvent(
            type_event="Fault",
            device_id=None,
            reason="FAULT_FENCE",
        )
        test_db.add(orphan_event)
        test_db.commit()
        test_db.refresh(orphan_event)

        # 장비를 ERROR로 설정
        activated_sensor.status = EnumDeviceStatus.ERROR
        test_db.commit()

        # device_id=None인 이벤트에 대한 조치
        action_resp = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "조치 완료",
            "user": "operator1",
            "from_event_id": orphan_event.id,
        })
        assert action_resp.status_code == 201

        # 원본에 device_id가 없으므로 장비 상태 변경 없음 (ERROR 유지)
        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ERROR


class TestIntegrationScenario:
    """Phase 4: 통합 시나리오"""

    def test_malfunction_then_action_cycle(self, client: TestClient, test_db, activated_sensor):
        """4.1 ACTIVATED → Malfunction → ERROR → Action → ACTIVATED"""
        assert activated_sensor.status == EnumDeviceStatus.ACTIVATED

        # Malfunction → ERROR
        mal_resp = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": activated_sensor.id,
            "reason": "FAULT_FENCE",
        })
        assert mal_resp.status_code == 201
        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ERROR

        # Action → ACTIVATED
        action_resp = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "조치 완료",
            "user": "operator1",
            "from_event_id": mal_resp.json()["data"]["id"],
        })
        assert action_resp.status_code == 201
        test_db.refresh(activated_sensor)
        assert activated_sensor.status == EnumDeviceStatus.ACTIVATED
