"""
Test: Sensor schemas
"""
import pytest
from datetime import datetime


def test_sensor_create_schema_requires_all_fields():
    """
    Test: SensorCreate schema requires all fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import SensorCreate

    # Valid data
    data = {
        "number_device": 100,
        "group_device": 1,
        "name_device": "PIR Sensor 1",
        "type_device": "PIR",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "controller_id": 1
    }
    sensor = SensorCreate(**data)

    assert sensor.number_device == 100
    assert sensor.group_device == 1
    assert sensor.name_device == "PIR Sensor 1"
    assert sensor.type_device == "PIR"
    assert sensor.version == "1.0.0"
    assert sensor.status == "ACTIVATED"
    assert sensor.controller_id == 1


def test_sensor_create_schema_validates_missing_fields():
    """
    Test: SensorCreate schema validates missing required fields

    Expected to fail initially (Red phase).
    """
    from pydantic import ValidationError
    from app.schemas.device import SensorCreate

    # Missing required field
    with pytest.raises(ValidationError):
        SensorCreate(
            number_device=100,
            group_device=1,
            name_device="PIR Sensor 1",
            type_device="PIR",
            version="1.0.0",
            # status missing
            controller_id=1
        )


def test_sensor_response_schema_includes_all_fields():
    """
    Test: SensorResponse schema includes all fields including timestamps

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import SensorResponse

    data = {
        "id": 1,
        "number_device": 100,
        "group_device": 1,
        "name_device": "PIR Sensor 1",
        "type_device": "PIR",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    sensor = SensorResponse(**data)

    assert sensor.id == 1
    assert sensor.number_device == 100
    assert sensor.group_device == 1
    assert sensor.name_device == "PIR Sensor 1"
    assert sensor.type_device == "PIR"
    assert sensor.version == "1.0.0"
    assert sensor.status == "ACTIVATED"
    assert sensor.controller_id == 1
    assert sensor.created_at is not None
    assert sensor.updated_at is not None


def test_sensor_update_schema_all_fields_optional():
    """
    Test: SensorUpdate schema has all fields as optional

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import SensorUpdate

    # Empty update (all fields optional)
    sensor = SensorUpdate()
    assert sensor.number_device is None
    assert sensor.group_device is None
    assert sensor.name_device is None
    assert sensor.type_device is None
    assert sensor.version is None
    assert sensor.status is None
    assert sensor.controller_id is None

    # Partial update
    sensor = SensorUpdate(name_device="Updated Sensor", status="ERROR")
    assert sensor.name_device == "Updated Sensor"
    assert sensor.status == "ERROR"
    assert sensor.number_device is None


def test_sensor_schema_enum_serialization():
    """
    Test: Sensor schemas work with enum serialization

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import SensorCreate, SensorResponse

    # Create with string enum values
    create_data = {
        "number_device": 100,
        "group_device": 1,
        "name_device": "PIR Sensor 1",
        "type_device": "PIR",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "controller_id": 1
    }
    sensor_create = SensorCreate(**create_data)
    assert sensor_create.type_device == "PIR"
    assert sensor_create.status == "ACTIVATED"

    # Response includes timestamps
    response_data = {
        **create_data,
        "id": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    sensor_response = SensorResponse(**response_data)
    assert sensor_response.type_device == "PIR"
    assert sensor_response.status == "ACTIVATED"
