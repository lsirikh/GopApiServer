"""
Test Action Event API with from_event_type field
"""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.event import ActionEvent, DetectionEvent, MalfunctionEvent, ConnectionEvent
from app.models.event import EnumTrueFalse, EnumDetectionType, EnumFaultType
from app.utils.enums import EnumDeviceType
from app.config import settings


def test_action_event_has_from_event_type_field(test_db):
    """Test that ActionEvent model has from_event_type field"""
    # Create a detection event first
    detection = DetectionEvent(
        group_event="test-group",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        action_reported=EnumTrueFalse.FALSE,
        result=EnumDetectionType.PIR_SENSOR,
        datetime=datetime.now(settings.tz)
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # Create action event with from_type_event
    action = ActionEvent(
        type_event="Action",
        content="Test action",
        user="test_user",
        from_event=detection.id,
        from_type_event="Intrusion",  # This field should exist
        datetime=datetime.now(settings.tz)
    )
    test_db.add(action)
    test_db.commit()
    test_db.refresh(action)

    # Verify from_type_event field exists and has correct value
    assert hasattr(action, 'from_type_event')
    assert action.from_type_event == "Intrusion"


def test_action_event_type_accepts_all_event_types(test_db):
    """Test that from_type_event accepts Intrusion, Fault, and Connection"""
    # Create source events
    detection = DetectionEvent(
        group_event="test-group",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        action_reported=EnumTrueFalse.FALSE,
        result=EnumDetectionType.PIR_SENSOR,
        datetime=datetime.now(settings.tz)
    )

    malfunction = MalfunctionEvent(
        group_event="test-group",
        type_event="Fault",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        action_reported=EnumTrueFalse.FALSE,
        reason=EnumFaultType.FAULT_CONTROLLER,
        first_start=0,
        first_end=10,
        second_start=20,
        second_end=30,
        datetime=datetime.now(settings.tz)
    )

    connection = ConnectionEvent(
        group_event="test-group",
        type_event="Connection",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        datetime=datetime.now(settings.tz)
    )

    test_db.add_all([detection, malfunction, connection])
    test_db.commit()
    test_db.refresh(detection)
    test_db.refresh(malfunction)
    test_db.refresh(connection)

    # Create action events for each type
    action1 = ActionEvent(
        type_event="Action",
        content="Test detection action",
        user="test_user",
        from_event=detection.id,
        from_type_event="Intrusion",
        datetime=datetime.now(settings.tz)
    )

    action2 = ActionEvent(
        type_event="Action",
        content="Test malfunction action",
        user="test_user",
        from_event=malfunction.id,
        from_type_event="Fault",
        datetime=datetime.now(settings.tz)
    )

    action3 = ActionEvent(
        type_event="Action",
        content="Test connection action",
        user="test_user",
        from_event=connection.id,
        from_type_event="Connection",
        datetime=datetime.now(settings.tz)
    )

    test_db.add_all([action1, action2, action3])
    test_db.commit()

    # Verify all event types are stored correctly
    assert action1.from_type_event == "Intrusion"
    assert action2.from_type_event == "Fault"
    assert action3.from_type_event == "Connection"


def test_action_event_requires_from_type_event(test_db):
    """Test that from_type_event is a required field"""
    # Create a detection event first
    detection = DetectionEvent(
        group_event="test-group",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.PIR,
        sequence=1,
        action_reported=EnumTrueFalse.FALSE,
        result=EnumDetectionType.PIR_SENSOR,
        datetime=datetime.now(settings.tz)
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # Try to create action event without from_type_event (should fail)
    action = ActionEvent(
        type_event="Action",
        content="Test action",
        user="test_user",
        from_event=detection.id,
        # from_type_event is missing
        datetime=datetime.now(settings.tz)
    )
    test_db.add(action)

    with pytest.raises(Exception):  # Should raise database constraint error
        test_db.commit()
