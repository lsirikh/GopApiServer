"""
Test: CameraSetting Router (GET/PATCH)
PRD: PRD_Device_Setting.md Section 5.2
"""
import pytest
from app.models.device import Camera
from app.models.device_setting import CameraSetting
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType


def _create_camera(db):
    """Helper to create a test camera"""
    camera = Camera(
        number_device=1,
        group_device=1,
        name_device="Test Camera",
        type_device=EnumDeviceType.IpCamera,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=80,
        mode=EnumCameraMode.ONVIF,
        category=EnumCameraType.PTZ,
        urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}}}
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


class TestCameraSettingGet:
    """Tests for GET /api/devices/cameras/{camera_id}/settings"""

    def test_get_camera_settings_not_found(self, client, test_db):
        """9.1: 존재하지 않는 카메라 → 404"""
        response = client.get("/api/devices/cameras/9999/settings")
        assert response.status_code == 404

    def test_get_camera_settings_lazy_create(self, client, test_db):
        """4.1/9.3: 설정 없을 때 → 기본값 Lazy 생성 후 200, tracking=IDLE, speed 없음"""
        camera = _create_camera(test_db)

        response = client.get(f"/api/devices/cameras/{camera.id}/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["camera_id"] == camera.id
        assert data["data"]["weather_mode"] == "NORMAL"
        assert data["data"]["camera_mode"] == "NORMAL"
        assert data["data"]["heater"] == "off"
        assert data["data"]["fan"] == "off"
        assert data["data"]["headlight"] == "off"
        assert data["data"]["day_night_mode"] == "AUTO"
        assert data["data"]["focus_mode"] == "AUTO"
        assert data["data"]["iris_mode"] == "AUTO"
        assert data["data"]["tracking"] == "IDLE"
        assert data["data"]["palette"] is None
        assert "pan_tilt_speed" not in data["data"]
        assert "zoom_speed" not in data["data"]

    def test_get_camera_settings_existing(self, client, test_db):
        """9.5: 기존 설정 반환"""
        camera = _create_camera(test_db)

        response1 = client.get(f"/api/devices/cameras/{camera.id}/settings")
        response2 = client.get(f"/api/devices/cameras/{camera.id}/settings")
        assert response2.json()["data"]["id"] == response1.json()["data"]["id"]

    def test_get_camera_settings_all_defaults(self, client, test_db):
        """9.7: 모든 기본값 정확성 확인 (tracking=IDLE, palette=null)"""
        camera = _create_camera(test_db)

        response = client.get(f"/api/devices/cameras/{camera.id}/settings")
        data = response.json()["data"]

        defaults = {
            "weather_mode": "NORMAL",
            "camera_mode": "NORMAL",
            "heater": "off",
            "fan": "off",
            "headlight": "off",
            "day_night_mode": "AUTO",
            "focus_mode": "AUTO",
            "iris_mode": "AUTO",
            "tracking": "IDLE",
            "palette": None,
        }
        for field, expected in defaults.items():
            assert data[field] == expected, f"{field} should be {expected}, got {data[field]}"


class TestCameraSettingPatch:
    """Tests for PATCH /api/devices/cameras/{camera_id}/settings"""

    def test_patch_camera_settings_not_found(self, client, test_db):
        """10.1: 존재하지 않는 카메라 → 404"""
        response = client.patch("/api/devices/cameras/9999/settings", json={"heater": "on"})
        assert response.status_code == 404

    def test_patch_camera_settings_upsert(self, client, test_db):
        """10.3: 설정 없을 때 → Upsert"""
        camera = _create_camera(test_db)

        response = client.patch(
            f"/api/devices/cameras/{camera.id}/settings",
            json={"heater": "on", "fan": "on"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["heater"] == "on"
        assert data["fan"] == "on"
        assert data["weather_mode"] == "NORMAL"  # default preserved

    def test_patch_camera_settings_partial_update(self, client, test_db):
        """4.2/10.5: PATCH tracking="ACTIVE" 부분 수정 확인"""
        camera = _create_camera(test_db)

        # Create settings first
        client.get(f"/api/devices/cameras/{camera.id}/settings")

        # Update tracking
        response = client.patch(
            f"/api/devices/cameras/{camera.id}/settings",
            json={"weather_mode": "FOG", "tracking": "ACTIVE"}
        )
        data = response.json()["data"]
        assert data["weather_mode"] == "FOG"
        assert data["tracking"] == "ACTIVE"
        assert data["heater"] == "off"  # unchanged

    def test_patch_camera_settings_invalid_tracking(self, client, test_db):
        """4.3: PATCH 잘못된 tracking 값 → 422"""
        camera = _create_camera(test_db)

        response = client.patch(
            f"/api/devices/cameras/{camera.id}/settings",
            json={"tracking": "INVALID_VALUE"}
        )
        assert response.status_code == 422

    def test_patch_camera_settings_palette(self, client, test_db):
        """10.9: palette null → 값 설정"""
        camera = _create_camera(test_db)

        # Create with default (palette=null)
        response = client.get(f"/api/devices/cameras/{camera.id}/settings")
        assert response.json()["data"]["palette"] is None

        # Set palette
        response = client.patch(
            f"/api/devices/cameras/{camera.id}/settings",
            json={"palette": "IRONBOW"}
        )
        assert response.json()["data"]["palette"] == "IRONBOW"

    def test_patch_camera_settings_focus_iris(self, client, test_db):
        """5.3 v1.1: PATCH focus_mode, iris_mode 부분 수정 확인"""
        camera = _create_camera(test_db)

        # Create via GET first
        client.get(f"/api/devices/cameras/{camera.id}/settings")

        # Update focus_mode and iris_mode
        response = client.patch(
            f"/api/devices/cameras/{camera.id}/settings",
            json={"focus_mode": "MANUAL", "iris_mode": "MANUAL"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["focus_mode"] == "MANUAL"
        assert data["iris_mode"] == "MANUAL"
        assert data["heater"] == "off"  # unchanged


class TestCameraSettingPut:
    """Tests for PUT /api/devices/cameras/{camera_id}/settings"""

    _full_body = {
        "weather_mode": "FOG",
        "camera_mode": "STABILIZATION",
        "heater": "on",
        "fan": "on",
        "headlight": "off",
        "day_night_mode": "NIGHT",
        "focus_mode": "MANUAL",
        "iris_mode": "AUTO",
        "tracking": "ACTIVE",
    }

    def test_put_camera_settings_not_found(self, client, test_db):
        """7.1 v1.1: PUT 존재하지 않는 카메라 → 404"""
        response = client.put("/api/devices/cameras/9999/settings", json=self._full_body)
        assert response.status_code == 404

    def test_put_camera_settings_upsert(self, client, test_db):
        """4.4/7.3: PUT 설정 없을 때 → Upsert (tracking 포함 확인)"""
        camera = _create_camera(test_db)

        response = client.put(
            f"/api/devices/cameras/{camera.id}/settings",
            json=self._full_body
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["weather_mode"] == "FOG"
        assert data["focus_mode"] == "MANUAL"
        assert data["iris_mode"] == "AUTO"
        assert data["tracking"] == "ACTIVE"
        assert data["camera_id"] == camera.id

    def test_put_camera_settings_full_replace(self, client, test_db):
        """4.4/7.5: PUT 기존 설정 전체 교체 (tracking 포함 확인)"""
        camera = _create_camera(test_db)

        # Create initial settings via GET (defaults)
        client.get(f"/api/devices/cameras/{camera.id}/settings")

        # Replace all fields
        response = client.put(
            f"/api/devices/cameras/{camera.id}/settings",
            json=self._full_body
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["weather_mode"] == "FOG"
        assert data["camera_mode"] == "STABILIZATION"
        assert data["heater"] == "on"
        assert data["fan"] == "on"
        assert data["headlight"] == "off"
        assert data["day_night_mode"] == "NIGHT"
        assert data["focus_mode"] == "MANUAL"
        assert data["iris_mode"] == "AUTO"
        assert data["tracking"] == "ACTIVE"
        assert data["palette"] is None

    def test_put_camera_settings_missing_field_422(self, client, test_db):
        """4.5/7.7: PUT tracking 누락 → 422 Validation Error"""
        camera = _create_camera(test_db)

        # Missing tracking (required)
        response = client.put(
            f"/api/devices/cameras/{camera.id}/settings",
            json={"weather_mode": "NORMAL", "camera_mode": "NORMAL"}
        )
        assert response.status_code == 422

        # Empty body
        response = client.put(
            f"/api/devices/cameras/{camera.id}/settings",
            json={}
        )
        assert response.status_code == 422

    def test_put_camera_settings_palette_null(self, client, test_db):
        """7.9 v1.1: PUT palette null 허용"""
        camera = _create_camera(test_db)

        body_with_palette = {**self._full_body, "palette": "IRONBOW"}
        response = client.put(
            f"/api/devices/cameras/{camera.id}/settings",
            json=body_with_palette
        )
        assert response.status_code == 200
        assert response.json()["data"]["palette"] == "IRONBOW"

        # Replace with palette=null
        body_no_palette = {**self._full_body}  # palette not included = null
        response = client.put(
            f"/api/devices/cameras/{camera.id}/settings",
            json=body_no_palette
        )
        assert response.status_code == 200
        assert response.json()["data"]["palette"] is None

    def test_put_camera_settings_invalid_tracking_422(self, client, test_db):
        """4.5: PUT 잘못된 tracking 값 → 422"""
        camera = _create_camera(test_db)

        body_bad_tracking = {**self._full_body, "tracking": "INVALID_VALUE"}
        response = client.put(
            f"/api/devices/cameras/{camera.id}/settings",
            json=body_bad_tracking
        )
        assert response.status_code == 422
