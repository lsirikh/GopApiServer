"""
Test: Camera model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_camera_model_has_required_fields(test_db):
    """
    Test: Camera model has all required fields including camera-specific fields

    Expected to fail initially (Red phase).
    """
    from app.models.device import Camera

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('cameras')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'number_device' in columns
    assert 'group_device' in columns
    assert 'name_device' in columns
    assert 'type_device' in columns
    assert 'version' in columns
    assert 'status' in columns
    assert 'ip_address' in columns
    assert 'ip_port' in columns
    assert 'user_name' in columns
    assert 'user_password' in columns
    assert 'rtsp_uri' in columns
    assert 'rtsp_port' in columns
    assert 'mode' in columns
    assert 'category' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_camera_model_timestamps_auto_set(test_db):
    """
    Test: Camera model automatically sets timestamps

    Expected to fail initially (Red phase).
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
        rtsp_uri="rtsp://192.168.1.100:554/stream",
        rtsp_port=554,
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

    Expected to fail initially (Red phase).
    """
    from app.models.device import Camera

    assert Camera.__tablename__ == "cameras"


def test_camera_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve Camera

    Expected to fail initially (Red phase).
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
        rtsp_uri="rtsp://192.168.1.100:554/stream1",
        rtsp_port=554,
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
    assert retrieved.rtsp_uri == "rtsp://192.168.1.100:554/stream1"
    assert retrieved.rtsp_port == 554
    assert retrieved.mode == EnumCameraMode.ONVIF
    assert retrieved.category == EnumCameraType.PTZ


def test_camera_enums_exist(test_db):
    """
    Test: Camera-specific enums exist and have correct values

    Expected to fail initially (Red phase).
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
    assert EnumCameraType.FISHEYES.value == "FISHEYES"
    assert EnumCameraType.THERMAL.value == "THERMAL"
