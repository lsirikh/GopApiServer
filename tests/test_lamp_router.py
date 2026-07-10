"""
Tests for Lamp Router (TDD)

PRD: PRD_Lamp_Device.md v1.1
Phase 2.3: Lamp Router Tests & Implementation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.device import Lamp
from app.utils.enums import EnumDeviceType, EnumDeviceStatus


class TestLampList:
    """Test GET /api/devices/lamps endpoint"""

    def test_get_lamps_returns_empty_list(self, client: TestClient, test_db: Session):
        """RED: GET /api/devices/lamps should return empty list when no lamps exist"""
        response = client.get("/api/devices/lamps")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_lamps_with_data(self, client: TestClient, test_db: Session):
        """RED: GET /api/devices/lamps should return lamps list"""
        # Arrange - Create a lamp
        lamp = Lamp(
            number_device=1,
            group_device=1,
            name_device="Lamp-Test-1",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.50",
            ip_port=80
        )
        test_db.add(lamp)
        test_db.commit()

        # Act
        response = client.get("/api/devices/lamps")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_get_lamps_with_pagination(self, client: TestClient, test_db: Session):
        """RED: GET /api/devices/lamps should support pagination"""
        # Arrange - Create multiple lamps
        for i in range(5):
            lamp = Lamp(
                number_device=100 + i,
                group_device=1,
                name_device=f"Lamp-Page-{i}",
                type_device=EnumDeviceType.Lamp,
                status=EnumDeviceStatus.ACTIVATED,
                ip_address=f"192.168.2.{50 + i}",
                ip_port=80
            )
            test_db.add(lamp)
        test_db.commit()

        # Act - Request page 1 with limit 2
        response = client.get("/api/devices/lamps?page=1&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data
        assert data["pagination"]["limit"] == 2

    def test_get_lamps_with_status_filter(self, client: TestClient, test_db: Session):
        """RED: GET /api/devices/lamps should filter by status"""
        # Arrange - Create lamps with different statuses
        lamp1 = Lamp(
            number_device=200,
            group_device=1,
            name_device="Lamp-Active",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.3.50",
            ip_port=80
        )
        lamp2 = Lamp(
            number_device=201,
            group_device=1,
            name_device="Lamp-Deactivated",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.DEACTIVATED,
            ip_address="192.168.3.51",
            ip_port=80
        )
        test_db.add_all([lamp1, lamp2])
        test_db.commit()

        # Act - Filter by ACTIVATED status
        response = client.get("/api/devices/lamps?status=ACTIVATED")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # All returned lamps should have ACTIVATED status
        for lamp_data in data["data"]:
            assert lamp_data["status"] == "ACTIVATED"

    def test_get_lamps_with_is_enable_filter(self, client: TestClient, test_db: Session):
        """RED: GET /api/devices/lamps should filter by is_enable"""
        # Arrange - Create lamps with different is_enable values
        lamp1 = Lamp(
            number_device=300,
            group_device=1,
            name_device="Lamp-Enabled",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.4.50",
            ip_port=80,
            is_enable=True
        )
        lamp2 = Lamp(
            number_device=301,
            group_device=1,
            name_device="Lamp-Disabled",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.4.51",
            ip_port=80,
            is_enable=False
        )
        test_db.add_all([lamp1, lamp2])
        test_db.commit()

        # Act - Filter by is_enable=true
        response = client.get("/api/devices/lamps?is_enable=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # All returned lamps should have is_enable=True
        for lamp_data in data["data"]:
            assert lamp_data["is_enable"] is True


class TestLampGet:
    """Test GET /api/devices/lamps/{lamp_id} endpoint"""

    def test_get_lamp_by_id(self, client: TestClient, test_db: Session):
        """RED: GET /api/devices/lamps/{lamp_id} should return single lamp"""
        # Arrange
        lamp = Lamp(
            number_device=400,
            group_device=1,
            name_device="Lamp-Get-Test",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.5.50",
            ip_port=80,
            description="Test lamp for GET"
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        # Act
        response = client.get(f"/api/devices/lamps/{lamp.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == lamp.id
        assert data["data"]["name_device"] == "Lamp-Get-Test"

    def test_get_lamp_not_found(self, client: TestClient, test_db: Session):
        """RED: GET /api/devices/lamps/{lamp_id} should return 404 for non-existent lamp"""
        response = client.get("/api/devices/lamps/99999")

        assert response.status_code == 404


class TestLampCreate:
    """Test POST /api/devices/lamps endpoint"""

    def test_create_lamp(self, client: TestClient, test_db: Session):
        """RED: POST /api/devices/lamps should create new lamp"""
        # Arrange
        lamp_data = {
            "number_device": 500,
            "group_device": 1,
            "name_device": "Lamp-Create-Test",
            "type_device": "Lamp",
            "ip_address": "192.168.6.50",
            "ip_port": 80,
            "description": "Created via API"
        }

        # Act
        response = client.post("/api/devices/lamps", json=lamp_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name_device"] == "Lamp-Create-Test"
        assert data["data"]["ip_address"] == "192.168.6.50"
        assert "id" in data["data"]

    def test_create_lamp_with_geolocation(self, client: TestClient, test_db: Session):
        """RED: POST /api/devices/lamps should accept geolocation"""
        # Arrange
        lamp_data = {
            "number_device": 501,
            "group_device": 1,
            "name_device": "Lamp-Geo-Test",
            "type_device": "Lamp",
            "ip_address": "192.168.6.51",
            "ip_port": 80,
            "geolocation": {
                "location": "GOP 1구역",
                "latitude": 38.1234,
                "longitude": 127.5678
            }
        }

        # Act
        response = client.post("/api/devices/lamps", json=lamp_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["geolocation"] is not None
        assert data["data"]["geolocation"]["location"] == "GOP 1구역"

    def test_create_lamp_missing_required_field(self, client: TestClient, test_db: Session):
        """RED: POST /api/devices/lamps should return 422 for missing required fields"""
        # Arrange - Missing ip_address
        lamp_data = {
            "number_device": 502,
            "group_device": 1,
            "name_device": "Lamp-Missing-Test",
            "type_device": "Lamp"
            # ip_address is missing
        }

        # Act
        response = client.post("/api/devices/lamps", json=lamp_data)

        # Assert
        assert response.status_code == 422


class TestLampUpdate:
    """Test PATCH /api/devices/lamps/{lamp_id} endpoint"""

    def test_patch_lamp(self, client: TestClient, test_db: Session):
        """RED: PATCH /api/devices/lamps/{lamp_id} should partially update lamp"""
        # Arrange
        lamp = Lamp(
            number_device=600,
            group_device=1,
            name_device="Lamp-Patch-Test",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.7.50",
            ip_port=80
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        # Act - Update only description
        response = client.patch(
            f"/api/devices/lamps/{lamp.id}",
            json={"description": "Updated description"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["description"] == "Updated description"
        assert data["data"]["ip_address"] == "192.168.7.50"  # Unchanged

    def test_patch_lamp_not_found(self, client: TestClient, test_db: Session):
        """RED: PATCH /api/devices/lamps/{lamp_id} should return 404 for non-existent lamp"""
        response = client.patch(
            "/api/devices/lamps/99999",
            json={"description": "Test"}
        )

        assert response.status_code == 404


class TestLampReplace:
    """Test PUT /api/devices/lamps/{lamp_id} endpoint"""

    def test_put_lamp(self, client: TestClient, test_db: Session):
        """RED: PUT /api/devices/lamps/{lamp_id} should replace lamp"""
        # Arrange
        lamp = Lamp(
            number_device=700,
            group_device=1,
            name_device="Lamp-Put-Test",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.8.50",
            ip_port=80
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        # Act - Replace entire lamp
        replace_data = {
            "number_device": 700,
            "group_device": 2,
            "name_device": "Lamp-Replaced",
            "type_device": "Lamp",
            "ip_address": "192.168.8.100",
            "ip_port": 8080,
            "description": "Replaced via PUT"
        }
        response = client.put(f"/api/devices/lamps/{lamp.id}", json=replace_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name_device"] == "Lamp-Replaced"
        assert data["data"]["ip_address"] == "192.168.8.100"
        assert data["data"]["ip_port"] == 8080


class TestLampDelete:
    """Test DELETE /api/devices/lamps/{lamp_id} endpoint"""

    def test_delete_lamp(self, client: TestClient, test_db: Session):
        """RED: DELETE /api/devices/lamps/{lamp_id} should delete lamp"""
        # Arrange
        lamp = Lamp(
            number_device=800,
            group_device=1,
            name_device="Lamp-Delete-Test",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.9.50",
            ip_port=80
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)
        lamp_id = lamp.id

        # Act
        response = client.delete(f"/api/devices/lamps/{lamp_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify lamp is deleted
        get_response = client.get(f"/api/devices/lamps/{lamp_id}")
        assert get_response.status_code == 404

    def test_delete_lamp_not_found(self, client: TestClient, test_db: Session):
        """RED: DELETE /api/devices/lamps/{lamp_id} should return 404 for non-existent lamp"""
        response = client.delete("/api/devices/lamps/99999")

        assert response.status_code == 404
