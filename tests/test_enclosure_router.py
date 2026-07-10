"""
Tests for Enclosure Router API endpoints
PRD: PRD_Enclosure_Device.md v1.1 - Phase 4 & 5: Router
TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient
from app.utils.enums import EnumDoorStatus, EnumDeviceStatus


class TestEnclosureRouterExists:
    """Test Enclosure router module exists"""

    def test_enclosure_router_module_exists(self):
        """enclosures router module should exist"""
        from app.routers import enclosures

        assert enclosures is not None

    def test_enclosure_router_has_router_object(self):
        """enclosures module should have router object"""
        from app.routers.enclosures import router

        assert router is not None


class TestEnclosureGetList:
    """Test GET /api/devices/enclosures"""

    def test_get_enclosures_returns_200(self, client: TestClient, test_db):
        """GET /api/devices/enclosures should return 200"""
        response = client.get("/api/devices/enclosures")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data

    def test_get_enclosures_returns_pagination_meta(self, client: TestClient, test_db):
        """GET /api/devices/enclosures should return pagination metadata"""
        response = client.get("/api/devices/enclosures")

        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data
        pagination = data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination

    def test_get_enclosures_filter_by_door_status(self, client: TestClient, test_db, test_enclosure):
        """GET /api/devices/enclosures?door_status=CLOSED should filter results"""
        response = client.get("/api/devices/enclosures?door_status=CLOSED")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_enclosures_filter_by_status(self, client: TestClient, test_db, test_enclosure):
        """GET /api/devices/enclosures?status=ACTIVATED should filter results"""
        response = client.get("/api/devices/enclosures?status=ACTIVATED")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestEnclosureGetOne:
    """Test GET /api/devices/enclosures/{id}"""

    def test_get_enclosure_returns_200(self, client: TestClient, test_db, test_enclosure):
        """GET /api/devices/enclosures/{id} should return 200"""
        response = client.get(f"/api/devices/enclosures/{test_enclosure.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_enclosure.id

    def test_get_enclosure_returns_404_for_nonexistent(self, client: TestClient, test_db):
        """GET /api/devices/enclosures/{id} should return 404 for non-existent ID"""
        response = client.get("/api/devices/enclosures/99999")

        assert response.status_code == 404

    def test_get_enclosure_includes_door_status_and_status(self, client: TestClient, test_db, test_enclosure):
        """GET /api/devices/enclosures/{id} should include both door_status and status"""
        response = client.get(f"/api/devices/enclosures/{test_enclosure.id}")

        assert response.status_code == 200
        data = response.json()["data"]
        # door_status: 도어 물리적 상태
        assert "door_status" in data
        # status: 장비 운영 상태 (Device 상속)
        assert "status" in data


class TestEnclosureCreate:
    """Test POST /api/devices/enclosures"""

    def test_create_enclosure_returns_201(self, client: TestClient, test_db):
        """POST /api/devices/enclosures should return 201"""
        payload = {
            "number_device": 201,
            "name_device": "GOP Test Enclosure",
            "group_device": 1
        }

        response = client.post("/api/devices/enclosures", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["number_device"] == 201
        assert data["data"]["name_device"] == "GOP Test Enclosure"

    def test_create_enclosure_with_door_status(self, client: TestClient, test_db):
        """POST /api/devices/enclosures with door_status should work"""
        payload = {
            "number_device": 202,
            "name_device": "Test Enclosure Open Door",
            "group_device": 1,
            "door_status": "OPEN"
        }

        response = client.post("/api/devices/enclosures", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["door_status"] == "OPEN"

    def test_create_enclosure_with_status(self, client: TestClient, test_db):
        """POST /api/devices/enclosures with status (Device status) should work"""
        payload = {
            "number_device": 203,
            "name_device": "Test Enclosure Deactivated",
            "group_device": 1,
            "status": "DEACTIVATED"
        }

        response = client.post("/api/devices/enclosures", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["status"] == "DEACTIVATED"

    def test_create_enclosure_without_detail_info(self, client: TestClient, test_db):
        """POST /api/devices/enclosures should NOT accept detail_info (use enclosure_metrics API)
        PRD: PRD_Enclosure_Metrics_Separation.md v1.0"""
        payload = {
            "number_device": 204,
            "name_device": "Test Enclosure without Detail",
            "group_device": 1
        }

        response = client.post("/api/devices/enclosures", json=payload)

        assert response.status_code == 201
        data = response.json()
        # detail_info should not be in response (removed)
        assert "detail_info" not in data["data"]

    def test_create_enclosure_with_geolocation(self, client: TestClient, test_db):
        """POST /api/devices/enclosures with geolocation JSONB should work"""
        payload = {
            "number_device": 205,
            "name_device": "Test Enclosure with Location",
            "group_device": 1,
            "geolocation": {
                "location": "GOP 3초소",
                "latitude": 38.1234,
                "longitude": 127.5678
            }
        }

        response = client.post("/api/devices/enclosures", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["geolocation"]["location"] == "GOP 3초소"

    def test_create_enclosure_with_threshold_config(self, client: TestClient, test_db):
        """POST /api/devices/enclosures with threshold_config JSONB should work"""
        payload = {
            "number_device": 206,
            "name_device": "Test Enclosure with Threshold",
            "group_device": 1,
            "threshold_config": {
                "temp_high": 45.0,
                "temp_low": -20.0,
                "humidity_high": 85.0
            }
        }

        response = client.post("/api/devices/enclosures", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["threshold_config"]["temp_high"] == 45.0


class TestEnclosureUpdate:
    """Test PATCH /api/devices/enclosures/{id}"""

    def test_update_enclosure_returns_200(self, client: TestClient, test_db, test_enclosure):
        """PATCH /api/devices/enclosures/{id} should return 200"""
        payload = {
            "name_device": "Updated Enclosure Name"
        }

        response = client.patch(f"/api/devices/enclosures/{test_enclosure.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name_device"] == "Updated Enclosure Name"

    def test_update_enclosure_door_status(self, client: TestClient, test_db, test_enclosure):
        """PATCH /api/devices/enclosures/{id} can update door_status"""
        payload = {
            "door_status": "OPEN"
        }

        response = client.patch(f"/api/devices/enclosures/{test_enclosure.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["door_status"] == "OPEN"

    def test_update_enclosure_status(self, client: TestClient, test_db, test_enclosure):
        """PATCH /api/devices/enclosures/{id} can update status (Device status)"""
        payload = {
            "status": "DEACTIVATED"
        }

        response = client.patch(f"/api/devices/enclosures/{test_enclosure.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "DEACTIVATED"

    def test_update_enclosure_returns_404_for_nonexistent(self, client: TestClient, test_db):
        """PATCH /api/devices/enclosures/{id} should return 404 for non-existent ID"""
        payload = {
            "name_device": "Updated Name"
        }

        response = client.patch("/api/devices/enclosures/99999", json=payload)

        assert response.status_code == 404


class TestEnclosureReplace:
    """Test PUT /api/devices/enclosures/{id}"""

    def test_replace_enclosure_returns_200(self, client: TestClient, test_db, test_enclosure):
        """PUT /api/devices/enclosures/{id} should return 200"""
        payload = {
            "number_device": 999,
            "name_device": "Completely Replaced Enclosure",
            "group_device": 1,
            "door_status": "OPEN",
            "status": "DEACTIVATED",
            "heater_enabled": True,
            "fan_enabled": True
        }

        response = client.put(f"/api/devices/enclosures/{test_enclosure.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name_device"] == "Completely Replaced Enclosure"
        assert data["data"]["door_status"] == "OPEN"
        assert data["data"]["status"] == "DEACTIVATED"


class TestEnclosureDelete:
    """Test DELETE /api/devices/enclosures/{id}"""

    def test_delete_enclosure_returns_200(self, client: TestClient, test_db, test_enclosure):
        """DELETE /api/devices/enclosures/{id} should return 200"""
        enclosure_id = test_enclosure.id

        response = client.delete(f"/api/devices/enclosures/{enclosure_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None  # DELETE returns None data

    def test_delete_enclosure_returns_404_for_nonexistent(self, client: TestClient, test_db):
        """DELETE /api/devices/enclosures/{id} should return 404 for non-existent ID"""
        response = client.delete("/api/devices/enclosures/99999")

        assert response.status_code == 404

    def test_delete_enclosure_cascades_to_device(self, client: TestClient, test_db, test_enclosure):
        """DELETE /api/devices/enclosures/{id} should cascade delete Device record"""
        from app.models.device import Device

        enclosure_id = test_enclosure.id

        # Delete enclosure
        response = client.delete(f"/api/devices/enclosures/{enclosure_id}")
        assert response.status_code == 200

        # Verify Device record is also deleted
        device = test_db.query(Device).filter(Device.id == enclosure_id).first()
        assert device is None


class TestEnclosureStatusUpdateAPI:
    """Test PATCH /api/devices/enclosures/{id}/status (Phase 5)
    Note: detail_info removed - use enclosure_metrics API (PRD_Enclosure_Metrics_Separation.md v1.0)"""

    def test_enclosure_status_update_returns_200(self, client: TestClient, test_db, test_enclosure):
        """PATCH /api/devices/enclosures/{id}/status should return 200"""
        payload = {
            "door_status": "OPEN"
        }

        response = client.patch(f"/api/devices/enclosures/{test_enclosure.id}/status", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["door_status"] == "OPEN"

    def test_enclosure_status_update_door_status(self, client: TestClient, test_db, test_enclosure):
        """PATCH /api/devices/enclosures/{id}/status can update door_status"""
        payload = {
            "door_status": "OPEN"
        }

        response = client.patch(f"/api/devices/enclosures/{test_enclosure.id}/status", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["door_status"] == "OPEN"


class TestEnclosureControlAPI:
    """Test POST /api/devices/enclosures/{id}/control (Phase 5)"""

    def test_enclosure_control_returns_200(self, client: TestClient, test_db, test_enclosure):
        """POST /api/devices/enclosures/{id}/control should return 200"""
        payload = {
            "heater_enabled": True,
            "fan_enabled": False
        }

        response = client.post(f"/api/devices/enclosures/{test_enclosure.id}/control", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["heater_enabled"] is True
        assert data["data"]["fan_enabled"] is False

    def test_enclosure_control_heater_only(self, client: TestClient, test_db, test_enclosure):
        """POST /api/devices/enclosures/{id}/control can control heater only"""
        payload = {
            "heater_enabled": True
        }

        response = client.post(f"/api/devices/enclosures/{test_enclosure.id}/control", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["heater_enabled"] is True

    def test_enclosure_control_fan_only(self, client: TestClient, test_db, test_enclosure):
        """POST /api/devices/enclosures/{id}/control can control fan only"""
        payload = {
            "fan_enabled": True
        }

        response = client.post(f"/api/devices/enclosures/{test_enclosure.id}/control", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["fan_enabled"] is True
