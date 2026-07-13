"""
Test: Detection Log API
PRD: PRD_DetectionLog_API.md v1.0

Phase 2-3: Detection Log API (GET 목록, GET 단건)
- DetectionEvent + ActionEvent LEFT JOIN
- action 필드: 조치완료 시 ActionNested, 미조치 시 null
"""
import pytest
from fastapi.testclient import TestClient


class TestDetectionLogList:
    """Phase 2.1: GET /api/detection-logs 기본 조회"""

    def test_get_detection_logs_returns_200_with_pagination(self, client: TestClient, test_db):
        """GET /api/detection-logs returns 200 with pagination"""
        response = client.get("/api/detection-logs")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)

    def test_get_detection_logs_pagination_fields(self, client: TestClient, test_db):
        """GET /api/detection-logs pagination has page, limit, total, total_pages"""
        response = client.get("/api/detection-logs?page=1&limit=5")
        assert response.status_code == 200

        pagination = response.json()["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination
        assert pagination["page"] == 1
        assert pagination["limit"] == 5


class TestDetectionLogFilter:
    """Phase 2.2: GET /api/detection-logs action_reported 필터"""

    def test_filter_by_action_reported_false(self, client: TestClient, test_db):
        """GET /api/detection-logs?action_reported=False returns only unreported events"""
        from app.models.device import Controller
        from app.models.event import DetectionEvent
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDetectionType

        # Create device
        device = Controller(
            number_device=901, group_device=1, name_device="LogTest-Device",
            type_device=EnumDeviceType.Controller, status=EnumDeviceStatus.ACTIVATED,
            ip_address="10.0.0.1", ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # Create detection (미조치)
        event = DetectionEvent(
            category_event="detection", type_event="Intrusion",
            device_id=device.id, device_description=f"[Controller] LogTest-Device (number: 901, id: {device.id})",
            action_reported="False", result=EnumDetectionType.PIR_SENSOR
        )
        test_db.add(event)
        test_db.commit()

        response = client.get("/api/detection-logs?action_reported=False")
        assert response.status_code == 200

        data = response.json()["data"]
        for item in data:
            assert item["action_reported"] == "False"


class TestDetectionLogActionJoin:
    """Phase 2.3: GET /api/detection-logs 응답에 action 필드 검증"""

    def test_detection_log_has_action_null_when_no_action(self, client: TestClient, test_db):
        """미조치 탐지 이벤트의 action 필드는 null"""
        from app.models.device import Controller
        from app.models.event import DetectionEvent
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDetectionType

        device = Controller(
            number_device=902, group_device=1, name_device="LogAction-Device",
            type_device=EnumDeviceType.Controller, status=EnumDeviceStatus.ACTIVATED,
            ip_address="10.0.0.2", ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        event = DetectionEvent(
            category_event="detection", type_event="Intrusion",
            device_id=device.id, device_description=f"[Controller] LogAction-Device (number: 902, id: {device.id})",
            action_reported="False", result=EnumDetectionType.PIR_SENSOR
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        response = client.get(f"/api/detection-logs/{event.id}")
        assert response.status_code == 200

        event_data = response.json()["data"]
        assert "action" in event_data, "Response should have 'action' field"
        assert event_data["action"] is None, "action should be null for unreported event"

    def test_detection_log_has_action_nested_when_action_exists(self, client: TestClient, test_db):
        """조치완료 탐지 이벤트의 action 필드에 ActionNested 포함"""
        from app.models.device import Controller
        from app.models.event import DetectionEvent, ActionEvent
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDetectionType

        device = Controller(
            number_device=903, group_device=1, name_device="LogAction-Device2",
            type_device=EnumDeviceType.Controller, status=EnumDeviceStatus.ACTIVATED,
            ip_address="10.0.0.3", ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # Create detection event (조치완료)
        event = DetectionEvent(
            category_event="detection", type_event="Intrusion",
            device_id=device.id, device_description=f"[Controller] LogAction-Device2 (number: 903, id: {device.id})",
            action_reported="True", result=EnumDetectionType.AI_DETECT
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        # Create action event linked to detection
        action = ActionEvent(
            type_event="Action",
            content="현장 확인 완료",
            user="operator_kim",
            from_event_id=event.id
        )
        test_db.add(action)
        test_db.commit()
        test_db.refresh(action)

        response = client.get(f"/api/detection-logs/{event.id}")
        assert response.status_code == 200

        event_data = response.json()["data"]
        assert event_data["action"] is not None, "action should not be null for reported event"
        assert event_data["action"]["id"] == action.id
        assert event_data["action"]["content"] == "현장 확인 완료"
        assert event_data["action"]["user"] == "operator_kim"
        assert "created_at" in event_data["action"]
        assert "updated_at" in event_data["action"]
        # from_event should NOT be in ActionNested (circular reference prevention)
        assert "from_event" not in event_data["action"]


class TestDetectionLogGetById:
    """Phase 3.1-3.2: GET /api/detection-logs/{event_id}"""

    def test_get_detection_log_by_id_returns_200(self, client: TestClient, test_db):
        """GET /api/detection-logs/{event_id} returns 200"""
        from app.models.device import Controller
        from app.models.event import DetectionEvent
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDetectionType

        device = Controller(
            number_device=904, group_device=1, name_device="LogById-Device",
            type_device=EnumDeviceType.Controller, status=EnumDeviceStatus.ACTIVATED,
            ip_address="10.0.0.4", ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        event = DetectionEvent(
            category_event="detection", type_event="Intrusion",
            device_id=device.id, device_description=f"[Controller] LogById-Device (number: 904, id: {device.id})",
            action_reported="False", result=EnumDetectionType.THERMAL_SENSOR
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        response = client.get(f"/api/detection-logs/{event.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == event.id
        assert data["data"]["result"] == "THERMAL_SENSOR"

    def test_get_detection_log_by_id_returns_404(self, client: TestClient, test_db):
        """GET /api/detection-logs/{event_id} returns 404 for non-existent ID"""
        response = client.get("/api/detection-logs/99999")
        assert response.status_code == 404
