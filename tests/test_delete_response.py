"""
Tests for Delete Response Format
PRD: PRD_API_Spec_Compliance.md v1.0 - SPEC-005
TDD: Red -> Green -> Refactor

스펙 요구사항:
DELETE 응답은 data: null을 반환해야 함
{
  "success": true,
  "message": "...",
  "data": null
}
"""
import pytest
from fastapi.testclient import TestClient


class TestDeleteResponseDataNull:
    """
    Phase SPEC-5: Delete Response data Field Tests

    스펙: DELETE 응답의 data 필드는 null이어야 함
    현재 구현: data: {"id": deleted_id} 반환 중
    """

    def test_delete_controller_returns_data_null(self, client: TestClient, test_controller):
        """
        Test: DELETE /api/devices/controllers/{id} - data: null 반환
        PRD: PRD_API_Spec_Compliance.md - SPEC-005
        """
        response = client.delete(f"/api/devices/controllers/{test_controller.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None, "DELETE response data field should be null"

    def test_delete_sensor_returns_data_null(self, client: TestClient, test_controller, test_db):
        """
        Test: DELETE /api/devices/sensors/{id} - data: null 반환
        PRD: PRD_API_Spec_Compliance.md - SPEC-005
        """
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # Create a sensor
        sensor = Sensor(
            number_device=1,
            group_device=1,
            name_device="Test Sensor",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=test_controller.id
        )
        test_db.add(sensor)
        test_db.commit()
        test_db.refresh(sensor)

        response = client.delete(f"/api/devices/sensors/{sensor.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None, "DELETE response data field should be null"

    def test_delete_camera_returns_data_null(self, client: TestClient, test_camera):
        """
        Test: DELETE /api/devices/cameras/{id} - data: null 반환
        PRD: PRD_API_Spec_Compliance.md - SPEC-005
        """
        response = client.delete(f"/api/devices/cameras/{test_camera.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None, "DELETE response data field should be null"

    def test_delete_speaker_returns_data_null(self, client: TestClient, test_speaker):
        """
        Test: DELETE /api/devices/speakers/{id} - data: null 반환
        PRD: PRD_API_Spec_Compliance.md - SPEC-005
        """
        response = client.delete(f"/api/devices/speakers/{test_speaker.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None, "DELETE response data field should be null"

    def test_delete_enclosure_returns_data_null(self, client: TestClient, test_enclosure):
        """
        Test: DELETE /api/devices/enclosures/{id} - data: null 반환
        PRD: PRD_API_Spec_Compliance.md - SPEC-005
        """
        response = client.delete(f"/api/devices/enclosures/{test_enclosure.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None, "DELETE response data field should be null"

    def test_delete_event_mapping_returns_data_null(
        self, client: TestClient, test_db, test_controller
    ):
        """
        Test: DELETE /api/integrations/event-mappings/{id} - data: null 반환
        PRD: PRD_API_Spec_Compliance.md - SPEC-005
        """
        from app.models.integration import EventMapping
        from app.utils.enums import EnumMappingEventCategory

        # Create device group
        from app.models.device_group import DeviceGroup
        device_group = DeviceGroup(name="Test Group", description="Test")
        test_db.add(device_group)
        test_db.commit()
        test_db.refresh(device_group)

        # Create event mapping
        event_mapping = EventMapping(
            name_event="Test Event Mapping",
            device_group_id=device_group.id,
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY
        )
        test_db.add(event_mapping)
        test_db.commit()
        test_db.refresh(event_mapping)

        response = client.delete(f"/api/integrations/event-mappings/{event_mapping.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None, "DELETE response data field should be null"
