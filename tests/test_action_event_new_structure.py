"""
Test: Action Event model with new structure (from_event single field)
PRD: Action-Event-Fix-Prd.md
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime

pytestmark = pytest.mark.skip(
    reason="Old \"new structure\" (from_event+from_type_event) — "
           "superseded by PRD v2.1 from_event_id; "
           "see tests/test_action_event_from_event_id.py"
)


def test_action_event_model_has_from_event_field(test_db):
    """
    Test: ActionEvent model has from_event AND from_type_event fields

    This test validates the current structure where both fields are required:
    - from_event: integer ID of the source event
    - from_type_event: type discriminator ("Intrusion", "Fault", or "Connection")
    """
    from app.models.event import ActionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('action_events')]

    # Current structure should have both from_event and from_type_event
    assert 'from_event' in columns
    assert 'from_type_event' in columns

    # Old structure fields should NOT exist
    assert 'from_event_id' not in columns
    assert 'message_type' not in columns
    assert 'device_id' not in columns


def test_action_event_model_create_with_from_event(test_db):
    """
    Test: Can create ActionEvent with from_event and from_type_event fields

    Expected to PASS with current structure.
    """
    from app.models.event import ActionEvent
    from app.config import settings

    event_datetime = datetime.now(settings.tz)

    # Create action event with current structure
    event = ActionEvent(
        type_event="Action",
        content="Verified and cleared the alert",
        user="admin",
        from_event=1001,
        from_type_event="Intrusion",  # Required field
        datetime=event_datetime
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Verify event was created
    assert event.id is not None
    assert event.type_event == "Action"
    assert event.content == "Verified and cleared the alert"
    assert event.user == "admin"
    assert event.from_event == 1001
    assert event.from_type_event == "Intrusion"
    assert event.datetime.replace(tzinfo=None) == event_datetime.replace(tzinfo=None)
    assert event.created_at is not None
    assert event.updated_at is not None


def test_action_event_query_by_from_event(test_db):
    """
    Test: Can query ActionEvent by from_event field

    Expected to PASS with current structure.
    """
    from app.models.event import ActionEvent
    from app.config import settings

    # Create multiple action events
    event1 = ActionEvent(
        type_event="Action",
        content="Action 1",
        user="user1",
        from_event=100,
        from_type_event="Intrusion",
        datetime=datetime.now(settings.tz)
    )
    event2 = ActionEvent(
        type_event="Action",
        content="Action 2",
        user="user2",
        from_event=200,
        from_type_event="Fault",
        datetime=datetime.now(settings.tz)
    )
    event3 = ActionEvent(
        type_event="Action",
        content="Action 3",
        user="user3",
        from_event=100,  # Same from_event as event1
        from_type_event="Connection",
        datetime=datetime.now(settings.tz)
    )

    test_db.add_all([event1, event2, event3])
    test_db.commit()

    # Query by from_event
    events_from_100 = test_db.query(ActionEvent).filter(ActionEvent.from_event == 100).all()

    assert len(events_from_100) == 2
    assert all(e.from_event == 100 for e in events_from_100)
