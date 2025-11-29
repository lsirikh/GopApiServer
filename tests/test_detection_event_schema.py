"""
Test: Detection Event schemas
"""
import pytest
from datetime import datetime


def test_detection_event_create_schema_fields():
    """Test: DetectionEventCreate schema has all required fields"""
    from app.schemas.event import DetectionEventCreate

    event_data = {
        "group_event": "GROUP_A",
        "type_event": "Intrusion",
        "controller": 1,
        "sensor": 1,
        "type_device": "PIR",
        "sequence": 1,
        "action_reported": "False",
        "result": "PIR_SENSOR"
    }

    event_create = DetectionEventCreate(**event_data)

    assert event_create.group_event == "GROUP_A"
    assert event_create.type_event == "Intrusion"
    assert event_create.controller == 1
    assert event_create.sensor == 1
    assert event_create.type_device == "PIR"
    assert event_create.sequence == 1
    assert event_create.action_reported == "False"
    assert event_create.result == "PIR_SENSOR"


def test_detection_event_response_schema_fields():
    """Test: DetectionEventResponse schema has all required fields"""
    from app.schemas.event import DetectionEventResponse

    event_data = {
        "id": 1,
        "group_event": "GROUP_A",
        "type_event": "Intrusion",
        "controller": 1,
        "sensor": 1,
        "type_device": "PIR",
        "sequence": 1,
        "action_reported": "False",
        "result": "PIR_SENSOR",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    event_response = DetectionEventResponse(**event_data)

    assert event_response.id == 1
    assert event_response.group_event == "GROUP_A"
    assert event_response.type_event == "Intrusion"
    assert event_response.result == "PIR_SENSOR"
    assert isinstance(event_response.created_at, datetime)
    assert isinstance(event_response.updated_at, datetime)


def test_detection_event_update_schema_optional_fields():
    """Test: DetectionEventUpdate schema has all optional fields"""
    from app.schemas.event import DetectionEventUpdate

    # Test with partial update
    event_update = DetectionEventUpdate(
        action_reported="True",
        result="THERMAL_SENSOR"
    )

    assert event_update.action_reported == "True"
    assert event_update.result == "THERMAL_SENSOR"
    assert event_update.controller is None
    assert event_update.sensor is None


def test_detection_event_response_from_model(test_db):
    """Test: DetectionEventResponse can be created from DetectionEvent model"""
    from app.models.event import DetectionEvent, EnumTrueFalse, EnumDetectionType, EnumDeviceType
    from app.schemas.event import DetectionEventResponse

    # Create detection event
    event = DetectionEvent(
        group_event="GROUP_A",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        action_reported=EnumTrueFalse.False_,
        result=EnumDetectionType.PIR_SENSOR
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Create response from model using model_validate
    event_response = DetectionEventResponse.model_validate(event)

    assert event_response.id == event.id
    assert event_response.action_reported == "False"
    assert event_response.result == "PIR_SENSOR"
    assert event_response.created_at is not None
    assert event_response.updated_at is not None


def test_detection_event_create_validation():
    """Test: DetectionEventCreate schema validates required fields"""
    from app.schemas.event import DetectionEventCreate
    from pydantic import ValidationError

    # Missing required fields should raise ValidationError
    with pytest.raises(ValidationError):
        DetectionEventCreate(
            group_event="GROUP_A"
            # Missing required fields: controller, sensor, etc.
        )
