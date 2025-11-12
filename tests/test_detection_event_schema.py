"""
Test: Detection Event schemas
"""
import pytest
from datetime import datetime


def test_detection_event_create_schema_fields():
    """
    Test: DetectionEventCreate schema has all required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import DetectionEventCreate

    event_data = {
        "message_type": 1,
        "device_id": 100,
        "group_event": "GROUP_A",
        "status": "True",
        "result": "PIR_SENSOR",
        "datetime": datetime.utcnow()
    }

    event_create = DetectionEventCreate(**event_data)

    assert event_create.message_type == 1
    assert event_create.device_id == 100
    assert event_create.group_event == "GROUP_A"
    assert event_create.status == "True"
    assert event_create.result == "PIR_SENSOR"
    assert isinstance(event_create.datetime, datetime)


def test_detection_event_response_schema_fields():
    """
    Test: DetectionEventResponse schema has all required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import DetectionEventResponse

    event_data = {
        "id": 1,
        "message_type": 1,
        "device_id": 100,
        "group_event": "GROUP_A",
        "status": "True",
        "result": "PIR_SENSOR",
        "datetime": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_response = DetectionEventResponse(**event_data)

    assert event_response.id == 1
    assert event_response.message_type == 1
    assert event_response.device_id == 100
    assert event_response.group_event == "GROUP_A"
    assert event_response.status == "True"
    assert event_response.result == "PIR_SENSOR"
    assert isinstance(event_response.datetime, datetime)
    assert isinstance(event_response.created_at, datetime)
    assert isinstance(event_response.updated_at, datetime)


def test_detection_event_update_schema_optional_fields():
    """
    Test: DetectionEventUpdate schema has all optional fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import DetectionEventUpdate

    # Test with partial update
    event_update = DetectionEventUpdate(
        status="False",
        result="THERMAL_SENSOR"
    )

    assert event_update.status == "False"
    assert event_update.result == "THERMAL_SENSOR"
    assert event_update.message_type is None
    assert event_update.device_id is None


def test_detection_event_response_from_model(test_db):
    """
    Test: DetectionEventResponse can be created from DetectionEvent model

    Expected to fail initially (Red phase).
    """
    from app.models.event import DetectionEvent, EnumTrueFalse, EnumDetectionType
    from app.schemas.event import DetectionEventResponse

    event_datetime = datetime.utcnow()

    # Create detection event
    event = DetectionEvent(
        message_type=1,
        device_id=100,
        group_event="GROUP_A",
        status=EnumTrueFalse.TRUE,
        result=EnumDetectionType.PIR_SENSOR,
        datetime=event_datetime
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Create response from model
    event_response = DetectionEventResponse(
        id=event.id,
        message_type=event.message_type,
        device_id=event.device_id,
        group_event=event.group_event,
        status=event.status.value,
        result=event.result.value,
        datetime=event.datetime,
        created_at=event.created_at,
        updated_at=event.updated_at
    )

    assert event_response.id == event.id
    assert event_response.status == "True"
    assert event_response.result == "PIR_SENSOR"


def test_detection_event_create_validation():
    """
    Test: DetectionEventCreate schema validates required fields

    Expected to fail initially (Red phase).
    """
    from app.schemas.event import DetectionEventCreate
    from pydantic import ValidationError

    # Missing required field should raise ValidationError
    with pytest.raises(ValidationError):
        DetectionEventCreate(
            message_type=1,
            device_id=100
            # Missing required fields
        )
