"""
Test: Sensor model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_sensor_model_has_required_fields(test_db):
    """
    Test: Sensor model has all required fields

    Expected to fail initially (Red phase).
    """
    from app.models.device import Sensor

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('sensors')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'number_device' in columns
    assert 'group_device' in columns
    assert 'name_device' in columns
    assert 'type_device' in columns
    assert 'version' in columns
    assert 'status' in columns
    assert 'controller_id' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_sensor_model_timestamps_auto_set(test_db):
    """
    Test: Sensor model automatically sets timestamps

    Expected to fail initially (Red phase).
    """
    from app.models.device import Sensor, EnumDeviceType, EnumDeviceStatus, Controller

    # Create a Controller first (FK requirement)
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.1",
        ip_port=8080
    )
    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    # Create sensor
    sensor = Sensor(
        number_device=100,
        group_device=1,
        name_device="Test Sensor",
        type_device=EnumDeviceType.PIR,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        controller_id=controller.id
    )
    test_db.add(sensor)
    test_db.commit()
    test_db.refresh(sensor)

    # Check timestamps are set
    assert sensor.created_at is not None
    assert sensor.updated_at is not None
    assert isinstance(sensor.created_at, datetime)
    assert isinstance(sensor.updated_at, datetime)


def test_sensor_model_table_name(test_db):
    """
    Test: Sensor model has correct table name

    Expected to fail initially (Red phase).
    """
    from app.models.device import Sensor

    assert Sensor.__tablename__ == "sensors"


def test_sensor_model_foreign_key_to_controller(test_db):
    """
    Test: Sensor model has foreign key relationship to Controller

    Expected to fail initially (Red phase).
    """
    from app.models.device import Sensor, EnumDeviceType, EnumDeviceStatus, Controller

    # Create a Controller first
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.1",
        ip_port=8080
    )
    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    # Create sensor with FK to controller
    sensor = Sensor(
        number_device=100,
        group_device=1,
        name_device="Test Sensor",
        type_device=EnumDeviceType.PIR,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        controller_id=controller.id
    )
    test_db.add(sensor)
    test_db.commit()
    test_db.refresh(sensor)

    # Check FK works
    assert sensor.controller_id == controller.id

    # Check relationship (if defined)
    if hasattr(sensor, 'controller'):
        assert sensor.controller.id == controller.id
        assert sensor.controller.name_device == "Test Controller"


def test_sensor_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve Sensor

    Expected to fail initially (Red phase).
    """
    from app.models.device import Sensor, EnumDeviceType, EnumDeviceStatus, Controller

    # Create a Controller first
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.1",
        ip_port=8080
    )
    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    # Create sensor
    sensor = Sensor(
        number_device=100,
        group_device=1,
        name_device="PIR Sensor 1",
        type_device=EnumDeviceType.PIR,
        version="2.1.0",
        status=EnumDeviceStatus.ACTIVATED,
        controller_id=controller.id
    )
    test_db.add(sensor)
    test_db.commit()
    test_db.refresh(sensor)

    # Retrieve sensor
    retrieved = test_db.query(Sensor).filter(Sensor.id == sensor.id).first()

    assert retrieved is not None
    assert retrieved.number_device == 100
    assert retrieved.group_device == 1
    assert retrieved.name_device == "PIR Sensor 1"
    assert retrieved.type_device == EnumDeviceType.PIR
    assert retrieved.version == "2.1.0"
    assert retrieved.status == EnumDeviceStatus.ACTIVATED
    assert retrieved.controller_id == controller.id
