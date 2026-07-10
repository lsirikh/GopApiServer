"""
DeviceGroup Lamp Integration Tests

PRD: PRD_Lamp_Device.md v1.1 - Section 4.2.3 DeviceGroup LampSummary
Tests for LampSummary schema validation and DeviceGroup Lamp integration

Phase 4: DeviceGroup Lamp Integration
"""
import pytest
from pydantic import ValidationError

from app.schemas.device_group import (
    LampSummary,
    DeviceSummaryBase,
    DeviceSummary,
    ControllerSummary,
    SensorSummary,
    CameraSummary,
    SpeakerSummary,
    EnclosureSummary,
)
from app.models.device import Lamp
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory


# =============================================================================
# Phase 4.1: LampSummary Schema Validation Tests
# =============================================================================

class TestLampSummarySchemaValidation:
    """LampSummary schema validation tests"""

    def test_lamp_summary_inherits_from_device_summary_base(self):
        """LampSummary should inherit from DeviceSummaryBase"""
        assert issubclass(LampSummary, DeviceSummaryBase)

    def test_lamp_summary_with_all_required_fields(self):
        """LampSummary should accept all required fields"""
        summary = LampSummary(
            id=501,
            number_device=5001,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            version="v1.0.0",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80,
            description="GOP 1구역 전방 경광등",
            geolocation={"location": "GOP 1구역", "latitude": 38.1234, "longitude": 127.5678}
        )
        assert summary.id == 501
        assert summary.number_device == 5001
        assert summary.name_device == "Lamp-A-1"
        assert summary.type_device == "Lamp"
        assert summary.ip_address == "192.168.1.109"
        assert summary.ip_port == 80

    def test_lamp_summary_requires_ip_address(self):
        """LampSummary should require ip_address field"""
        with pytest.raises(ValidationError) as exc_info:
            LampSummary(
                id=501,
                number_device=5001,
                group_device=1,
                name_device="Lamp-A-1",
                type_device="Lamp",
                status="ACTIVATED",
                is_enable=True,
                # ip_address missing
                ip_port=80
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("ip_address",) for e in errors)

    def test_lamp_summary_requires_ip_port(self):
        """LampSummary should require ip_port field"""
        with pytest.raises(ValidationError) as exc_info:
            LampSummary(
                id=501,
                number_device=5001,
                group_device=1,
                name_device="Lamp-A-1",
                type_device="Lamp",
                status="ACTIVATED",
                is_enable=True,
                ip_address="192.168.1.109"
                # ip_port missing
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("ip_port",) for e in errors)

    def test_lamp_summary_description_is_optional(self):
        """LampSummary description field should be optional"""
        summary = LampSummary(
            id=501,
            number_device=5001,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80
            # description omitted
        )
        assert summary.description is None

    def test_lamp_summary_geolocation_is_optional(self):
        """LampSummary geolocation field should be optional"""
        summary = LampSummary(
            id=501,
            number_device=5001,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80
            # geolocation omitted
        )
        assert summary.geolocation is None

    def test_lamp_summary_version_is_optional(self):
        """LampSummary version field should be optional"""
        summary = LampSummary(
            id=501,
            number_device=5001,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80
            # version omitted
        )
        assert summary.version is None

    def test_lamp_summary_geolocation_accepts_dict(self):
        """LampSummary geolocation should accept dict with location data"""
        geolocation = {
            "location": "GOP 1구역 경광등",
            "latitude": 38.1234,
            "longitude": 127.5678,
            "altitude": 245.5
        }
        summary = LampSummary(
            id=501,
            number_device=5001,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80,
            geolocation=geolocation
        )
        assert summary.geolocation == geolocation
        assert summary.geolocation["latitude"] == 38.1234


# =============================================================================
# Phase 4.1: DeviceSummary Union Tests
# =============================================================================

class TestDeviceSummaryUnion:
    """DeviceSummary Union type tests for Lamp discrimination"""

    def test_device_summary_includes_lamp_summary(self):
        """DeviceSummary Union should include LampSummary"""
        # Check that LampSummary is part of the Union
        union_args = getattr(DeviceSummary, "__args__", None)
        assert union_args is not None, "DeviceSummary should be a Union type"
        assert LampSummary in union_args, "LampSummary should be in DeviceSummary Union"

    def test_device_summary_union_has_six_types(self):
        """DeviceSummary Union should have 6 device types"""
        union_args = getattr(DeviceSummary, "__args__", None)
        assert len(union_args) == 6
        expected_types = {ControllerSummary, SensorSummary, CameraSummary, SpeakerSummary, EnclosureSummary, LampSummary}
        assert set(union_args) == expected_types

    def test_lamp_summary_can_be_used_as_device_summary(self):
        """LampSummary instance should be valid as DeviceSummary"""
        lamp_summary = LampSummary(
            id=501,
            number_device=5001,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80
        )
        # This should not raise
        assert isinstance(lamp_summary, LampSummary)


# =============================================================================
# Phase 4.2: DeviceGroup Lamp Integration API Tests
# =============================================================================

class TestDeviceGroupLampIntegration:
    """DeviceGroup API integration tests for Lamp devices"""

    def test_get_device_group_includes_lamp_in_devices(self, client, test_db):
        """GET /api/devices/groups/{id} should include Lamp in devices list"""
        # Create DeviceGroup
        group = DeviceGroup(name="Lamp Test Group", description="Group with Lamp")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create Lamp
        lamp = Lamp(
            number_device=5001,
            group_device=1,
            name_device="Lamp-A-1",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80,
            description="Test lamp",
            geolocation={"location": "GOP 1구역", "latitude": 38.1234}
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        # Assign Lamp to DeviceGroup
        mapping = DeviceGroupMapping(
            device_id=lamp.id,
            category_device=EnumDeviceCategory.LAMP,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # GET request
        response = client.get(f"/api/devices/groups/{group.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "devices" in data["data"]
        assert len(data["data"]["devices"]) == 1

        lamp_data = data["data"]["devices"][0]
        assert lamp_data["id"] == lamp.id
        assert lamp_data["type_device"] == "Lamp"
        assert lamp_data["ip_address"] == "192.168.1.109"
        assert lamp_data["ip_port"] == 80
        assert lamp_data["description"] == "Test lamp"
        assert lamp_data["geolocation"]["location"] == "GOP 1구역"

    def test_get_device_group_with_lamp_has_correct_device_count(self, client, test_db):
        """GET /api/devices/groups/{id} should have correct device_count including Lamp"""
        # Create DeviceGroup
        group = DeviceGroup(name="Lamp Count Group", description="Group for count test")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create 2 Lamps
        for i in range(2):
            lamp = Lamp(
                number_device=5001 + i,
                group_device=1,
                name_device=f"Lamp-{i}",
                type_device=EnumDeviceType.Lamp,
                status=EnumDeviceStatus.ACTIVATED,
                ip_address=f"192.168.1.{109 + i}",
                ip_port=80
            )
            test_db.add(lamp)
            test_db.commit()
            test_db.refresh(lamp)

            mapping = DeviceGroupMapping(
                device_id=lamp.id,
                category_device=EnumDeviceCategory.LAMP,
                group_id=group.id
            )
            test_db.add(mapping)
        test_db.commit()

        # GET request
        response = client.get(f"/api/devices/groups/{group.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["device_count"] == 2
        assert len(data["data"]["devices"]) == 2

    def test_get_device_group_lamp_has_all_lamp_summary_fields(self, client, test_db):
        """GET /api/devices/groups/{id} Lamp should have all LampSummary fields"""
        # Create DeviceGroup
        group = DeviceGroup(name="Lamp Fields Group", description="Group for fields test")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create Lamp with all fields
        lamp = Lamp(
            number_device=5001,
            group_device=1,
            name_device="Lamp-Full",
            type_device=EnumDeviceType.Lamp,
            version="v1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80,
            user_name="admin",
            user_password="secret123",
            description="Full lamp with all fields",
            geolocation={"location": "GOP 1구역", "latitude": 38.1234, "longitude": 127.5678}
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        mapping = DeviceGroupMapping(
            device_id=lamp.id,
            category_device=EnumDeviceCategory.LAMP,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # GET request
        response = client.get(f"/api/devices/groups/{group.id}")
        assert response.status_code == 200

        lamp_data = response.json()["data"]["devices"][0]

        # Check all LampSummary fields are present
        assert "id" in lamp_data
        assert "number_device" in lamp_data
        assert "group_device" in lamp_data
        assert "name_device" in lamp_data
        assert "type_device" in lamp_data
        assert "version" in lamp_data
        assert "status" in lamp_data
        assert "is_enable" in lamp_data
        assert "ip_address" in lamp_data
        assert "ip_port" in lamp_data
        assert "description" in lamp_data
        assert "geolocation" in lamp_data

        # LampSummary should NOT include user_name and user_password
        assert "user_name" not in lamp_data
        assert "user_password" not in lamp_data

    def test_get_device_group_lamp_with_null_optional_fields(self, client, test_db):
        """GET /api/devices/groups/{id} Lamp should handle null optional fields"""
        # Create DeviceGroup
        group = DeviceGroup(name="Lamp Null Group", description="Group for null test")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create Lamp with null optional fields
        lamp = Lamp(
            number_device=5001,
            group_device=0,
            name_device="Lamp-Minimal",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.109",
            ip_port=80
            # description and geolocation are null
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        mapping = DeviceGroupMapping(
            device_id=lamp.id,
            category_device=EnumDeviceCategory.LAMP,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # GET request
        response = client.get(f"/api/devices/groups/{group.id}")
        assert response.status_code == 200

        lamp_data = response.json()["data"]["devices"][0]
        assert lamp_data["description"] is None
        assert lamp_data["geolocation"] is None

    def test_get_device_group_include_devices_false_excludes_lamp(self, client, test_db):
        """GET /api/devices/groups/{id}?include_devices=false should not include Lamp devices"""
        # Create DeviceGroup
        group = DeviceGroup(name="Lamp Exclude Group", description="Group for exclude test")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create Lamp
        lamp = Lamp(
            number_device=5001,
            group_device=1,
            name_device="Lamp-Exclude",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.109",
            ip_port=80
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        mapping = DeviceGroupMapping(
            device_id=lamp.id,
            category_device=EnumDeviceCategory.LAMP,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # GET request with include_devices=false
        response = client.get(f"/api/devices/groups/{group.id}?include_devices=false")
        assert response.status_code == 200

        data = response.json()["data"]
        # devices key should not be present
        assert "devices" not in data


class TestDeviceGroupMixedDevices:
    """Tests for DeviceGroup with mixed device types including Lamp"""

    def test_get_device_group_with_lamp_and_other_devices(self, client, test_db):
        """GET /api/devices/groups/{id} should correctly include Lamp among other device types"""
        from app.models.device import Controller

        # Create DeviceGroup
        group = DeviceGroup(name="Mixed Devices Group", description="Group with mixed devices")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create Controller
        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Controller-1",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=8001
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        # Create Lamp
        lamp = Lamp(
            number_device=5001,
            group_device=1,
            name_device="Lamp-1",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.109",
            ip_port=80,
            description="Mixed group lamp"
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        # Assign devices to group
        mapping_controller = DeviceGroupMapping(
            device_id=controller.id,
            category_device=EnumDeviceCategory.CONTROLLER,
            group_id=group.id
        )
        mapping_lamp = DeviceGroupMapping(
            device_id=lamp.id,
            category_device=EnumDeviceCategory.LAMP,
            group_id=group.id
        )
        test_db.add(mapping_controller)
        test_db.add(mapping_lamp)
        test_db.commit()

        # GET request
        response = client.get(f"/api/devices/groups/{group.id}")
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["device_count"] == 2
        assert len(data["devices"]) == 2

        # Check device types
        device_types = [d["type_device"] for d in data["devices"]]
        assert "Controller" in device_types
        assert "Lamp" in device_types

        # Verify Lamp has correct fields
        lamp_device = next(d for d in data["devices"] if d["type_device"] == "Lamp")
        assert lamp_device["ip_address"] == "192.168.1.109"
        assert lamp_device["description"] == "Mixed group lamp"
