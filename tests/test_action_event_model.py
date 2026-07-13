"""
Test: Action Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime

pytestmark = pytest.mark.skip(
    reason="Legacy ActionEvent from_event/from_type_event structure — "
           "superseded by PRD v2.1 from_event_id polymorphic FK; "
           "see tests/test_action_event_from_event_id.py"
)


def test_action_event_model_has_required_fields(test_db):
    """
    Test: ActionEvent model has all required fields including from_event references

    Expected to pass with new structure.
    """
    from app.models.event import ActionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('action_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'type_event' in columns
    assert 'content' in columns
    assert 'user' in columns
    assert 'from_event' in columns
    assert 'from_type_event' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_action_event_model_timestamps_auto_set(test_db):
    """
    Test: ActionEvent model automatically sets timestamps

    Expected to pass with new structure.
    """
    from app.models.event import ActionEvent
    from app.config import settings

    # Create action event
    event = ActionEvent(
        type_event="Action",
        content="User acknowledged the detection event",
        user="admin",
        from_event=1,
        from_type_event="Intrusion"
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

    Expected to pass with new structure.
    """
    from app.models.event import ActionEvent
    from app.config import settings

    event_datetime = datetime.now(settings.tz)

    # Create action event
    event = ActionEvent(
        type_event="Action",
        content="Inspection completed",
        user="operator1",
        from_event=5,
        from_type_event="Fault"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Retrieve event
    retrieved = test_db.query(ActionEvent).filter(ActionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.type_event == "Action"
    assert retrieved.content == "Inspection completed"
    assert retrieved.user == "operator1"
    assert retrieved.from_event == 5
    assert retrieved.from_type_event == "Fault"
    # Check that created_at was automatically set
    assert retrieved.created_at is not None


def test_action_event_polymorphic_reference(test_db):
    """
    Test: ActionEvent can reference different event types (detection, malfunction, connection)

    Expected to pass with new structure.
    """
    from app.models.event import ActionEvent
    from app.config import settings

    # Create action referencing detection event
    action1 = ActionEvent(
        type_event="Action",
        content="Acknowledged detection",
        user="user1",
        from_event=10,
        from_type_event="Intrusion"
    )
    test_db.add(action1)

    # Create action referencing malfunction event
    action2 = ActionEvent(
        type_event="Action",
        content="Fixed malfunction",
        user="user2",
        from_event=20,
        from_type_event="Fault"
    )
    test_db.add(action2)

    # Create action referencing connection event
    action3 = ActionEvent(
        type_event="Action",
        content="Verified connection",
        user="user3",
        from_event=30,
        from_type_event="Connection"
    )
    test_db.add(action3)

    test_db.commit()

    # Verify all three actions were created
    actions = test_db.query(ActionEvent).all()
    assert len(actions) == 3
    assert actions[0].from_type_event == "Intrusion"
    assert actions[1].from_type_event == "Fault"
    assert actions[2].from_type_event == "Connection"
