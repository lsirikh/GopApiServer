"""
Test: ActionEvent DELETE resets source event's action_reported to False
PRD: Action-Event-Fix-Prd4.md (Phase 18.1)

1:1 Relationship: 1 source event = max 1 ActionEvent
Therefore, when ActionEvent is deleted, unconditionally reset action_reported to "False"
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.event import ActionEvent, DetectionEvent, MalfunctionEvent, ConnectionEvent

client = TestClient(app)


def test_delete_action_resets_detection_action_reported_to_false():
    """
    Test: Deleting ActionEvent resets DetectionEvent.action_reported from True to False

    Expected to FAIL initially (Red phase).
    """
    db = SessionLocal()
    try:
        # Create a detection event with action_reported="False"
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
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # Create action event (which sets action_reported to "True")
        action = ActionEvent(
            type_event="Action",
            content="Verified and cleared",
            user="admin",
            from_event=detection.id,
            from_type_event="Intrusion",
            datetime=datetime.utcnow()
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        # Manually set action_reported to "True" (simulating Phase 17 behavior)
        detection.action_reported = "True"
        db.commit()
        db.refresh(detection)

        # Verify initial state
        assert detection.action_reported == "True"

        # Delete the ActionEvent
        response = client.delete(f"/api/events/actions/{action.id}")

        # Verify deletion succeeded
        assert response.status_code == 200

        # Verify DetectionEvent.action_reported was reset to "False"
        db.refresh(detection)
        assert detection.action_reported == "False", "action_reported should be reset to 'False' after ActionEvent deletion"

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.from_type_event == "Intrusion").delete()
        db.query(DetectionEvent).filter(DetectionEvent.group_event == "GROUP_A").delete()
        db.commit()
        db.close()


def test_delete_action_resets_malfunction_action_reported_to_false():
    """
    Test: Deleting ActionEvent resets MalfunctionEvent.action_reported from True to False

    Expected to FAIL initially (Red phase).
    """
    db = SessionLocal()
    try:
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
            second_end=400,
            datetime=datetime.utcnow()
        )
        db.add(malfunction)
        db.commit()
        db.refresh(malfunction)

        # Create action event
        action = ActionEvent(
            type_event="Action",
            content="Fixed the controller",
            user="technician",
            from_event=malfunction.id,
            from_type_event="Fault",
            datetime=datetime.utcnow()
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        # Manually set action_reported to "True"
        malfunction.action_reported = "True"
        db.commit()
        db.refresh(malfunction)

        # Verify initial state
        assert malfunction.action_reported == "True"

        # Delete the ActionEvent
        response = client.delete(f"/api/events/actions/{action.id}")

        # Verify deletion succeeded
        assert response.status_code == 200

        # Verify MalfunctionEvent.action_reported was reset to "False"
        db.refresh(malfunction)
        assert malfunction.action_reported == "False", "action_reported should be reset to 'False' after ActionEvent deletion"

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.from_type_event == "Fault").delete()
        db.query(MalfunctionEvent).filter(MalfunctionEvent.group_event == "GROUP_B").delete()
        db.commit()
        db.close()


def test_delete_action_connection_no_error():
    """
    Test: Deleting ActionEvent for ConnectionEvent should not cause errors
    (ConnectionEvent has no action_reported field)

    Expected to PASS (Connection events don't have action_reported).
    """
    db = SessionLocal()
    try:
        # Create a connection event (no action_reported field)
        connection = ConnectionEvent(
            group_event="GROUP_C",
            type_event="Connection",
            controller=3,
            sensor=3,
            type_device="PIR",
            sequence=3,
            datetime=datetime.utcnow()
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)

        # Create action event referencing connection
        action = ActionEvent(
            type_event="Action",
            content="Verified connection",
            user="operator",
            from_event=connection.id,
            from_type_event="Connection",
            datetime=datetime.utcnow()
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        # Delete the ActionEvent - should not raise error
        response = client.delete(f"/api/events/actions/{action.id}")

        # Verify deletion succeeded
        assert response.status_code == 200

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.from_type_event == "Connection").delete()
        db.query(ConnectionEvent).filter(ConnectionEvent.group_event == "GROUP_C").delete()
        db.commit()
        db.close()


def test_delete_action_updates_source_updated_at_timestamp():
    """
    Test: Deleting ActionEvent updates the source event's updated_at timestamp

    Expected to FAIL initially (Red phase).
    """
    import time

    db = SessionLocal()
    try:
        # Create a detection event
        detection = DetectionEvent(
            group_event="GROUP_D",
            type_event="Intrusion",
            controller=4,
            sensor=4,
            type_device="PIR",
            sequence=4,
            action_reported="False",
            result="VIBRATION_SENSOR",
            datetime=datetime.utcnow()
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # Create action event
        action = ActionEvent(
            type_event="Action",
            content="Action taken",
            user="admin",
            from_event=detection.id,
            from_type_event="Intrusion",
            datetime=datetime.utcnow()
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        # Set action_reported to "True"
        detection.action_reported = "True"
        db.commit()
        db.refresh(detection)

        # Save original updated_at
        original_updated_at = detection.updated_at

        # Wait a bit to ensure timestamp difference
        time.sleep(0.1)

        # Delete the ActionEvent
        response = client.delete(f"/api/events/actions/{action.id}")

        # Verify deletion succeeded
        assert response.status_code == 200

        # Verify updated_at changed
        db.refresh(detection)
        assert detection.updated_at > original_updated_at, "updated_at should be changed when action_reported is reset"

    finally:
        # Cleanup
        db.query(ActionEvent).delete()
        db.query(DetectionEvent).filter(DetectionEvent.group_event == "GROUP_D").delete()
        db.commit()
        db.close()


def test_delete_nonexistent_action_returns_404():
    """
    Test: Deleting a non-existent ActionEvent should return 404

    Expected to PASS (existing error handling).
    """
    # Try to delete non-existent ActionEvent
    response = client.delete("/api/events/actions/99999")

    # Verify 404 error
    assert response.status_code == 404
    response_data = response.json()
    # Check if it's ApiResponse format or HTTPException format
    if "detail" in response_data:
        assert "not found" in response_data["detail"].lower()
    elif "message" in response_data:
        assert "not found" in response_data["message"].lower()
