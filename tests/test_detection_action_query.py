"""
Phase 20.1 RED Phase: Detection Event의 Action Event 조회 테스트

Test Cases:
1. action_reported="True"인 DetectionEvent의 ActionEvent 조회 성공
2. action_reported="False"인 DetectionEvent 조회 시 404 (Action 없음)
3. 존재하지 않는 DetectionEvent 조회 시 404
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.database import SessionLocal
from app.models.event import DetectionEvent, ActionEvent

client = TestClient(app)


def test_get_action_for_detection_with_action_reported_true():
    """
    Test: action_reported="True"인 DetectionEvent의 ActionEvent 조회 성공

    Given: DetectionEvent(action_reported="True")와 연관된 ActionEvent 생성
    When: GET /api/events/detections/{id}/action 호출
    Then: 200 OK, ActionEvent 데이터 반환
    """
    db = SessionLocal()
    try:
        # Given: DetectionEvent 생성
        detection = DetectionEvent(
            group_event="GROUP_TEST_QUERY_1",
            type_event="Intrusion",
            controller=1,
            sensor=1,
            type_device="PIR",
            sequence=1,
            action_reported="False",  # 초기값
            result="PIR_SENSOR"
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # ActionEvent 생성 (자동으로 action_reported="True"로 업데이트됨)
        action = ActionEvent(
            type_event="Action",
            content="침입 탐지 확인 및 순찰 출동 요청",
            user="operator_test",
            from_event=detection.id,
            from_type_event="Intrusion"
        )
        db.add(action)

        # action_reported 수동 업데이트 (실제로는 auto-update되지만 테스트에서는 명시)
        detection.action_reported = "True"
        db.commit()
        db.refresh(action)

        # When: GET /api/events/detections/{id}/action
        response = client.get(f"/api/events/detections/{detection.id}/action")

        # Then: 200 OK
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["message"] == "Action event retrieved successfully"

        # ActionEvent 데이터 검증
        action_data = response_data["data"]
        assert action_data["id"] == action.id
        assert action_data["type_event"] == "Action"
        assert action_data["content"] == "침입 탐지 확인 및 순찰 출동 요청"
        assert action_data["user"] == "operator_test"

        # from_event는 nested object (DetectionEventResponse)
        assert isinstance(action_data["from_event"], dict)
        assert action_data["from_event"]["id"] == detection.id
        assert action_data["from_event"]["type_event"] == "Intrusion"
        assert action_data["from_event"]["action_reported"] == "True"

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.id == action.id).delete()
        db.query(DetectionEvent).filter(DetectionEvent.id == detection.id).delete()
        db.commit()
        db.close()


def test_get_action_for_detection_with_action_reported_false():
    """
    Test: action_reported="False"인 DetectionEvent 조회 시 404 (Action 없음)

    Given: DetectionEvent(action_reported="False")만 생성 (ActionEvent 없음)
    When: GET /api/events/detections/{id}/action 호출
    Then: 404 Not Found, 명확한 에러 메시지
    """
    db = SessionLocal()
    try:
        # Given: DetectionEvent만 생성 (ActionEvent 없음)
        detection = DetectionEvent(
            group_event="GROUP_TEST_QUERY_2",
            type_event="Intrusion",
            controller=1,
            sensor=2,
            type_device="Fence",
            sequence=2,
            action_reported="False",  # ActionEvent 없음
            result="THERMAL_SENSOR"
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # When: GET /api/events/detections/{id}/action
        response = client.get(f"/api/events/detections/{detection.id}/action")

        # Then: 404 Not Found
        assert response.status_code == 404

        response_data = response.json()
        assert response_data["success"] is False

        # 에러 메시지 검증 (한글 또는 영문)
        error_message = response_data.get("message") or response_data.get("detail", "")
        assert "조치 보고가 등록되지 않은" in error_message or "No action event found" in error_message

    finally:
        # Cleanup
        db.query(DetectionEvent).filter(DetectionEvent.id == detection.id).delete()
        db.commit()
        db.close()


def test_get_action_for_nonexistent_detection():
    """
    Test: 존재하지 않는 DetectionEvent 조회 시 404

    Given: 존재하지 않는 DetectionEvent ID
    When: GET /api/events/detections/999999/action 호출
    Then: 404 Not Found, "Detection event not found" 메시지
    """
    # When: GET /api/events/detections/999999/action
    response = client.get("/api/events/detections/999999/action")

    # Then: 404 Not Found
    assert response.status_code == 404

    response_data = response.json()
    assert response_data["success"] is False

    # 에러 메시지 검증
    error_message = response_data.get("message") or response_data.get("detail", "")
    assert "Detection event not found" in error_message or "not found" in error_message.lower()
