"""
Test: Detection Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_detection_event_model_has_required_fields(test_db):
    """Test: DetectionEvent model has all required fields"""
    from app.models.event import DetectionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('detection_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'group_event' in columns
    assert 'type_event' in columns
    assert 'controller' in columns
    assert 'sensor' in columns
    assert 'type_device' in columns
    assert 'sequence' in columns
    assert 'action_reported' in columns
    assert 'result' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    # datetime should NOT exist
    assert 'datetime' not in columns


def test_detection_event_model_timestamps_auto_set(test_db):
    """Test: DetectionEvent model automatically sets timestamps"""
    from app.models.event import DetectionEvent, EnumTrueFalse, EnumDetectionType, EnumDeviceType

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

    # Check timestamps are automatically set
    assert event.created_at is not None
    assert event.updated_at is not None
    assert isinstance(event.created_at, datetime)
    assert isinstance(event.updated_at, datetime)


def test_detection_event_model_table_name(test_db):
    """Test: DetectionEvent model has correct table name"""
    from app.models.event import DetectionEvent

    assert DetectionEvent.__tablename__ == "detection_events"


def test_detection_event_model_create_and_retrieve(test_db):
    """Test: Can create and retrieve DetectionEvent"""
    from app.models.event import DetectionEvent, EnumTrueFalse, EnumDetectionType, EnumDeviceType

    # Create detection event
    event = DetectionEvent(
        group_event="GROUP_TEST",
        type_event="Intrusion",
        controller=1,
        sensor=2,
        type_device=EnumDeviceType.Fence,
        sequence=10,
        action_reported=EnumTrueFalse.False_,
        result=EnumDetectionType.THERMAL_SENSOR
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Retrieve event
    retrieved = test_db.query(DetectionEvent).filter(DetectionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.group_event == "GROUP_TEST"
    assert retrieved.controller == 1
    assert retrieved.sensor == 2
    assert retrieved.sequence == 10
    assert retrieved.created_at is not None


def test_detection_event_enums_exist():
    """Test: Detection Event related enums exist"""
    from app.models.event import EnumDeviceType, EnumTrueFalse, EnumDetectionType

    # Test EnumDeviceType
    assert hasattr(EnumDeviceType, 'PIR')
    assert hasattr(EnumDeviceType, 'Fence')

    # Test EnumTrueFalse
    assert hasattr(EnumTrueFalse, 'True_')
    assert hasattr(EnumTrueFalse, 'False_')

    # Test EnumDetectionType
    assert hasattr(EnumDetectionType, 'PIR_SENSOR')
    assert hasattr(EnumDetectionType, 'THERMAL_SENSOR')
