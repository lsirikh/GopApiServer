"""
Phase 31: Enum Update Tests
PRD: docs/Enum-Update-PRD.md

Tests to verify Enum definitions match C# client specifications.
"""
import pytest
from app.utils.enums import (
    EnumMappingEventCategory,
    EnumEventType,
    EnumDetectionType,
    EnumDeviceType,
    EnumTrueFalse,
)


class TestEnumEventCategory:
    """EnumMappingEventCategory 테스트 - 신규 Enum
    Renamed: EnumEventCategory → EnumMappingEventCategory (PRD_CategoryEvent_Refactoring)
    """

    def test_enum_event_category_has_all_values(self):
        """EnumMappingEventCategory가 8개 값을 모두 포함하는지 확인"""
        expected_values = [
            "NONE",
            "FENCE_SENSOR_ONLY",
            "FENCE_SENSOR_WITH_MULTI_SENSOR",
            "MULTI_SENSOR_ONLY",
            "SENSOR_WITH_CAMERA",
            "SENSOR_WITH_AI_CAMERA",
            "AI_CAMERA_ONLY",
            "CAMERA_ONLY",
        ]

        actual_values = [e.value for e in EnumMappingEventCategory]

        for expected in expected_values:
            assert expected in actual_values, f"Missing value: {expected}"

        assert len(actual_values) == 8, f"Expected 8 values, got {len(actual_values)}"

    def test_enum_event_category_legacy_mapping(self):
        """기존 EnumCategoryEvent 값이 호환되는지 확인"""
        # 기존 값 → 신규 값 매핑 테스트
        legacy_mappings = {
            "SENSOR_ONLY": "FENCE_SENSOR_ONLY",  # 기존 SENSOR_ONLY → FENCE_SENSOR_ONLY
            "SENSOR_WITH_AI_DETECT": "SENSOR_WITH_AI_CAMERA",
            "AI_DETECT_ONLY": "AI_CAMERA_ONLY",
        }

        for legacy_value, new_value in legacy_mappings.items():
            # _missing_ 메서드로 기존 값 처리
            result = EnumMappingEventCategory(legacy_value)
            assert result.value == new_value, f"Legacy {legacy_value} should map to {new_value}"

    def test_enum_event_category_sensor_with_camera_unchanged(self):
        """SENSOR_WITH_CAMERA는 변경 없이 유지"""
        assert EnumMappingEventCategory.SENSOR_WITH_CAMERA.value == "SENSOR_WITH_CAMERA"


class TestEnumEventType:
    """EnumEventType 테스트"""

    def test_enum_event_type_values(self):
        """EnumEventType이 7개 값만 포함하는지 확인 (불필요 항목 제거됨)"""
        expected_values = [
            "None",
            "Intrusion",
            "ContactOn",
            "ContactOff",
            "Connection",
            "Action",
            "Fault",
            "WindyMode",
        ]

        actual_values = [e.value for e in EnumEventType]

        for expected in expected_values:
            assert expected in actual_values, f"Missing value: {expected}"

        # 제거된 값들이 없는지 확인
        removed_values = ["Lowlight", "DetectionMode", "TrackingMode"]
        for removed in removed_values:
            assert removed not in actual_values, f"Value should be removed: {removed}"

    def test_enum_event_type_none_alias(self):
        """None 값 별칭 처리 확인"""
        assert EnumEventType("None") == EnumEventType.None_


class TestEnumDetectionType:
    """EnumDetectionType 테스트"""

    def test_enum_detection_type_ai_detect(self):
        """AI_DETECT 값이 존재하는지 확인"""
        assert hasattr(EnumDetectionType, "AI_DETECT")
        assert EnumDetectionType.AI_DETECT.value == "AI_DETECT"

    def test_enum_detection_type_all_values(self):
        """EnumDetectionType이 9개 값을 포함하는지 확인"""
        expected_values = [
            "NONE",
            "CABLE_CUTTING",
            "CABLE_CONNECTED",
            "PIR_SENSOR",
            "THERMAL_SENSOR",
            "VIBRATION_SENSOR",
            "CONTACT_SENSOR",
            "DISTANCE_SENSOR",
            "AI_DETECT",
        ]

        actual_values = [e.value for e in EnumDetectionType]

        for expected in expected_values:
            assert expected in actual_values, f"Missing value: {expected}"

        assert len(actual_values) == 9, f"Expected 9 values, got {len(actual_values)}"


class TestEnumDeviceType:
    """EnumDeviceType 테스트 - 변경 없음 확인"""

    def test_enum_device_type_unchanged(self):
        """EnumDeviceType이 기존 값을 유지하는지 확인"""
        expected_values = [
            "NONE",
            "Controller",
            "Multi",
            "Fence",
            "Underground",
            "Contact",
            "PIR",
            "IoController",
            "Laser",
            "Cable",
            "IpCamera",
            "SmartSensor",
            "SmartSensor2",
            "SmartCompound",
            "IpSpeaker",
            "Radar",
            "OpticalCable",
            "Fence_Group",
        ]

        actual_values = [e.value for e in EnumDeviceType]

        for expected in expected_values:
            assert expected in actual_values, f"Missing value: {expected}"


class TestEnumTrueFalse:
    """EnumTrueFalse 테스트 - 변경 없음 확인"""

    def test_enum_true_false_unchanged(self):
        """EnumTrueFalse가 기존 값을 유지하는지 확인"""
        assert EnumTrueFalse.False_.value == "False"
        assert EnumTrueFalse.True_.value == "True"

    def test_enum_true_false_alias(self):
        """True/False 별칭 처리 확인"""
        assert EnumTrueFalse("False") == EnumTrueFalse.False_
        assert EnumTrueFalse("True") == EnumTrueFalse.True_
