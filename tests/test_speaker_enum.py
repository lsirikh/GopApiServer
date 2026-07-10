"""
Tests for Speaker-related Enums
PRD: PRD_Speaker_Device.md - Phase 1: Enum
TDD: Red -> Green -> Refactor
"""
import pytest


class TestEnumDeviceCategoryExtension:
    """Test EnumDeviceCategory extension for SPEAKER"""

    def test_enum_device_category_has_speaker_value(self):
        """EnumDeviceCategory should have SPEAKER value"""
        from app.utils.enums import EnumDeviceCategory

        assert hasattr(EnumDeviceCategory, 'SPEAKER')

    def test_enum_device_category_speaker_equals_speaker_string(self):
        """EnumDeviceCategory.SPEAKER should equal 'speaker' string"""
        from app.utils.enums import EnumDeviceCategory

        assert EnumDeviceCategory.SPEAKER.value == "speaker"


class TestEnumSpeakerType:
    """Test EnumSpeakerType (New)"""

    def test_enum_speaker_type_exists(self):
        """EnumSpeakerType should exist"""
        from app.utils.enums import EnumSpeakerType

        assert EnumSpeakerType is not None

    def test_enum_speaker_type_has_normal_value(self):
        """EnumSpeakerType should have NORMAL value"""
        from app.utils.enums import EnumSpeakerType

        assert hasattr(EnumSpeakerType, 'NORMAL')
        assert EnumSpeakerType.NORMAL.value == "NORMAL"

    def test_enum_speaker_type_has_admin_value(self):
        """EnumSpeakerType should have ADMIN value"""
        from app.utils.enums import EnumSpeakerType

        assert hasattr(EnumSpeakerType, 'ADMIN')
        assert EnumSpeakerType.ADMIN.value == "ADMIN"

    def test_enum_speaker_type_has_monitor_value(self):
        """EnumSpeakerType should have MONITOR value"""
        from app.utils.enums import EnumSpeakerType

        assert hasattr(EnumSpeakerType, 'MONITOR')
        assert EnumSpeakerType.MONITOR.value == "MONITOR"

    def test_enum_speaker_type_has_dev_value(self):
        """EnumSpeakerType should have DEV value"""
        from app.utils.enums import EnumSpeakerType

        assert hasattr(EnumSpeakerType, 'DEV')
        assert EnumSpeakerType.DEV.value == "DEV"
