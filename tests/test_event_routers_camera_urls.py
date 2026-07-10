"""
Phase 5: Event Routers Camera URLs Tests
PRD: PRD_Camera_Urls_JsonB.md v1.0

Test that Event routers return device.urls for Camera type and do NOT return device.rtsp_uri/rtsp_port.
"""
import pytest
from fastapi.testclient import TestClient

from app.models.device import Camera
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType


class TestDetectionsRouterCameraUrls:
    """Phase 5.1: detections.py - _build_device_nested_response tests"""

    def test_get_detections_returns_device_urls_for_camera(self, client: TestClient, test_db):
        """Test: GET /api/events/detections returns device.urls for Camera type"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5001,
            group_device=1,
            name_device="Detection Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "homepage": {"url": "http://192.168.1.200"},
                "streams": {"rtsp": {"main": "rtsp://192.168.1.200:554/main"}}
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A detection event exists for this camera
        detection_data = {
            "type_event": "AI_DETECT",
            "device_id": camera.id,
            "result": "AI_DETECT"
        }
        detection_resp = client.post("/api/events/detections", json=detection_data)
        assert detection_resp.status_code == 201

        # When: GET /api/events/detections
        response = client.get("/api/events/detections")

        # Then: Response contains device.urls for Camera type
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "urls" in device
        assert device["urls"]["homepage"]["url"] == "http://192.168.1.200"

    def test_get_detections_does_not_return_device_rtsp_uri(self, client: TestClient, test_db):
        """Test: GET /api/events/detections does NOT return device.rtsp_uri"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5002,
            group_device=1,
            name_device="Detection Test Camera 2",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.201",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.201:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A detection event exists for this camera
        detection_data = {
            "type_event": "AI_DETECT",
            "device_id": camera.id,
            "result": "AI_DETECT"
        }
        detection_resp = client.post("/api/events/detections", json=detection_data)
        assert detection_resp.status_code == 201

        # When: GET /api/events/detections
        response = client.get("/api/events/detections")

        # Then: Response does NOT contain device.rtsp_uri
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "rtsp_uri" not in device

    def test_get_detections_does_not_return_device_rtsp_port(self, client: TestClient, test_db):
        """Test: GET /api/events/detections does NOT return device.rtsp_port"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5003,
            group_device=1,
            name_device="Detection Test Camera 3",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.202",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.202:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A detection event exists for this camera
        detection_data = {
            "type_event": "AI_DETECT",
            "device_id": camera.id,
            "result": "AI_DETECT"
        }
        detection_resp = client.post("/api/events/detections", json=detection_data)
        assert detection_resp.status_code == 201

        # When: GET /api/events/detections
        response = client.get("/api/events/detections")

        # Then: Response does NOT contain device.rtsp_port
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "rtsp_port" not in device


class TestConnectionsRouterCameraUrls:
    """Phase 5.2: connections.py - _build_device_nested_response tests"""

    def test_get_connections_returns_device_urls_for_camera(self, client: TestClient, test_db):
        """Test: GET /api/events/connections returns device.urls for Camera type"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5101,
            group_device=1,
            name_device="Connection Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.210",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "homepage": {"url": "http://192.168.1.210"},
                "streams": {"rtsp": {"main": "rtsp://192.168.1.210:554/main"}}
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A connection event exists for this camera
        connection_data = {
            "type_event": "CONNECTED",
            "device_id": camera.id,
            "result": "CAMERA_ON"
        }
        connection_resp = client.post("/api/events/connections", json=connection_data)
        assert connection_resp.status_code == 201

        # When: GET /api/events/connections
        response = client.get("/api/events/connections")

        # Then: Response contains device.urls for Camera type
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "urls" in device
        assert device["urls"]["homepage"]["url"] == "http://192.168.1.210"

    def test_get_connections_does_not_return_device_rtsp_uri(self, client: TestClient, test_db):
        """Test: GET /api/events/connections does NOT return device.rtsp_uri"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5102,
            group_device=1,
            name_device="Connection Test Camera 2",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.211",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.211:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A connection event exists for this camera
        connection_data = {
            "type_event": "CONNECTED",
            "device_id": camera.id,
            "result": "CAMERA_ON"
        }
        connection_resp = client.post("/api/events/connections", json=connection_data)
        assert connection_resp.status_code == 201

        # When: GET /api/events/connections
        response = client.get("/api/events/connections")

        # Then: Response does NOT contain device.rtsp_uri
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "rtsp_uri" not in device

    def test_get_connections_does_not_return_device_rtsp_port(self, client: TestClient, test_db):
        """Test: GET /api/events/connections does NOT return device.rtsp_port"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5103,
            group_device=1,
            name_device="Connection Test Camera 3",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.212",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.212:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A connection event exists for this camera
        connection_data = {
            "type_event": "CONNECTED",
            "device_id": camera.id,
            "result": "CAMERA_ON"
        }
        connection_resp = client.post("/api/events/connections", json=connection_data)
        assert connection_resp.status_code == 201

        # When: GET /api/events/connections
        response = client.get("/api/events/connections")

        # Then: Response does NOT contain device.rtsp_port
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "rtsp_port" not in device


class TestMalfunctionsRouterCameraUrls:
    """Phase 5.3: malfunctions.py - _build_device_nested_response tests"""

    def test_get_malfunctions_returns_device_urls_for_camera(self, client: TestClient, test_db):
        """Test: GET /api/events/malfunctions returns device.urls for Camera type"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5201,
            group_device=1,
            name_device="Malfunction Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.220",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "homepage": {"url": "http://192.168.1.220"},
                "streams": {"rtsp": {"main": "rtsp://192.168.1.220:554/main"}}
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A malfunction event exists for this camera
        # MalfunctionEventCreate requires: type_event, device_id, reason, first_start, first_end, second_start, second_end
        malfunction_data = {
            "type_event": "Fault",
            "device_id": camera.id,
            "reason": "FAULT_ETC",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0
        }
        malfunction_resp = client.post("/api/events/malfunctions", json=malfunction_data)
        assert malfunction_resp.status_code == 201

        # When: GET /api/events/malfunctions
        response = client.get("/api/events/malfunctions")

        # Then: Response contains device.urls for Camera type
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "urls" in device
        assert device["urls"]["homepage"]["url"] == "http://192.168.1.220"

    def test_get_malfunctions_does_not_return_device_rtsp_uri(self, client: TestClient, test_db):
        """Test: GET /api/events/malfunctions does NOT return device.rtsp_uri"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5202,
            group_device=1,
            name_device="Malfunction Test Camera 2",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.221",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.221:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A malfunction event exists for this camera
        # MalfunctionEventCreate requires: type_event, device_id, reason, first_start, first_end, second_start, second_end
        malfunction_data = {
            "type_event": "Fault",
            "device_id": camera.id,
            "reason": "FAULT_ETC",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0
        }
        malfunction_resp = client.post("/api/events/malfunctions", json=malfunction_data)
        assert malfunction_resp.status_code == 201

        # When: GET /api/events/malfunctions
        response = client.get("/api/events/malfunctions")

        # Then: Response does NOT contain device.rtsp_uri
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "rtsp_uri" not in device

    def test_get_malfunctions_does_not_return_device_rtsp_port(self, client: TestClient, test_db):
        """Test: GET /api/events/malfunctions does NOT return device.rtsp_port"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5203,
            group_device=1,
            name_device="Malfunction Test Camera 3",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.222",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.222:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A malfunction event exists for this camera
        # MalfunctionEventCreate requires: type_event, device_id, reason, first_start, first_end, second_start, second_end
        malfunction_data = {
            "type_event": "Fault",
            "device_id": camera.id,
            "reason": "FAULT_ETC",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0
        }
        malfunction_resp = client.post("/api/events/malfunctions", json=malfunction_data)
        assert malfunction_resp.status_code == 201

        # When: GET /api/events/malfunctions
        response = client.get("/api/events/malfunctions")

        # Then: Response does NOT contain device.rtsp_port
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        device = data[0]["device"]
        assert device is not None
        assert "rtsp_port" not in device


class TestActionsRouterCameraUrls:
    """Phase 5.4: actions.py - _build_device_nested_response tests"""

    def test_get_actions_returns_device_urls_for_camera(self, client: TestClient, test_db):
        """Test: GET /api/events/actions returns device.urls for Camera type"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5301,
            group_device=1,
            name_device="Action Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.230",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "homepage": {"url": "http://192.168.1.230"},
                "streams": {"rtsp": {"main": "rtsp://192.168.1.230:554/main"}}
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A detection event exists for this camera
        detection_data = {
            "type_event": "AI_DETECT",
            "device_id": camera.id,
            "result": "AI_DETECT"
        }
        detection_resp = client.post("/api/events/detections", json=detection_data)
        assert detection_resp.status_code == 201
        detection_id = detection_resp.json()["data"]["id"]

        # And: An action event exists for this detection
        action_data = {
            "type_event": "Action",
            "content": "Test action taken",
            "user": "operator1",
            "from_event_id": detection_id
        }
        action_resp = client.post("/api/events/actions", json=action_data)
        assert action_resp.status_code == 201

        # When: GET /api/events/actions
        response = client.get("/api/events/actions")

        # Then: Response contains device.urls for Camera type in from_event.device
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        from_event = data[0]["from_event"]
        assert from_event is not None
        device = from_event["device"]
        assert device is not None
        assert "urls" in device
        assert device["urls"]["homepage"]["url"] == "http://192.168.1.230"

    def test_get_actions_does_not_return_device_rtsp_uri(self, client: TestClient, test_db):
        """Test: GET /api/events/actions does NOT return device.rtsp_uri"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5302,
            group_device=1,
            name_device="Action Test Camera 2",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.231",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.231:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A detection event exists for this camera
        detection_data = {
            "type_event": "AI_DETECT",
            "device_id": camera.id,
            "result": "AI_DETECT"
        }
        detection_resp = client.post("/api/events/detections", json=detection_data)
        assert detection_resp.status_code == 201
        detection_id = detection_resp.json()["data"]["id"]

        # And: An action event exists for this detection
        action_data = {
            "type_event": "Action",
            "content": "Test action taken",
            "user": "operator1",
            "from_event_id": detection_id
        }
        action_resp = client.post("/api/events/actions", json=action_data)
        assert action_resp.status_code == 201

        # When: GET /api/events/actions
        response = client.get("/api/events/actions")

        # Then: Response does NOT contain device.rtsp_uri in from_event.device
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        from_event = data[0]["from_event"]
        assert from_event is not None
        device = from_event["device"]
        assert device is not None
        assert "rtsp_uri" not in device

    def test_get_actions_does_not_return_device_rtsp_port(self, client: TestClient, test_db):
        """Test: GET /api/events/actions does NOT return device.rtsp_port"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=5303,
            group_device=1,
            name_device="Action Test Camera 3",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.232",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.232:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A detection event exists for this camera
        detection_data = {
            "type_event": "AI_DETECT",
            "device_id": camera.id,
            "result": "AI_DETECT"
        }
        detection_resp = client.post("/api/events/detections", json=detection_data)
        assert detection_resp.status_code == 201
        detection_id = detection_resp.json()["data"]["id"]

        # And: An action event exists for this detection
        action_data = {
            "type_event": "Action",
            "content": "Test action taken",
            "user": "operator1",
            "from_event_id": detection_id
        }
        action_resp = client.post("/api/events/actions", json=action_data)
        assert action_resp.status_code == 201

        # When: GET /api/events/actions
        response = client.get("/api/events/actions")

        # Then: Response does NOT contain device.rtsp_port in from_event.device
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) > 0
        from_event = data[0]["from_event"]
        assert from_event is not None
        device = from_event["device"]
        assert device is not None
        assert "rtsp_port" not in device
