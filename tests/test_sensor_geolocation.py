"""
Tests for Sensor Geolocation feature
PRD: PRD_Controller_Sensor_Geolocation.md v1.0 - Phase 1-3
TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient


class TestSensorGeolocationModel:
    """Phase 1.2: Test Sensor model has geolocation column"""

    def test_sensor_model_has_geolocation_column(self, test_db):
        """Sensor model should have geolocation column"""
        from app.models.device import Sensor
        from sqlalchemy import inspect

        mapper = inspect(Sensor)
        column_names = [c.key for c in mapper.columns]

        assert "geolocation" in column_names

    def test_sensor_geolocation_accepts_dict(self, test_db, test_controller):
        """Sensor geolocation should accept dict (JSONB)"""
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        sensor = Sensor(
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=test_controller.id,
            geolocation={
                "location": "GOP 3cho-so cheolchaek A gugan",
                "latitude": 38.1235,
                "longitude": 127.5680,
                "altitude": 148.5
            }
        )
        test_db.add(sensor)
        test_db.commit()
        test_db.refresh(sensor)

        assert sensor.geolocation is not None
        assert sensor.geolocation["location"] == "GOP 3cho-so cheolchaek A gugan"
        assert sensor.geolocation["latitude"] == 38.1235

    def test_sensor_geolocation_nullable(self, test_db, test_controller):
        """Sensor geolocation should be nullable"""
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        sensor = Sensor(
            number_device=102,
            group_device=1,
            name_device="Sensor No Location",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=test_controller.id
            # No geolocation
        )
        test_db.add(sensor)
        test_db.commit()
        test_db.refresh(sensor)

        assert sensor.geolocation is None


class TestSensorGeolocationSchema:
    """Phase 2.2: Test Sensor schemas have geolocation field"""

    def test_sensor_create_has_geolocation_field(self):
        """SensorCreate schema should have geolocation field"""
        from app.schemas.device import SensorCreate, Geolocation

        data = SensorCreate(
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device="Fence",
            version="1.0",
            status="ACTIVATED",
            controller_id=1,
            geolocation=Geolocation(
                location="GOP 3cho-so fence A",
                latitude=38.1235,
                longitude=127.5680
            )
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "GOP 3cho-so fence A"

    def test_sensor_create_geolocation_optional(self):
        """SensorCreate geolocation should be optional"""
        from app.schemas.device import SensorCreate

        data = SensorCreate(
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device="Fence",
            version="1.0",
            status="ACTIVATED",
            controller_id=1
            # No geolocation
        )
        assert data.geolocation is None

    def test_sensor_update_has_geolocation_field(self):
        """SensorUpdate schema should have geolocation field"""
        from app.schemas.device import SensorUpdate, Geolocation

        data = SensorUpdate(
            geolocation=Geolocation(
                location="Updated Sensor Location",
                latitude=38.5678
            )
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Updated Sensor Location"

    def test_sensor_response_has_geolocation_field(self):
        """SensorResponse schema should have geolocation field"""
        from app.schemas.device import SensorResponse, Geolocation
        from datetime import datetime

        data = SensorResponse(
            id=101,
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device="Fence",
            version="1.0",
            status="ACTIVATED",
            is_enable=True,
            controller_id=1,
            geolocation=Geolocation(location="Sensor Location"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Sensor Location"

    def test_sensor_nested_response_has_geolocation_field(self):
        """SensorNestedResponse schema should have geolocation field"""
        from app.schemas.device import SensorNestedResponse, Geolocation

        data = SensorNestedResponse(
            id=101,
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device="Fence",
            status="ACTIVATED",
            is_enable=True,
            controller_id=1,
            geolocation=Geolocation(location="Nested Sensor Location")
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Nested Sensor Location"


class TestSensorGeolocationAPI:
    """Phase 3.2: Test Sensor API with geolocation"""

    def test_create_sensor_with_geolocation(self, client: TestClient, test_db):
        """POST /api/devices/sensors should accept geolocation"""
        # First create a controller
        controller_payload = {
            "number_device": 1,
            "group_device": 1,
            "name_device": "Controller for Sensor",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.100",
            "ip_port": 8080
        }
        controller_response = client.post("/api/devices/controllers", json=controller_payload)
        assert controller_response.status_code == 201
        controller_id = controller_response.json()["data"]["id"]

        # Now create sensor with geolocation
        payload = {
            "number_device": 101,
            "group_device": 1,
            "name_device": "Sensor with Location",
            "type_device": "Fence",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": controller_id,
            "geolocation": {
                "location": "GOP 3cho-so fence A",
                "latitude": 38.1235,
                "longitude": 127.5680,
                "altitude": 148.5
            }
        }
        response = client.post("/api/devices/sensors", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["geolocation"] is not None
        assert data["data"]["geolocation"]["location"] == "GOP 3cho-so fence A"
        assert data["data"]["geolocation"]["latitude"] == 38.1235

    def test_create_sensor_without_geolocation(self, client: TestClient, test_db):
        """POST /api/devices/sensors without geolocation should work"""
        # First create a controller
        controller_payload = {
            "number_device": 2,
            "group_device": 1,
            "name_device": "Controller for Sensor 2",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.101",
            "ip_port": 8080
        }
        controller_response = client.post("/api/devices/controllers", json=controller_payload)
        assert controller_response.status_code == 201
        controller_id = controller_response.json()["data"]["id"]

        payload = {
            "number_device": 102,
            "group_device": 1,
            "name_device": "Sensor No Location",
            "type_device": "Fence",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": controller_id
        }
        response = client.post("/api/devices/sensors", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["geolocation"] is None

    def test_get_sensor_includes_geolocation(self, client: TestClient, test_db):
        """GET /api/devices/sensors/{id} should include geolocation"""
        # Create controller
        controller_payload = {
            "number_device": 3,
            "group_device": 1,
            "name_device": "Controller for GET test",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.102",
            "ip_port": 8080
        }
        controller_response = client.post("/api/devices/controllers", json=controller_payload)
        assert controller_response.status_code == 201
        controller_id = controller_response.json()["data"]["id"]

        # Create sensor with geolocation
        sensor_payload = {
            "number_device": 103,
            "group_device": 1,
            "name_device": "Sensor for GET test",
            "type_device": "Fence",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": controller_id,
            "geolocation": {
                "location": "Test Location",
                "latitude": 38.5,
                "longitude": 127.5
            }
        }
        create_response = client.post("/api/devices/sensors", json=sensor_payload)
        assert create_response.status_code == 201
        sensor_id = create_response.json()["data"]["id"]

        response = client.get(f"/api/devices/sensors/{sensor_id}")
        assert response.status_code == 200
        data = response.json()
        assert "geolocation" in data["data"]
        assert data["data"]["geolocation"]["location"] == "Test Location"

    def test_update_sensor_geolocation(self, client: TestClient, test_db):
        """PATCH /api/devices/sensors/{id} should update geolocation"""
        # Create controller
        controller_payload = {
            "number_device": 4,
            "group_device": 1,
            "name_device": "Controller for PATCH test",
            "type_device": "IoController",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.103",
            "ip_port": 8080
        }
        controller_response = client.post("/api/devices/controllers", json=controller_payload)
        assert controller_response.status_code == 201
        controller_id = controller_response.json()["data"]["id"]

        # Create sensor without geolocation
        sensor_payload = {
            "number_device": 104,
            "group_device": 1,
            "name_device": "Sensor for PATCH test",
            "type_device": "Fence",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": controller_id
        }
        create_response = client.post("/api/devices/sensors", json=sensor_payload)
        assert create_response.status_code == 201
        sensor_id = create_response.json()["data"]["id"]

        # Now update with geolocation
        payload = {
            "geolocation": {
                "location": "Updated Location",
                "latitude": 39.0,
                "longitude": 128.0
            }
        }
        response = client.patch(f"/api/devices/sensors/{sensor_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["geolocation"]["location"] == "Updated Location"
        assert data["data"]["geolocation"]["latitude"] == 39.0
