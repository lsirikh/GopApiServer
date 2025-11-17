"""
Test: Action Event with nested from_event response
PRD: Action-Event-Fix-Prd.md - Section 3 (Phase 3)
"""
import pytest
from datetime import datetime


def test_get_action_event_returns_nested_detection_event(test_db):
    """
    Test: GET single ActionEvent returns nested DetectionEvent object

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import ActionEvent, DetectionEvent
    from app.routers.actions import get_action_event
    from app.schemas.event import DetectionEventResponse
    from unittest.mock import MagicMock

    # Create a detection event
    detection = DetectionEvent(
        group_event="GROUP_A",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device="Controller",
        sequence=1,
        action_reported="False",
        result="PIR_SENSOR",
        datetime=datetime.utcnow()
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # Create action event referencing the detection
    action = ActionEvent(
        type_event="Action",
        content="Verified and cleared the alert",
        user="admin",
        from_event=detection.id,
        from_type_event="Intrusion",
        datetime=datetime.utcnow()
    )
    test_db.add(action)
    test_db.commit()
    test_db.refresh(action)

    # Mock current_user
    mock_user = MagicMock()

    # Get the action event (async function)
    import asyncio
    response = asyncio.run(get_action_event(action.id, mock_user, test_db))

    # Verify response structure
    assert response.success is True
    assert response.data is not None

    # Verify from_event is a nested object, not just an ID
    from_event = response.data.from_event
    assert isinstance(from_event, DetectionEventResponse)
    assert from_event.id == detection.id
    assert from_event.type_event == "Intrusion"
    assert from_event.result == "PIR_SENSOR"
    assert from_event.controller == 1


def test_get_action_event_returns_nested_malfunction_event(test_db):
    """
    Test: GET single ActionEvent returns nested MalfunctionEvent object

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import ActionEvent, MalfunctionEvent
    from app.routers.actions import get_action_event
    from app.schemas.event import MalfunctionEventResponse
    from unittest.mock import MagicMock

    # Create a malfunction event
    malfunction = MalfunctionEvent(
        group_event="GROUP_B",
        type_event="Fault",
        controller=2,
        sensor=0,
        type_device="Controller",
        sequence=2,
        action_reported="False",
        reason="FAULT_CONTROLLER",
        first_start=100,
        first_end=200,
        second_start=300,
        second_end=400,
        datetime=datetime.utcnow()
    )
    test_db.add(malfunction)
    test_db.commit()
    test_db.refresh(malfunction)

    # Create action event
    action = ActionEvent(
        type_event="Action",
        content="Fixed the controller",
        user="technician",
        from_event=malfunction.id,
        from_type_event="Fault",
        datetime=datetime.utcnow()
    )
    test_db.add(action)
    test_db.commit()
    test_db.refresh(action)

    # Mock current_user
    mock_user = MagicMock()

    # Get the action event
    import asyncio
    response = asyncio.run(get_action_event(action.id, mock_user, test_db))

    # Verify from_event is nested MalfunctionEvent
    from_event = response.data.from_event
    assert isinstance(from_event, MalfunctionEventResponse)
    assert from_event.id == malfunction.id
    assert from_event.type_event == "Fault"
    assert from_event.reason == "FAULT_CONTROLLER"


def test_get_action_events_list_returns_nested_objects(test_db):
    """
    Test: GET list of ActionEvents returns nested event objects for all items

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import ActionEvent, DetectionEvent, ConnectionEvent
    from app.routers.actions import get_action_events
    from app.schemas.event import DetectionEventResponse, ConnectionEventResponse
    from unittest.mock import MagicMock

    # Create detection event
    detection = DetectionEvent(
        group_event="GROUP_A",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device="Controller",
        sequence=1,
        action_reported="False",
        result="PIR_SENSOR",
        datetime=datetime.utcnow()
    )
    test_db.add(detection)

    # Create connection event
    connection = ConnectionEvent(
        group_event="GROUP_C",
        type_event="Connection",
        controller=3,
        sensor=3,
        type_device="PIR",
        sequence=3,
        datetime=datetime.utcnow()
    )
    test_db.add(connection)
    test_db.commit()
    test_db.refresh(detection)
    test_db.refresh(connection)

    # Create action events
    action1 = ActionEvent(
        type_event="Action",
        content="Action on detection",
        user="user1",
        from_event=detection.id,
        from_type_event="Intrusion",
        datetime=datetime.utcnow()
    )
    action2 = ActionEvent(
        type_event="Action",
        content="Action on connection",
        user="user2",
        from_event=connection.id,
        from_type_event="Connection",
        datetime=datetime.utcnow()
    )
    test_db.add_all([action1, action2])
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get list of action events
    import asyncio
    response = asyncio.run(get_action_events(
        page=1,
        limit=20,
        user=None,
        from_event=None,
        start_date=None,
        end_date=None,
        current_user=mock_user,
        db=test_db
    ))

    # Verify response
    assert response.success is True
    assert len(response.data) == 2

    # Verify first action has nested DetectionEvent
    first_action = response.data[0]
    assert isinstance(first_action.from_event, (DetectionEventResponse, ConnectionEventResponse))

    # Verify second action has nested ConnectionEvent
    second_action = response.data[1]
    assert isinstance(second_action.from_event, (DetectionEventResponse, ConnectionEventResponse))
