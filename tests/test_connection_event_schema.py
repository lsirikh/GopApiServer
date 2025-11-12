"""
Test: Connection Event schemas
"""
import pytest
from datetime import datetime


def test_connection_event_create_schema_fields():
    """
    Test: ConnectionEventCreate schema has all required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import ConnectionEventCreate

    event_data = {
        "message_type": 3,
        "device_id": 300,
        "group_event": "GROUP_C",
        "status": "True",
        "datetime": datetime.utcnow()
    }

    event_create = ConnectionEventCreate(**event_data)

    assert event_create.message_type == 3
    assert event_create.device_id == 300
    assert event_create.group_event == "GROUP_C"
    assert event_create.status == "True"
    assert isinstance(event_create.datetime, datetime)


def test_connection_event_response_schema_fields():
    """
    Test: ConnectionEventResponse schema has all required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import ConnectionEventResponse

    event_data = {
        "id": 1,
        "message_type": 3,
        "device_id": 300,
        "group_event": "GROUP_C",
        "status": "False",
        "datetime": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_response = ConnectionEventResponse(**event_data)

    assert event_response.id == 1
    assert event_response.message_type == 3
    assert event_response.device_id == 300
    assert event_response.group_event == "GROUP_C"
    assert event_response.status == "False"
    assert isinstance(event_response.datetime, datetime)
    assert isinstance(event_response.created_at, datetime)
    assert isinstance(event_response.updated_at, datetime)


def test_connection_event_update_schema_optional_fields():
    """
    Test: ConnectionEventUpdate schema has all optional fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import ConnectionEventUpdate

    # Test with partial update
    event_update = ConnectionEventUpdate(
        status="True",
        device_id=350
    )

    assert event_update.status == "True"
    assert event_update.device_id == 350
    assert event_update.message_type is None
    assert event_update.group_event is None


def test_connection_event_response_from_model(test_db):
    """
    Test: ConnectionEventResponse can be created from ConnectionEvent model

    Expected to fail initially (Red phase).
    """
    from app.models.event import ConnectionEvent, EnumTrueFalse
    from app.schemas.event import ConnectionEventResponse

    event_datetime = datetime.utcnow()

    # Create connection event
    event = ConnectionEvent(
        message_type=3,
        device_id=300,
        group_event="GROUP_C",
        status=EnumTrueFalse.TRUE,
        datetime=event_datetime
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Create response from model
    event_response = ConnectionEventResponse(
        id=event.id,
        message_type=event.message_type,
        device_id=event.device_id,
        group_event=event.group_event,
        status=event.status.value,
        datetime=event.datetime,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    assert event_response.id == event.id
    assert event_response.status == "True"


def test_connection_event_create_validation():
    """
    Test: ConnectionEventCreate schema validates required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import ConnectionEventCreate
    from pydantic import ValidationError

    # Missing required field should raise ValidationError
    with pytest.raises(ValidationError):
        ConnectionEventCreate(
            message_type=3,
            device_id=300
            # Missing required fields
        )
