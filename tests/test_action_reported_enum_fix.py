"""
Test for action_reported Enum fix

이 테스트는 ActionEvent 생성/삭제 시 원본 이벤트의 action_reported 필드가
올바르게 업데이트되는지 검증합니다.

Bug: 문자열 "True"를 할당하여 SQLAlchemy가 업데이트를 무시함
Fix: EnumTrueFalse.True_ Enum 값을 할당

Phase 22: action_reported Enum 타입 버그 수정
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.event import DetectionEvent, MalfunctionEvent, ActionEvent
from app.dependencies import get_db
from app.utils.enums import EnumTrueFalse, EnumDeviceType, EnumDetectionType, EnumFaultType

client = TestClient(app)


def test_action_creation_updates_detection_action_reported_in_db(test_db):
    """
    ActionEvent 생성 후 DetectionEvent의 action_reported가 DB에서 "True"로 업데이트되는지 검증

    RED Phase: 현재 문자열 "True"를 할당하므로 DB 업데이트 실패 예상
    GREEN Phase: EnumTrueFalse.True_로 수정하면 통과
    """
    # 1. DetectionEvent 생성 (action_reported = "False")
    detection = DetectionEvent(
        group_event="test_group",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.Fence,
        sequence=1,
        action_reported=EnumTrueFalse.False_,
        result=EnumDetectionType.PIR_SENSOR
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # 2. ActionEvent 생성
    action_data = {
        "type_event": "Action",
        "content": "Test action",
        "user": "admin",
        "from_event": detection.id,
        "from_type_event": "Intrusion"
    }
    response = client.post("/api/events/actions", json=action_data)
    assert response.status_code == 201

    # 3. DB에서 DetectionEvent 다시 조회
    test_db.expire(detection)  # 캐시 무효화
    test_db.refresh(detection)

    # 4. action_reported가 EnumTrueFalse.True_인지 검증
    assert detection.action_reported == EnumTrueFalse.True_, \
        f"Expected EnumTrueFalse.True_, got {detection.action_reported}"

    # 5. DB에 실제로 "True" 문자열로 저장되었는지 검증
    from sqlalchemy import text
    result = test_db.execute(
        text("SELECT action_reported FROM detection_events WHERE id = :id"),
        {"id": detection.id}
    ).fetchone()
    assert result[0] == "True", f"Expected 'True' in DB, got '{result[0]}'"


def test_action_creation_updates_malfunction_action_reported_in_db(test_db):
    """
    ActionEvent 생성 후 MalfunctionEvent의 action_reported가 DB에서 "True"로 업데이트되는지 검증

    RED Phase: 현재 문자열 "True"를 할당하므로 DB 업데이트 실패 예상
    GREEN Phase: EnumTrueFalse.True_로 수정하면 통과
    """
    # 1. MalfunctionEvent 생성 (action_reported = "False")
    malfunction = MalfunctionEvent(
        group_event="test_group",
        type_event="Fault",
        controller=1,
        sensor=2,
        type_device=EnumDeviceType.Multi,
        sequence=1,
        action_reported=EnumTrueFalse.False_,
        reason=EnumFaultType.FAULT_CABLE_CUTTING,
        first_start=1,
        first_end=1,
        second_start=0,
        second_end=0
    )
    test_db.add(malfunction)
    test_db.commit()
    test_db.refresh(malfunction)

    # 2. ActionEvent 생성
    action_data = {
        "type_event": "Action",
        "content": "Test malfunction action",
        "user": "admin",
        "from_event": malfunction.id,
        "from_type_event": "Fault"
    }
    response = client.post("/api/events/actions", json=action_data)
    assert response.status_code == 201

    # 3. DB에서 MalfunctionEvent 다시 조회
    test_db.expire(malfunction)
    test_db.refresh(malfunction)

    # 4. action_reported가 EnumTrueFalse.True_인지 검증
    assert malfunction.action_reported == EnumTrueFalse.True_, \
        f"Expected EnumTrueFalse.True_, got {malfunction.action_reported}"

    # 5. DB에 실제로 "True" 문자열로 저장되었는지 검증
    from sqlalchemy import text
    result = test_db.execute(
        text("SELECT action_reported FROM malfunction_events WHERE id = :id"),
        {"id": malfunction.id}
    ).fetchone()
    assert result[0] == "True", f"Expected 'True' in DB, got '{result[0]}'"


def test_get_action_response_has_correct_action_reported(test_db):
    """
    GET /api/events/actions 응답의 from_event.action_reported가 "True"인지 검증

    RED Phase: DB에 "False"로 저장되어 응답도 "False" 예상
    GREEN Phase: Enum 타입 수정 후 "True" 반환
    """
    # 1. DetectionEvent 생성
    detection = DetectionEvent(
        group_event="test_group",
        type_event="Intrusion",
        controller=1,
        sensor=3,
        type_device=EnumDeviceType.Underground,
        sequence=1,
        action_reported=EnumTrueFalse.False_,
        result=EnumDetectionType.THERMAL_SENSOR
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # 2. ActionEvent 생성
    action_data = {
        "type_event": "Action",
        "content": "Test response action",
        "user": "admin",
        "from_event": detection.id,
        "from_type_event": "Intrusion"
    }
    create_response = client.post("/api/events/actions", json=action_data)
    assert create_response.status_code == 201
    action_id = create_response.json()["data"]["id"]

    # 3. GET /api/events/actions 호출
    list_response = client.get("/api/events/actions")
    assert list_response.status_code == 200

    # 4. from_event.action_reported가 "True"인지 검증
    actions = list_response.json()["data"]
    target_action = next((a for a in actions if a["id"] == action_id), None)
    assert target_action is not None, "Created action not found in list"
    assert target_action["from_event"]["action_reported"] == "True", \
        f"Expected 'True', got '{target_action['from_event']['action_reported']}'"


def test_action_deletion_restores_action_reported_to_false_in_db(test_db):
    """
    ActionEvent 삭제 후 DetectionEvent의 action_reported가 DB에서 "False"로 복원되는지 검증

    RED Phase: 현재 문자열 "False"를 할당하므로 DB 업데이트 실패 예상
    GREEN Phase: EnumTrueFalse.False_로 수정하면 통과
    """
    # 1. DetectionEvent 생성
    detection = DetectionEvent(
        group_event="test_group",
        type_event="Intrusion",
        controller=1,
        sensor=4,
        type_device=EnumDeviceType.Fence,
        sequence=1,
        action_reported=EnumTrueFalse.False_,
        result=EnumDetectionType.VIBRATION_SENSOR
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # 2. ActionEvent 생성
    action_data = {
        "type_event": "Action",
        "content": "Test delete action",
        "user": "admin",
        "from_event": detection.id,
        "from_type_event": "Intrusion"
    }
    create_response = client.post("/api/events/actions", json=action_data)
    assert create_response.status_code == 201
    action_id = create_response.json()["data"]["id"]

    # 3. ActionEvent 삭제
    delete_response = client.delete(f"/api/events/actions/{action_id}")
    assert delete_response.status_code == 200

    # 4. DB에서 DetectionEvent 다시 조회
    test_db.expire(detection)
    test_db.refresh(detection)

    # 5. action_reported가 EnumTrueFalse.False_로 복원되었는지 검증
    assert detection.action_reported == EnumTrueFalse.False_, \
        f"Expected EnumTrueFalse.False_, got {detection.action_reported}"

    # 6. DB에 실제로 "False" 문자열로 저장되었는지 검증
    from sqlalchemy import text
    result = test_db.execute(
        text("SELECT action_reported FROM detection_events WHERE id = :id"),
        {"id": detection.id}
    ).fetchone()
    assert result[0] == "False", f"Expected 'False' in DB, got '{result[0]}'"
