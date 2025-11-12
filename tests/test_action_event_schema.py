"""
Test: Action Event schemas
"""
import pytest
from datetime import datetime


def test_action_event_create_schema_fields():
    """Test: ActionEventCreate schema has all required fields"""
    from app.schemas.event import ActionEventCreate

    event_data = {
        "message_type": 4,
        "device_id": 400,
        "group_event": "GROUP_D",
        "content": "User acknowledged event",
        "user": "admin",
        "from_event_id": 10,
        "from_event_type": "detection",
        "datetime": datetime.utcnow()
    }

    event_create = ActionEventCreate(**event_data)

    assert event_create.message_type == 4
    assert event_create.device_id == 400
    assert event_create.content == "User acknowledged event"
    assert event_create.user == "admin"
    assert event_create.from_event_id == 10
    assert event_create.from_event_type == "detection"


def test_action_event_response_schema_fields():
    """Test: ActionEventResponse schema has all required fields"""
    from app.schemas.event import ActionEventResponse

    event_data = {
        "id": 1,
        "message_type": 4,
        "device_id": 400,
        "group_event": "GROUP_D",
        "content": "Fixed malfunction",
        "user": "operator1",
        "from_event_id": 20,
        "from_event_type": "malfunction",
        "datetime": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_response = ActionEventResponse(**event_data)

    assert event_response.id == 1
    assert event_response.content == "Fixed malfunction"
    assert event_response.user == "operator1"
    assert event_response.from_event_id == 20
    assert event_response.from_event_type == "malfunction"


def test_action_event_update_schema_optional_fields():
    """Test: ActionEventUpdate schema has all optional fields"""
    from app.schemas.event import ActionEventUpdate

    event_update = ActionEventUpdate(
        content="Updated action description",
        user="admin2"
    )

    assert event_update.content == "Updated action description"
    assert event_update.user == "admin2"
    assert event_update.message_type is None


def test_action_event_response_from_model(test_db):
    """Test: ActionEventResponse can be created from ActionEvent model"""
    from app.models.event import ActionEvent
    from app.schemas.event import ActionEventResponse

    event_datetime = datetime.utcnow()

    event = ActionEvent(
        message_type=4,
        device_id=400,
        group_event="GROUP_D",
        content="Inspection completed",
        user="operator1",
        from_event_id=5,
        from_event_type="malfunction",
        datetime=event_datetime
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    event_response = ActionEventResponse(
        id=event.id,
        message_type=event.message_type,
        device_id=event.device_id,
        group_event=event.group_event,
        content=event.content,
        user=event.user,
        from_event_id=event.from_event_id,
        from_event_type=event.from_event_type,
        datetime=event.datetime,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    assert event_response.id == event.id
    assert event_response.content == "Inspection completed"


def test_action_event_create_validation():
    """Test: ActionEventCreate schema validates required fields"""
    from app.schemas.event import ActionEventCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ActionEventCreate(
            message_type=4,
            device_id=400
            # Missing required fields
        )
