"""
Phase 6: DeviceGroup Router Camera URLs Tests
PRD: PRD_Camera_Urls_JsonB.md v1.0

Test that device_groups router returns cameras[].urls and does NOT return cameras[].rtsp_uri/rtsp_port.
"""
import pytest
from fastapi.testclient import TestClient

from app.models.device import Camera
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory


class TestDeviceGroupsRouterCameraUrls:
    """Phase 6.1: device_groups.py - Camera 조회 tests"""

    def test_get_device_group_returns_cameras_urls(self, client: TestClient, test_db):
        """Test: GET /api/devices/groups/{id} returns cameras[].urls"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=6001,
            group_device=1,
            name_device="DeviceGroup Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.250",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "homepage": {"url": "http://192.168.1.250"},
                "streams": {"rtsp": {"main": "rtsp://192.168.1.250:554/main"}}
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A device group exists with the camera assigned
        group = DeviceGroup(name="Test Group 1", description="Test description")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=camera.id,
            category_device=EnumDeviceCategory.CAMERA,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # When: GET /api/devices/groups/{id}
        response = client.get(f"/api/devices/groups/{group.id}")

        # Then: Response contains cameras[].urls
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["devices"]) > 0

        # Find the camera in devices
        camera_device = None
        for device in data["devices"]:
            if device["id"] == camera.id:
                camera_device = device
                break

        assert camera_device is not None
        assert "urls" in camera_device
        assert camera_device["urls"]["homepage"]["url"] == "http://192.168.1.250"

    def test_get_device_group_does_not_return_cameras_rtsp_uri(self, client: TestClient, test_db):
        """Test: GET /api/devices/groups/{id} does NOT return cameras[].rtsp_uri"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=6002,
            group_device=1,
            name_device="DeviceGroup Test Camera 2",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.251",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.251:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A device group exists with the camera assigned
        group = DeviceGroup(name="Test Group 2", description="Test description")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=camera.id,
            category_device=EnumDeviceCategory.CAMERA,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # When: GET /api/devices/groups/{id}
        response = client.get(f"/api/devices/groups/{group.id}")

        # Then: Response does NOT contain cameras[].rtsp_uri
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["devices"]) > 0

        # Find the camera in devices
        camera_device = None
        for device in data["devices"]:
            if device["id"] == camera.id:
                camera_device = device
                break

        assert camera_device is not None
        assert "rtsp_uri" not in camera_device

    def test_get_device_group_does_not_return_cameras_rtsp_port(self, client: TestClient, test_db):
        """Test: GET /api/devices/groups/{id} does NOT return cameras[].rtsp_port"""
        # Given: A camera with urls exists
        camera = Camera(
            number_device=6003,
            group_device=1,
            name_device="DeviceGroup Test Camera 3",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.252",
            ip_port=8080,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.252:554/main"}}}
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        # And: A device group exists with the camera assigned
        group = DeviceGroup(name="Test Group 3", description="Test description")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=camera.id,
            category_device=EnumDeviceCategory.CAMERA,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # When: GET /api/devices/groups/{id}
        response = client.get(f"/api/devices/groups/{group.id}")

        # Then: Response does NOT contain cameras[].rtsp_port
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["devices"]) > 0

        # Find the camera in devices
        camera_device = None
        for device in data["devices"]:
            if device["id"] == camera.id:
                camera_device = device
                break

        assert camera_device is not None
        assert "rtsp_port" not in camera_device
