"""
Test: Malfunction Event schemas
"""
import pytest
from datetime import datetime


def test_malfunction_event_create_schema_fields():
    """
    Test: MalfunctionEventCreate schema has all required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import MalfunctionEventCreate

    event_data = {
        "message_type": 2,
        "device_id": 200,
        "group_event": "GROUP_B",
        "status": "True",
        "reason": "FAULT_CONTROLLER",
        "first_start": 100,
        "first_end": 200,
        "second_start": 300,
        "second_end": 400,
        "datetime": datetime.utcnow()
    }

    event_create = MalfunctionEventCreate(**event_data)

    assert event_create.message_type == 2
    assert event_create.device_id == 200
    assert event_create.group_event == "GROUP_B"
    assert event_create.status == "True"
    assert event_create.reason == "FAULT_CONTROLLER"
    assert event_create.first_start == 100
    assert event_create.first_end == 200
    assert event_create.second_start == 300
    assert event_create.second_end == 400
    assert isinstance(event_create.datetime, datetime)


def test_malfunction_event_response_schema_fields():
    """
    Test: MalfunctionEventResponse schema has all required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import MalfunctionEventResponse

    event_data = {
        "id": 1,
        "message_type": 2,
        "device_id": 200,
        "group_event": "GROUP_B",
        "status": "True",
        "reason": "FAULT_FENCE",
        "first_start": 100,
        "first_end": 200,
        "second_start": 300,
        "second_end": 400,
        "datetime": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_response = MalfunctionEventResponse(**event_data)

    assert event_response.id == 1
    assert event_response.message_type == 2
    assert event_response.device_id == 200
    assert event_response.group_event == "GROUP_B"
    assert event_response.status == "True"
    assert event_response.reason == "FAULT_FENCE"
    assert event_response.first_start == 100
    assert event_response.first_end == 200
    assert event_response.second_start == 300
    assert event_response.second_end == 400
    assert isinstance(event_response.datetime, datetime)
    assert isinstance(event_response.created_at, datetime)
    assert isinstance(event_response.updated_at, datetime)


def test_malfunction_event_update_schema_optional_fields():
    """
    Test: MalfunctionEventUpdate schema has all optional fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import MalfunctionEventUpdate

    # Test with partial update
    event_update = MalfunctionEventUpdate(
        status="False",
        reason="FAULT_ETC",
        first_end=250
    )

    assert event_update.status == "False"
    assert event_update.reason == "FAULT_ETC"
    assert event_update.first_end == 250
    assert event_update.message_type is None
    assert event_update.device_id is None


def test_malfunction_event_response_from_model(test_db):
    """
    Test: MalfunctionEventResponse can be created from MalfunctionEvent model

    Expected to fail initially (Red phase).
    """
    from app.models.event import MalfunctionEvent, EnumTrueFalse, EnumFaultType
    from app.schemas.event import MalfunctionEventResponse

    event_datetime = datetime.utcnow()

    # Create malfunction event
    event = MalfunctionEvent(
        message_type=2,
        device_id=200,
        group_event="GROUP_B",
        status=EnumTrueFalse.TRUE,
        reason=EnumFaultType.FAULT_CONTROLLER,
        first_start=100,
        first_end=200,
        second_start=300,
        second_end=400,
        datetime=event_datetime
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Create response from model
    event_response = MalfunctionEventResponse(
        id=event.id,
        message_type=event.message_type,
        device_id=event.device_id,
        group_event=event.group_event,
        status=event.status.value,
        reason=event.reason.value,
        first_start=event.first_start,
        first_end=event.first_end,
        second_start=event.second_start,
        second_end=event.second_end,
        datetime=event.datetime,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    assert event_response.id == event.id
    assert event_response.status == "True"
    assert event_response.reason == "FAULT_CONTROLLER"


def test_malfunction_event_create_validation():
    """
    Test: MalfunctionEventCreate schema validates required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import MalfunctionEventCreate
    from pydantic import ValidationError

    # Missing required field should raise ValidationError
    with pytest.raises(ValidationError):
        MalfunctionEventCreate(
            message_type=2,
            device_id=200
            # Missing required fields
        )
