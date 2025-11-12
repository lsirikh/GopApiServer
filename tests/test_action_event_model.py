"""
Test: Action Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_action_event_model_has_required_fields(test_db):
    """
    Test: ActionEvent model has all required fields including from_event references

    Expected to fail initially (Red phase).
    """
    from app.models.event import ActionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('action_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'message_type' in columns
    assert 'device_id' in columns
    assert 'group_event' in columns
    assert 'content' in columns
    assert 'user' in columns
    assert 'from_event_id' in columns
    assert 'from_event_type' in columns
    assert 'datetime' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_action_event_model_timestamps_auto_set(test_db):
    """
    Test: ActionEvent model automatically sets timestamps

    Expected to fail initially (Red phase).
    """
    from app.models.event import ActionEvent

    # Create action event
    event = ActionEvent(
        message_type=4,
        device_id=400,
        group_event="GROUP_D",
        content="User acknowledged the detection event",
        user="admin",
        from_event_id=1,
        from_event_type="detection",
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


def test_action_event_model_table_name(test_db):
    """
    Test: ActionEvent model has correct table name

    Expected to fail initially (Red phase).
    """
    from app.models.event import ActionEvent

    assert ActionEvent.__tablename__ == "action_events"


def test_action_event_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve ActionEvent with polymorphic reference

    Expected to fail initially (Red phase).
    """
    from app.models.event import ActionEvent

    event_datetime = datetime.utcnow()

    # Create action event
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

    # Retrieve event
    retrieved = test_db.query(ActionEvent).filter(ActionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.message_type == 4
    assert retrieved.device_id == 400
    assert retrieved.group_event == "GROUP_D"
    assert retrieved.content == "Inspection completed"
    assert retrieved.user == "operator1"
    assert retrieved.from_event_id == 5
    assert retrieved.from_event_type == "malfunction"
    assert retrieved.datetime == event_datetime


def test_action_event_polymorphic_reference(test_db):
    """
    Test: ActionEvent can reference different event types (detection, malfunction, connection)

    Expected to fail initially (Red phase).
    """
    from app.models.event import ActionEvent

    # Create action referencing detection event
    action1 = ActionEvent(
        message_type=4,
        device_id=100,
        group_event="GROUP_A",
        content="Acknowledged detection",
        user="user1",
        from_event_id=10,
        from_event_type="detection",
        datetime=datetime.utcnow()
    )
    test_db.add(action1)

    # Create action referencing malfunction event
    action2 = ActionEvent(
        message_type=4,
        device_id=200,
        group_event="GROUP_B",
        content="Fixed malfunction",
        user="user2",
        from_event_id=20,
        from_event_type="malfunction",
        datetime=datetime.utcnow()
    )
    test_db.add(action2)

    # Create action referencing connection event
    action3 = ActionEvent(
        message_type=4,
        device_id=300,
        group_event="GROUP_C",
        content="Verified connection",
        user="user3",
        from_event_id=30,
        from_event_type="connection",
        datetime=datetime.utcnow()
    )
    test_db.add(action3)

    test_db.commit()

    # Verify all three actions were created
    actions = test_db.query(ActionEvent).all()
    assert len(actions) == 3
    assert actions[0].from_event_type == "detection"
    assert actions[1].from_event_type == "malfunction"
    assert actions[2].from_event_type == "connection"
