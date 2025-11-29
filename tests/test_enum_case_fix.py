"""
Phase 22.6.1: TDD RED Phase - Enum 대소문자 불일치 테스트

Problem:
- Database에 "False", "True" (첫 글자만 대문자) 저장
- SQLAlchemy Enum이 자동으로 uppercase 정규화 시도 → "FALSE", "TRUE"
- EnumTrueFalse 정의는 "False", "True"만 있음
- Result: LookupError

Solution:
- Model에서 native_enum=False 설정으로 정규화 비활성화

Expected: 현재 상태에서 4개 테스트 모두 FAIL (LookupError)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.event import DetectionEvent, MalfunctionEvent, ActionEvent
from app.utils.enums import EnumTrueFalse, EnumDeviceType, EnumDetectionType, EnumFaultType

client = TestClient(app)


def test_enum_case_existing_data_detection(test_db):
    """
    Test: 기존 "False" 데이터를 가진 DetectionEvent 조회 성공

    Given: DetectionEvent with action_reported=EnumTrueFalse.False_ (DB에 "False" 저장됨)
    When: DB에서 DetectionEvent 조회
    Then: LookupError 발생 (현재) → 정상 조회 (수정 후)

    RED Phase: SQLAlchemy가 "False" → "FALSE" 정규화 시도, Enum에 없어서 실패
    GREEN Phase: native_enum=False 설정 후 통과
    """
    # Given: DetectionEvent 생성
    detection = DetectionEvent(
        group_event="test_enum_case_1",
        type_event="Intrusion",
        controller=1,
        sensor=1,
        type_device=EnumDeviceType.Fence,
        sequence=1,
        action_reported="False",  # DB에 "False" 저장
        result=EnumDetectionType.PIR_SENSOR
    )
    test_db.add(detection)
    test_db.commit()
    detection_id = detection.id

    # When: 세션 클리어 후 다시 조회 (DB에서 읽기)
    test_db.expire_all()
    retrieved = test_db.query(DetectionEvent).filter(DetectionEvent.id == detection_id).first()

    # Then: 정상 조회 (LookupError 발생하지 않음)
    assert retrieved is not None, "DetectionEvent should be retrieved"
    assert retrieved.action_reported == "False", \
        f"Expected 'False', got {retrieved.action_reported}"


def test_enum_case_existing_data_malfunction(test_db):
    """
    Test: 기존 "False" 데이터를 가진 MalfunctionEvent 조회 성공

    Given: MalfunctionEvent with action_reported=EnumTrueFalse.False_
    When: DB에서 MalfunctionEvent 조회
    Then: LookupError 발생 (현재) → 정상 조회 (수정 후)
    """
    # Given: MalfunctionEvent 생성
    malfunction = MalfunctionEvent(
        group_event="test_enum_case_2",
        type_event="Fault",
        controller=2,
        sensor=2,
        type_device=EnumDeviceType.Multi,
        sequence=1,
        action_reported="False",  # DB에 "False" 저장
        reason=EnumFaultType.FAULT_CONTROLLER,
        first_start=1,
        first_end=1,
        second_start=0,
        second_end=0
    )
    test_db.add(malfunction)
    test_db.commit()
    malfunction_id = malfunction.id

    # When: 세션 클리어 후 다시 조회
    test_db.expire_all()
    retrieved = test_db.query(MalfunctionEvent).filter(MalfunctionEvent.id == malfunction_id).first()

    # Then: 정상 조회
    assert retrieved is not None, "MalfunctionEvent should be retrieved"
    assert retrieved.action_reported == "False", \
        f"Expected 'False', got {retrieved.action_reported}"


def test_enum_case_after_action_creation(test_db):
    """
    Test: ActionEvent 생성 후 "True" 값 조회 성공

    Given: DetectionEvent with action_reported="False"
    When: ActionEvent 생성 → action_reported="True"로 업데이트
    And: DB에서 DetectionEvent 다시 조회
    Then: LookupError 발생 (현재) → action_reported==EnumTrueFalse.True_ (수정 후)

    이 테스트가 가장 중요: Phase 22.3 수정 후 실제 사용 시나리오
    """
    # Given: DetectionEvent 생성
    detection = DetectionEvent(
        group_event="test_enum_case_3",
        type_event="Intrusion",
        controller=3,
        sensor=3,
        type_device=EnumDeviceType.Underground,
        sequence=1,
        action_reported="False",
        result=EnumDetectionType.THERMAL_SENSOR
    )
    test_db.add(detection)
    test_db.commit()
    test_db.refresh(detection)

    # When: ActionEvent 생성 via API
    action_data = {
        "type_event": "Action",
        "content": "Test enum case action",
        "user": "admin",
        "from_event": detection.id,
        "from_type_event": "Intrusion"
    }
    response = client.post("/api/events/actions", json=action_data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    # And: API를 통해 DetectionEvent 다시 조회 (TestClient는 별도 세션 사용)
    get_response = client.get(f"/api/events/detections/{detection.id}")
    assert get_response.status_code == 200

    # Then: action_reported가 "True"로 업데이트됨
    detection_data = get_response.json()["data"]
    assert detection_data["action_reported"] == "True", \
        f"Expected 'True', got '{detection_data['action_reported']}'"


def test_enum_case_api_list_response(test_db):
    """
    Test: GET /api/events/detections 응답 정상

    Given: DetectionEvent with action_reported=EnumTrueFalse.False_
    When: GET /api/events/detections 호출
    Then: LookupError 발생 (현재) → 정상 응답 (수정 후)

    API endpoint가 DB 조회 시 Enum 변환 실패하는 시나리오
    """
    # Given: DetectionEvent 생성
    detection = DetectionEvent(
        group_event="test_enum_case_4",
        type_event="Intrusion",
        controller=4,
        sensor=4,
        type_device=EnumDeviceType.Fence,
        sequence=1,
        action_reported="False",
        result=EnumDetectionType.VIBRATION_SENSOR
    )
    test_db.add(detection)
    test_db.commit()

    # When: GET /api/events/detections
    response = client.get("/api/events/detections")

    # Then: 200 OK 응답 (LookupError 발생하지 않음)
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}: {response.text}"

    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data

    # 생성한 detection이 응답에 포함되어 있는지 확인
    detections = response_data["data"]
    found = any(d["id"] == detection.id for d in detections)
    assert found, f"Detection {detection.id} should be in response"
