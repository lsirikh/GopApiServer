"""
Test: Action Event schemas
"""
import pytest
from datetime import datetime


def test_action_event_create_schema_fields():
    """Test: ActionEventCreate schema has all required fields"""
    from app.schemas.event import ActionEventCreate

    event_data = {
        "type_event": "Action",
        "content": "User acknowledged event",
        "user": "admin",
        "from_event": 10,
        "from_type_event": "Intrusion",
        "datetime": datetime.utcnow()
    }

    event_create = ActionEventCreate(**event_data)

    assert event_create.type_event == "Action"
    assert event_create.content == "User acknowledged event"
    assert event_create.user == "admin"
    assert event_create.from_event == 10
    assert event_create.from_type_event == "Intrusion"


def test_action_event_update_schema_optional_fields():
    """Test: ActionEventUpdate schema has all optional fields"""
    from app.schemas.event import ActionEventUpdate

    event_update = ActionEventUpdate(
        content="Updated action description",
        user="admin2"
    )

    assert event_update.content == "Updated action description"
    assert event_update.user == "admin2"
    assert event_update.type_event is None
    assert event_update.from_event is None
    assert event_update.from_type_event is None


def test_action_event_create_validation():
    """Test: ActionEventCreate schema validates required fields"""
    from app.schemas.event import ActionEventCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ActionEventCreate(
            type_event="Action",
            content="Test"
            # Missing required fields: user, from_event, from_type_event, datetime
        )


def test_action_event_response_has_correct_fields():
    """Test: ActionEventResponse has correct field structure"""
    from app.schemas.event import ActionEventResponse, DetectionEventResponse
    from datetime import datetime

    # Create a mock detection event for the nested object
    detection = DetectionEventResponse(
        id=1,
        group_event="GROUP_A",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device="PIR",
        sequence=1,
        action_reported="False",
        result="PIR_SENSOR",
        datetime=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    # Create ActionEventResponse with nested event
    action_response = ActionEventResponse(
        id=1,
        type_event="Action",
        content="Test action",
        user="test_user",
        from_event=detection,  # Nested object
        datetime=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    assert action_response.id == 1
    assert action_response.type_event == "Action"
    assert action_response.content == "Test action"
    assert action_response.user == "test_user"
    assert isinstance(action_response.from_event, DetectionEventResponse)
    assert action_response.from_event.id == 1
