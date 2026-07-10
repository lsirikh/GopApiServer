"""
Tests for Enclosure-related Enums
PRD: PRD_Enclosure_Device.md v1.1 - Phase 1: Enum
TDD: Red -> Green -> Refactor
"""
import pytest


class TestEnumDoorStatus:
    """Test EnumDoorStatus (New)"""

    def test_enum_door_status_exists(self):
        """EnumDoorStatus should exist"""
        from app.utils.enums import EnumDoorStatus

        assert EnumDoorStatus is not None

    def test_enum_door_status_has_closed_value(self):
        """EnumDoorStatus should have CLOSED value"""
        from app.utils.enums import EnumDoorStatus

        assert hasattr(EnumDoorStatus, 'CLOSED')
        assert EnumDoorStatus.CLOSED.value == "CLOSED"

    def test_enum_door_status_has_open_value(self):
        """EnumDoorStatus should have OPEN value"""
        from app.utils.enums import EnumDoorStatus

        assert hasattr(EnumDoorStatus, 'OPEN')
        assert EnumDoorStatus.OPEN.value == "OPEN"

    def test_enum_door_status_inherits_from_str_and_enum(self):
        """EnumDoorStatus should inherit from str and Enum"""
        from app.utils.enums import EnumDoorStatus
        from enum import Enum

        assert issubclass(EnumDoorStatus, str)
        assert issubclass(EnumDoorStatus, Enum)

    def test_enum_door_status_has_exactly_two_values(self):
        """EnumDoorStatus should have exactly 2 values (CLOSED, OPEN)"""
        from app.utils.enums import EnumDoorStatus

        values = list(EnumDoorStatus)
        assert len(values) == 2


class TestEnumDeviceCategoryExtension:
    """Test EnumDeviceCategory extension for ENCLOSURE"""

    def test_enum_device_category_has_enclosure_value(self):
        """EnumDeviceCategory should have ENCLOSURE value"""
        from app.utils.enums import EnumDeviceCategory

        assert hasattr(EnumDeviceCategory, 'ENCLOSURE')

    def test_enum_device_category_enclosure_equals_enclosure_string(self):
        """EnumDeviceCategory.ENCLOSURE should equal 'enclosure' string"""
        from app.utils.enums import EnumDeviceCategory

        assert EnumDeviceCategory.ENCLOSURE.value == "enclosure"
