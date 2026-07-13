"""
Tests for DeviceGroup API include_devices query parameter
PRD: PRD_API_Gap_Analysis.md (IMP-003)

TDD Phase 2: DeviceGroup Query Parameters
"""
import pytest


class TestDeviceGroupGetApiCurrentBehavior:
    """Test GET /api/devices/groups/{id} current behavior (Phase 2.1)

    Verify current behavior includes devices by default.
    Uses conftest fixtures for proper test database setup.
    """

    def test_get_device_group_returns_devices_by_default(self, client, test_db):
        """Test: GET /api/devices/groups/{id} returns devices by default"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        # Create a device group
        group = DeviceGroup(name="Test Group", description="Test Description")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create a controller and assign to group
        controller = Controller(
            number_device=100,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.50",
            ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        # Create mapping
        mapping = DeviceGroupMapping(
            device_id=controller.id,
            category_device=EnumDeviceCategory.CONTROLLER,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # Test API
        response = client.get(f"/api/devices/groups/{group.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Default behavior should include devices
        assert "devices" in data["data"]
        assert isinstance(data["data"]["devices"], list)
        assert len(data["data"]["devices"]) >= 1


class TestDeviceGroupGetApiWithIncludeDevicesFalse:
    """Test GET /api/devices/groups/{id}?include_devices=false (Phase 2.2)"""

    def test_get_device_group_with_include_devices_false(self, client, test_db):
        """Test: GET /api/devices/groups/{id}?include_devices=false does not include devices"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        # Create a device group
        group = DeviceGroup(name="Test Group 2", description="Test Description")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create a controller and assign to group
        controller = Controller(
            number_device=101,
            group_device=1,
            name_device="Test Controller 2",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.51",
            ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        # Create mapping
        mapping = DeviceGroupMapping(
            device_id=controller.id,
            category_device=EnumDeviceCategory.CONTROLLER,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # Test API with include_devices=false
        response = client.get(f"/api/devices/groups/{group.id}?include_devices=false")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # include_devices=false should NOT include devices
        assert "devices" not in data["data"]
        # But should still have device_count
        assert "device_count" in data["data"]
        assert data["data"]["device_count"] >= 1


class TestDeviceGroupGetApiWithIncludeDevicesTrue:
    """Test GET /api/devices/groups/{id}?include_devices=true (Phase 2.3)"""

    def test_get_device_group_with_include_devices_true(self, client, test_db):
        """Test: GET /api/devices/groups/{id}?include_devices=true includes devices"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        # Create a device group
        group = DeviceGroup(name="Test Group 3", description="Test Description")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create a controller and assign to group
        controller = Controller(
            number_device=102,
            group_device=1,
            name_device="Test Controller 3",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.52",
            ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        # Create mapping
        mapping = DeviceGroupMapping(
            device_id=controller.id,
            category_device=EnumDeviceCategory.CONTROLLER,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # Test API with include_devices=true
        response = client.get(f"/api/devices/groups/{group.id}?include_devices=true")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # include_devices=true should include devices
        assert "devices" in data["data"]
        assert isinstance(data["data"]["devices"], list)
        assert len(data["data"]["devices"]) >= 1
        # Verify device structure
        device = data["data"]["devices"][0]
        assert "id" in device
        assert "name_device" in device
        assert "ip_address" in device
