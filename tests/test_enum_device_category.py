"""
Test: EnumDeviceCategory ENUM
PRD: PRD_Device_Inheritance_Structure_Refactoring.md Section 8.1

TDD Phase 1: Red - Write failing tests for EnumDeviceCategory
"""
import pytest
from enum import Enum


class TestEnumDeviceCategory:
    """EnumDeviceCategory ENUM 테스트"""

    def test_enum_device_category_exists(self):
        """EnumDeviceCategory 클래스가 존재하는지 확인"""
        from app.utils.enums import EnumDeviceCategory
        assert EnumDeviceCategory is not None

    def test_enum_device_category_is_str_enum(self):
        """EnumDeviceCategory가 str과 Enum을 상속하는지 확인"""
        from app.utils.enums import EnumDeviceCategory
        assert issubclass(EnumDeviceCategory, str)
        assert issubclass(EnumDeviceCategory, Enum)

    def test_enum_device_category_has_controller(self):
        """CONTROLLER 값이 존재하는지 확인"""
        from app.utils.enums import EnumDeviceCategory
        assert hasattr(EnumDeviceCategory, 'CONTROLLER')
        assert EnumDeviceCategory.CONTROLLER.value == "controller"

    def test_enum_device_category_has_sensor(self):
        """SENSOR 값이 존재하는지 확인"""
        from app.utils.enums import EnumDeviceCategory
        assert hasattr(EnumDeviceCategory, 'SENSOR')
        assert EnumDeviceCategory.SENSOR.value == "sensor"

    def test_enum_device_category_has_camera(self):
        """CAMERA 값이 존재하는지 확인"""
        from app.utils.enums import EnumDeviceCategory
        assert hasattr(EnumDeviceCategory, 'CAMERA')
        assert EnumDeviceCategory.CAMERA.value == "camera"

    def test_enum_device_category_values_count(self):
        """EnumDeviceCategory가 정확히 6개의 값을 가지는지 확인.
        PRD v2.5/v2.6/v3.4에서 SPEAKER/ENCLOSURE/LAMP 추가됨.
        """
        from app.utils.enums import EnumDeviceCategory
        assert len(EnumDeviceCategory) == 6
        # SPEAKER/ENCLOSURE/LAMP 3개 신규 값 검증
        assert hasattr(EnumDeviceCategory, 'SPEAKER')
        assert EnumDeviceCategory.SPEAKER.value == "speaker"
        assert hasattr(EnumDeviceCategory, 'ENCLOSURE')
        assert EnumDeviceCategory.ENCLOSURE.value == "enclosure"
        assert hasattr(EnumDeviceCategory, 'LAMP')
        assert EnumDeviceCategory.LAMP.value == "lamp"

    def test_enum_device_category_string_comparison(self):
        """EnumDeviceCategory 값이 문자열과 비교 가능한지 확인"""
        from app.utils.enums import EnumDeviceCategory
        assert EnumDeviceCategory.CONTROLLER == "controller"
        assert EnumDeviceCategory.SENSOR == "sensor"
        assert EnumDeviceCategory.CAMERA == "camera"
