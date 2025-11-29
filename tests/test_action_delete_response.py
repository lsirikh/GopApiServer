"""
Test: ActionEvent DELETE Response Standardization
PRD: Event-Delete-Response-Prd.md (Phase 19.1)

DELETE 응답에서 data 필드가 null인지 검증
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.event import ActionEvent, DetectionEvent

client = TestClient(app)


def test_action_delete_response_data_is_null():
    """
    Test: ActionEvent DELETE 성공 시 data 필드가 null

    Expected to FAIL initially (Red phase).
    """
    db = SessionLocal()
    try:
        # Create a detection event (source event for action)
        detection = DetectionEvent(
            group_event="GROUP_DELETE_TEST",
            type_event="Intrusion",
            controller=1,
            sensor=1,
            type_device="PIR",
            sequence=1,
            action_reported="False",
            result="PIR_SENSOR",
            datetime=datetime.utcnow()
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # Create action event
        action = ActionEvent(
            type_event="Action",
            content="Test action for delete response",
            user="admin",
            from_event=detection.id,
            from_type_event="Intrusion",
            datetime=datetime.utcnow()
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        action_id = action.id

        # Delete the ActionEvent
        response = client.delete(f"/api/events/actions/{action_id}")

        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        response_data = response.json()

        # Main assertion: data field should be null
        assert response_data["data"] is None, f"Expected data to be null, got {response_data['data']}"

        # Additional assertions
        assert response_data["success"] is True, "Expected success to be true"
        assert "deleted successfully" in response_data["message"].lower(), f"Expected 'deleted successfully' in message, got {response_data['message']}"

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.from_type_event == "Intrusion").delete()
        db.query(DetectionEvent).filter(DetectionEvent.group_event == "GROUP_DELETE_TEST").delete()
        db.commit()
        db.close()
