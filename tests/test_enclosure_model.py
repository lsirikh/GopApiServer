"""
Tests for Enclosure Model
PRD: PRD_Enclosure_Device.md v1.1 - Phase 2: Model
TDD: Red -> Green -> Refactor
"""
import pytest
from sqlalchemy import inspect


class TestEnclosureModelInheritance:
    """Test Enclosure model inheritance from Device"""

    def test_enclosure_model_exists(self):
        """Enclosure model class should exist"""
        from app.models.device import Enclosure

        assert Enclosure is not None

    def test_enclosure_inherits_from_device(self):
        """Enclosure should inherit from Device"""
        from app.models.device import Enclosure, Device

        assert issubclass(Enclosure, Device)

    def test_enclosure_has_polymorphic_identity_enclosure(self):
        """Enclosure should have polymorphic_identity = EnumDeviceCategory.ENCLOSURE"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceCategory

        assert Enclosure.__mapper_args__.get("polymorphic_identity") == EnumDeviceCategory.ENCLOSURE


class TestEnclosureTableColumns:
    """Test Enclosure table columns"""

    def test_enclosure_tablename_is_enclosures(self):
        """Enclosure table name should be 'enclosures'"""
        from app.models.device import Enclosure

        assert Enclosure.__tablename__ == "enclosures"

    def test_enclosure_has_id_column(self):
        """Enclosure should have id column (FK to devices)"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "id" in columns

    def test_enclosure_has_door_status_column(self):
        """Enclosure should have door_status column"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "door_status" in columns

    def test_enclosure_does_not_have_detail_info_column(self):
        """Enclosure should NOT have detail_info column (moved to enclosure_metrics)
        PRD: PRD_Enclosure_Metrics_Separation.md v1.0"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "detail_info" not in columns

    def test_enclosure_has_geolocation_column(self):
        """Enclosure should have geolocation JSONB column"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "geolocation" in columns

    def test_enclosure_has_threshold_config_column(self):
        """Enclosure should have threshold_config JSONB column"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "threshold_config" in columns

    def test_enclosure_has_heater_enabled_column(self):
        """Enclosure should have heater_enabled boolean column"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "heater_enabled" in columns

    def test_enclosure_has_fan_enabled_column(self):
        """Enclosure should have fan_enabled boolean column"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "fan_enabled" in columns


class TestEnclosureInheritsDeviceFields:
    """Test that Enclosure inherits Device fields"""

    def test_enclosure_inherits_status_from_device(self):
        """Enclosure should inherit status field from Device"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "status" in columns

    def test_enclosure_inherits_number_device_from_device(self):
        """Enclosure should inherit number_device field from Device"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "number_device" in columns

    def test_enclosure_inherits_name_device_from_device(self):
        """Enclosure should inherit name_device field from Device"""
        from app.models.device import Enclosure

        mapper = inspect(Enclosure)
        columns = [c.key for c in mapper.columns]
        assert "name_device" in columns


class TestEnclosureColumnDefaults:
    """Test Enclosure column default values"""

    def test_door_status_default_is_closed(self):
        """door_status should default to CLOSED"""
        from app.models.device import Enclosure
        from app.utils.enums import EnumDoorStatus

        # Check column default
        column = Enclosure.__table__.c.door_status
        assert column.default.arg == EnumDoorStatus.CLOSED

    def test_heater_enabled_default_is_false(self):
        """heater_enabled should default to False"""
        from app.models.device import Enclosure

        column = Enclosure.__table__.c.heater_enabled
        assert column.default.arg is False

    def test_fan_enabled_default_is_false(self):
        """fan_enabled should default to False"""
        from app.models.device import Enclosure

        column = Enclosure.__table__.c.fan_enabled
        assert column.default.arg is False


class TestEnclosureForeignKey:
    """Test Enclosure FK relationship to Device"""

    def test_enclosure_id_is_foreign_key_to_devices(self):
        """Enclosure.id should be FK to devices.id"""
        from app.models.device import Enclosure

        column = Enclosure.__table__.c.id
        fks = list(column.foreign_keys)
        assert len(fks) == 1
        assert fks[0].target_fullname == "devices.id"

    def test_enclosure_fk_has_cascade_delete(self):
        """Enclosure FK should have CASCADE on delete"""
        from app.models.device import Enclosure

        column = Enclosure.__table__.c.id
        fks = list(column.foreign_keys)
        assert fks[0].ondelete == "CASCADE"
