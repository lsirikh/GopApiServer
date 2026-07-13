"""
Tests for ROI Router - Phase 5
TDD: Red phase - Write failing tests first
"""
import pytest
from fastapi.testclient import TestClient


class TestROIRouterGetList:
    """Tests for GET /api/presets/{preset_id}/rois"""

    def test_returns_empty_list_when_no_rois_exist(self, client: TestClient, test_preset):
        """Test: Returns empty list when no ROIs exist"""
        response = client.get(f"/api/presets/{test_preset.id}/rois")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_returns_list_of_rois_for_preset(self, client: TestClient, test_preset, test_db):
        """Test: Returns list of ROIs for preset"""
        from app.models.camera_preset import ROI

        # Create test ROIs
        roi1 = ROI(
            preset_id=test_preset.id,
            name="ROI 1",
            resolution_width=1920,
            resolution_height=1080
        )
        roi2 = ROI(
            preset_id=test_preset.id,
            name="ROI 2",
            resolution_width=1280,
            resolution_height=720
        )
        test_db.add_all([roi1, roi2])
        test_db.commit()

        response = client.get(f"/api/presets/{test_preset.id}/rois")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 2
        assert data["data"]["total"] == 2

    def test_returns_404_when_preset_not_found(self, client: TestClient):
        """Test: Returns 404 when preset not found"""
        response = client.get("/api/presets/99999/rois")

        assert response.status_code == 404

    def test_each_roi_includes_point_count(self, client: TestClient, test_preset, test_db):
        """Test: Each ROI includes point_count"""
        from app.models.camera_preset import ROI, XyPoint

        # Create ROI with points
        roi = ROI(
            preset_id=test_preset.id,
            name="ROI with points",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        # Add points
        for i in range(3):
            point = XyPoint(roi_id=roi.id, x=i*100, y=i*100, order=i)
            test_db.add(point)
        test_db.commit()

        response = client.get(f"/api/presets/{test_preset.id}/rois")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"][0]["point_count"] == 3

    def test_include_points_false_returns_no_points_array(self, client: TestClient, test_preset, test_db):
        """Test: include_points=false does not include points array"""
        from app.models.camera_preset import ROI, XyPoint

        # Create ROI with points
        roi = ROI(
            preset_id=test_preset.id,
            name="ROI with points",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        # Add points
        for i in range(3):
            point = XyPoint(roi_id=roi.id, x=i*100, y=i*100, order=i)
            test_db.add(point)
        test_db.commit()

        response = client.get(f"/api/presets/{test_preset.id}/rois?include_points=false")

        assert response.status_code == 200
        data = response.json()
        assert "points" not in data["data"]["items"][0]
        assert data["data"]["items"][0]["point_count"] == 3

    def test_include_points_true_returns_points_array(self, client: TestClient, test_preset, test_db):
        """Test: include_points=true includes points array"""
        from app.models.camera_preset import ROI, XyPoint

        # Create ROI with points
        roi = ROI(
            preset_id=test_preset.id,
            name="ROI with points",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        # Add points
        for i in range(3):
            point = XyPoint(roi_id=roi.id, x=i*100, y=i*100, order=i)
            test_db.add(point)
        test_db.commit()

        response = client.get(f"/api/presets/{test_preset.id}/rois?include_points=true")

        assert response.status_code == 200
        data = response.json()
        assert "points" in data["data"]["items"][0]
        assert len(data["data"]["items"][0]["points"]) == 3
        # Verify point structure
        point = data["data"]["items"][0]["points"][0]
        assert "id" in point
        assert "x" in point
        assert "y" in point
        assert "order" in point


class TestROIRouterGetDetail:
    """Tests for GET /api/presets/{preset_id}/rois/{roi_id}"""

    def test_returns_roi_with_points(self, client: TestClient, test_preset, test_db):
        """Test: Returns ROI with points"""
        from app.models.camera_preset import ROI, XyPoint

        # Create ROI with points
        roi = ROI(
            preset_id=test_preset.id,
            name="Test ROI",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        # Add points
        for i in range(3):
            point = XyPoint(roi_id=roi.id, x=i*100, y=i*100, order=i)
            test_db.add(point)
        test_db.commit()

        response = client.get(f"/api/presets/{test_preset.id}/rois/{roi.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test ROI"
        assert len(data["data"]["points"]) == 3

    def test_returns_404_when_roi_not_found(self, client: TestClient, test_preset):
        """Test: Returns 404 when ROI not found"""
        response = client.get(f"/api/presets/{test_preset.id}/rois/99999")

        assert response.status_code == 404

    def test_returns_404_when_preset_not_found(self, client: TestClient):
        """Test: Returns 404 when preset not found"""
        response = client.get("/api/presets/99999/rois/1")

        assert response.status_code == 404


class TestROIRouterCreate:
    """Tests for POST /api/presets/{preset_id}/rois"""

    def test_creates_roi_with_minimum_3_points(self, client: TestClient, test_preset):
        """Test: Creates ROI with minimum 3 points (polygon requirement)"""
        response = client.post(
            f"/api/presets/{test_preset.id}/rois",
            json={
                "name": "New ROI",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1},
                    {"x": 0.5, "y": 0.9, "order": 2}
                ]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New ROI"
        assert data["data"]["resolution_width"] == 1920
        assert data["data"]["resolution_height"] == 1080
        assert data["data"]["is_enable"] is True
        assert data["data"]["point_count"] == 3

    def test_creates_roi_with_points(self, client: TestClient, test_preset):
        """Test: Creates ROI with points"""
        response = client.post(
            f"/api/presets/{test_preset.id}/rois",
            json={
                "name": "ROI with points",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "points": [
                    {"x": 0, "y": 0, "order": 0},
                    {"x": 100, "y": 0, "order": 1},
                    {"x": 100, "y": 100, "order": 2}
                ]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["point_count"] == 3

    def test_returns_404_when_preset_not_found(self, client: TestClient):
        """Test: Returns 404 when preset not found"""
        response = client.post(
            "/api/presets/99999/rois",
            json={
                "name": "New ROI",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1},
                    {"x": 0.5, "y": 0.9, "order": 2}
                ]
            }
        )

        assert response.status_code == 404

    def test_returns_422_for_invalid_data(self, client: TestClient, test_preset):
        """Test: Returns 422 for invalid data"""
        response = client.post(
            f"/api/presets/{test_preset.id}/rois",
            json={
                "name": "Invalid ROI"
                # Missing required fields
            }
        )

        assert response.status_code == 422

    def test_returns_422_when_only_1_point(self, client: TestClient, test_preset):
        """BUG-1: POST ROI with 1 point should return 422 (minimum 3 for polygon)"""
        response = client.post(
            f"/api/presets/{test_preset.id}/rois",
            json={
                "name": "Bad ROI",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0}
                ]
            }
        )

        assert response.status_code == 422

    def test_returns_422_when_points_omitted(self, client: TestClient, test_preset):
        """BUG-1: POST ROI without points should return 422 (points required)"""
        response = client.post(
            f"/api/presets/{test_preset.id}/rois",
            json={
                "name": "No Points ROI",
                "resolution_width": 1920,
                "resolution_height": 1080
            }
        )

        assert response.status_code == 422

    def test_returns_422_when_only_2_points(self, client: TestClient, test_preset):
        """BUG-1: POST ROI with 2 points should return 422 (minimum 3 for polygon)"""
        response = client.post(
            f"/api/presets/{test_preset.id}/rois",
            json={
                "name": "Bad ROI",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1}
                ]
            }
        )

        assert response.status_code == 422


class TestROIRouterUpdate:
    """Tests for PATCH /api/presets/{preset_id}/rois/{roi_id}"""

    def test_updates_roi_name_only(self, client: TestClient, test_preset, test_db):
        """Test: Updates ROI name only"""
        from app.models.camera_preset import ROI

        roi = ROI(
            preset_id=test_preset.id,
            name="Original Name",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        response = client.patch(
            f"/api/presets/{test_preset.id}/rois/{roi.id}",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["resolution_width"] == 1920  # Unchanged

    def test_updates_is_enable_only(self, client: TestClient, test_preset, test_db):
        """Test: Updates is_enable only"""
        from app.models.camera_preset import ROI

        roi = ROI(
            preset_id=test_preset.id,
            name="Test ROI",
            resolution_width=1920,
            resolution_height=1080,
            is_enable=True
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        response = client.patch(
            f"/api/presets/{test_preset.id}/rois/{roi.id}",
            json={"is_enable": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_enable"] is False

    def test_returns_404_when_roi_not_found(self, client: TestClient, test_preset):
        """Test: Returns 404 when ROI not found"""
        response = client.patch(
            f"/api/presets/{test_preset.id}/rois/99999",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 404


class TestROIRouterReplace:
    """Tests for PUT /api/presets/{preset_id}/rois/{roi_id}"""

    def test_replaces_all_roi_fields(self, client: TestClient, test_preset, test_db):
        """Test: Replaces all ROI fields including points"""
        from app.models.camera_preset import ROI

        roi = ROI(
            preset_id=test_preset.id,
            name="Original",
            resolution_width=1920,
            resolution_height=1080,
            is_enable=True
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        response = client.put(
            f"/api/presets/{test_preset.id}/rois/{roi.id}",
            json={
                "name": "Replaced",
                "resolution_width": 1280,
                "resolution_height": 720,
                "is_enable": False,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1},
                    {"x": 0.5, "y": 0.9, "order": 2}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Replaced"
        assert data["data"]["resolution_width"] == 1280
        assert data["data"]["resolution_height"] == 720
        assert data["data"]["is_enable"] is False

    def test_returns_404_when_roi_not_found(self, client: TestClient, test_preset):
        """Test: Returns 404 when ROI not found"""
        response = client.put(
            f"/api/presets/{test_preset.id}/rois/99999",
            json={
                "name": "Replaced",
                "resolution_width": 1280,
                "resolution_height": 720,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1},
                    {"x": 0.5, "y": 0.9, "order": 2}
                ]
            }
        )

        assert response.status_code == 404

    def test_put_roi_saves_3_points(self, client: TestClient, test_preset, test_db):
        """BUG-2: PUT ROI with 3 points should save all 3 (point_count == 3)"""
        from app.models.camera_preset import ROI

        roi = ROI(
            preset_id=test_preset.id,
            name="Test ROI",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        response = client.put(
            f"/api/presets/{test_preset.id}/rois/{roi.id}",
            json={
                "name": "Updated ROI",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1},
                    {"x": 0.5, "y": 0.9, "order": 2}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["point_count"] == 3

    def test_put_roi_replaces_existing_points(self, client: TestClient, test_preset, test_db):
        """BUG-2: PUT ROI should replace existing 4 points with new 3 points"""
        from app.models.camera_preset import ROI, XyPoint

        roi = ROI(
            preset_id=test_preset.id,
            name="ROI with 4 points",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        # Create 4 existing points
        for i in range(4):
            point = XyPoint(roi_id=roi.id, x=i * 0.25, y=i * 0.25, order=i)
            test_db.add(point)
        test_db.commit()

        # Verify 4 points exist
        assert test_db.query(XyPoint).filter(XyPoint.roi_id == roi.id).count() == 4

        # PUT with new 3 points → should replace
        response = client.put(
            f"/api/presets/{test_preset.id}/rois/{roi.id}",
            json={
                "name": "Replaced ROI",
                "resolution_width": 1280,
                "resolution_height": 720,
                "points": [
                    {"x": 0.2, "y": 0.2, "order": 0},
                    {"x": 0.8, "y": 0.2, "order": 1},
                    {"x": 0.5, "y": 0.8, "order": 2}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["point_count"] == 3

        # Verify in DB: only 3 points remain
        db_points = test_db.query(XyPoint).filter(XyPoint.roi_id == roi.id).order_by(XyPoint.order).all()
        assert len(db_points) == 3
        assert db_points[0].x == 0.2
        assert db_points[1].x == 0.8
        assert db_points[2].x == 0.5

    def test_put_roi_creates_config_change_log(self, client: TestClient, test_preset, test_db):
        """PUT ROI should create a ConfigChangeLog entry"""
        from app.models.camera_preset import ROI
        from app.models.config_change_log import ConfigChangeLog

        roi = ROI(
            preset_id=test_preset.id,
            name="Log Test ROI",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        # Count existing logs
        log_count_before = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == "ROI"
        ).count()

        response = client.put(
            f"/api/presets/{test_preset.id}/rois/{roi.id}",
            json={
                "name": "Updated ROI",
                "resolution_width": 1280,
                "resolution_height": 720,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0},
                    {"x": 0.9, "y": 0.1, "order": 1},
                    {"x": 0.5, "y": 0.9, "order": 2}
                ]
            }
        )

        assert response.status_code == 200

        # Verify ConfigChangeLog was created
        log_count_after = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == "ROI"
        ).count()
        assert log_count_after > log_count_before

        # Verify latest log entry
        latest_log = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == "ROI",
            ConfigChangeLog.resource_id == roi.id,
            ConfigChangeLog.action == "UPDATED"
        ).order_by(ConfigChangeLog.id.desc()).first()
        assert latest_log is not None

    def test_put_roi_with_1_point_returns_422(self, client: TestClient, test_preset, test_db):
        """PUT ROI with 1 point should return 422 (minimum 3 for polygon)"""
        from app.models.camera_preset import ROI

        roi = ROI(
            preset_id=test_preset.id,
            name="Test ROI",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        response = client.put(
            f"/api/presets/{test_preset.id}/rois/{roi.id}",
            json={
                "name": "Bad Update",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "points": [
                    {"x": 0.1, "y": 0.1, "order": 0}
                ]
            }
        )

        assert response.status_code == 422


class TestROIRouterDelete:
    """Tests for DELETE /api/presets/{preset_id}/rois/{roi_id}"""

    def test_deletes_roi_successfully(self, client: TestClient, test_preset, test_db):
        """Test: Deletes ROI successfully"""
        from app.models.camera_preset import ROI

        roi = ROI(
            preset_id=test_preset.id,
            name="To Delete",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)
        roi_id = roi.id

        response = client.delete(f"/api/presets/{test_preset.id}/rois/{roi_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        deleted_roi = test_db.query(ROI).filter(ROI.id == roi_id).first()
        assert deleted_roi is None

    def test_cascade_deletes_xypoints(self, client: TestClient, test_preset, test_db):
        """Test: Cascade deletes XyPoints"""
        from app.models.camera_preset import ROI, XyPoint

        roi = ROI(
            preset_id=test_preset.id,
            name="ROI with points",
            resolution_width=1920,
            resolution_height=1080
        )
        test_db.add(roi)
        test_db.commit()
        test_db.refresh(roi)

        # Add points
        point_ids = []
        for i in range(3):
            point = XyPoint(roi_id=roi.id, x=i*100, y=i*100, order=i)
            test_db.add(point)
        test_db.commit()

        # Get point IDs
        points = test_db.query(XyPoint).filter(XyPoint.roi_id == roi.id).all()
        point_ids = [p.id for p in points]

        roi_id = roi.id
        response = client.delete(f"/api/presets/{test_preset.id}/rois/{roi_id}")

        assert response.status_code == 200

        # Verify points deleted
        for point_id in point_ids:
            deleted_point = test_db.query(XyPoint).filter(XyPoint.id == point_id).first()
            assert deleted_point is None

    def test_returns_404_when_roi_not_found(self, client: TestClient, test_preset):
        """Test: Returns 404 when ROI not found"""
        response = client.delete(f"/api/presets/{test_preset.id}/rois/99999")

        assert response.status_code == 404
