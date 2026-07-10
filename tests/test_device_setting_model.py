"""
Test: Device Setting Model (ProxySetting, CameraSetting)
PRD: PRD_Device_Setting.md Section 3
"""
import pytest
from sqlalchemy import inspect


def test_proxy_setting_model_has_required_columns():
    """2.1: ProxySetting model should have 6 columns"""
    from app.models.device_setting import ProxySetting

    mapper = inspect(ProxySetting)
    column_names = [col.key for col in mapper.columns]

    expected = ["id", "server_id", "operation_mode", "windy_mode", "created_at", "updated_at"]
    for col in expected:
        assert col in column_names, f"ProxySetting should have column '{col}'"


def test_proxy_setting_server_id_unique():
    """2.3: server_id should have UNIQUE constraint"""
    from app.models.device_setting import ProxySetting

    mapper = inspect(ProxySetting)
    server_id_col = mapper.columns["server_id"]
    assert server_id_col.unique is True, "server_id should be UNIQUE"


def test_proxy_setting_defaults():
    """2.5: Default values - operation_mode=NORMAL, windy_mode=wind0"""
    from app.models.device_setting import ProxySetting
    from app.utils.enums import EnumOperationMode, EnumWindyMode

    mapper = inspect(ProxySetting)
    op_mode_col = mapper.columns["operation_mode"]
    windy_col = mapper.columns["windy_mode"]

    assert op_mode_col.default is not None, "operation_mode should have a default"
    assert windy_col.default is not None, "windy_mode should have a default"

    # Check default values
    op_default = op_mode_col.default.arg
    windy_default = windy_col.default.arg
    assert op_default == EnumOperationMode.NORMAL
    assert windy_default == EnumWindyMode.WIND0


def test_proxy_setting_cascade_delete():
    """2.7: server_id FK should have CASCADE ondelete"""
    from app.models.device_setting import ProxySetting

    mapper = inspect(ProxySetting)
    server_id_col = mapper.columns["server_id"]

    fk = list(server_id_col.foreign_keys)[0]
    assert fk.ondelete == "CASCADE", "server_id FK should have CASCADE ondelete"


# ============================================================
# CameraSetting Model Tests
# ============================================================

def test_camera_setting_model_has_required_columns():
    """2.1/2.3: CameraSetting 14 columns (speed 삭제, tracking 추가)"""
    from app.models.device_setting import CameraSetting

    mapper = inspect(CameraSetting)
    column_names = [col.key for col in mapper.columns]

    expected = [
        "id", "camera_id", "weather_mode", "camera_mode",
        "heater", "fan", "headlight", "day_night_mode",
        "focus_mode", "iris_mode", "tracking", "palette",
        "created_at", "updated_at"
    ]
    for col in expected:
        assert col in column_names, f"CameraSetting should have column '{col}'"

    # 2.1: pan_tilt_speed, zoom_speed 삭제 확인
    assert "pan_tilt_speed" not in column_names, "pan_tilt_speed should be removed"
    assert "zoom_speed" not in column_names, "zoom_speed should be removed"

    # 2.3: 총 14개 컬럼
    assert len(column_names) == 14, f"CameraSetting should have exactly 14 columns, got {len(column_names)}"


def test_camera_setting_camera_id_unique():
    """3.3: camera_id should have UNIQUE constraint"""
    from app.models.device_setting import CameraSetting

    mapper = inspect(CameraSetting)
    camera_id_col = mapper.columns["camera_id"]
    assert camera_id_col.unique is True, "camera_id should be UNIQUE"


def test_camera_setting_defaults():
    """2.2/3.5: All defaults should match schema (tracking=IDLE)"""
    from app.models.device_setting import CameraSetting
    from app.utils.enums import (
        EnumWeatherMode, EnumCameraVideoMode, EnumOnOff, EnumDayNightMode,
        EnumFocusMode, EnumIrisMode, EnumTrackingStatus
    )

    mapper = inspect(CameraSetting)

    checks = {
        "weather_mode": EnumWeatherMode.NORMAL,
        "camera_mode": EnumCameraVideoMode.NORMAL,
        "heater": EnumOnOff.OFF,
        "fan": EnumOnOff.OFF,
        "headlight": EnumOnOff.OFF,
        "day_night_mode": EnumDayNightMode.AUTO,
        "focus_mode": EnumFocusMode.AUTO,
        "iris_mode": EnumIrisMode.AUTO,
        "tracking": EnumTrackingStatus.IDLE,
    }
    for col_name, expected_val in checks.items():
        col = mapper.columns[col_name]
        assert col.default is not None, f"{col_name} should have a default"
        assert col.default.arg == expected_val, f"{col_name} default should be {expected_val}"


def test_camera_setting_palette_nullable():
    """3.7: palette should be nullable"""
    from app.models.device_setting import CameraSetting

    mapper = inspect(CameraSetting)
    palette_col = mapper.columns["palette"]
    assert palette_col.nullable is True, "palette should be nullable"


def test_camera_setting_cascade_delete():
    """3.9: camera_id FK should have CASCADE ondelete"""
    from app.models.device_setting import CameraSetting

    mapper = inspect(CameraSetting)
    camera_id_col = mapper.columns["camera_id"]

    fk = list(camera_id_col.foreign_keys)[0]
    assert fk.ondelete == "CASCADE", "camera_id FK should have CASCADE ondelete"
