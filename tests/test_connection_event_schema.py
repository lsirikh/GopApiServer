"""
Test: Connection Event schemas
"""
import pytest
from datetime import datetime


def test_connection_event_create_schema_fields():
    """Test: ConnectionEventCreate schema has all required fields"""
    from app.schemas.event import ConnectionEventCreate

    event_data = {
        "group_event": "GROUP_C",
        "type_event": "Connection",
        "controller": 3,
        "sensor": 1,
        "type_device": "PIR",
        "sequence": 1
    }

    event_create = ConnectionEventCreate(**event_data)

    assert event_create.group_event == "GROUP_C"
    assert event_create.type_event == "Connection"
    assert event_create.controller == 3
    assert event_create.sensor == 1
    assert event_create.type_device == "PIR"
    assert event_create.sequence == 1


def test_connection_event_response_schema_fields():
    """Test: ConnectionEventResponse schema has all required fields"""
    from app.schemas.event import ConnectionEventResponse

    event_data = {
        "id": 1,
        "group_event": "GROUP_C",
        "type_event": "Connection",
        "controller": 3,
        "sensor": 1,
        "type_device": "PIR",
        "sequence": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_response = ConnectionEventResponse(**event_data)

    assert event_response.id == 1
    assert event_response.group_event == "GROUP_C"
    assert event_response.type_event == "Connection"
    assert event_response.type_device == "PIR"
    assert isinstance(event_response.created_at, datetime)
    assert isinstance(event_response.updated_at, datetime)


def test_connection_event_update_schema_optional_fields():
    """Test: ConnectionEventUpdate schema has all optional fields"""
    from app.schemas.event import ConnectionEventUpdate

    # Test with partial update
    event_update = ConnectionEventUpdate(
        type_device="Fence",
        sensor=2
    )

    assert event_update.type_device == "Fence"
    assert event_update.sensor == 2
    assert event_update.controller is None
    assert event_update.group_event is None


def test_connection_event_response_from_model(test_db):
    """Test: ConnectionEventResponse can be created from ConnectionEvent model"""
    from app.models.event import ConnectionEvent, EnumDeviceType
    from app.schemas.event import ConnectionEventResponse

    # Create connection event
    event = ConnectionEvent(
        group_event="GROUP_C",
        type_event="Connection",
        controller=3,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Create response from model using model_validate
    event_response = ConnectionEventResponse.model_validate(event)

    assert event_response.id == event.id
    assert event_response.type_device == "PIR"
    assert event_response.created_at is not None
    assert event_response.updated_at is not None


def test_connection_event_create_validation():
    """Test: ConnectionEventCreate schema validates required fields"""
    from app.schemas.event import ConnectionEventCreate
    from pydantic import ValidationError

    # Missing required field should raise ValidationError
    with pytest.raises(ValidationError):
        ConnectionEventCreate(
            group_event="GROUP_C",
            type_event="Connection"
            # Missing required fields: controller, sensor, type_device, sequence
        )
