"""
Test: EventMappingCamera Router
PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5
PRD: PRD_CategoryEvent_Refactoring.md v1.1 - category_event → category_event_mapping

Phase 3-6: Router Tests (TDD - Red Phase)
Endpoints: /api/integrations/event-mappings/{mapping_id}/cameras
"""
import pytest
from fastapi.testclient import TestClient
from app.utils.enums import EnumMappingEventCategory


@pytest.fixture
def test_event_mapping(test_db):
    """Create a test EventMapping"""
    from app.models.integration import EventMapping

    event_mapping = EventMapping(
        name_event="Test Event Mapping",
        category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        status=True
    )
    test_db.add(event_mapping)
    test_db.commit()
    test_db.refresh(event_mapping)
    return event_mapping


@pytest.fixture
def test_event_mapping_camera(test_db, test_event_mapping, test_camera, test_preset):
    """Create a test EventMappingCamera"""
    from app.models.integration import EventMappingCamera

    emc = EventMappingCamera(
        event_mapping_id=test_event_mapping.id,
        camera_id=test_camera.id,
        target_preset_id=test_preset.id,
        delay_time=10,
        is_enable=True,
        priority=1
    )
    test_db.add(emc)
    test_db.commit()
    test_db.refresh(emc)
    return emc


# ============================================================
# Phase 3.1: List Endpoint Tests
# ============================================================

class TestEventMappingCameraListEndpoint:
    """GET /api/integrations/event-mappings/{mapping_id}/cameras Tests"""

    def test_get_event_mapping_cameras_list_success(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: GET /api/integrations/event-mappings/{id}/cameras returns 200"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert len(data["data"]["items"]) == 1

    def test_get_event_mapping_cameras_list_empty(self, client, test_event_mapping):
        """Test: GET /api/integrations/event-mappings/{id}/cameras returns empty list if no cameras"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_get_event_mapping_cameras_list_event_mapping_not_found(self, client):
        """Test: GET /api/integrations/event-mappings/{id}/cameras returns 404 if mapping not found"""
        response = client.get("/api/integrations/event-mappings/99999/cameras")

        assert response.status_code == 404

    def test_get_event_mapping_cameras_list_includes_nested_camera(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: Response includes nested camera object with full properties"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras")

        assert response.status_code == 200
        data = response.json()
        camera_data = data["data"]["items"][0]["camera"]

        assert camera_data is not None
        assert "id" in camera_data
        assert "name_device" in camera_data
        assert "ip_address" in camera_data
        # Nested object should NOT have timestamps
        assert "created_at" not in camera_data
        assert "updated_at" not in camera_data

    def test_get_event_mapping_cameras_list_includes_nested_presets(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: Response includes nested preset objects"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras")

        assert response.status_code == 200
        data = response.json()
        item = data["data"]["items"][0]

        # target_preset should be nested
        if item["target_preset"]:
            assert "id" in item["target_preset"]
            assert "preset_name" in item["target_preset"]
            assert "touring_time" in item["target_preset"]
            # Nested object should NOT have timestamps
            assert "created_at" not in item["target_preset"]


# ============================================================
# Phase 3.2: Get Single Endpoint Tests
# ============================================================

class TestEventMappingCameraGetEndpoint:
    """GET /api/integrations/event-mappings/{mapping_id}/cameras/{id} Tests"""

    def test_get_event_mapping_camera_by_id_success(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: GET single camera returns 200"""
        response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_event_mapping_camera.id

    def test_get_event_mapping_camera_by_id_not_found(self, client, test_event_mapping):
        """Test: GET returns 404 if camera config not found"""
        response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/99999"
        )

        assert response.status_code == 404

    def test_get_event_mapping_camera_by_id_wrong_mapping(self, client, test_db, test_event_mapping_camera):
        """Test: GET returns 404 if camera belongs to different mapping"""
        from app.models.integration import EventMapping

        # Create another event mapping (PRD: category_event_mapping)
        other_mapping = EventMapping(
            name_event="Other Mapping",
            category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            status=True
        )
        test_db.add(other_mapping)
        test_db.commit()
        test_db.refresh(other_mapping)

        # Try to get camera using different mapping ID
        response = client.get(
            f"/api/integrations/event-mappings/{other_mapping.id}/cameras/{test_event_mapping_camera.id}"
        )

        assert response.status_code == 404


# ============================================================
# Phase 4.1: Create Endpoint Tests
# ============================================================

class TestEventMappingCameraCreateEndpoint:
    """POST /api/integrations/event-mappings/{mapping_id}/cameras Tests"""

    def test_create_event_mapping_camera_success(self, client, test_event_mapping, test_camera, test_preset):
        """Test: POST creates camera config and returns 201"""
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras",
            json={
                "camera_id": test_camera.id,
                "target_preset_id": test_preset.id,
                "delay_time": 15,
                "is_enable": True,
                "priority": 1
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["camera"]["id"] == test_camera.id
        assert data["data"]["delay_time"] == 15

    def test_create_event_mapping_camera_event_mapping_not_found(self, client, test_camera):
        """Test: POST returns 404 if event mapping not found"""
        response = client.post(
            "/api/integrations/event-mappings/99999/cameras",
            json={"camera_id": test_camera.id}
        )

        assert response.status_code == 404

    def test_create_event_mapping_camera_camera_not_found(self, client, test_event_mapping):
        """Test: POST returns 404 if camera not found"""
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras",
            json={"camera_id": 99999}
        )

        assert response.status_code == 404

    def test_create_event_mapping_camera_target_preset_not_found(self, client, test_event_mapping, test_camera):
        """Test: POST returns 404 if target_preset_id not found"""
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras",
            json={
                "camera_id": test_camera.id,
                "target_preset_id": 99999
            }
        )

        assert response.status_code == 404

    def test_create_event_mapping_camera_home_preset_not_found(self, client, test_event_mapping, test_camera):
        """Test: POST returns 404 if home_preset_id not found"""
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras",
            json={
                "camera_id": test_camera.id,
                "home_preset_id": 99999
            }
        )

        assert response.status_code == 404

    def test_create_event_mapping_camera_minimal_fields(self, client, test_event_mapping, test_camera):
        """Test: POST with only required field (camera_id)"""
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras",
            json={"camera_id": test_camera.id}
        )

        assert response.status_code == 201
        data = response.json()
        # Defaults should be applied
        assert data["data"]["delay_time"] == 0
        assert data["data"]["is_enable"] is True
        assert data["data"]["priority"] is None

    def test_create_event_mapping_camera_all_fields(self, client, test_event_mapping, test_camera, test_preset, test_db):
        """Test: POST with all fields"""
        from app.models.camera_preset import CameraPreset

        # Create home preset
        home_preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=0,
            preset_name="Home",
            touring_time=0
        )
        test_db.add(home_preset)
        test_db.commit()
        test_db.refresh(home_preset)

        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras",
            json={
                "camera_id": test_camera.id,
                "target_preset_id": test_preset.id,
                "home_preset_id": home_preset.id,
                "delay_time": 30,
                "is_enable": False,
                "priority": 2
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["target_preset"]["id"] == test_preset.id
        assert data["data"]["home_preset"]["id"] == home_preset.id
        assert data["data"]["delay_time"] == 30
        assert data["data"]["is_enable"] is False
        assert data["data"]["priority"] == 2

    def test_create_event_mapping_camera_validates_delay_time_non_negative(self, client, test_event_mapping, test_camera):
        """Test: POST validates delay_time >= 0"""
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras",
            json={
                "camera_id": test_camera.id,
                "delay_time": -1
            }
        )

        assert response.status_code == 422  # Validation error


# ============================================================
# Phase 5.1: PATCH Endpoint Tests
# ============================================================

class TestEventMappingCameraPatchEndpoint:
    """PATCH /api/integrations/event-mappings/{mapping_id}/cameras/{id} Tests"""

    def test_patch_event_mapping_camera_success(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: PATCH updates camera config and returns 200"""
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}",
            json={"delay_time": 99}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["delay_time"] == 99

    def test_patch_event_mapping_camera_not_found(self, client, test_event_mapping):
        """Test: PATCH returns 404 if config not found"""
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/99999",
            json={"delay_time": 10}
        )

        assert response.status_code == 404

    def test_patch_event_mapping_camera_partial_update(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: PATCH only updates provided fields"""
        original_camera_id = test_event_mapping_camera.camera_id

        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}",
            json={"is_enable": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_enable"] is False
        # Other fields should remain unchanged
        assert data["data"]["camera"]["id"] == original_camera_id

    def test_patch_event_mapping_camera_update_camera_id(self, client, test_db, test_event_mapping, test_event_mapping_camera):
        """Test: PATCH can update camera_id"""
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        # Create another camera
        new_camera = Camera(
            number_device=2,
            group_device=1,
            name_device="New Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.FIXED
        )
        test_db.add(new_camera)
        test_db.commit()
        test_db.refresh(new_camera)

        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}",
            json={"camera_id": new_camera.id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["camera"]["id"] == new_camera.id

    def test_patch_event_mapping_camera_update_presets(self, client, test_db, test_event_mapping, test_event_mapping_camera, test_camera):
        """Test: PATCH can update preset IDs"""
        from app.models.camera_preset import CameraPreset

        # Create new preset
        new_preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=2,
            preset_name="New Preset",
            touring_time=20
        )
        test_db.add(new_preset)
        test_db.commit()
        test_db.refresh(new_preset)

        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}",
            json={"target_preset_id": new_preset.id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["target_preset"]["id"] == new_preset.id

    def test_patch_event_mapping_camera_wrong_mapping(self, client, test_db, test_event_mapping_camera):
        """Test: PATCH returns 404 if camera belongs to different mapping"""
        from app.models.integration import EventMapping

        # Create another event mapping (PRD: category_event_mapping)
        other_mapping = EventMapping(
            name_event="Other Mapping",
            category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            status=True
        )
        test_db.add(other_mapping)
        test_db.commit()
        test_db.refresh(other_mapping)

        response = client.patch(
            f"/api/integrations/event-mappings/{other_mapping.id}/cameras/{test_event_mapping_camera.id}",
            json={"delay_time": 10}
        )

        assert response.status_code == 404


# ============================================================
# Phase 5.2: PUT Endpoint Tests
# ============================================================

class TestEventMappingCameraPutEndpoint:
    """PUT /api/integrations/event-mappings/{mapping_id}/cameras/{id} Tests"""

    def test_put_event_mapping_camera_success(self, client, test_event_mapping, test_event_mapping_camera, test_camera):
        """Test: PUT replaces camera config and returns 200"""
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}",
            json={
                "camera_id": test_camera.id,
                "delay_time": 50,
                "is_enable": False,
                "priority": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["delay_time"] == 50
        assert data["data"]["is_enable"] is False
        assert data["data"]["priority"] == 5

    def test_put_event_mapping_camera_replaces_all_fields(self, client, test_event_mapping, test_event_mapping_camera, test_camera):
        """Test: PUT replaces all fields, Optional fields become null"""
        # PUT without optional preset IDs should set them to null
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}",
            json={
                "camera_id": test_camera.id,
                "delay_time": 0,
                "is_enable": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Presets should be null if not provided
        assert data["data"]["target_preset"] is None
        assert data["data"]["home_preset"] is None
        assert data["data"]["priority"] is None


# ============================================================
# Phase 6.1: Delete Endpoint Tests
# ============================================================

class TestEventMappingCameraDeleteEndpoint:
    """DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{id} Tests"""

    def test_delete_event_mapping_camera_success(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: DELETE removes camera config and returns 200"""
        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}"
        )

        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/{test_event_mapping_camera.id}"
        )
        assert get_response.status_code == 404

    def test_delete_event_mapping_camera_not_found(self, client, test_event_mapping):
        """Test: DELETE returns 404 if config not found"""
        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/cameras/99999"
        )

        assert response.status_code == 404

    def test_delete_event_mapping_camera_wrong_mapping(self, client, test_db, test_event_mapping_camera):
        """Test: DELETE returns 404 if camera belongs to different mapping"""
        from app.models.integration import EventMapping

        # Create another event mapping (PRD: category_event_mapping)
        other_mapping = EventMapping(
            name_event="Other Mapping",
            category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            status=True
        )
        test_db.add(other_mapping)
        test_db.commit()
        test_db.refresh(other_mapping)

        response = client.delete(
            f"/api/integrations/event-mappings/{other_mapping.id}/cameras/{test_event_mapping_camera.id}"
        )

        assert response.status_code == 404
