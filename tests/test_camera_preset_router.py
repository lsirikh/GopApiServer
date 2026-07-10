"""
Tests for CameraPreset Router (CRUD operations)
TDD Phase 4: Router Tests
"""
import pytest
from fastapi.testclient import TestClient


class TestCameraPresetRouterGetList:
    """Phase 4.1: GET /api/devices/cameras/{camera_id}/presets"""

    def test_returns_empty_list_when_no_presets_exist(self, client: TestClient, test_camera):
        """Test: Returns empty list when no presets exist"""
        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_returns_list_of_presets_for_camera(self, client: TestClient, test_camera, test_db):
        """Test: Returns list of presets for camera"""
        from app.models.camera_preset import CameraPreset

        # Create test presets
        preset1 = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        preset2 = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=2,
            preset_name="Entry Gate",
            touring_time=15
        )
        test_db.add_all([preset1, preset2])
        test_db.commit()

        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["total"] == 2
        assert len(data["data"]["items"]) == 2
        assert data["data"]["items"][0]["preset_name"] == "Home Position"
        assert data["data"]["items"][1]["preset_name"] == "Entry Gate"

    def test_returns_404_when_camera_not_found(self, client: TestClient):
        """Test: Returns 404 when camera not found"""
        response = client.get("/api/devices/cameras/99999/presets")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] == False

    def test_pagination_works_correctly(self, client: TestClient, test_camera, test_db):
        """Test: Pagination works correctly"""
        from app.models.camera_preset import CameraPreset

        # Create 5 test presets
        for i in range(5):
            preset = CameraPreset(
                camera_id=test_camera.id,
                camera_name=test_camera.name_device,
                preset_index=i + 1,
                preset_name=f"Preset {i + 1}",
                touring_time=10
            )
            test_db.add(preset)
        test_db.commit()

        # Get first page with limit 2
        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets?page=1&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 5
        assert len(data["data"]["items"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 2
        assert data["pagination"]["total_pages"] == 3

    def test_include_rois_false_returns_roi_count_only(self, client: TestClient, test_camera, test_db):
        """Test: include_rois=false returns roi_count only"""
        from app.models.camera_preset import CameraPreset

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()

        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets?include_rois=false")

        assert response.status_code == 200
        data = response.json()
        item = data["data"]["items"][0]
        assert "roi_count" in item
        assert "rois" not in item

    def test_include_rois_true_returns_rois_array(self, client: TestClient, test_camera, test_db):
        """Test: include_rois=true returns rois array"""
        from app.models.camera_preset import CameraPreset

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()

        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets?include_rois=true")

        assert response.status_code == 200
        data = response.json()
        item = data["data"]["items"][0]
        assert "rois" in item
        assert isinstance(item["rois"], list)


class TestCameraPresetRouterGetDetail:
    """Phase 4.2: GET /api/devices/cameras/{camera_id}/presets/{preset_id}"""

    def test_returns_preset_with_rois_and_points(self, client: TestClient, test_camera, test_db):
        """Test: Returns preset with ROIs and points"""
        from app.models.camera_preset import CameraPreset, ROI, XyPoint

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        roi = ROI(
            preset_id=preset.id,
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0,
            is_enable=True
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        point = XyPoint(roi_id=roi.id, x=0.1, y=0.1, order=0)
        test_db.add(point)
        test_db.commit()

        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets/{preset.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["preset_name"] == "Home Position"
        assert len(data["data"]["rois"]) == 1
        assert data["data"]["rois"][0]["name"] == "Entry Zone"
        assert len(data["data"]["rois"][0]["points"]) == 1

    def test_returns_404_when_preset_not_found(self, client: TestClient, test_camera):
        """Test: Returns 404 when preset not found"""
        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] == False

    def test_returns_404_when_camera_not_found(self, client: TestClient):
        """Test: Returns 404 when camera not found"""
        response = client.get("/api/devices/cameras/99999/presets/1")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] == False


class TestCameraPresetRouterCreate:
    """Phase 4.3: POST /api/devices/cameras/{camera_id}/presets"""

    def test_creates_preset_with_valid_data(self, client: TestClient, test_camera):
        """Test: Creates preset with valid data"""
        payload = {
            "preset_index": 1,
            "preset_name": "Home Position",
            "touring_time": 10
        }
        response = client.post(
            f"/api/devices/cameras/{test_camera.id}/presets",
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] == True
        assert data["data"]["preset_name"] == "Home Position"
        assert data["data"]["preset_index"] == 1
        assert data["data"]["touring_time"] == 10

    def test_auto_fills_camera_name_from_camera(self, client: TestClient, test_camera):
        """Test: Auto-fills camera_name from camera"""
        payload = {
            "preset_index": 1,
            "preset_name": "Home Position"
        }
        response = client.post(
            f"/api/devices/cameras/{test_camera.id}/presets",
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["camera_name"] == test_camera.name_device

    def test_returns_404_when_camera_not_found(self, client: TestClient):
        """Test: Returns 404 when camera not found"""
        payload = {
            "preset_index": 1,
            "preset_name": "Home Position"
        }
        response = client.post(
            "/api/devices/cameras/99999/presets",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_409_when_preset_index_already_exists(self, client: TestClient, test_camera, test_db):
        """Test: Returns 409 when preset_index already exists for camera"""
        from app.models.camera_preset import CameraPreset

        existing = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Existing",
            touring_time=10
        )
        test_db.add(existing)
        test_db.commit()

        payload = {
            "preset_index": 1,  # Same index
            "preset_name": "New Preset"
        }
        response = client.post(
            f"/api/devices/cameras/{test_camera.id}/presets",
            json=payload
        )

        assert response.status_code == 409

    def test_returns_422_for_invalid_data(self, client: TestClient, test_camera):
        """Test: Returns 422 for invalid data"""
        payload = {
            "preset_name": "Missing Index"
            # Missing preset_index
        }
        response = client.post(
            f"/api/devices/cameras/{test_camera.id}/presets",
            json=payload
        )

        assert response.status_code == 422


class TestCameraPresetRouterUpdate:
    """Phase 4.4: PATCH /api/devices/cameras/{camera_id}/presets/{preset_id}"""

    def test_updates_preset_name_only(self, client: TestClient, test_camera, test_db):
        """Test: Updates preset_name only"""
        from app.models.camera_preset import CameraPreset

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Original Name",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        response = client.patch(
            f"/api/devices/cameras/{test_camera.id}/presets/{preset.id}",
            json={"preset_name": "Updated Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["preset_name"] == "Updated Name"
        assert data["data"]["touring_time"] == 10  # Unchanged

    def test_updates_touring_time_only(self, client: TestClient, test_camera, test_db):
        """Test: Updates touring_time only"""
        from app.models.camera_preset import CameraPreset

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Test",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        response = client.patch(
            f"/api/devices/cameras/{test_camera.id}/presets/{preset.id}",
            json={"touring_time": 20}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["touring_time"] == 20
        assert data["data"]["preset_name"] == "Test"  # Unchanged

    def test_updates_multiple_fields(self, client: TestClient, test_camera, test_db):
        """Test: Updates multiple fields"""
        from app.models.camera_preset import CameraPreset

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Original",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        response = client.patch(
            f"/api/devices/cameras/{test_camera.id}/presets/{preset.id}",
            json={"preset_name": "Updated", "touring_time": 30}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["preset_name"] == "Updated"
        assert data["data"]["touring_time"] == 30

    def test_returns_404_when_preset_not_found(self, client: TestClient, test_camera):
        """Test: Returns 404 when preset not found"""
        response = client.patch(
            f"/api/devices/cameras/{test_camera.id}/presets/99999",
            json={"preset_name": "New Name"}
        )

        assert response.status_code == 404

    def test_returns_409_when_changing_to_existing_preset_index(self, client: TestClient, test_camera, test_db):
        """Test: Returns 409 when changing to existing preset_index"""
        from app.models.camera_preset import CameraPreset

        preset1 = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="First",
            touring_time=10
        )
        preset2 = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=2,
            preset_name="Second",
            touring_time=10
        )
        test_db.add_all([preset1, preset2])
        test_db.commit()
        test_db.refresh(preset2)

        # Try to change preset2's index to 1 (already taken)
        response = client.patch(
            f"/api/devices/cameras/{test_camera.id}/presets/{preset2.id}",
            json={"preset_index": 1}
        )

        assert response.status_code == 409


class TestCameraPresetRouterReplace:
    """Phase 4.5: PUT /api/devices/cameras/{camera_id}/presets/{preset_id}"""

    def test_replaces_all_preset_fields(self, client: TestClient, test_camera, test_db):
        """Test: Replaces all preset fields"""
        from app.models.camera_preset import CameraPreset

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Original",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        response = client.put(
            f"/api/devices/cameras/{test_camera.id}/presets/{preset.id}",
            json={
                "preset_index": 5,
                "preset_name": "Replaced",
                "touring_time": 25
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["preset_index"] == 5
        assert data["data"]["preset_name"] == "Replaced"
        assert data["data"]["touring_time"] == 25

    def test_returns_404_when_preset_not_found(self, client: TestClient, test_camera):
        """Test: Returns 404 when preset not found"""
        response = client.put(
            f"/api/devices/cameras/{test_camera.id}/presets/99999",
            json={
                "preset_index": 1,
                "preset_name": "Test",
                "touring_time": 10
            }
        )

        assert response.status_code == 404


class TestCameraPresetRouterDelete:
    """Phase 4.6: DELETE /api/devices/cameras/{camera_id}/presets/{preset_id}"""

    def test_deletes_preset_successfully(self, client: TestClient, test_camera, test_db):
        """Test: Deletes preset successfully"""
        from app.models.camera_preset import CameraPreset

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="To Delete",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)
        preset_id = preset.id

        response = client.delete(f"/api/devices/cameras/{test_camera.id}/presets/{preset_id}")

        assert response.status_code == 200

        # Verify it's deleted
        deleted = test_db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
        assert deleted is None

    def test_cascade_deletes_rois_and_xypoints(self, client: TestClient, test_camera, test_db):
        """Test: Cascade deletes ROIs and XyPoints"""
        from app.models.camera_preset import CameraPreset, ROI, XyPoint

        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="To Delete",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        roi = ROI(
            preset_id=preset.id,
            name="Zone",
            resolution_width=1920.0,
            resolution_height=1080.0
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        point = XyPoint(roi_id=roi.id, x=0.1, y=0.1, order=0)
        test_db.add(point)
        test_db.commit()
        test_db.refresh(point)

        preset_id = preset.id
        roi_id = roi.id
        point_id = point.id

        response = client.delete(f"/api/devices/cameras/{test_camera.id}/presets/{preset_id}")

        assert response.status_code == 200

        # Verify cascade delete
        assert test_db.query(CameraPreset).filter(CameraPreset.id == preset_id).first() is None
        assert test_db.query(ROI).filter(ROI.id == roi_id).first() is None
        assert test_db.query(XyPoint).filter(XyPoint.id == point_id).first() is None

    def test_returns_404_when_preset_not_found(self, client: TestClient, test_camera):
        """Test: Returns 404 when preset not found"""
        response = client.delete(f"/api/devices/cameras/{test_camera.id}/presets/99999")

        assert response.status_code == 404
