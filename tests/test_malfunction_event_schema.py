"""
Test: Malfunction Event schemas
"""
import pytest
from datetime import datetime


def test_malfunction_event_create_schema_fields():
    """Test: MalfunctionEventCreate schema has all required fields"""
    from app.schemas.event import MalfunctionEventCreate

    event_data = {
        "group_event": "GROUP_B",
        "type_event": "Fault",
        "controller": 2,
        "sensor": 1,
        "type_device": "PIR",
        "sequence": 1,
        "action_reported": "False",
        "reason": "FAULT_CONTROLLER",
        "first_start": 100,
        "first_end": 200,
        "second_start": 300,
        "second_end": 400
    }

    event_create = MalfunctionEventCreate(**event_data)

    assert event_create.group_event == "GROUP_B"
    assert event_create.type_event == "Fault"
    assert event_create.controller == 2
    assert event_create.sensor == 1
    assert event_create.type_device == "PIR"
    assert event_create.sequence == 1
    assert event_create.action_reported == "False"
    assert event_create.reason == "FAULT_CONTROLLER"
    assert event_create.first_start == 100
    assert event_create.first_end == 200
    assert event_create.second_start == 300
    assert event_create.second_end == 400


def test_malfunction_event_response_schema_fields():
    """Test: MalfunctionEventResponse schema has all required fields"""
    from app.schemas.event import MalfunctionEventResponse

    event_data = {
        "id": 1,
        "group_event": "GROUP_B",
        "type_event": "Fault",
        "controller": 2,
        "sensor": 1,
        "type_device": "PIR",
        "sequence": 1,
        "action_reported": "False",
        "reason": "FAULT_FENCE",
        "first_start": 100,
        "first_end": 200,
        "second_start": 300,
        "second_end": 400,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_response = MalfunctionEventResponse(**event_data)

    assert event_response.id == 1
    assert event_response.group_event == "GROUP_B"
    assert event_response.type_event == "Fault"
    assert event_response.action_reported == "False"
    assert event_response.reason == "FAULT_FENCE"
    assert isinstance(event_response.created_at, datetime)
    assert isinstance(event_response.updated_at, datetime)


def test_malfunction_event_update_schema_optional_fields():
    """Test: MalfunctionEventUpdate schema has all optional fields"""
    from app.schemas.event import MalfunctionEventUpdate

    # Test with partial update
    event_update = MalfunctionEventUpdate(
        action_reported="True",
        reason="FAULT_ETC",
        first_end=250
    )

    assert event_update.action_reported == "True"
    assert event_update.reason == "FAULT_ETC"
    assert event_update.first_end == 250
    assert event_update.controller is None
    assert event_update.sensor is None


def test_malfunction_event_response_from_model(test_db):
    """Test: MalfunctionEventResponse can be created from MalfunctionEvent model"""
    from app.models.event import MalfunctionEvent, EnumTrueFalse, EnumFaultType, EnumDeviceType
    from app.schemas.event import MalfunctionEventResponse

    # Create malfunction event
    event = MalfunctionEvent(
        group_event="GROUP_B",
        type_event="Fault",
        controller=2,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        action_reported=EnumTrueFalse.False_,
        reason=EnumFaultType.FAULT_CONTROLLER,
        first_start=100,
        first_end=200,
        second_start=300,
        second_end=400
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Create response from model using model_validate
    event_response = MalfunctionEventResponse.model_validate(event)

    assert event_response.id == event.id
    assert event_response.action_reported == "False"
    assert event_response.reason == "FAULT_CONTROLLER"
    assert event_response.created_at is not None
    assert event_response.updated_at is not None


def test_malfunction_event_create_validation():
    """Test: MalfunctionEventCreate schema validates required fields"""
    from app.schemas.event import MalfunctionEventCreate
    from pydantic import ValidationError

    # Missing required field should raise ValidationError
    with pytest.raises(ValidationError):
        MalfunctionEventCreate(
            group_event="GROUP_B",
            type_event="Fault"
            # Missing required fields: controller, sensor, type_device, sequence, action_reported, reason, etc.
        )
