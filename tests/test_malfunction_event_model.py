"""
Test: Malfunction Event model
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


def test_malfunction_event_model_has_required_fields(test_db):
    """Test: MalfunctionEvent model has all required fields"""
    from app.models.event import MalfunctionEvent

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('malfunction_events')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'group_event' in columns
    assert 'type_event' in columns
    assert 'controller' in columns
    assert 'sensor' in columns
    assert 'type_device' in columns
    assert 'sequence' in columns
    assert 'action_reported' in columns
    assert 'reason' in columns
    assert 'first_start' in columns
    assert 'first_end' in columns
    assert 'second_start' in columns
    assert 'second_end' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    # datetime should NOT exist
    assert 'datetime' not in columns


def test_malfunction_event_model_timestamps_auto_set(test_db):
    """Test: MalfunctionEvent model automatically sets timestamps"""
    from app.models.event import MalfunctionEvent, EnumTrueFalse, EnumFaultType, EnumDeviceType

    # Create malfunction event
    event = MalfunctionEvent(
        group_event="GROUP_B",
        type_event="Fault",
        controller=2,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        action_reported=EnumTrueFalse.False_,
        reason=EnumFaultType.FAULT_CONTROLLER,
        first_start=100,
        first_end=200,
        second_start=300,
        second_end=400
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Check timestamps are automatically set
    assert event.created_at is not None
    assert event.updated_at is not None
    assert isinstance(event.created_at, datetime)
    assert isinstance(event.updated_at, datetime)


def test_malfunction_event_model_table_name(test_db):
    """Test: MalfunctionEvent model has correct table name"""
    from app.models.event import MalfunctionEvent

    assert MalfunctionEvent.__tablename__ == "malfunction_events"


def test_malfunction_event_model_create_and_retrieve(test_db):
    """Test: Can create and retrieve MalfunctionEvent"""
    from app.models.event import MalfunctionEvent, EnumTrueFalse, EnumFaultType, EnumDeviceType

    # Create malfunction event
    event = MalfunctionEvent(
        group_event="GROUP_TEST_MALFUNCTION",
        type_event="Fault",
        controller=2,
        sensor=2,
        type_device=EnumDeviceType.Fence,
        sequence=2,
        action_reported=EnumTrueFalse.False_,
        reason=EnumFaultType.FAULT_FENCE,
        first_start=100,
        first_end=200,
        second_start=300,
        second_end=400
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Retrieve event
    retrieved = test_db.query(MalfunctionEvent).filter(MalfunctionEvent.id == event.id).first()

    assert retrieved is not None
    assert retrieved.group_event == "GROUP_TEST_MALFUNCTION"
    assert retrieved.controller == 2
    assert retrieved.sensor == 2
    assert retrieved.action_reported == EnumTrueFalse.False_
    assert retrieved.reason == EnumFaultType.FAULT_FENCE
    assert retrieved.first_start == 100
    assert retrieved.first_end == 200
    assert retrieved.second_start == 300
    assert retrieved.second_end == 400
    assert retrieved.created_at is not None


def test_malfunction_event_enums_exist():
    """Test: Malfunction Event related enums exist"""
    from app.models.event import EnumFaultType, EnumTrueFalse, EnumDeviceType

    # Test EnumFaultType
    assert hasattr(EnumFaultType, 'FAULT_CONTROLLER')
    assert hasattr(EnumFaultType, 'FAULT_FENCE')
    assert hasattr(EnumFaultType, 'FAULT_MULTI')
    assert hasattr(EnumFaultType, 'FAULT_CABLE_CUTTING')
    assert hasattr(EnumFaultType, 'FAULT_ETC')

    # Test EnumTrueFalse
    assert hasattr(EnumTrueFalse, 'True_')
    assert hasattr(EnumTrueFalse, 'False_')

    # Test EnumDeviceType
    assert hasattr(EnumDeviceType, 'PIR')
    assert hasattr(EnumDeviceType, 'Fence')
