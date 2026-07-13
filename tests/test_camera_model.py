"""
Test: Camera model
PRD: PRD_Camera_Urls_JsonB.md v1.0 - Updated to use urls JSONB instead of rtsp_uri/rtsp_port
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_camera_model_has_required_fields(test_db):
    """
    Test: Camera model has all required fields including camera-specific fields

    Note: Camera inherits from Device (Joined Table Inheritance).
    Common fields are in 'devices' table, camera-specific fields in 'cameras' table.

    PRD: PRD_Camera_Urls_JsonB.md v1.0
    - rtsp_uri, rtsp_port 제거
    - urls JSONB 필드 추가
    """
    from app.models.device import Camera

    # Get table columns for cameras table (camera-specific fields)
    inspector = inspect(test_db.bind)
    camera_columns = [col['name'] for col in inspector.get_columns('cameras')]

    # Camera-specific fields in cameras table
    assert 'id' in camera_columns
    assert 'ip_address' in camera_columns
    assert 'ip_port' in camera_columns
    assert 'user_name' in camera_columns
    assert 'user_password' in camera_columns
    # PRD_Camera_Urls_JsonB.md: rtsp_uri/rtsp_port removed, urls added
    assert 'urls' in camera_columns
    assert 'rtsp_uri' not in camera_columns
    assert 'rtsp_port' not in camera_columns
    assert 'mode' in camera_columns
    assert 'category' in camera_columns

    # Common fields are in devices table (from Device base class)
    device_columns = [col['name'] for col in inspector.get_columns('devices')]
    assert 'id' in device_columns
    assert 'number_device' in device_columns
    assert 'group_device' in device_columns
    assert 'name_device' in device_columns
    assert 'type_device' in device_columns
    assert 'version' in device_columns
    assert 'status' in device_columns
    assert 'created_at' in device_columns
    assert 'updated_at' in device_columns


def test_camera_model_timestamps_auto_set(test_db):
    """
    Test: Camera model automatically sets timestamps

    PRD: PRD_Camera_Urls_JsonB.md v1.0 - uses urls JSONB
    """
    from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

    # Create camera
    camera = Camera(
        number_device=1000,
        group_device=1,
        name_device="Test Camera",
        type_device=EnumDeviceType.IpCamera,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=80,
        user_name="admin",
        user_password="password123",
        urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream"}}},
        mode=EnumCameraMode.ONVIF,
        category=EnumCameraType.PTZ
    )
    test_db.add(camera)
    test_db.commit()
    test_db.refresh(camera)

    # Check timestamps are set
    assert camera.created_at is not None
    assert camera.updated_at is not None
    assert isinstance(camera.created_at, datetime)
    assert isinstance(camera.updated_at, datetime)


def test_camera_model_table_name(test_db):
    """
    Test: Camera model has correct table name
    """
    from app.models.device import Camera

    assert Camera.__tablename__ == "cameras"


def test_camera_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve Camera

    PRD: PRD_Camera_Urls_JsonB.md v1.0 - uses urls JSONB
    """
    from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

    # Create camera
    camera = Camera(
        number_device=1000,
        group_device=1,
        name_device="PTZ Camera 1",
        type_device=EnumDeviceType.IpCamera,
        version="2.1.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=80,
        user_name="admin",
        user_password="securepass",
        urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}}},
        mode=EnumCameraMode.ONVIF,
        category=EnumCameraType.PTZ
    )
    test_db.add(camera)
    test_db.commit()
    test_db.refresh(camera)

    # Retrieve camera
    retrieved = test_db.query(Camera).filter(Camera.id == camera.id).first()

    assert retrieved is not None
    assert retrieved.number_device == 1000
    assert retrieved.group_device == 1
    assert retrieved.name_device == "PTZ Camera 1"
    assert retrieved.type_device == EnumDeviceType.IpCamera
    assert retrieved.version == "2.1.0"
    assert retrieved.status == EnumDeviceStatus.ACTIVATED
    assert retrieved.ip_address == "192.168.1.100"
    assert retrieved.ip_port == 80
    assert retrieved.user_name == "admin"
    assert retrieved.user_password == "securepass"
    assert retrieved.urls["streams"]["rtsp"]["main"] == "rtsp://192.168.1.100:554/stream1"
    assert retrieved.mode == EnumCameraMode.ONVIF
    assert retrieved.category == EnumCameraType.PTZ


def test_camera_enums_exist(test_db):
    """
    Test: Camera-specific enums exist and have correct values
    """
    from app.models.device import EnumCameraMode, EnumCameraType

    # Test EnumCameraMode
    assert EnumCameraMode.NONE.value == "NONE"
    assert EnumCameraMode.ONVIF.value == "ONVIF"
    assert EnumCameraMode.EMSTONE_API.value == "EMSTONE_API"
    assert EnumCameraMode.INNODEP_API.value == "INNODEP_API"
    assert EnumCameraMode.ETC.value == "ETC"

    # Test EnumCameraType
    assert EnumCameraType.NONE.value == "NONE"
    assert EnumCameraType.FIXED.value == "FIXED"
    assert EnumCameraType.PTZ.value == "PTZ"
