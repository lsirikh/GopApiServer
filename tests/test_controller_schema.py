"""
Test: Controller schemas validation
"""
import pytest
from pydantic import ValidationError


def test_controller_create_schema_requires_all_fields():
    """
    Test: ControllerCreate schema requires all mandatory fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import ControllerCreate
    from app.models.device import EnumDeviceType, EnumDeviceStatus

    # Valid data with all required fields
    valid_data = {
        "number_device": 100,
        "group_device": 5,
        "name_device": "Main Gate Controller",
        "type_device": "Controller",
        "version": "2.1.0",
        "status": "ACTIVATED",
        "ip_address": "10.0.0.50",
        "ip_port": 9000
    }

    # Should create successfully with all fields
    schema = ControllerCreate(**valid_data)
    assert schema.number_device == 100
    assert schema.group_device == 5
    assert schema.name_device == "Main Gate Controller"
    assert schema.type_device == "Controller"
    assert schema.version == "2.1.0"
    assert schema.status == "ACTIVATED"
    assert schema.ip_address == "10.0.0.50"
    assert schema.ip_port == 9000

    # Should fail without required fields
    with pytest.raises(ValidationError):
        ControllerCreate(number_device=100)


def test_controller_response_schema_includes_all_fields():
    """
    Test: ControllerResponse schema includes all fields including id and timestamps

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import ControllerResponse
    from datetime import datetime

    data = {
        "id": 1,
        "number_device": 100,
        "group_device": 5,
        "name_device": "Main Gate Controller",
        "type_device": "Controller",
        "version": "2.1.0",
        "status": "ACTIVATED",
        "ip_address": "10.0.0.50",
        "ip_port": 9000,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    schema = ControllerResponse(**data)
    assert schema.id == 1
    assert schema.number_device == 100
    assert schema.group_device == 5
    assert schema.name_device == "Main Gate Controller"
    assert schema.type_device == "Controller"
    assert schema.version == "2.1.0"
    assert schema.status == "ACTIVATED"
    assert schema.ip_address == "10.0.0.50"
    assert schema.ip_port == 9000
    assert schema.created_at is not None
    assert schema.updated_at is not None


def test_controller_update_schema_all_fields_optional():
    """
    Test: ControllerUpdate schema has all fields as optional (for PATCH)

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import ControllerUpdate

    # Should accept empty update
    schema = ControllerUpdate()
    assert schema is not None

    # Should accept partial update (only name)
    schema = ControllerUpdate(name_device="Updated Name")
    assert schema.name_device == "Updated Name"

    # Should accept partial update (only status)
    schema = ControllerUpdate(status="ERROR")
    assert schema.status == "ERROR"

    # Should accept multiple field update
    schema = ControllerUpdate(
        name_device="New Name",
        ip_address="192.168.1.100",
        status="DEACTIVATED"
    )
    assert schema.name_device == "New Name"
    assert schema.ip_address == "192.168.1.100"
    assert schema.status == "DEACTIVATED"


def test_controller_schema_enum_serialization():
    """
    Test: Enum fields serialize correctly as strings

    Expected to fail initially (Red phase).
    """
    from app.schemas.device import ControllerCreate

    data = {
        "number_device": 100,
        "group_device": 5,
        "name_device": "Test Controller",
        "type_device": "Controller",  # String value
        "version": "1.0.0",
        "status": "ACTIVATED",  # String value
        "ip_address": "10.0.0.1",
        "ip_port": 8080
    }

    schema = ControllerCreate(**data)

    # Should serialize to dict with string enum values
    schema_dict = schema.model_dump()
    assert isinstance(schema_dict["type_device"], str)
    assert isinstance(schema_dict["status"], str)
    assert schema_dict["type_device"] == "Controller"
    assert schema_dict["status"] == "ACTIVATED"
