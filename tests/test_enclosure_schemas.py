"""
Tests for Enclosure Schemas
PRD: PRD_Enclosure_Device.md v1.1 - Phase 3: Schema
TDD: Red -> Green -> Refactor
"""
import pytest
from datetime import datetime


class TestEnclosureDetailInfoSchemaRemoved:
    """Test EnclosureDetailInfo schema has been removed
    PRD: PRD_Enclosure_Metrics_Separation.md v1.0"""

    def test_enclosure_detail_info_schema_not_exists(self):
        """EnclosureDetailInfo schema should NOT exist (moved to EnclosureMetricCreate)"""
        import importlib
        import app.schemas.device as device_module

        # Reload to get fresh state
        importlib.reload(device_module)

        # Verify EnclosureDetailInfo does not exist
        assert not hasattr(device_module, 'EnclosureDetailInfo')


class TestEnclosureThresholdConfigSchema:
    """Test EnclosureThresholdConfig schema"""

    def test_enclosure_threshold_config_schema_exists(self):
        """EnclosureThresholdConfig schema should exist"""
        from app.schemas.device import EnclosureThresholdConfig

        assert EnclosureThresholdConfig is not None

    def test_enclosure_threshold_config_has_temp_high_field(self):
        """EnclosureThresholdConfig should have temp_high field"""
        from app.schemas.device import EnclosureThresholdConfig

        config = EnclosureThresholdConfig(temp_high=45.0)
        assert config.temp_high == 45.0

    def test_enclosure_threshold_config_has_temp_low_field(self):
        """EnclosureThresholdConfig should have temp_low field"""
        from app.schemas.device import EnclosureThresholdConfig

        config = EnclosureThresholdConfig(temp_low=-20.0)
        assert config.temp_low == -20.0

    def test_enclosure_threshold_config_has_humidity_high_field(self):
        """EnclosureThresholdConfig should have humidity_high field"""
        from app.schemas.device import EnclosureThresholdConfig

        config = EnclosureThresholdConfig(humidity_high=85.0)
        assert config.humidity_high == 85.0

    def test_enclosure_threshold_config_has_current_high_field(self):
        """EnclosureThresholdConfig should have current_high field"""
        from app.schemas.device import EnclosureThresholdConfig

        config = EnclosureThresholdConfig(current_high=15.0)
        assert config.current_high == 15.0

    def test_enclosure_threshold_config_has_voltage_low_field(self):
        """EnclosureThresholdConfig should have voltage_low field"""
        from app.schemas.device import EnclosureThresholdConfig

        config = EnclosureThresholdConfig(voltage_low=180.0)
        assert config.voltage_low == 180.0

    def test_enclosure_threshold_config_has_vibration_high_field(self):
        """EnclosureThresholdConfig should have vibration_high field"""
        from app.schemas.device import EnclosureThresholdConfig

        config = EnclosureThresholdConfig(vibration_high=80)
        assert config.vibration_high == 80


class TestEnclosureCreateSchema:
    """Test EnclosureCreate schema"""

    def test_enclosure_create_schema_exists(self):
        """EnclosureCreate schema should exist"""
        from app.schemas.device import EnclosureCreate

        assert EnclosureCreate is not None

    def test_enclosure_create_has_required_fields(self):
        """EnclosureCreate should have required fields"""
        from app.schemas.device import EnclosureCreate
        from app.utils.enums import EnumDoorStatus, EnumDeviceStatus

        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="GOP 3초소 함체 A",
        )

        assert create_data.number_device == 101
        assert create_data.name_device == "GOP 3초소 함체 A"

    def test_enclosure_create_has_door_status_field(self):
        """EnclosureCreate should have door_status field"""
        from app.schemas.device import EnclosureCreate
        from app.utils.enums import EnumDoorStatus

        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test",
            door_status=EnumDoorStatus.OPEN
        )

        assert create_data.door_status == EnumDoorStatus.OPEN

    def test_enclosure_create_has_status_field(self):
        """EnclosureCreate should have status field (Device inherited)"""
        from app.schemas.device import EnclosureCreate
        from app.utils.enums import EnumDeviceStatus

        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test",
            status=EnumDeviceStatus.DEACTIVATED
        )

        assert create_data.status == EnumDeviceStatus.DEACTIVATED

    def test_enclosure_create_does_not_have_detail_info_field(self):
        """EnclosureCreate should NOT have detail_info field (moved to enclosure_metrics)
        PRD: PRD_Enclosure_Metrics_Separation.md v1.0"""
        from app.schemas.device import EnclosureCreate

        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test"
        )

        assert not hasattr(create_data, 'detail_info') or create_data.model_fields.get('detail_info') is None

    def test_enclosure_create_has_geolocation_field(self):
        """EnclosureCreate should have geolocation field"""
        from app.schemas.device import EnclosureCreate
        from app.schemas.device import Geolocation

        geolocation = Geolocation(
            location="GOP 3초소",
            latitude=38.1234,
            longitude=127.5678
        )
        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test",
            geolocation=geolocation
        )

        assert create_data.geolocation.location == "GOP 3초소"

    def test_enclosure_create_has_threshold_config_field(self):
        """EnclosureCreate should have threshold_config field"""
        from app.schemas.device import EnclosureCreate, EnclosureThresholdConfig

        threshold = EnclosureThresholdConfig(temp_high=45.0)
        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test",
            threshold_config=threshold
        )

        assert create_data.threshold_config.temp_high == 45.0

    def test_enclosure_create_has_heater_enabled_field(self):
        """EnclosureCreate should have heater_enabled field"""
        from app.schemas.device import EnclosureCreate

        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test",
            heater_enabled=True
        )

        assert create_data.heater_enabled is True

    def test_enclosure_create_has_fan_enabled_field(self):
        """EnclosureCreate should have fan_enabled field"""
        from app.schemas.device import EnclosureCreate

        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test",
            fan_enabled=True
        )

        assert create_data.fan_enabled is True


class TestEnclosureUpdateSchema:
    """Test EnclosureUpdate schema"""

    def test_enclosure_update_schema_exists(self):
        """EnclosureUpdate schema should exist"""
        from app.schemas.device import EnclosureUpdate

        assert EnclosureUpdate is not None

    def test_enclosure_update_all_fields_optional(self):
        """EnclosureUpdate should have all fields optional"""
        from app.schemas.device import EnclosureUpdate

        # Should work with empty data
        update_data = EnclosureUpdate()

        assert update_data.name_device is None
        assert update_data.door_status is None
        assert update_data.status is None
        assert update_data.heater_enabled is None
        assert update_data.fan_enabled is None
        # detail_info removed - PRD_Enclosure_Metrics_Separation.md v1.0

    def test_enclosure_update_can_update_single_field(self):
        """EnclosureUpdate should allow updating single field"""
        from app.schemas.device import EnclosureUpdate

        update_data = EnclosureUpdate(name_device="Updated Name")

        assert update_data.name_device == "Updated Name"
        assert update_data.door_status is None

    def test_enclosure_update_can_update_door_status(self):
        """EnclosureUpdate should allow updating door_status"""
        from app.schemas.device import EnclosureUpdate
        from app.utils.enums import EnumDoorStatus

        update_data = EnclosureUpdate(door_status=EnumDoorStatus.OPEN)

        assert update_data.door_status == EnumDoorStatus.OPEN

    def test_enclosure_update_can_update_status(self):
        """EnclosureUpdate should allow updating status (Device inherited)"""
        from app.schemas.device import EnclosureUpdate
        from app.utils.enums import EnumDeviceStatus

        update_data = EnclosureUpdate(status=EnumDeviceStatus.DEACTIVATED)

        assert update_data.status == EnumDeviceStatus.DEACTIVATED


class TestEnclosureResponseSchema:
    """Test EnclosureResponse schema"""

    def test_enclosure_response_schema_exists(self):
        """EnclosureResponse schema should exist"""
        from app.schemas.device import EnclosureResponse

        assert EnclosureResponse is not None

    def test_enclosure_response_has_all_fields(self):
        """EnclosureResponse should have all required fields
        Note: detail_info removed - PRD_Enclosure_Metrics_Separation.md v1.0"""
        from app.schemas.device import EnclosureResponse
        from app.utils.enums import EnumDoorStatus, EnumDeviceStatus

        now = datetime.now()
        response = EnclosureResponse(
            id=1,
            number_device=101,
            group_device=1,
            name_device="GOP 3초소 함체 A",
            type_device="IoController",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            door_status=EnumDoorStatus.CLOSED,
            geolocation=None,
            threshold_config=None,
            heater_enabled=False,
            fan_enabled=False,
            created_at=now,
            updated_at=now
        )

        assert response.id == 1
        assert response.number_device == 101
        assert response.name_device == "GOP 3초소 함체 A"
        assert response.status == EnumDeviceStatus.ACTIVATED
        assert response.is_enable is True
        assert response.door_status == EnumDoorStatus.CLOSED
        assert response.heater_enabled is False
        assert response.fan_enabled is False
        assert response.created_at == now
        assert response.updated_at == now

    def test_enclosure_response_has_status_field(self):
        """EnclosureResponse should have status field (EnumDeviceStatus)"""
        from app.schemas.device import EnclosureResponse
        from app.utils.enums import EnumDoorStatus, EnumDeviceStatus

        now = datetime.now()
        response = EnclosureResponse(
            id=1,
            number_device=101,
            group_device=1,
            name_device="Test",
            type_device="IoController",
            status=EnumDeviceStatus.ERROR,
            is_enable=True,
            door_status=EnumDoorStatus.CLOSED,
            geolocation=None,
            threshold_config=None,
            heater_enabled=False,
            fan_enabled=False,
            created_at=now,
            updated_at=now
        )

        assert response.status == EnumDeviceStatus.ERROR

    def test_enclosure_response_has_door_status_field(self):
        """EnclosureResponse should have door_status field (EnumDoorStatus)"""
        from app.schemas.device import EnclosureResponse
        from app.utils.enums import EnumDoorStatus, EnumDeviceStatus

        now = datetime.now()
        response = EnclosureResponse(
            id=1,
            number_device=101,
            group_device=1,
            name_device="Test",
            type_device="IoController",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            door_status=EnumDoorStatus.OPEN,
            geolocation=None,
            threshold_config=None,
            heater_enabled=False,
            fan_enabled=False,
            created_at=now,
            updated_at=now
        )

        assert response.door_status == EnumDoorStatus.OPEN


class TestEnclosureControlSchema:
    """Test EnclosureControl schema (for /control endpoint)"""

    def test_enclosure_control_schema_exists(self):
        """EnclosureControl schema should exist"""
        from app.schemas.device import EnclosureControl

        assert EnclosureControl is not None

    def test_enclosure_control_has_heater_enabled_field(self):
        """EnclosureControl should have heater_enabled field"""
        from app.schemas.device import EnclosureControl

        control = EnclosureControl(heater_enabled=True)
        assert control.heater_enabled is True

    def test_enclosure_control_has_fan_enabled_field(self):
        """EnclosureControl should have fan_enabled field"""
        from app.schemas.device import EnclosureControl

        control = EnclosureControl(fan_enabled=True)
        assert control.fan_enabled is True

    def test_enclosure_control_fields_are_optional(self):
        """EnclosureControl fields should be optional"""
        from app.schemas.device import EnclosureControl

        # Only heater
        control1 = EnclosureControl(heater_enabled=True)
        assert control1.heater_enabled is True
        assert control1.fan_enabled is None

        # Only fan
        control2 = EnclosureControl(fan_enabled=False)
        assert control2.heater_enabled is None
        assert control2.fan_enabled is False


class TestEnclosureStatusUpdateSchema:
    """Test EnclosureStatusUpdate schema (for /status endpoint)"""

    def test_enclosure_status_update_schema_exists(self):
        """EnclosureStatusUpdate schema should exist"""
        from app.schemas.device import EnclosureStatusUpdate

        assert EnclosureStatusUpdate is not None

    def test_enclosure_status_update_does_not_have_detail_info_field(self):
        """EnclosureStatusUpdate should NOT have detail_info field (use enclosure_metrics API)
        PRD: PRD_Enclosure_Metrics_Separation.md v1.0"""
        from app.schemas.device import EnclosureStatusUpdate

        status_update = EnclosureStatusUpdate()

        assert not hasattr(status_update, 'detail_info') or 'detail_info' not in status_update.model_fields

    def test_enclosure_status_update_has_door_status_field(self):
        """EnclosureStatusUpdate should have door_status field"""
        from app.schemas.device import EnclosureStatusUpdate
        from app.utils.enums import EnumDoorStatus

        status_update = EnclosureStatusUpdate(door_status=EnumDoorStatus.OPEN)

        assert status_update.door_status == EnumDoorStatus.OPEN
