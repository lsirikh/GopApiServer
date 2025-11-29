"""
Phase 20.2 RED Phase: Malfunction Event의 Action Event 조회 테스트

Test Cases:
1. action_reported="True"인 MalfunctionEvent의 ActionEvent 조회 성공
2. action_reported="False"인 MalfunctionEvent 조회 시 404 (Action 없음)
3. 존재하지 않는 MalfunctionEvent 조회 시 404
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.database import SessionLocal
from app.models.event import MalfunctionEvent, ActionEvent

client = TestClient(app)


def test_get_action_for_malfunction_with_action_reported_true():
    """
    Test: action_reported="True"인 MalfunctionEvent의 ActionEvent 조회 성공

    Given: MalfunctionEvent(action_reported="True")와 연관된 ActionEvent 생성
    When: GET /api/events/malfunctions/{id}/action 호출
    Then: 200 OK, ActionEvent 데이터 반환
    """
    db = SessionLocal()
    try:
        # Given: MalfunctionEvent 생성
        malfunction = MalfunctionEvent(
            group_event="GROUP_TEST_MALFUNCTION_1",
            type_event="Fault",
            controller=1,
            sensor=1,
            type_device="Multi",
            sequence=1,
            action_reported="False",  # 초기값
            reason="FAULT_CONTROLLER",
            first_start=1,
            first_end=1,
            second_start=2,
            second_end=2
        )
        db.add(malfunction)
        db.commit()
        db.refresh(malfunction)

        # ActionEvent 생성 (자동으로 action_reported="True"로 업데이트됨)
        action = ActionEvent(
            type_event="Action",
            content="장애 확인 및 유지보수팀 연락",
            user="operator_malfunction",
            from_event=malfunction.id,
            from_type_event="Fault"
        )
        db.add(action)

        # action_reported 수동 업데이트 (실제로는 auto-update되지만 테스트에서는 명시)
        malfunction.action_reported = "True"
        db.commit()
        db.refresh(action)

        # When: GET /api/events/malfunctions/{id}/action
        response = client.get(f"/api/events/malfunctions/{malfunction.id}/action")

        # Then: 200 OK
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["message"] == "Action event retrieved successfully"

        # ActionEvent 데이터 검증
        action_data = response_data["data"]
        assert action_data["id"] == action.id
        assert action_data["type_event"] == "Action"
        assert action_data["content"] == "장애 확인 및 유지보수팀 연락"
        assert action_data["user"] == "operator_malfunction"

        # from_event는 nested object (MalfunctionEventResponse)
        assert isinstance(action_data["from_event"], dict)
        assert action_data["from_event"]["id"] == malfunction.id
        assert action_data["from_event"]["type_event"] == "Fault"
        assert action_data["from_event"]["action_reported"] == "True"

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.id == action.id).delete()
        db.query(MalfunctionEvent).filter(MalfunctionEvent.id == malfunction.id).delete()
        db.commit()
        db.close()


def test_get_action_for_malfunction_with_action_reported_false():
    """
    Test: action_reported="False"인 MalfunctionEvent 조회 시 404 (Action 없음)

    Given: MalfunctionEvent(action_reported="False")만 생성 (ActionEvent 없음)
    When: GET /api/events/malfunctions/{id}/action 호출
    Then: 404 Not Found, 명확한 에러 메시지
    """
    db = SessionLocal()
    try:
        # Given: MalfunctionEvent만 생성 (ActionEvent 없음)
        malfunction = MalfunctionEvent(
            group_event="GROUP_TEST_MALFUNCTION_2",
            type_event="Fault",
            controller=1,
            sensor=2,
            type_device="Fence",
            sequence=2,
            action_reported="False",  # ActionEvent 없음
            reason="FAULT_ETC",
            first_start=3,
            first_end=3,
            second_start=4,
            second_end=4
        )
        db.add(malfunction)
        db.commit()
        db.refresh(malfunction)

        # When: GET /api/events/malfunctions/{id}/action
        response = client.get(f"/api/events/malfunctions/{malfunction.id}/action")

        # Then: 404 Not Found
        assert response.status_code == 404

        response_data = response.json()
        assert response_data["success"] is False

        # 에러 메시지 검증 (한글 또는 영문)
        error_message = response_data.get("message") or response_data.get("detail", "")
        assert "조치 보고가 등록되지 않은" in error_message or "No action event found" in error_message

    finally:
        # Cleanup
        db.query(MalfunctionEvent).filter(MalfunctionEvent.id == malfunction.id).delete()
        db.commit()
        db.close()


def test_get_action_for_nonexistent_malfunction():
    """
    Test: 존재하지 않는 MalfunctionEvent 조회 시 404

    Given: 존재하지 않는 MalfunctionEvent ID
    When: GET /api/events/malfunctions/999999/action 호출
    Then: 404 Not Found, "Malfunction event not found" 메시지
    """
    # When: GET /api/events/malfunctions/999999/action
    response = client.get("/api/events/malfunctions/999999/action")

    # Then: 404 Not Found
    assert response.status_code == 404

    response_data = response.json()
    assert response_data["success"] is False

    # 에러 메시지 검증
    error_message = response_data.get("message") or response_data.get("detail", "")
    assert "Malfunction event not found" in error_message or "not found" in error_message.lower()
