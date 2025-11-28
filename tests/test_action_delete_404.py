"""
Phase 23.1: TDD RED Phase - ActionEvent 삭제 404 검증 강화

Test Cases:
1. 전혀 존재하지 않은 ID (999999) 삭제 시 404 반환
2. ActionEvent 생성 → 삭제 → 재삭제 시 404 반환
3. 여러 ActionEvent 중 특정 ID만 삭제 후 다른 ID 삭제 가능 확인

Goal: 엣지 케이스 커버리지 강화
Expected: 모든 테스트 PASS (코드는 이미 올바르게 구현되어 있음)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.event import DetectionEvent, ActionEvent
from app.utils.enums import EnumDeviceType, EnumDetectionType

client = TestClient(app)


def test_delete_nonexistent_action_id_returns_404():
    """
    Test: 전혀 존재하지 않은 큰 ID (999999) 삭제 시 404 반환

    Given: ActionEvent ID=999999가 존재하지 않음
    When: DELETE /api/events/actions/999999 호출
    Then: 404 Not Found, 명확한 에러 메시지
    """
    # When: DELETE nonexistent ActionEvent
    response = client.delete("/api/events/actions/999999")

    # Then: 404 Not Found
    assert response.status_code == 404

    response_data = response.json()
    assert response_data["success"] is False

    # 에러 메시지 검증
    error_message = response_data.get("message") or response_data.get("detail", "")
    assert "Action event with id 999999 not found" in error_message or "not found" in error_message.lower()


def test_delete_already_deleted_action_returns_404():
    """
    Test: ActionEvent 생성 → 삭제 → 재삭제 시 404 반환

    Given: ActionEvent 생성 및 삭제 완료
    When: 동일 ID로 재삭제 시도
    Then: 404 Not Found (이미 삭제됨)
    """
    db = SessionLocal()
    try:
        # Given: DetectionEvent 생성
        detection = DetectionEvent(
            group_event="GROUP_DELETE_404_1",
            type_event="Intrusion",
            controller=201,
            sensor=201,
            type_device=EnumDeviceType.Fence,
            sequence=1,
            action_reported="False",
            result=EnumDetectionType.PIR_SENSOR
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # ActionEvent 생성
        action_data = {
            "type_event": "Action",
            "content": "First delete test",
            "user": "operator_delete_404",
            "from_event": detection.id,
            "from_type_event": "Intrusion"
        }
        create_response = client.post("/api/events/actions", json=action_data)
        assert create_response.status_code == 201

        action_id = create_response.json()["data"]["id"]

        # When: 첫 번째 삭제 (성공해야 함)
        delete_response1 = client.delete(f"/api/events/actions/{action_id}")
        assert delete_response1.status_code == 200
        assert delete_response1.json()["success"] is True

        # And: 동일 ID로 재삭제 시도
        delete_response2 = client.delete(f"/api/events/actions/{action_id}")

        # Then: 404 Not Found
        assert delete_response2.status_code == 404

        response_data = delete_response2.json()
        assert response_data["success"] is False

        error_message = response_data.get("message") or response_data.get("detail", "")
        assert "not found" in error_message.lower()

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.user == "operator_delete_404").delete()
        db.query(DetectionEvent).filter(DetectionEvent.group_event == "GROUP_DELETE_404_1").delete()
        db.commit()
        db.close()


def test_delete_specific_action_among_multiple():
    """
    Test: 여러 ActionEvent 중 특정 ID만 삭제하고 나머지는 유지

    Given: 2개의 DetectionEvent와 2개의 ActionEvent 생성
    When: ActionEvent 1 삭제
    Then: ActionEvent 1은 404, ActionEvent 2는 여전히 존재
    """
    db = SessionLocal()
    try:
        # Given: DetectionEvent 2개 생성
        detection1 = DetectionEvent(
            group_event="GROUP_DELETE_404_2A",
            type_event="Intrusion",
            controller=202,
            sensor=202,
            type_device=EnumDeviceType.Underground,
            sequence=1,
            action_reported="False",
            result=EnumDetectionType.THERMAL_SENSOR
        )
        detection2 = DetectionEvent(
            group_event="GROUP_DELETE_404_2B",
            type_event="Intrusion",
            controller=203,
            sensor=203,
            type_device=EnumDeviceType.Fence,
            sequence=1,
            action_reported="False",
            result=EnumDetectionType.VIBRATION_SENSOR
        )
        db.add(detection1)
        db.add(detection2)
        db.commit()
        db.refresh(detection1)
        db.refresh(detection2)

        # ActionEvent 1 생성
        action_data1 = {
            "type_event": "Action",
            "content": "Action for detection 1",
            "user": "user_multi_delete_1",
            "from_event": detection1.id,
            "from_type_event": "Intrusion"
        }
        response1 = client.post("/api/events/actions", json=action_data1)
        assert response1.status_code == 201
        action_id1 = response1.json()["data"]["id"]

        # ActionEvent 2 생성
        action_data2 = {
            "type_event": "Action",
            "content": "Action for detection 2",
            "user": "user_multi_delete_2",
            "from_event": detection2.id,
            "from_type_event": "Intrusion"
        }
        response2 = client.post("/api/events/actions", json=action_data2)
        assert response2.status_code == 201
        action_id2 = response2.json()["data"]["id"]

        # When: ActionEvent 1 삭제
        delete_response = client.delete(f"/api/events/actions/{action_id1}")
        assert delete_response.status_code == 200

        # Then: ActionEvent 1 재조회 시 404
        get_response1 = client.get(f"/api/events/actions/{action_id1}")
        assert get_response1.status_code == 404

        # And: ActionEvent 2는 여전히 존재
        get_response2 = client.get(f"/api/events/actions/{action_id2}")
        assert get_response2.status_code == 200
        assert get_response2.json()["data"]["id"] == action_id2

        # And: ActionEvent 2도 삭제 가능
        delete_response2 = client.delete(f"/api/events/actions/{action_id2}")
        assert delete_response2.status_code == 200

    finally:
        # Cleanup
        db.query(ActionEvent).filter(ActionEvent.user.in_(["user_multi_delete_1", "user_multi_delete_2"])).delete(synchronize_session=False)
        db.query(DetectionEvent).filter(DetectionEvent.group_event.in_(["GROUP_DELETE_404_2A", "GROUP_DELETE_404_2B"])).delete(synchronize_session=False)
        db.commit()
        db.close()
