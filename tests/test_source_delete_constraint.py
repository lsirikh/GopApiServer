"""
Test: Source Event Delete Constraint - Cannot delete when action_reported="True"
PRD: Action-Event-Fix-Prd4.md (Phase 18.2)

Prevents deleting DetectionEvent/MalfunctionEvent when ActionEvent exists
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.event import ActionEvent, DetectionEvent, MalfunctionEvent, ConnectionEvent

client = TestClient(app)


def test_cannot_delete_detection_with_action_reported_true():
    """
    Test: DetectionEvent with action_reported="True" cannot be deleted

    Expected to FAIL initially (Red phase).
    """
    db = SessionLocal()
    try:
        # Create a detection event with action_reported="True"
        detection = DetectionEvent(
            group_event="GROUP_A",
            type_event="Intrusion",
            controller=1,
            sensor=1,
            type_device="Controller",
            sequence=1,
            action_reported="True",  # Already has action reported
            result="PIR_SENSOR",
            datetime=datetime.utcnow()
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # Try to delete the DetectionEvent
        response = client.delete(f"/api/events/detections/{detection.id}")

        # Should return 409 Conflict
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"

        # Verify error message (ApiResponse format with "message" field)
        response_data = response.json()
        assert "message" in response_data or "detail" in response_data
        error_msg = response_data.get("message") or response_data.get("detail")
        assert "조치보고" in error_msg or "Action" in error_msg
        assert "먼저" in error_msg or "first" in error_msg.lower()

    finally:
        # Cleanup
        db.query(DetectionEvent).filter(DetectionEvent.group_event == "GROUP_A").delete()
        db.commit()
        db.close()


def test_cannot_delete_malfunction_with_action_reported_true():
    """
    Test: MalfunctionEvent with action_reported="True" cannot be deleted

    Expected to FAIL initially (Red phase).
    """
    db = SessionLocal()
    try:
        # Create a malfunction event with action_reported="True"
        malfunction = MalfunctionEvent(
            group_event="GROUP_B",
            type_event="Fault",
            controller=2,
            sensor=0,
            type_device="Controller",
            sequence=2,
            action_reported="True",  # Already has action reported
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

        # Try to delete the MalfunctionEvent
        response = client.delete(f"/api/events/malfunctions/{malfunction.id}")

        # Should return 409 Conflict
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"

        # Verify error message (ApiResponse format with "message" field)
        response_data = response.json()
        assert "message" in response_data or "detail" in response_data
        error_msg = response_data.get("message") or response_data.get("detail")
        assert "조치보고" in error_msg or "Action" in error_msg

    finally:
        # Cleanup
        db.query(MalfunctionEvent).filter(MalfunctionEvent.group_event == "GROUP_B").delete()
        db.commit()
        db.close()


def test_can_delete_detection_with_action_reported_false():
    """
    Test: DetectionEvent with action_reported="False" CAN be deleted

    Expected to PASS after implementation.
    """
    db = SessionLocal()
    try:
        # Create a detection event with action_reported="False"
        detection = DetectionEvent(
            group_event="GROUP_C",
            type_event="Intrusion",
            controller=3,
            sensor=3,
            type_device="PIR",
            sequence=3,
            action_reported="False",  # No action reported
            result="PIR_SENSOR",
            datetime=datetime.utcnow()
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        detection_id = detection.id

        # Try to delete the DetectionEvent
        response = client.delete(f"/api/events/detections/{detection_id}")

        # Should return 200 Success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify event was actually deleted
        deleted = db.query(DetectionEvent).filter(DetectionEvent.id == detection_id).first()
        assert deleted is None, "DetectionEvent should be deleted"

    finally:
        # Cleanup
        db.query(DetectionEvent).filter(DetectionEvent.group_event == "GROUP_C").delete()
        db.commit()
        db.close()


def test_can_delete_malfunction_with_action_reported_false():
    """
    Test: MalfunctionEvent with action_reported="False" CAN be deleted

    Expected to PASS after implementation.
    """
    db = SessionLocal()
    try:
        # Create a malfunction event with action_reported="False"
        malfunction = MalfunctionEvent(
            group_event="GROUP_D",
            type_event="Fault",
            controller=4,
            sensor=0,
            type_device="Controller",
            sequence=4,
            action_reported="False",  # No action reported
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

        malfunction_id = malfunction.id

        # Try to delete the MalfunctionEvent
        response = client.delete(f"/api/events/malfunctions/{malfunction_id}")

        # Should return 200 Success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify event was actually deleted
        deleted = db.query(MalfunctionEvent).filter(MalfunctionEvent.id == malfunction_id).first()
        assert deleted is None, "MalfunctionEvent should be deleted"

    finally:
        # Cleanup
        db.query(MalfunctionEvent).filter(MalfunctionEvent.group_event == "GROUP_D").delete()
        db.commit()
        db.close()


def test_can_delete_connection_anytime():
    """
    Test: ConnectionEvent can be deleted anytime (no action_reported field)

    Expected to PASS (no constraint on ConnectionEvent).
    """
    db = SessionLocal()
    try:
        # Create a connection event (no action_reported field)
        connection = ConnectionEvent(
            group_event="GROUP_E",
            type_event="Connection",
            controller=5,
            sensor=5,
            type_device="PIR",
            sequence=5,
            datetime=datetime.utcnow()
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)

        connection_id = connection.id

        # Delete the ConnectionEvent - should always succeed
        response = client.delete(f"/api/events/connections/{connection_id}")

        # Should return 200 Success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify event was actually deleted
        deleted = db.query(ConnectionEvent).filter(ConnectionEvent.id == connection_id).first()
        assert deleted is None, "ConnectionEvent should be deleted"

    finally:
        # Cleanup
        db.query(ConnectionEvent).filter(ConnectionEvent.group_event == "GROUP_E").delete()
        db.commit()
        db.close()
