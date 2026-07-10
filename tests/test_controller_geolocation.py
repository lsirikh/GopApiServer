"""
Tests for Controller Geolocation feature
PRD: PRD_Controller_Sensor_Geolocation.md v1.0 - Phase 1-3
TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


class TestControllerGeolocationModel:
    """Phase 1.1: Test Controller model has geolocation column"""

    def test_controller_model_has_geolocation_column(self, test_db):
        """Controller model should have geolocation column"""
        from app.models.device import Controller
        from sqlalchemy import inspect

        mapper = inspect(Controller)
        column_names = [c.key for c in mapper.columns]

        assert "geolocation" in column_names

    def test_controller_geolocation_accepts_dict(self, test_db):
        """Controller geolocation should accept dict (JSONB)"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        controller = Controller(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=8080,
            geolocation={
                "location": "GOP 3초소",
                "latitude": 38.1234,
                "longitude": 127.5678,
                "altitude": 150.0
            }
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        assert controller.geolocation is not None
        assert controller.geolocation["location"] == "GOP 3초소"
        assert controller.geolocation["latitude"] == 38.1234

    def test_controller_geolocation_nullable(self, test_db):
        """Controller geolocation should be nullable"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        controller = Controller(
            number_device=2,
            group_device=1,
            name_device="Controller No Location",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.101",
            ip_port=8080
            # No geolocation
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        assert controller.geolocation is None


class TestControllerGeolocationSchema:
    """Phase 2.1: Test Controller schemas have geolocation field"""

    def test_controller_create_has_geolocation_field(self):
        """ControllerCreate schema should have geolocation field"""
        from app.schemas.device import ControllerCreate, Geolocation

        # Create with geolocation (all required fields from existing schema)
        data = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="IoController",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8080,
            geolocation=Geolocation(
                location="GOP 3cho-so",
                latitude=38.1234,
                longitude=127.5678
            )
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "GOP 3cho-so"

    def test_controller_create_geolocation_optional(self):
        """ControllerCreate geolocation should be optional"""
        from app.schemas.device import ControllerCreate

        data = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="IoController",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8080
            # No geolocation
        )
        assert data.geolocation is None

    def test_controller_update_has_geolocation_field(self):
        """ControllerUpdate schema should have geolocation field"""
        from app.schemas.device import ControllerUpdate, Geolocation

        data = ControllerUpdate(
            geolocation=Geolocation(
                location="Updated Location",
                latitude=38.5678
            )
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Updated Location"

    def test_controller_response_has_geolocation_field(self):
        """ControllerResponse schema should have geolocation field"""
        from app.schemas.device import ControllerResponse, Geolocation
        from datetime import datetime

        data = ControllerResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="IoController",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8080,
            geolocation=Geolocation(location="Test Location"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Test Location"

    def test_controller_nested_response_has_geolocation_field(self):
        """ControllerNestedResponse schema should have geolocation field"""
        from app.schemas.device import ControllerNestedResponse, Geolocation

        data = ControllerNestedResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="IoController",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8080,
            geolocation=Geolocation(location="Nested Location")
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Nested Location"


class TestControllerGeolocationAPI:
    """Phase 3.1: Test Controller API with geolocation"""

    def test_create_controller_with_geolocation(self, client: TestClient, test_db):
        """POST /api/devices/controllers should accept geolocation"""
        payload = {
            "number_device": 10,
            "group_device": 1,
            "name_device": "Controller with Location",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.200",
            "ip_port": 8080,
            "geolocation": {
                "location": "GOP 3cho-so main gate",
                "latitude": 38.1234,
                "longitude": 127.5678,
                "altitude": 150.0
            }
        }
        response = client.post("/api/devices/controllers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["geolocation"] is not None
        assert data["data"]["geolocation"]["location"] == "GOP 3cho-so main gate"
        assert data["data"]["geolocation"]["latitude"] == 38.1234

    def test_create_controller_without_geolocation(self, client: TestClient, test_db):
        """POST /api/devices/controllers without geolocation should work"""
        payload = {
            "number_device": 11,
            "group_device": 1,
            "name_device": "Controller No Location",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.201",
            "ip_port": 8080
        }
        response = client.post("/api/devices/controllers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["geolocation"] is None

    def test_get_controller_includes_geolocation(self, client: TestClient, test_db):
        """GET /api/devices/controllers/{id} should include geolocation"""
        # Create a controller with geolocation via API
        payload = {
            "number_device": 100,
            "group_device": 1,
            "name_device": "Controller for GET test",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.100",
            "ip_port": 8080,
            "geolocation": {
                "location": "Test Location",
                "latitude": 38.5,
                "longitude": 127.5
            }
        }
        create_response = client.post("/api/devices/controllers", json=payload)
        assert create_response.status_code == 201
        controller_id = create_response.json()["data"]["id"]

        response = client.get(f"/api/devices/controllers/{controller_id}")
        assert response.status_code == 200
        data = response.json()
        assert "geolocation" in data["data"]
        assert data["data"]["geolocation"]["location"] == "Test Location"

    def test_update_controller_geolocation(self, client: TestClient, test_db):
        """PATCH /api/devices/controllers/{id} should update geolocation"""
        # Create a controller first via API
        create_payload = {
            "number_device": 101,
            "group_device": 1,
            "name_device": "Controller for PATCH test",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.101",
            "ip_port": 8080
        }
        create_response = client.post("/api/devices/controllers", json=create_payload)
        assert create_response.status_code == 201
        controller_id = create_response.json()["data"]["id"]

        # Now update with geolocation
        payload = {
            "geolocation": {
                "location": "Updated Location",
                "latitude": 39.0,
                "longitude": 128.0
            }
        }
        response = client.patch(f"/api/devices/controllers/{controller_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["geolocation"]["location"] == "Updated Location"
        assert data["data"]["geolocation"]["latitude"] == 39.0
