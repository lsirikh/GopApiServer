"""
Phase 8: Camera URLs Validation Tests
PRD: PRD_Camera_Urls_JsonB.md v1.0

Test URL format validation and null handling for CameraUrls JSONB.
Updated: 2026-01-07 - Simplified schema (dict-based instead of nested models)
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.device import CameraUrls


class TestCameraUrlsNullHandling:
    """Phase 8.2: Null 처리 tests"""

    def test_urls_null_is_acceptable(self, client: TestClient, test_db):
        """Test: urls=null is acceptable"""
        # When: POST camera with urls=null
        camera_data = {
            "number_device": 8001,
            "group_device": 1,
            "name_device": "Null URLs Camera",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.100",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": None
        }
        response = client.post("/api/devices/cameras", json=camera_data)

        # Then: Camera created successfully
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["urls"] is None

    def test_urls_streams_null_is_acceptable(self, client: TestClient, test_db):
        """Test: urls.streams=null is acceptable"""
        # When: POST camera with urls.streams=null
        camera_data = {
            "number_device": 8002,
            "group_device": 1,
            "name_device": "Null Streams Camera",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.101",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "homepage": {"url": "http://192.168.1.101"},
                "streams": None
            }
        }
        response = client.post("/api/devices/cameras", json=camera_data)

        # Then: Camera created successfully
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["urls"]["homepage"]["url"] == "http://192.168.1.101"
        assert data["urls"]["streams"] is None

    def test_urls_streams_rtsp_can_be_omitted(self, client: TestClient, test_db):
        """Test: urls.streams.rtsp can be omitted (only webrtc present)"""
        # When: POST camera with only webrtc stream (no rtsp key)
        camera_data = {
            "number_device": 8003,
            "group_device": 1,
            "name_device": "WebRTC Only Camera",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.102",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "streams": {
                    "webrtc": {"main": "https://192.168.1.102/webrtc/main"}
                }
            }
        }
        response = client.post("/api/devices/cameras", json=camera_data)

        # Then: Camera created successfully
        assert response.status_code == 201
        data = response.json()["data"]
        # rtsp key doesn't exist in streams (not null)
        assert "rtsp" not in data["urls"]["streams"]
        assert data["urls"]["streams"]["webrtc"]["main"] == "https://192.168.1.102/webrtc/main"


class TestCameraUrlsSchemaValidation:
    """Phase 8.1: URL 형식 검증 tests (schema-level) - Simplified dict-based schema"""

    def test_camera_urls_accepts_rtsp_url(self):
        """Test: urls.streams.rtsp.main accepts RTSP URL format"""
        # When: Create CameraUrls with RTSP URL (dict-based)
        urls = CameraUrls(
            streams={
                "rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}
            }
        )

        # Then: Schema validates successfully
        assert urls.streams["rtsp"]["main"] == "rtsp://192.168.1.100:554/stream1"

    def test_camera_urls_accepts_https_url(self):
        """Test: urls.streams.webrtc.main accepts HTTPS URL format"""
        # When: Create CameraUrls with HTTPS URL (dict-based)
        urls = CameraUrls(
            streams={
                "webrtc": {"main": "https://192.168.1.100/webrtc/main"}
            }
        )

        # Then: Schema validates successfully
        assert urls.streams["webrtc"]["main"] == "https://192.168.1.100/webrtc/main"

    def test_camera_urls_accepts_http_homepage(self):
        """Test: urls.homepage.url accepts HTTP/HTTPS URL format"""
        # When: Create CameraUrls with HTTP homepage (dict-based)
        urls = CameraUrls(
            homepage={"url": "http://192.168.1.100"}
        )

        # Then: Schema validates successfully
        assert urls.homepage["url"] == "http://192.168.1.100"

    def test_camera_urls_accepts_https_homepage(self):
        """Test: urls.homepage.url accepts HTTPS URL format"""
        # When: Create CameraUrls with HTTPS homepage (dict-based)
        urls = CameraUrls(
            homepage={"url": "https://192.168.1.100"}
        )

        # Then: Schema validates successfully
        assert urls.homepage["url"] == "https://192.168.1.100"


class TestCameraUrlsApiValidation:
    """Phase 8.1: URL 형식 검증 API tests"""

    def test_api_accepts_valid_urls(self, client: TestClient, test_db):
        """Test: API accepts valid URL formats"""
        # When: POST camera with valid URLs
        camera_data = {
            "number_device": 8004,
            "group_device": 1,
            "name_device": "Valid URLs Camera",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.103",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "homepage": {"url": "http://192.168.1.103"},
                "streams": {
                    "rtsp": {"main": "rtsp://192.168.1.103:554/main", "sub": "rtsp://192.168.1.103:554/sub"},
                    "webrtc": {"main": "https://192.168.1.103/webrtc/main"}
                },
                "onvif": {
                    "device_service": "http://192.168.1.103/onvif/device_service",
                    "media_service": "http://192.168.1.103/onvif/media_service"
                }
            }
        }
        response = client.post("/api/devices/cameras", json=camera_data)

        # Then: Camera created successfully
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["urls"]["homepage"]["url"] == "http://192.168.1.103"
        assert data["urls"]["streams"]["rtsp"]["main"] == "rtsp://192.168.1.103:554/main"
        assert data["urls"]["streams"]["webrtc"]["main"] == "https://192.168.1.103/webrtc/main"
