"""
Test: Device Setting Enum 정의 검증
PRD: PRD_Device_Setting.md Section 2
"""
from enum import Enum


def test_enum_operation_mode_exists():
    """EnumOperationMode should have NORMAL, REGISTER (2 values)"""
    from app.utils.enums import EnumOperationMode

    assert issubclass(EnumOperationMode, Enum)
    assert issubclass(EnumOperationMode, str)

    values = [m.value for m in EnumOperationMode]
    assert values == ["NORMAL", "REGISTER"]


def test_enum_windy_mode_exists():
    """EnumWindyMode should have wind0~wind3 (4 values)"""
    from app.utils.enums import EnumWindyMode

    assert issubclass(EnumWindyMode, Enum)
    assert issubclass(EnumWindyMode, str)

    values = [m.value for m in EnumWindyMode]
    assert values == ["wind0", "wind1", "wind2", "wind3"]


def test_enum_weather_mode_exists():
    """EnumWeatherMode should have 7 values"""
    from app.utils.enums import EnumWeatherMode

    assert issubclass(EnumWeatherMode, Enum)
    assert issubclass(EnumWeatherMode, str)

    values = [m.value for m in EnumWeatherMode]
    assert values == ["NORMAL", "FOG", "SEA_FOG", "YELLOW_DUST", "RAIN", "SNOW", "HEAT_HAZE"]


def test_enum_camera_video_mode_exists():
    """EnumCameraVideoMode should have 4 values (not EnumCameraMode which is connection protocol)"""
    from app.utils.enums import EnumCameraVideoMode

    assert issubclass(EnumCameraVideoMode, Enum)
    assert issubclass(EnumCameraVideoMode, str)

    values = [m.value for m in EnumCameraVideoMode]
    assert values == ["NORMAL", "STABILIZATION", "BLC", "NIGHT_ENHANCE"]


def test_enum_on_off_exists():
    """EnumOnOff should have on, off (lowercase, 2 values)"""
    from app.utils.enums import EnumOnOff

    assert issubclass(EnumOnOff, Enum)
    assert issubclass(EnumOnOff, str)

    values = [m.value for m in EnumOnOff]
    assert values == ["on", "off"]


def test_enum_day_night_mode_exists():
    """EnumDayNightMode should have AUTO, DAY, NIGHT (3 values)"""
    from app.utils.enums import EnumDayNightMode

    assert issubclass(EnumDayNightMode, Enum)
    assert issubclass(EnumDayNightMode, str)

    values = [m.value for m in EnumDayNightMode]
    assert values == ["AUTO", "DAY", "NIGHT"]


def test_enum_palette_exists():
    """EnumPalette should have 4 values"""
    from app.utils.enums import EnumPalette

    assert issubclass(EnumPalette, Enum)
    assert issubclass(EnumPalette, str)

    values = [m.value for m in EnumPalette]
    assert values == ["WHITE_HOT", "BLACK_HOT", "RAINBOW", "IRONBOW"]


def test_enum_focus_mode_exists():
    """EnumFocusMode should have AUTO, MANUAL (2 values)"""
    from app.utils.enums import EnumFocusMode

    assert issubclass(EnumFocusMode, Enum)
    assert issubclass(EnumFocusMode, str)

    values = [m.value for m in EnumFocusMode]
    assert values == ["AUTO", "MANUAL"]


def test_enum_iris_mode_exists():
    """EnumIrisMode should have AUTO, MANUAL (2 values)"""
    from app.utils.enums import EnumIrisMode

    assert issubclass(EnumIrisMode, Enum)
    assert issubclass(EnumIrisMode, str)

    values = [m.value for m in EnumIrisMode]
    assert values == ["AUTO", "MANUAL"]


def test_enum_tracking_status_exists():
    """1.1: EnumTrackingStatus should have ACTIVE, LOST, IDLE (3 values)"""
    from app.utils.enums import EnumTrackingStatus

    assert issubclass(EnumTrackingStatus, Enum)
    assert issubclass(EnumTrackingStatus, str)

    values = [m.value for m in EnumTrackingStatus]
    assert values == ["ACTIVE", "LOST", "IDLE"]
