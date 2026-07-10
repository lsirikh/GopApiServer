"""
Test: Connection Event API
PRD: PRD_Event_ActionEvent_Refactoring.md v2.1

Phase 6.3: Connection Event API
- POST /api/events/connections does NOT accept group_event
- POST /api/events/connections creates Event with device_description auto-sync
- GET /api/events/connections returns device_description
"""
import pytest
from fastapi.testclient import TestClient


class TestConnectionEventAPIGroupEventRemoval:
    """Phase 6.3: Connection Event API - group_event 제거 테스트"""

    def test_post_connection_event_does_not_accept_group_event(self, client: TestClient, test_db):
        """Test: POST /api/events/connections does NOT accept group_event"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # Create a test device first
        device = Controller(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.1",
            ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # POST request with group_event should ignore the field
        # (schema doesn't accept it, so it should be excluded)
        response = client.post(
            "/api/events/connections",
            json={
                "type_event": "Connection",
                "device_id": device.id,
                "sequence": 1,
                "group_event": "SHOULD_BE_IGNORED"  # This field should be ignored
            }
        )

        # The API should succeed (group_event is silently ignored by Pydantic)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

        # Verify the response doesn't have group_event in request data
        data = response.json()
        assert data["success"] is True

        # The schema should have excluded group_event from processing
        # Verify by checking the schema fields directly
        from app.schemas.event import ConnectionEventCreate
        assert "group_event" not in ConnectionEventCreate.model_fields, \
            "ConnectionEventCreate schema should NOT have 'group_event' field"


class TestConnectionEventAPIDeviceDescription:
    """Phase 6.3: Connection Event API - device_description 자동 동기화 테스트"""

    def test_post_connection_event_creates_event_with_device_description_auto_sync(
        self, client: TestClient, test_db
    ):
        """Test: POST /api/events/connections creates Event with device_description auto-sync"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # Create a test device
        device = Controller(
            number_device=5,
            group_device=2,
            name_device="Main Gate Controller",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # POST request to create connection event
        response = client.post(
            "/api/events/connections",
            json={
                "type_event": "Connection",
                "device_id": device.id,
                "sequence": 1
            }
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

        data = response.json()
        assert data["success"] is True

        # Verify device_description is auto-generated
        event_data = data["data"]
        assert "device_description" in event_data, "Response should include device_description"
        assert event_data["device_description"] is not None, "device_description should not be null"

        # Verify device_description format: "[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
        expected_description = f"[{device.type_device.value}] {device.name_device} (number: {device.number_device}, id: {device.id})"
        assert event_data["device_description"] == expected_description, \
            f"Expected '{expected_description}', got '{event_data['device_description']}'"

    def test_get_connection_events_returns_device_description(
        self, client: TestClient, test_db
    ):
        """Test: GET /api/events/connections returns device_description"""
        from app.models.device import Controller
        from app.models.event import ConnectionEvent
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # Create a test device
        device = Controller(
            number_device=3,
            group_device=1,
            name_device="Fence Controller",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.20",
            ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # Create a connection event with device_description
        expected_description = f"[{device.type_device.value}] {device.name_device} (number: {device.number_device}, id: {device.id})"
        event = ConnectionEvent(
            category_event="connection",
            type_event="Connection",
            device_id=device.id,
            device_description=expected_description,
            sequence=1
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        # GET connection events list
        response = client.get("/api/events/connections")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

        # Find our created event
        event_data = next((e for e in data["data"] if e["id"] == event.id), None)
        assert event_data is not None, "Created event should be in the list"

        # Verify device_description is in response
        assert "device_description" in event_data, "Response should include device_description"
        assert event_data["device_description"] == expected_description, \
            f"Expected '{expected_description}', got '{event_data['device_description']}'"
