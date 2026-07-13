"""
Test: Device Setting Schema (ProxySetting, CameraSetting)
PRD: PRD_Device_Setting.md Section 4
"""
import pytest
from pydantic import ValidationError


def test_proxy_setting_update_all_optional():
    """4.1: ProxySettingUpdate - all fields should be Optional"""
    from app.schemas.device_setting import ProxySettingUpdate

    # Empty body should be valid
    schema = ProxySettingUpdate()
    assert schema.operation_mode is None
    assert schema.windy_mode is None

    # Partial update should be valid
    schema2 = ProxySettingUpdate(operation_mode="REGISTER")
    assert schema2.operation_mode == "REGISTER"
    assert schema2.windy_mode is None


def test_proxy_setting_response_fields():
    """4.3: ProxySettingResponse should have all required fields"""
    from app.schemas.device_setting import ProxySettingResponse

    fields = ProxySettingResponse.model_fields
    expected = ["id", "server_id", "operation_mode", "windy_mode", "created_at", "updated_at"]
    for f in expected:
        assert f in fields, f"ProxySettingResponse should have field '{f}'"


def test_proxy_setting_response_from_attributes():
    """4.5: ProxySettingResponse should support ORM mapping"""
    from app.schemas.device_setting import ProxySettingResponse

    assert ProxySettingResponse.model_config.get("from_attributes") is True


# ============================================================
# CameraSetting Schema Tests
# ============================================================

def test_camera_setting_update_all_optional():
    """3.2: CameraSettingUpdate - all fields Optional, tracking 포함, speed 없음"""
    from app.schemas.device_setting import CameraSettingUpdate

    # Empty body should be valid
    schema = CameraSettingUpdate()
    assert schema.weather_mode is None
    assert schema.camera_mode is None
    assert schema.heater is None
    assert schema.fan is None
    assert schema.headlight is None
    assert schema.day_night_mode is None
    assert schema.focus_mode is None
    assert schema.iris_mode is None
    assert schema.tracking is None
    assert schema.palette is None

    # pan_tilt_speed, zoom_speed 없음 확인
    assert not hasattr(schema, "pan_tilt_speed")
    assert not hasattr(schema, "zoom_speed")


def test_camera_setting_update_tracking_enum():
    """3.2: CameraSettingUpdate - tracking should accept EnumTrackingStatus values"""
    from app.schemas.device_setting import CameraSettingUpdate

    schema = CameraSettingUpdate(tracking="ACTIVE")
    assert schema.tracking == "ACTIVE"

    schema2 = CameraSettingUpdate(tracking="LOST")
    assert schema2.tracking == "LOST"

    with pytest.raises(ValidationError):
        CameraSettingUpdate(tracking="INVALID")


def test_camera_setting_response_fields():
    """3.3: CameraSettingResponse should have 14 fields (tracking, no speed)"""
    from app.schemas.device_setting import CameraSettingResponse

    fields = CameraSettingResponse.model_fields
    expected = [
        "id", "camera_id", "weather_mode", "camera_mode",
        "heater", "fan", "headlight", "day_night_mode",
        "focus_mode", "iris_mode", "tracking", "palette",
        "created_at", "updated_at"
    ]
    for f in expected:
        assert f in fields, f"CameraSettingResponse should have field '{f}'"

    # speed 필드 없음 확인
    assert "pan_tilt_speed" not in fields
    assert "zoom_speed" not in fields
    assert len(fields) == 14


def test_camera_setting_response_palette_nullable():
    """5.7: palette should be Optional[str] in response"""
    from app.schemas.device_setting import CameraSettingResponse

    field_info = CameraSettingResponse.model_fields["palette"]
    # palette should allow None
    assert field_info.is_required() is False


# ============================================================
# PUT Schema Tests (v1.1)
# ============================================================

def test_proxy_setting_create_all_required():
    """4.1 v1.1: ProxySettingCreate - all fields should be required"""
    from app.schemas.device_setting import ProxySettingCreate

    fields = ProxySettingCreate.model_fields
    assert fields["operation_mode"].is_required() is True
    assert fields["windy_mode"].is_required() is True

    # Valid creation
    schema = ProxySettingCreate(operation_mode="REGISTER", windy_mode="wind2")
    assert schema.operation_mode == "REGISTER"
    assert schema.windy_mode == "wind2"


def test_proxy_setting_create_missing_field_error():
    """4.3 v1.1: ProxySettingCreate - missing field should raise ValidationError"""
    from app.schemas.device_setting import ProxySettingCreate

    with pytest.raises(ValidationError):
        ProxySettingCreate(operation_mode="NORMAL")  # windy_mode missing

    with pytest.raises(ValidationError):
        ProxySettingCreate(windy_mode="wind0")  # operation_mode missing

    with pytest.raises(ValidationError):
        ProxySettingCreate()  # all missing


def test_camera_setting_create_all_required_except_palette():
    """3.1: CameraSettingCreate - tracking required, speed 없음, palette optional"""
    from app.schemas.device_setting import CameraSettingCreate

    fields = CameraSettingCreate.model_fields
    required_fields = [
        "weather_mode", "camera_mode", "heater", "fan", "headlight",
        "day_night_mode", "focus_mode", "iris_mode", "tracking"
    ]
    for f in required_fields:
        assert fields[f].is_required() is True, f"{f} should be required"

    # palette should be optional
    assert fields["palette"].is_required() is False

    # pan_tilt_speed, zoom_speed 없음 확인
    assert "pan_tilt_speed" not in fields
    assert "zoom_speed" not in fields

    # Valid creation
    schema = CameraSettingCreate(
        weather_mode="FOG", camera_mode="STABILIZATION",
        heater="on", fan="on", headlight="off",
        day_night_mode="NIGHT", focus_mode="MANUAL", iris_mode="AUTO",
        tracking="ACTIVE"
    )
    assert schema.tracking == "ACTIVE"
    assert schema.palette is None


def test_camera_setting_create_missing_field_error():
    """3.1: CameraSettingCreate - missing required field → ValidationError"""
    from app.schemas.device_setting import CameraSettingCreate

    # Missing all fields
    with pytest.raises(ValidationError):
        CameraSettingCreate()

    # Missing tracking
    with pytest.raises(ValidationError):
        CameraSettingCreate(
            weather_mode="NORMAL", camera_mode="NORMAL",
            heater="off", fan="off", headlight="off",
            day_night_mode="AUTO", focus_mode="AUTO", iris_mode="AUTO"
        )

    # Invalid tracking value
    with pytest.raises(ValidationError):
        CameraSettingCreate(
            weather_mode="NORMAL", camera_mode="NORMAL",
            heater="off", fan="off", headlight="off",
            day_night_mode="AUTO", focus_mode="AUTO", iris_mode="AUTO",
            tracking="INVALID"
        )
