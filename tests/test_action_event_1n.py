"""
Test: ActionEvent 1:N 관계 리팩토링
PRD: PRD_ActionEvent_1N_Refactoring.md v2.0

1개의 DetectionEvent/MalfunctionEvent에 대해 N개의 ActionEvent가 가능하도록
비즈니스 로직을 변경하고, action_reported를 카운트 기반으로 관리한다.
"""
import pytest


# ===== Phase 1: 1:N 관계 기본 동작 확인 =====

class TestActionEvent1NBasic:
    """동일 이벤트에 ActionEvent를 여러 개 생성할 수 있는지 확인"""

    def test_create_two_action_events_for_same_detection(self, client, test_controller):
        """
        1.1 TEST: 동일 DetectionEvent에 ActionEvent 2개 생성 가능 확인

        DB 스키마에 UNIQUE 제약조건이 없으므로 from_event_id가 같은
        ActionEvent를 여러 개 만들 수 있어야 한다.
        """
        device_id = test_controller.id

        # 1. DetectionEvent 생성
        detection_resp = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })
        assert detection_resp.status_code == 201
        detection_id = detection_resp.json()["data"]["id"]

        # 2. 첫 번째 ActionEvent 생성
        action1_resp = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "1차 확인 조치",
            "user": "operator1",
            "from_event_id": detection_id,
        })
        assert action1_resp.status_code == 201
        action1_id = action1_resp.json()["data"]["id"]

        # 3. 두 번째 ActionEvent 생성 (동일 from_event_id)
        action2_resp = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "2차 경비 출동",
            "user": "operator2",
            "from_event_id": detection_id,
        })
        assert action2_resp.status_code == 201
        action2_id = action2_resp.json()["data"]["id"]

        # 4. 두 ActionEvent가 서로 다른 ID를 가짐
        assert action1_id != action2_id


# ===== Phase 2: action_reported 카운트 기반 로직 =====

class TestActionReportedCountBased:
    """action_reported가 남은 ActionEvent 수 기반으로 관리되는지 확인"""

    def test_action_reported_true_after_one_action_created(self, client, test_controller):
        """
        2.1 TEST: ActionEvent 1개 생성 → action_reported = "True"
        """
        device_id = test_controller.id

        # DetectionEvent 생성
        det_resp = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })
        detection_id = det_resp.json()["data"]["id"]

        # ActionEvent 생성
        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "확인 조치",
            "user": "operator1",
            "from_event_id": detection_id,
        })

        # DetectionEvent 조회 → action_reported = "True"
        det_get = client.get(f"/api/events/detections/{detection_id}")
        assert det_get.status_code == 200
        assert det_get.json()["data"]["action_reported"] == "True"

    def test_action_reported_stays_true_after_deleting_one_of_two(self, client, test_controller):
        """
        2.3 TEST: ActionEvent 2개 생성 후 1개 삭제 → action_reported = "True" 유지

        현재 코드는 삭제 시 무조건 "False"로 리셋하므로 이 테스트는 FAIL해야 한다.
        PRD v2.0: 남은 ActionEvent가 1개 이상이면 "True" 유지.
        """
        device_id = test_controller.id

        # DetectionEvent 생성
        det_resp = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })
        detection_id = det_resp.json()["data"]["id"]

        # ActionEvent 2개 생성
        a1 = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "1차 조치",
            "user": "operator1",
            "from_event_id": detection_id,
        })
        action1_id = a1.json()["data"]["id"]

        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "2차 조치",
            "user": "operator2",
            "from_event_id": detection_id,
        })

        # 첫 번째 ActionEvent 삭제
        del_resp = client.delete(f"/api/events/actions/{action1_id}")
        assert del_resp.status_code == 200

        # DetectionEvent 조회 → 아직 ActionEvent 1개 남음 → action_reported = "True"
        det_get = client.get(f"/api/events/detections/{detection_id}")
        assert det_get.status_code == 200
        assert det_get.json()["data"]["action_reported"] == "True"

    def test_action_reported_false_after_deleting_last_action(self, client, test_controller):
        """
        2.5 TEST: 마지막 ActionEvent 삭제 → action_reported = "False"
        """
        device_id = test_controller.id

        # DetectionEvent 생성
        det_resp = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })
        detection_id = det_resp.json()["data"]["id"]

        # ActionEvent 1개 생성
        a1 = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "확인 조치",
            "user": "operator1",
            "from_event_id": detection_id,
        })
        action_id = a1.json()["data"]["id"]

        # ActionEvent 삭제 (마지막)
        client.delete(f"/api/events/actions/{action_id}")

        # DetectionEvent 조회 → 남은 ActionEvent 0개 → action_reported = "False"
        det_get = client.get(f"/api/events/detections/{detection_id}")
        assert det_get.status_code == 200
        assert det_get.json()["data"]["action_reported"] == "False"


# ===== Phase 3: 이벤트별 조치 목록 API 변경 =====

class TestEventActionsListApi:
    """GET /{event_id}/actions → 리스트 반환으로 변경"""

    def test_detection_actions_empty_list(self, client, test_controller):
        """
        3.1 TEST: GET /api/events/detections/{id}/actions → 빈 리스트 반환

        조치가 없는 경우 404 대신 빈 리스트(items: [], total: 0)를 반환해야 한다.
        """
        device_id = test_controller.id

        # DetectionEvent 생성
        det_resp = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })
        detection_id = det_resp.json()["data"]["id"]

        # 조치 없이 바로 actions 조회
        resp = client.get(f"/api/events/detections/{detection_id}/actions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data == []

    def test_detection_actions_returns_multiple(self, client, test_controller):
        """
        3.3 TEST: GET /api/events/detections/{id}/actions → N건 반환
        """
        device_id = test_controller.id

        # DetectionEvent 생성
        det_resp = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })
        detection_id = det_resp.json()["data"]["id"]

        # ActionEvent 2개 생성
        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "1차 조치",
            "user": "operator1",
            "from_event_id": detection_id,
        })
        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "2차 조치",
            "user": "operator2",
            "from_event_id": detection_id,
        })

        # actions 조회
        resp = client.get(f"/api/events/detections/{detection_id}/actions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2

    def test_malfunction_actions_empty_list(self, client, test_controller):
        """
        3.5 TEST: GET /api/events/malfunctions/{id}/actions → 빈 리스트 반환
        """
        device_id = test_controller.id

        # MalfunctionEvent 생성
        mal_resp = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": device_id,
            "reason": "FAULT_CONTROLLER",
        })
        assert mal_resp.status_code == 201
        malfunction_id = mal_resp.json()["data"]["id"]

        # 조치 없이 actions 조회
        resp = client.get(f"/api/events/malfunctions/{malfunction_id}/actions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data == []

    def test_malfunction_actions_returns_multiple(self, client, test_controller):
        """
        3.7 TEST: GET /api/events/malfunctions/{id}/actions → N건 반환
        """
        device_id = test_controller.id

        # MalfunctionEvent 생성
        mal_resp = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": device_id,
            "reason": "FAULT_CONTROLLER",
        })
        malfunction_id = mal_resp.json()["data"]["id"]

        # ActionEvent 2개 생성
        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "1차 조치",
            "user": "operator1",
            "from_event_id": malfunction_id,
        })
        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "2차 조치",
            "user": "operator2",
            "from_event_id": malfunction_id,
        })

        # actions 조회
        resp = client.get(f"/api/events/malfunctions/{malfunction_id}/actions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2


# ===== Phase 4: DetectionLog 조치 리스트화 =====

class TestDetectionLogActionsList:
    """DetectionLog의 action 필드가 actions 리스트로 변경되었는지 확인"""

    def test_detection_log_has_actions_list_field(self, client, test_controller):
        """
        4.1 TEST: DetectionLog 응답에 `actions` 필드가 리스트로 반환

        기존 `action` (단건, nullable) → `actions` (리스트) 변경 확인
        """
        device_id = test_controller.id

        # DetectionEvent 생성
        det_resp = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })
        detection_id = det_resp.json()["data"]["id"]

        # ActionEvent 2개 생성
        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "1차 조치",
            "user": "operator1",
            "from_event_id": detection_id,
        })
        client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "2차 조치",
            "user": "operator2",
            "from_event_id": detection_id,
        })

        # DetectionLog 목록 조회
        resp = client.get("/api/detection-logs")
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) > 0

        log_item = items[0]
        # `actions` 필드가 리스트로 존재해야 함 (기존 `action` 단건이 아님)
        assert "actions" in log_item
        assert isinstance(log_item["actions"], list)
        assert len(log_item["actions"]) == 2

    def test_detection_log_no_actions_empty_list(self, client, test_controller):
        """
        4.3 TEST: 조치 없는 DetectionLog → `actions: []`
        """
        device_id = test_controller.id

        # DetectionEvent 생성 (조치 없음)
        client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": device_id,
            "result": "PIR_SENSOR",
        })

        # DetectionLog 목록 조회
        resp = client.get("/api/detection-logs")
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) > 0

        log_item = items[0]
        assert "actions" in log_item
        assert log_item["actions"] == []


# ===== Phase 5: 엣지 케이스 =====

class TestActionEvent1NEdgeCases:
    """엣지 케이스 테스트"""

    def test_connection_event_action_no_action_reported_field(self, client, test_controller):
        """
        5.1 TEST: ConnectionEvent에 ActionEvent 생성 → action_reported 무관

        ConnectionEvent는 action_reported 필드가 없으므로 영향 없이 동작해야 한다.
        """
        device_id = test_controller.id

        # ConnectionEvent 생성
        conn_resp = client.post("/api/events/connections", json={
            "type_event": "Connection",
            "device_id": device_id,
        })
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["data"]["id"]

        # ActionEvent 생성 (ConnectionEvent 대상)
        action_resp = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "연결 확인 조치",
            "user": "operator1",
            "from_event_id": conn_id,
        })
        assert action_resp.status_code == 201

    def test_delete_action_with_null_source_event(self, client, test_controller):
        """
        5.3 TEST: source_event가 NULL인 ActionEvent 삭제 → 에러 없음

        from_event_id가 없는(NULL) ActionEvent를 삭제해도 에러가 발생하지 않아야 한다.
        """
        # from_event_id 없이 ActionEvent 생성
        action_resp = client.post("/api/events/actions", json={
            "type_event": "Action",
            "content": "독립 조치",
            "user": "operator1",
        })
        # from_event_id가 필수인지 확인 — 필수이면 422, 선택이면 201
        if action_resp.status_code == 201:
            action_id = action_resp.json()["data"]["id"]
            del_resp = client.delete(f"/api/events/actions/{action_id}")
            assert del_resp.status_code == 200
