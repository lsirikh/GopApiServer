"""
Test: Connection Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_connection_event_model_has_required_fields(test_db):
    """
    Test: ConnectionEvent model has all required fields

    Expected to fail initially (Red phase).
    """
    from app.models.event import ConnectionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('connection_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'message_type' in columns
    assert 'device_id' in columns
    assert 'group_event' in columns
    assert 'status' in columns
    assert 'datetime' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_connection_event_model_timestamps_auto_set(test_db):
    """
    Test: ConnectionEvent model automatically sets timestamps

    Expected to fail initially (Red phase).
    """
    from app.models.event import ConnectionEvent, EnumTrueFalse

    # Create connection event
    event = ConnectionEvent(
        message_type=3,
        device_id=300,
        group_event="GROUP_C",
        status=EnumTrueFalse.TRUE,
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


def test_connection_event_model_table_name(test_db):
    """
    Test: ConnectionEvent model has correct table name

    Expected to fail initially (Red phase).
    """
    from app.models.event import ConnectionEvent

    assert ConnectionEvent.__tablename__ == "connection_events"


def test_connection_event_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve ConnectionEvent

    Expected to fail initially (Red phase).
    """
    from app.models.event import ConnectionEvent, EnumTrueFalse

    event_datetime = datetime.utcnow()

    # Create connection event
    event = ConnectionEvent(
        message_type=3,
        device_id=300,
        group_event="GROUP_C",
        status=EnumTrueFalse.FALSE,
        datetime=event_datetime
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Retrieve event
    retrieved = test_db.query(ConnectionEvent).filter(ConnectionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.message_type == 3
    assert retrieved.device_id == 300
    assert retrieved.group_event == "GROUP_C"
    assert retrieved.status == EnumTrueFalse.FALSE
    assert retrieved.datetime == event_datetime


def test_connection_event_uses_enum_true_false(test_db):
    """
    Test: ConnectionEvent uses EnumTrueFalse for status

    Expected to fail initially (Red phase).
    """
    from app.models.event import ConnectionEvent, EnumTrueFalse

    # Create with TRUE status
    event = ConnectionEvent(
        message_type=3,
        device_id=300,
        group_event="GROUP_C",
        status=EnumTrueFalse.TRUE,
        datetime=datetime.utcnow()
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    assert event.status == EnumTrueFalse.TRUE
    assert event.status.value == "True"
