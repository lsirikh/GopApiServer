"""
Integration tests for Camera Preset, ROI, XyPoint - Phase 7
TDD: Integration tests for full workflow

PRD: PRD_Camera_Urls_JsonB.md v1.0 - Updated to use urls JSONB instead of rtsp_uri/rtsp_port
"""
import pytest
from fastapi.testclient import TestClient


class TestCameraPresetIntegration:
    """Integration tests for the full Camera → Preset → ROI → Points workflow"""

    def test_full_flow_create_camera_preset_roi_points(self, client: TestClient, test_camera, test_db):
        """Test: Full flow - Create Camera → Preset → ROI → Points"""
        # Step 1: Create a preset for the camera
        preset_response = client.post(
            f"/api/devices/cameras/{test_camera.id}/presets",
            json={
                "preset_index": 1,
                "preset_name": "Home Position",
                "touring_time": 15
            }
        )
        assert preset_response.status_code == 201
        preset_data = preset_response.json()["data"]
        preset_id = preset_data["id"]
        assert preset_data["camera_name"] == test_camera.name_device
        assert preset_data["roi_count"] == 0

        # Step 2: Create an ROI for the preset
        roi_response = client.post(
            f"/api/presets/{preset_id}/rois",
            json={
                "name": "Detection Zone 1",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "is_enable": True
            }
        )
        assert roi_response.status_code == 201
        roi_data = roi_response.json()["data"]
        roi_id = roi_data["id"]
        assert roi_data["point_count"] == 0

        # Step 3: Create points for the ROI (polygon vertices)
        points_response = client.put(
            f"/api/rois/{roi_id}/points",
            json={
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1},
                    {"x": 0.9, "y": 0.9, "order": 2},
                    {"x": 0.1, "y": 0.9, "order": 3}
                ]
            }
        )
        assert points_response.status_code == 200
        points_data = points_response.json()["data"]
        assert len(points_data["points"]) == 4

        # Step 4: Verify the full structure via GET preset detail
        detail_response = client.get(f"/api/devices/cameras/{test_camera.id}/presets/{preset_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()["data"]

        assert detail_data["preset_name"] == "Home Position"
        assert len(detail_data["rois"]) == 1
        assert detail_data["rois"][0]["name"] == "Detection Zone 1"
        assert len(detail_data["rois"][0]["points"]) == 4

    def test_cascade_delete_camera_removes_all_children(self, client: TestClient, test_db):
        """Test: Cascade delete - Delete Camera removes all children"""
        from app.models.device import Camera
        from app.models.camera_preset import CameraPreset, ROI, XyPoint
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        # Create a camera
        camera = Camera(
            number_device=99,
            group_device=1,
            name_device="Cascade Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.199",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)
        camera_id = camera.id

        # Create preset
        preset = CameraPreset(
            camera_id=camera_id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Test Preset",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)
        preset_id = preset.id

        # Create ROI
        roi = ROI(
            preset_id=preset_id,
            name="Test ROI",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)
        roi_id = roi.id

        # Create points
        point_ids = []
        for i in range(4):
            point = XyPoint(roi_id=roi_id, x=i*0.25, y=i*0.25, order=i)
            test_db.add(point)
        test_db.commit()

        points = test_db.query(XyPoint).filter(XyPoint.roi_id == roi_id).all()
        point_ids = [p.id for p in points]

        # Delete the camera
        response = client.delete(f"/api/devices/cameras/{camera_id}")
        assert response.status_code == 200

        # Expire cached objects
        test_db.expire_all()

        # Verify cascade delete - all children should be gone
        deleted_camera = test_db.query(Camera).filter(Camera.id == camera_id).first()
        assert deleted_camera is None

        deleted_preset = test_db.query(CameraPreset).filter(CameraPreset.id == preset_id).first()
        assert deleted_preset is None

        deleted_roi = test_db.query(ROI).filter(ROI.id == roi_id).first()
        assert deleted_roi is None

        for point_id in point_ids:
            deleted_point = test_db.query(XyPoint).filter(XyPoint.id == point_id).first()
            assert deleted_point is None

    def test_include_rois_with_nested_structure(self, client: TestClient, test_camera, test_db):
        """Test: include_rois with nested structure"""
        from app.models.camera_preset import CameraPreset, ROI, XyPoint

        # Create preset with ROIs and points
        preset = CameraPreset(
            camera_id=test_camera.id,
            camera_name=test_camera.name_device,
            preset_index=1,
            preset_name="Test Preset",
            touring_time=10
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        # Create 2 ROIs
        roi1 = ROI(preset_id=preset.id, name="ROI 1", resolution_width=1920, resolution_height=1080)
        roi2 = ROI(preset_id=preset.id, name="ROI 2", resolution_width=1280, resolution_height=720)
        test_db.add_all([roi1, roi2])
        test_db.commit()
        test_db.refresh(roi1)
        test_db.refresh(roi2)

        # Create points for ROI 1
        for i in range(3):
            point = XyPoint(roi_id=roi1.id, x=i*0.1, y=i*0.1, order=i)
            test_db.add(point)

        # Create points for ROI 2
        for i in range(4):
            point = XyPoint(roi_id=roi2.id, x=i*0.2, y=i*0.2, order=i)
            test_db.add(point)

        test_db.commit()

        # Test GET preset detail - should include full nested structure
        response = client.get(f"/api/devices/cameras/{test_camera.id}/presets/{preset.id}")

        assert response.status_code == 200
        data = response.json()["data"]

        assert data["preset_name"] == "Test Preset"
        assert len(data["rois"]) == 2

        # Find ROI 1 and verify its points
        roi1_data = next(r for r in data["rois"] if r["name"] == "ROI 1")
        assert len(roi1_data["points"]) == 3

        # Find ROI 2 and verify its points
        roi2_data = next(r for r in data["rois"] if r["name"] == "ROI 2")
        assert len(roi2_data["points"]) == 4
