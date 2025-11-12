"""
Test: Camera schemas
"""
import pytest
from datetime import datetime


def test_camera_create_schema_fields():
    """
    Test: CameraCreate schema has all required fields including camera-specific fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import CameraCreate

    camera_data = {
        "number_device": 2000,
        "group_device": 1,
        "name_device": "PTZ Camera 1",
        "type_device": "IpCamera",
        "version": "2.1.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.100",
        "ip_port": 80,
        "user_name": "admin",
        "user_password": "password123",
        "rtsp_uri": "rtsp://192.168.1.100:554/stream",
        "rtsp_port": 554,
        "mode": "ONVIF",
        "category": "PTZ"
    }

    camera_create = CameraCreate(**camera_data)

    assert camera_create.number_device == 2000
    assert camera_create.group_device == 1
    assert camera_create.name_device == "PTZ Camera 1"
    assert camera_create.type_device == "IpCamera"
    assert camera_create.version == "2.1.0"
    assert camera_create.status == "ACTIVATED"
    assert camera_create.ip_address == "192.168.1.100"
    assert camera_create.ip_port == 80
    assert camera_create.user_name == "admin"
    assert camera_create.user_password == "password123"
    assert camera_create.rtsp_uri == "rtsp://192.168.1.100:554/stream"
    assert camera_create.rtsp_port == 554
    assert camera_create.mode == "ONVIF"
    assert camera_create.category == "PTZ"


def test_camera_response_schema_fields():
    """
    Test: CameraResponse schema has all required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import CameraResponse

    camera_data = {
        "id": 1,
        "number_device": 2000,
        "group_device": 1,
        "name_device": "PTZ Camera 1",
        "type_device": "IpCamera",
        "version": "2.1.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.100",
        "ip_port": 80,
        "user_name": "admin",
        "user_password": "password123",
        "rtsp_uri": "rtsp://192.168.1.100:554/stream",
        "rtsp_port": 554,
        "mode": "ONVIF",
        "category": "PTZ",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    camera_response = CameraResponse(**camera_data)

    assert camera_response.id == 1
    assert camera_response.number_device == 2000
    assert camera_response.group_device == 1
    assert camera_response.name_device == "PTZ Camera 1"
    assert camera_response.type_device == "IpCamera"
    assert camera_response.version == "2.1.0"
    assert camera_response.status == "ACTIVATED"
    assert camera_response.ip_address == "192.168.1.100"
    assert camera_response.ip_port == 80
    assert camera_response.user_name == "admin"
    assert camera_response.user_password == "password123"
    assert camera_response.rtsp_uri == "rtsp://192.168.1.100:554/stream"
    assert camera_response.rtsp_port == 554
    assert camera_response.mode == "ONVIF"
    assert camera_response.category == "PTZ"
    assert isinstance(camera_response.created_at, datetime)
    assert isinstance(camera_response.updated_at, datetime)


def test_camera_update_schema_optional_fields():
    """
    Test: CameraUpdate schema has all optional fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import CameraUpdate

    # Test with partial update
    camera_update = CameraUpdate(
        name_device="Updated Camera",
        status="ERROR",
        mode="EMSTONE_API"
    )

    assert camera_update.name_device == "Updated Camera"
    assert camera_update.status == "ERROR"
    assert camera_update.mode == "EMSTONE_API"
    assert camera_update.number_device is None
    assert camera_update.ip_address is None


def test_camera_response_from_model(test_db):
    """
    Test: CameraResponse can be created from Camera model

    Expected to fail initially (Red phase).
    """
    from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType
    from app.schemas.device import CameraResponse

    # Create camera
    camera = Camera(
        number_device=2000,
        group_device=1,
        name_device="Test Camera",
        type_device=EnumDeviceType.IpCamera,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=80,
        user_name="admin",
        user_password="password123",
        rtsp_uri="rtsp://192.168.1.100:554/stream",
        rtsp_port=554,
        mode=EnumCameraMode.ONVIF,
        category=EnumCameraType.PTZ
    )
    test_db.add(camera)
    test_db.commit()
    test_db.refresh(camera)

    # Create response from model
    camera_response = CameraResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device.value,
        version=camera.version,
        status=camera.status.value,
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        user_name=camera.user_name,
        user_password=camera.user_password,
        rtsp_uri=camera.rtsp_uri,
        rtsp_port=camera.rtsp_port,
        mode=camera.mode.value,
        category=camera.category.value,
        created_at=camera.created_at,
        updated_at=camera.updated_at
    )

    assert camera_response.id == camera.id
    assert camera_response.number_device == camera.number_device
    assert camera_response.mode == "ONVIF"
    assert camera_response.category == "PTZ"


def test_camera_create_validation():
    """
    Test: CameraCreate schema validates required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import CameraCreate
    from pydantic import ValidationError

    # Missing required field should raise ValidationError
    with pytest.raises(ValidationError):
        CameraCreate(
            number_device=2000,
            group_device=1,
            name_device="Test Camera"
            # Missing many required fields
        )
