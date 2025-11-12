"""
Test: Detection Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_detection_event_model_has_required_fields(test_db):
    """
    Test: DetectionEvent model has all required fields

    Expected to fail initially (Red phase).
    """
    from app.models.event import DetectionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('detection_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'message_type' in columns
    assert 'device_id' in columns
    assert 'group_event' in columns
    assert 'status' in columns
    assert 'result' in columns
    assert 'datetime' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_detection_event_model_timestamps_auto_set(test_db):
    """
    Test: DetectionEvent model automatically sets timestamps

    Expected to fail initially (Red phase).
    """
    from app.models.event import DetectionEvent, EnumTrueFalse, EnumDetectionType

    # Create detection event
    event = DetectionEvent(
        message_type=1,
        device_id=100,
        group_event="GROUP_A",
        status=EnumTrueFalse.TRUE,
        result=EnumDetectionType.PIR_SENSOR,
        datetime=datetime.utcnow()
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Check timestamps are set
    assert event.created_at is not None
    assert event.updated_at is not None
    assert isinstance(event.created_at, datetime)
    assert isinstance(event.updated_at, datetime)


def test_detection_event_model_table_name(test_db):
    """
    Test: DetectionEvent model has correct table name

    Expected to fail initially (Red phase).
    """
    from app.models.event import DetectionEvent

    assert DetectionEvent.__tablename__ == "detection_events"


def test_detection_event_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve DetectionEvent

    Expected to fail initially (Red phase).
    """
    from app.models.event import DetectionEvent, EnumTrueFalse, EnumDetectionType

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

    # Retrieve event
    retrieved = test_db.query(DetectionEvent).filter(DetectionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.message_type == 1
    assert retrieved.device_id == 100
    assert retrieved.group_event == "GROUP_A"
    assert retrieved.status == EnumTrueFalse.TRUE
    assert retrieved.result == EnumDetectionType.PIR_SENSOR
    assert retrieved.datetime == event_datetime


def test_detection_event_enums_exist(test_db):
    """
    Test: Detection event-specific enums exist and have correct values

    Expected to fail initially (Red phase).
    """
    from app.models.event import EnumTrueFalse, EnumDetectionType

    # Test EnumTrueFalse
    assert EnumTrueFalse.FALSE.value == "False"
    assert EnumTrueFalse.TRUE.value == "True"

    # Test EnumDetectionType
    assert EnumDetectionType.NONE.value == "NONE"
    assert EnumDetectionType.CABLE_CUTTING.value == "CABLE_CUTTING"
    assert EnumDetectionType.CABLE_CONNECTED.value == "CABLE_CONNECTED"
    assert EnumDetectionType.PIR_SENSOR.value == "PIR_SENSOR"
    assert EnumDetectionType.THERMAL_SENSOR.value == "THERMAL_SENSOR"
    assert EnumDetectionType.VIBRATION_SENSOR.value == "VIBRATION_SENSOR"
    assert EnumDetectionType.CONTACT_SENSOR.value == "CONTACT_SENSOR"
    assert EnumDetectionType.DISTANCE_SENSOR.value == "DISTANCE_SENSOR"
