"""
Tests for XyPoint Router - Phase 6
TDD: Red phase - Write failing tests first
"""
import pytest
from fastapi.testclient import TestClient


class TestXyPointRouterGetList:
    """Tests for GET /api/rois/{roi_id}/points"""

    def test_returns_empty_list_when_no_points_exist(self, client: TestClient, test_roi):
        """Test: Returns empty list when no points exist"""
        response = client.get(f"/api/rois/{test_roi.id}/points")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_returns_list_of_points_ordered_by_order_field(self, client: TestClient, test_roi, test_db):
        """Test: Returns list of points ordered by order field"""
        from app.models.camera_preset import XyPoint

        # Create points in random order
        point3 = XyPoint(roi_id=test_roi.id, x=300, y=300, order=2)
        point1 = XyPoint(roi_id=test_roi.id, x=100, y=100, order=0)
        point2 = XyPoint(roi_id=test_roi.id, x=200, y=200, order=1)
        test_db.add_all([point3, point1, point2])
        test_db.commit()

        response = client.get(f"/api/rois/{test_roi.id}/points")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 3
        # Check order
        assert data["data"]["items"][0]["order"] == 0
        assert data["data"]["items"][1]["order"] == 1
        assert data["data"]["items"][2]["order"] == 2

    def test_returns_404_when_roi_not_found(self, client: TestClient):
        """Test: Returns 404 when ROI not found"""
        response = client.get("/api/rois/99999/points")

        assert response.status_code == 404


class TestXyPointRouterCreate:
    """Tests for POST /api/rois/{roi_id}/points"""

    def test_creates_single_point(self, client: TestClient, test_roi):
        """Test: Creates single point"""
        response = client.post(
            f"/api/rois/{test_roi.id}/points",
            json={"x": 100.0, "y": 200.0, "order": 0}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["x"] == 100.0
        assert data["data"]["y"] == 200.0
        assert data["data"]["order"] == 0

    def test_returns_404_when_roi_not_found(self, client: TestClient):
        """Test: Returns 404 when ROI not found"""
        response = client.post(
            "/api/rois/99999/points",
            json={"x": 100.0, "y": 200.0, "order": 0}
        )

        assert response.status_code == 404

    def test_returns_409_when_order_already_exists(self, client: TestClient, test_roi, test_db):
        """Test: Returns 409 when order already exists"""
        from app.models.camera_preset import XyPoint

        # Create existing point with order=0
        existing = XyPoint(roi_id=test_roi.id, x=50, y=50, order=0)
        test_db.add(existing)
        test_db.commit()

        response = client.post(
            f"/api/rois/{test_roi.id}/points",
            json={"x": 100.0, "y": 200.0, "order": 0}
        )

        assert response.status_code == 409


class TestXyPointRouterBulkReplace:
    """Tests for PUT /api/rois/{roi_id}/points"""

    def test_replaces_all_points_bulk_update(self, client: TestClient, test_roi, test_db):
        """Test: Replaces all points (bulk update)"""
        from app.models.camera_preset import XyPoint

        # Create existing points
        for i in range(3):
            point = XyPoint(roi_id=test_roi.id, x=i*10, y=i*10, order=i)
            test_db.add(point)
        test_db.commit()

        # Replace with new points
        response = client.put(
            f"/api/rois/{test_roi.id}/points",
            json={
                "points": [
                    {"x": 0, "y": 0, "order": 0},
                    {"x": 100, "y": 0, "order": 1},
                    {"x": 100, "y": 100, "order": 2},
                    {"x": 0, "y": 100, "order": 3}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["points"]) == 4

    def test_deletes_existing_points_and_creates_new_ones(self, client: TestClient, test_roi, test_db):
        """Test: Deletes existing points and creates new ones"""
        from app.models.camera_preset import XyPoint

        # Create existing points
        old_point_ids = []
        for i in range(3):
            point = XyPoint(roi_id=test_roi.id, x=i*10, y=i*10, order=i)
            test_db.add(point)
        test_db.commit()

        # Get old point IDs
        old_points = test_db.query(XyPoint).filter(XyPoint.roi_id == test_roi.id).all()
        old_point_ids = [p.id for p in old_points]

        # Replace with new points
        response = client.put(
            f"/api/rois/{test_roi.id}/points",
            json={
                "points": [
                    {"x": 0, "y": 0, "order": 0},
                    {"x": 50, "y": 0, "order": 1},
                    {"x": 50, "y": 50, "order": 2}
                ]
            }
        )

        assert response.status_code == 200

        # Expire cached objects to get fresh data from DB
        test_db.expire_all()

        # Verify: now only 3 points exist (new ones replaced old ones)
        current_points = test_db.query(XyPoint).filter(XyPoint.roi_id == test_roi.id).all()
        assert len(current_points) == 3

        # Verify new points have the expected x values
        x_values = sorted([p.x for p in current_points])
        assert x_values == [0.0, 50.0, 50.0]

    def test_returns_404_when_roi_not_found(self, client: TestClient):
        """Test: Returns 404 when ROI not found"""
        response = client.put(
            "/api/rois/99999/points",
            json={
                "points": [
                    {"x": 0, "y": 0, "order": 0},
                    {"x": 100, "y": 0, "order": 1},
                    {"x": 100, "y": 100, "order": 2}
                ]
            }
        )

        assert response.status_code == 404

    def test_validates_minimum_3_points_for_polygon(self, client: TestClient, test_roi):
        """Test: Validates minimum 3 points for polygon"""
        response = client.put(
            f"/api/rois/{test_roi.id}/points",
            json={
                "points": [
                    {"x": 0, "y": 0, "order": 0},
                    {"x": 100, "y": 0, "order": 1}
                ]
            }
        )

        assert response.status_code == 422


class TestXyPointRouterDelete:
    """Tests for DELETE /api/rois/{roi_id}/points/{point_id}"""

    def test_deletes_point_successfully(self, client: TestClient, test_roi, test_db):
        """Test: Deletes point successfully"""
        from app.models.camera_preset import XyPoint

        point = XyPoint(roi_id=test_roi.id, x=100, y=100, order=0)
        test_db.add(point)
        test_db.commit()
        test_db.refresh(point)
        point_id = point.id

        response = client.delete(f"/api/rois/{test_roi.id}/points/{point_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        deleted = test_db.query(XyPoint).filter(XyPoint.id == point_id).first()
        assert deleted is None

    def test_returns_404_when_point_not_found(self, client: TestClient, test_roi):
        """Test: Returns 404 when point not found"""
        response = client.delete(f"/api/rois/{test_roi.id}/points/99999")

        assert response.status_code == 404

    def test_returns_404_when_roi_not_found(self, client: TestClient):
        """Test: Returns 404 when ROI not found"""
        response = client.delete("/api/rois/99999/points/1")

        assert response.status_code == 404
