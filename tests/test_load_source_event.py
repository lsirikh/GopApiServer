"""
Test: load_source_event helper function
PRD: Action-Event-Fix-Prd.md - Section 3.5 Helper Functions
"""
import pytest
from datetime import datetime


def test_load_source_event_detection(test_db):
    """
    Test: load_source_event returns DetectionEvent when given detection event ID

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import DetectionEvent
    from app.routers.actions import load_source_event
    from app.schemas.event import DetectionEventResponse

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

    # Load the event with event_type
    loaded = load_source_event(test_db, detection.id, "detection")

    # Verify it's a DetectionEventResponse
    assert isinstance(loaded, DetectionEventResponse)
    assert loaded.id == detection.id
    assert loaded.type_event == "Intrusion"
    assert loaded.result == "PIR_SENSOR"


def test_load_source_event_malfunction(test_db):
    """
    Test: load_source_event returns MalfunctionEvent when given malfunction event ID

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import MalfunctionEvent
    from app.routers.actions import load_source_event
    from app.schemas.event import MalfunctionEventResponse

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

    # Load the event with event_type
    loaded = load_source_event(test_db, malfunction.id, "malfunction")

    # Verify it's a MalfunctionEventResponse
    assert isinstance(loaded, MalfunctionEventResponse)
    assert loaded.id == malfunction.id
    assert loaded.type_event == "Fault"
    assert loaded.reason == "FAULT_CONTROLLER"


def test_load_source_event_connection(test_db):
    """
    Test: load_source_event returns ConnectionEvent when given connection event ID

    Expected to FAIL initially (Red phase).
    """
    from app.models.event import ConnectionEvent
    from app.routers.actions import load_source_event
    from app.schemas.event import ConnectionEventResponse

    # Create a connection event
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
    test_db.refresh(connection)

    # Load the event with event_type
    loaded = load_source_event(test_db, connection.id, "connection")

    # Verify it's a ConnectionEventResponse
    assert isinstance(loaded, ConnectionEventResponse)
    assert loaded.id == connection.id
    assert loaded.type_event == "Connection"


def test_load_source_event_not_found(test_db):
    """
    Test: load_source_event raises HTTPException when event ID not found

    Expected to FAIL initially (Red phase).
    """
    from app.routers.actions import load_source_event
    from fastapi import HTTPException

    # Try to load non-existent event with event_type
    with pytest.raises(HTTPException) as exc_info:
        load_source_event(test_db, 99999, "detection")

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()
