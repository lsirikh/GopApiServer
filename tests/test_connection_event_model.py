"""
Test: Connection Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_connection_event_model_has_required_fields(test_db):
    """Test: ConnectionEvent model has all required fields"""
    from app.models.event import ConnectionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('connection_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'group_event' in columns
    assert 'type_event' in columns
    assert 'controller' in columns
    assert 'sensor' in columns
    assert 'type_device' in columns
    assert 'sequence' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    # datetime should NOT exist
    assert 'datetime' not in columns


def test_connection_event_model_timestamps_auto_set(test_db):
    """Test: ConnectionEvent model automatically sets timestamps"""
    from app.models.event import ConnectionEvent, EnumDeviceType

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

    # Check timestamps are automatically set
    assert event.created_at is not None
    assert event.updated_at is not None
    assert isinstance(event.created_at, datetime)
    assert isinstance(event.updated_at, datetime)


def test_connection_event_model_table_name(test_db):
    """Test: ConnectionEvent model has correct table name"""
    from app.models.event import ConnectionEvent

    assert ConnectionEvent.__tablename__ == "connection_events"


def test_connection_event_model_create_and_retrieve(test_db):
    """Test: Can create and retrieve ConnectionEvent"""
    from app.models.event import ConnectionEvent, EnumDeviceType

    # Create connection event
    event = ConnectionEvent(
        group_event="GROUP_TEST_CONNECTION",
        type_event="Connection",
        controller=3,
        sensor=2,
        type_device=EnumDeviceType.Fence,
        sequence=2
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Retrieve event
    retrieved = test_db.query(ConnectionEvent).filter(ConnectionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.group_event == "GROUP_TEST_CONNECTION"
    assert retrieved.controller == 3
    assert retrieved.sensor == 2
    assert retrieved.type_device == EnumDeviceType.Fence
    assert retrieved.sequence == 2
    assert retrieved.created_at is not None


def test_connection_event_uses_enum_device_type(test_db):
    """Test: ConnectionEvent uses EnumDeviceType for type_device"""
    from app.models.event import ConnectionEvent, EnumDeviceType

    # Create with PIR type_device
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

    assert event.type_device == EnumDeviceType.PIR
    assert event.type_device.value == "PIR"
