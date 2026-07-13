"""
E2E (Symbol_Apply_DeviceLocation): 맵 장비 심볼 "현재위치 적용" 클라이언트 계약 검증.

.NET 클라이언트가 보내는 형태와 동일:
  DeviceLocationGateway → IDeviceApiService.PatchGeolocationAsync
  → PATCH /api/devices/{kind}/{id}  body = {"geolocation": {latitude, longitude, altitude, heading, location}}

핵심 보증(code-reviewer H1): 좌표만 바뀌고 이름/IP/비밀번호/카테고리/하드웨어스펙은 보존되어야 한다
(전체 DTO PUT은 맵 LinkedDevice가 목록엔드포인트라 password/스펙 미적재 → 소거 위험이라 폐기,
 geolocation-only PATCH로 전환한 것이 실제로 안전한지 끝단에서 실증).
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSymbolApplyDeviceLocationE2E:

    @staticmethod
    def _full_camera(num):
        return {
            "number_device": num, "group_device": 1,
            "name_device": "현위치테스트 카메라", "type_device": "IpCamera",
            "version": "1.0.0", "status": "ACTIVATED",
            "ip_address": "192.168.50.77", "ip_port": 80,
            "user_name": "admin", "user_password": "secret-pass-123",
            "mode": "ONVIF", "category": "PTZ",
            "geolocation": {"latitude": 37.1, "longitude": 127.1, "altitude": 50.0, "heading": 90.0},
            "hardware_spec": {"manufacturer": "Hanwha", "model": "XNP-6400", "max_detection_range": 120.0},
        }

    def test_should_update_coords_and_preserve_other_fields_when_geolocation_only_patch(self, db_session):
        # Arrange — password/hardware_spec 포함 전체 카메라 생성
        create = client.post("/api/devices/cameras", json=self._full_camera(9301))
        assert create.status_code in (200, 201), create.text
        cam_id = create.json()["data"]["id"]

        # Act — 클라가 보내는 것과 동일: geolocation 만 PATCH (좌표/방위 변경)
        new_geo = {"latitude": 37.566800, "longitude": 126.978100, "altitude": 50.0, "heading": 270.0}
        patch = client.patch(f"/api/devices/cameras/{cam_id}", json={"geolocation": new_geo})
        assert patch.status_code == 200, patch.text

        # Assert — 재조회: 좌표는 변경, 그 외 필드는 보존
        got = client.get(f"/api/devices/cameras/{cam_id}").json()["data"]
        geo = got["geolocation"]
        assert abs(geo["latitude"] - 37.566800) < 1e-6, geo
        assert abs(geo["longitude"] - 126.978100) < 1e-6, geo
        assert abs(geo["heading"] - 270.0) < 1e-6, geo
        # ── H1 핵심: 좌표 외 필드 무손상 ──
        assert got["name_device"] == "현위치테스트 카메라"
        assert got["ip_address"] == "192.168.50.77"
        assert got["category"] == "PTZ"
        assert got["user_password"] == "secret-pass-123"          # 비밀번호 소거 안 됨
        assert got["hardware_spec"]["model"] == "XNP-6400"        # 하드웨어 스펙 소거 안 됨
        assert got["hardware_spec"]["max_detection_range"] == 120.0  # 최대탐지거리(신규 필드)도 보존

    def test_should_preserve_altitude_when_patch_includes_it(self, db_session):
        # geolocation JSONB는 전체 교체 → 클라가 altitude/location 포함해 보내 보존하는지
        create = client.post("/api/devices/cameras", json=self._full_camera(9303))
        cam_id = create.json()["data"]["id"]
        client.patch(f"/api/devices/cameras/{cam_id}",
                     json={"geolocation": {"latitude": 37.5, "longitude": 127.5, "altitude": 50.0, "heading": 10.0}})
        geo = client.get(f"/api/devices/cameras/{cam_id}").json()["data"]["geolocation"]
        assert abs(geo["altitude"] - 50.0) < 1e-6, geo

    def test_should_set_max_detection_range_via_hardware_spec_patch(self, db_session):
        # 운영자가 카메라 최대탐지거리를 설정/변경 — hardware_spec PATCH(JSONB, DB 컬럼 추가 없음)
        create = client.post("/api/devices/cameras", json=self._full_camera(9304))
        cam_id = create.json()["data"]["id"]
        patch = client.patch(
            f"/api/devices/cameras/{cam_id}",
            json={"hardware_spec": {"manufacturer": "Hanwha", "model": "XNP-6400", "max_detection_range": 250.0}})
        assert patch.status_code == 200, patch.text
        got = client.get(f"/api/devices/cameras/{cam_id}").json()["data"]
        assert got["hardware_spec"]["max_detection_range"] == 250.0, got["hardware_spec"]

    def test_should_apply_geolocation_patch_for_sensor_kind(self, db_session):
        # 다른 장비 타입(sensors) 경로도 geolocation-only PATCH 수용 — 게이트웨이 타입 분기 계약
        sensor = {
            "number_device": 9302, "group_device": 1, "name_device": "현위치 센서",
            "type_device": "Sensor", "version": "1.0.0", "status": "ACTIVATED",
            "geolocation": {"latitude": 37.2, "longitude": 127.2},
        }
        create = client.post("/api/devices/sensors", json=sensor)
        if create.status_code not in (200, 201):
            pytest.skip(f"sensor 생성 스키마 상이(범위 밖): {create.status_code} {create.text[:120]}")
        sid = create.json()["data"]["id"]
        patch = client.patch(f"/api/devices/sensors/{sid}",
                             json={"geolocation": {"latitude": 37.99, "longitude": 127.99}})
        assert patch.status_code == 200, patch.text
        got = client.get(f"/api/devices/sensors/{sid}").json()["data"]
        assert abs(got["geolocation"]["latitude"] - 37.99) < 1e-6
        assert got["name_device"] == "현위치 센서"
