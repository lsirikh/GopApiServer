"""
Test: Malfunction Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_malfunction_event_model_has_required_fields(test_db):
    """
    Test: MalfunctionEvent model has all required fields including malfunction-specific fields

    Expected to fail initially (Red phase).
    """
    from app.models.event import MalfunctionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('malfunction_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'message_type' in columns
    assert 'device_id' in columns
    assert 'group_event' in columns
    assert 'status' in columns
    assert 'reason' in columns
    assert 'first_start' in columns
    assert 'first_end' in columns
    assert 'second_start' in columns
    assert 'second_end' in columns
    assert 'datetime' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_malfunction_event_model_timestamps_auto_set(test_db):
    """
    Test: MalfunctionEvent model automatically sets timestamps

    Expected to fail initially (Red phase).
    """
    from app.models.event import MalfunctionEvent, EnumTrueFalse, EnumFaultType

    # Create malfunction event
    event = MalfunctionEvent(
        message_type=2,
        device_id=200,
        group_event="GROUP_B",
        status=EnumTrueFalse.TRUE,
        reason=EnumFaultType.FAULT_CONTROLLER,
        first_start=100,
        first_end=200,
        second_start=300,
        second_end=400,
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


def test_malfunction_event_model_table_name(test_db):
    """
    Test: MalfunctionEvent model has correct table name

    Expected to fail initially (Red phase).
    """
    from app.models.event import MalfunctionEvent

    assert MalfunctionEvent.__tablename__ == "malfunction_events"


def test_malfunction_event_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve MalfunctionEvent

    Expected to fail initially (Red phase).
    """
    from app.models.event import MalfunctionEvent, EnumTrueFalse, EnumFaultType

    event_datetime = datetime.utcnow()

    # Create malfunction event
    event = MalfunctionEvent(
        message_type=2,
        device_id=200,
        group_event="GROUP_B",
        status=EnumTrueFalse.TRUE,
        reason=EnumFaultType.FAULT_FENCE,
        first_start=100,
        first_end=200,
        second_start=300,
        second_end=400,
        datetime=event_datetime
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Retrieve event
    retrieved = test_db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.message_type == 2
    assert retrieved.device_id == 200
    assert retrieved.group_event == "GROUP_B"
    assert retrieved.status == EnumTrueFalse.TRUE
    assert retrieved.reason == EnumFaultType.FAULT_FENCE
    assert retrieved.first_start == 100
    assert retrieved.first_end == 200
    assert retrieved.second_start == 300
    assert retrieved.second_end == 400
    assert retrieved.datetime == event_datetime


def test_malfunction_event_fault_types_exist(test_db):
    """
    Test: EnumFaultType exists and has correct values

    Expected to fail initially (Red phase).
    """
    from app.models.event import EnumFaultType

    # Test EnumFaultType (already created in Phase 8, just verify)
    assert EnumFaultType.FAULT_CONTROLLER.value == "FAULT_CONTROLLER"
    assert EnumFaultType.FAULT_FENCE.value == "FAULT_FENCE"
    assert EnumFaultType.FAULT_MULTI.value == "FAULT_MULTI"
    assert EnumFaultType.FAULT_CABLE_CUTTING.value == "FAULT_CABLE_CUTTING"
    assert EnumFaultType.FAULT_ETC.value == "FAULT_ETC"
