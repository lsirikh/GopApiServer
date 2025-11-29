"""
Test: Action Event auto-updates source event action_reported
PRD: Action-Event-Fix-Prd3.md
"""
import pytest
from datetime import datetime


def test_create_action_updates_detection_event_action_reported(test_db):
    """
    Test: Creating ActionEvent updates DetectionEvent.action_reported from False to True

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import ActionEvent, DetectionEvent
    from app.routers.actions import create_action_event
    from app.schemas.event import ActionEventCreate
    from unittest.mock import MagicMock

    # Create a detection event with action_reported="False"
    detection = DetectionEvent(
        group_event="GROUP_A",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device="Controller",
        sequence=1,
        action_reported="False",
        result="PIR_SENSOR"
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # Verify initial state
    assert detection.action_reported == "False"

    # Create action event via API endpoint
    event_data = ActionEventCreate(
        type_event="Action",
        content="Verified and cleared the alert",
        user="admin",
        from_event=detection.id,
        from_type_event="Intrusion"
    )

    # Mock current_user
    mock_user = MagicMock()

    # Call create_action_event
    import asyncio
    response = asyncio.run(create_action_event(event_data, mock_user, test_db))

    # Verify response is successful
    assert response.success is True

    # Query the detection event again to verify action_reported was updated
    test_db.refresh(detection)
    assert detection.action_reported == "True", "action_reported should be updated to 'True' after creating ActionEvent"


def test_create_action_updates_malfunction_event_action_reported(test_db):
    """
    Test: Creating ActionEvent updates MalfunctionEvent.action_reported from False to True

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import ActionEvent, MalfunctionEvent
    from app.routers.actions import create_action_event
    from app.schemas.event import ActionEventCreate
    from unittest.mock import MagicMock

    # Create a malfunction event with action_reported="False"
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
        second_end=400
    )
    test_db.add(malfunction)
    test_db.commit()
    test_db.refresh(malfunction)

    # Verify initial state
    assert malfunction.action_reported == "False"

    # Create action event via API endpoint
    event_data = ActionEventCreate(
        type_event="Action",
        content="Fixed the controller",
        user="technician",
        from_event=malfunction.id,
        from_type_event="Fault"
    )

    # Mock current_user
    mock_user = MagicMock()

    # Call create_action_event
    import asyncio
    response = asyncio.run(create_action_event(event_data, mock_user, test_db))

    # Verify response is successful
    assert response.success is True

    # Query the malfunction event again to verify action_reported was updated
    test_db.refresh(malfunction)
    assert malfunction.action_reported == "True", "action_reported should be updated to 'True' after creating ActionEvent"


def test_create_action_does_not_affect_connection_event(test_db):
    """
    Test: Creating ActionEvent for ConnectionEvent does not cause errors
    (ConnectionEvent does not have action_reported field)

    Expected to PASS (Connection events should work without errors).
    """
    from app.models.event import ActionEvent, ConnectionEvent
    from app.routers.actions import create_action_event
    from app.schemas.event import ActionEventCreate
    from unittest.mock import MagicMock

    # Create a connection event (no action_reported field)
    connection = ConnectionEvent(
        group_event="GROUP_C",
        type_event="Connection",
        controller=3,
        sensor=3,
        type_device="PIR",
        sequence=3
    )
    test_db.add(connection)
    test_db.commit()
    test_db.refresh(connection)

    # Create action event via API endpoint
    event_data = ActionEventCreate(
        type_event="Action",
        content="Verified connection",
        user="operator",
        from_event=connection.id,
        from_type_event="Connection"
    )

    # Mock current_user
    mock_user = MagicMock()

    # Call create_action_event - should not raise error
    import asyncio
    response = asyncio.run(create_action_event(event_data, mock_user, test_db))

    # Verify response is successful
    assert response.success is True
    assert response.data.from_event.id == connection.id


def test_action_reported_remains_true_on_second_action(test_db):
    """
    Test: action_reported remains "True" when creating second ActionEvent on same source
    (Idempotent operation)

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import ActionEvent, DetectionEvent
    from app.routers.actions import create_action_event
    from app.schemas.event import ActionEventCreate
    from unittest.mock import MagicMock

    # Create a detection event with action_reported="False"
    detection = DetectionEvent(
        group_event="GROUP_D",
        type_event="Intrusion",
        controller=4,
        sensor=4,
        type_device="PIR",
        sequence=4,
        action_reported="False",
        result="VIBRATION_SENSOR"
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # Verify initial state
    assert detection.action_reported == "False"

    # Create first action event
    event_data1 = ActionEventCreate(
        type_event="Action",
        content="First action taken",
        user="user1",
        from_event=detection.id,
        from_type_event="Intrusion"
    )

    mock_user = MagicMock()

    import asyncio
    response1 = asyncio.run(create_action_event(event_data1, mock_user, test_db))
    assert response1.success is True

    # Verify action_reported was updated to "True"
    test_db.refresh(detection)
    assert detection.action_reported == "True"

    # Create second action event on same detection
    event_data2 = ActionEventCreate(
        type_event="Action",
        content="Second action taken",
        user="user2",
        from_event=detection.id,
        from_type_event="Intrusion"
    )

    response2 = asyncio.run(create_action_event(event_data2, mock_user, test_db))
    assert response2.success is True

    # Verify action_reported remains "True" (idempotent)
    test_db.refresh(detection)
    assert detection.action_reported == "True"


def test_action_reported_in_response_reflects_updated_value(test_db):
    """
    Test: The response from create_action_event shows updated action_reported="True"

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import DetectionEvent
    from app.routers.actions import create_action_event
    from app.schemas.event import ActionEventCreate
    from unittest.mock import MagicMock

    # Create a detection event with action_reported="False"
    detection = DetectionEvent(
        group_event="GROUP_E",
        type_event="Intrusion",
        controller=5,
        sensor=5,
        type_device="PIR",
        sequence=5,
        action_reported="False",
        result="VIBRATION_SENSOR"
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # Create action event
    event_data = ActionEventCreate(
        type_event="Action",
        content="Action taken",
        user="admin",
        from_event=detection.id,
        from_type_event="Intrusion"
    )

    mock_user = MagicMock()

    import asyncio
    response = asyncio.run(create_action_event(event_data, mock_user, test_db))

    # Verify response includes nested source event with updated action_reported
    assert response.success is True
    assert response.data.from_event.action_reported == "True", "Response should show updated action_reported='True'"
