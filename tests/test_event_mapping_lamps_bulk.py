"""
EventMappingLamp Bulk Endpoints Tests (TDD - Red Phase)

PRD: PRD_EventMapping_Bulk.md v1.0 (mirrors PRD_DeviceGroup_BulkUnassign.md v1.0)
Endpoints:
  POST   /api/integrations/event-mappings/{mapping_id}/lamps/bulk
         Body: {"items": [{lamp_id, color, buzzer_time, buzzer_sound, light_mode, ...}, ...]} (1~100)
         Response 3-way: created / skipped(duplicate) / not_found(lamp)
  DELETE /api/integrations/event-mappings/{mapping_id}/lamps/bulk
         Body: {"config_ids": [int, ...]} (1~100)
         Response 3-way: removed / skipped(not_belong) / not_found(absent)
"""
import pytest
from app.models.integration import EventMapping, EventMappingLamp
from app.models.device import Lamp
from app.models.config_change_log import ConfigChangeLog
from app.utils.enums import (
    EnumMappingEventCategory, EnumDeviceType, EnumDeviceStatus,
    EnumConfigActionType, EnumConfigResourceType,
)


# =============================================================================
# Test fixtures (local helpers — conftest.py의 client/test_db 재사용)
# =============================================================================

def _make_event_mapping(test_db, name="EM-lamp-bulk"):
    em = EventMapping(
        name_event=name,
        category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        status=True,
    )
    test_db.add(em)
    test_db.commit()
    test_db.refresh(em)
    return em


def _make_lamp(test_db, num=9001, group=1):
    lp = Lamp(
        number_device=num, group_device=group,
        name_device=f"LAMP-{num:04d}", type_device=EnumDeviceType.Lamp,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address=f"10.2.{group}.{num % 250}", ip_port=80,
    )
    test_db.add(lp)
    test_db.commit()
    test_db.refresh(lp)
    return lp


def _attach_lamp_config(test_db, em, lamp, priority=1):
    """기존에 등록된 EventMappingLamp 매핑 생성 — 벌크 해제 테스트용"""
    eml = EventMappingLamp(
        event_mapping_id=em.id,
        lamp_id=lamp.id,
        is_enable=True,
        priority=priority,
    )
    test_db.add(eml)
    test_db.commit()
    test_db.refresh(eml)
    return eml


# =============================================================================
# TestBulkCreate — POST /api/integrations/event-mappings/{id}/lamps/bulk
# =============================================================================

class TestBulkCreate:
    """POST /api/integrations/event-mappings/{mapping_id}/lamps/bulk 통합 테스트"""

    # 1.1 happy path
    def test_should_create_all_configs_when_all_lamps_valid(self, client, test_db):
        """happy — 모든 lamp_id 유효 → 전부 created"""
        em = _make_event_mapping(test_db, "EM-lamp-happy")
        lp1 = _make_lamp(test_db, num=9011)
        lp2 = _make_lamp(test_db, num=9012)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/lamps/bulk",
            json={"items": [
                {"event_mapping_id": 0, "lamp_id": lp1.id, "color": "Red", "buzzer_time": 5,
                 "buzzer_sound": "PI-PI-PI", "light_mode": "steady",
                 "is_enable": True, "priority": 1},
                {"event_mapping_id": 0, "lamp_id": lp2.id, "color": "Green", "buzzer_time": 3,
                 "buzzer_sound": "PI-PI-PI", "light_mode": "steady",
                 "is_enable": True, "priority": 2},
            ]},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["mapping_id"] == em.id
        assert len(data["created_ids"]) == 2
        assert data["skipped_config_ids"] == []
        assert data["not_found_config_ids"] == []
        rows = test_db.query(EventMappingLamp).filter(
            EventMappingLamp.event_mapping_id == em.id
        ).count()
        assert rows == 2

    # 1.2 partial — 일부 lamp 부재
    def test_should_partial_create_when_some_lamps_not_found(self, client, test_db):
        """partial — 일부 lamp_id 부재 → created + not_found 분리"""
        em = _make_event_mapping(test_db, "EM-lamp-partial")
        lp = _make_lamp(test_db, num=9021)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/lamps/bulk",
            json={"items": [
                {"event_mapping_id": 0, "lamp_id": lp.id, "priority": 1},
                {"event_mapping_id": 0, "lamp_id": 99999, "priority": 1},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["created_ids"]) == 1
        assert data["not_found_config_ids"] == [99999]

    # 1.3 not_found — 모든 lamp 부재
    def test_should_classify_all_not_found_when_all_lamps_absent(self, client, test_db):
        """전부 lamp 부재 → 전부 not_found (404 아님)"""
        em = _make_event_mapping(test_db, "EM-lamp-allnf")

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/lamps/bulk",
            json={"items": [
                {"event_mapping_id": 0, "lamp_id": 77777, "priority": 1},
                {"event_mapping_id": 0, "lamp_id": 88888, "priority": 1},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["created_ids"] == []
        assert set(data["not_found_config_ids"]) == {77777, 88888}

    # 1.4 404 — mapping_id 부재
    def test_should_return_404_when_event_mapping_not_found(self, client, test_db):
        """mapping 부재 → 404"""
        resp = client.post(
            "/api/integrations/event-mappings/99999/lamps/bulk",
            json={"items": [{"event_mapping_id": 0, "lamp_id": 1, "priority": 1}]},
        )
        assert resp.status_code in (404, 422)

    # 1.5 422 — 빈 배열
    def test_should_return_422_when_items_is_empty(self, client, test_db):
        """빈 배열 → 422 (Pydantic min_length=1)"""
        em = _make_event_mapping(test_db, "EM-lamp-empty")

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/lamps/bulk",
            json={"items": []},
        )
        assert resp.status_code == 422

    # 1.6 멱등 — 중복 lamp_id
    def test_should_skip_duplicates_when_lamp_id_repeated(self, client, test_db):
        """중복 lamp_id → 1회만 처리 (멱등, 나머지는 skipped)"""
        em = _make_event_mapping(test_db, "EM-lamp-dup")
        lp = _make_lamp(test_db, num=9041)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/lamps/bulk",
            json={"items": [
                {"event_mapping_id": 0, "lamp_id": lp.id, "priority": 1},
                {"event_mapping_id": 0, "lamp_id": lp.id, "priority": 1},
                {"event_mapping_id": 0, "lamp_id": lp.id, "priority": 1},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["created_ids"]) == 1
        assert len(data["skipped_config_ids"]) == 2
        rows = test_db.query(EventMappingLamp).filter(
            EventMappingLamp.event_mapping_id == em.id
        ).count()
        assert rows == 1

    # 1.7 config_log
    def test_should_log_config_change_with_lamp_ids_when_bulk_created(self, client, test_db):
        """ConfigChangeLog 1건 발행 — after_state에 lamp_ids 포함"""
        em = _make_event_mapping(test_db, "EM-lamp-log")
        lp1 = _make_lamp(test_db, num=9051)
        lp2 = _make_lamp(test_db, num=9052)

        before_log_count = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_LAMP,
            ConfigChangeLog.action == EnumConfigActionType.CREATED,
        ).count()

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/lamps/bulk",
            json={"items": [
                {"event_mapping_id": 0, "lamp_id": lp1.id, "priority": 1},
                {"event_mapping_id": 0, "lamp_id": lp2.id, "priority": 2},
            ]},
        )
        assert resp.status_code == 200

        logs = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_LAMP,
            ConfigChangeLog.action == EnumConfigActionType.CREATED,
        ).all()
        assert len(logs) >= before_log_count + 1
        latest = logs[-1]
        after = latest.after_state
        assert "config_ids" in after
        assert set(after["lamp_ids"]) == {lp1.id, lp2.id}


# =============================================================================
# TestBulkDelete — DELETE /api/integrations/event-mappings/{id}/lamps/bulk
# =============================================================================

class TestBulkDelete:
    """DELETE /api/integrations/event-mappings/{mapping_id}/lamps/bulk 통합 테스트"""

    # 2.1 happy
    def test_should_remove_all_configs_when_all_belong_to_mapping(self, client, test_db):
        """happy — 모든 config_id가 매핑 소속 → 전부 removed"""
        em = _make_event_mapping(test_db, "EM-lamp-del-happy")
        lp1 = _make_lamp(test_db, num=9101)
        lp2 = _make_lamp(test_db, num=9102)
        eml1 = _attach_lamp_config(test_db, em, lp1)
        eml2 = _attach_lamp_config(test_db, em, lp2)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/lamps",
            json={"config_ids": [eml1.id, eml2.id]},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["mapping_id"] == em.id
        assert set(data["removed_config_ids"]) == {eml1.id, eml2.id}
        assert data["skipped_config_ids"] == []
        assert data["not_found_config_ids"] == []
        remaining = test_db.query(EventMappingLamp).filter(
            EventMappingLamp.event_mapping_id == em.id
        ).count()
        assert remaining == 0

    # 2.2 partial — 다른 mapping 소속
    def test_should_partial_remove_when_some_belong_to_other_mapping(self, client, test_db):
        """부분 — 일부 config가 다른 mapping 소속 → removed + skipped 분리"""
        em1 = _make_event_mapping(test_db, "EM-lamp-del-p1")
        em2 = _make_event_mapping(test_db, "EM-lamp-del-p2")
        lp1 = _make_lamp(test_db, num=9111)
        lp2 = _make_lamp(test_db, num=9112)
        eml_own = _attach_lamp_config(test_db, em1, lp1)
        eml_other = _attach_lamp_config(test_db, em2, lp2)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em1.id}/lamps",
            json={"config_ids": [eml_own.id, eml_other.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [eml_own.id]
        assert data["skipped_config_ids"] == [eml_other.id]
        assert data["not_found_config_ids"] == []

    # 2.3 not_found — config_id 부재
    def test_should_classify_not_found_when_config_id_absent(self, client, test_db):
        """config 자체 부재 → not_found_config_ids (404 아님)"""
        em = _make_event_mapping(test_db, "EM-lamp-del-nf")
        lp = _make_lamp(test_db, num=9121)
        eml = _attach_lamp_config(test_db, em, lp)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/lamps",
            json={"config_ids": [eml.id, 99999]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [eml.id]
        assert data["not_found_config_ids"] == [99999]

    # 2.4 404 — mapping_id 부재
    def test_should_return_404_when_event_mapping_not_found(self, client, test_db):
        """mapping 부재 → 404"""
        resp = client.request(
            "DELETE",
            "/api/integrations/event-mappings/99999/lamps/bulk",
            json={"config_ids": [1]},
        )
        assert resp.status_code in (404, 422)
        body = resp.json()
        detail = body.get("detail")
        if isinstance(detail, dict):
            assert detail["success"] is False
            assert "not found" in detail["message"].lower()

    # 2.5 422 — 빈 배열
    def test_should_return_422_when_config_ids_is_empty(self, client, test_db):
        """빈 배열 → 422 (Pydantic min_length=1)"""
        em = _make_event_mapping(test_db, "EM-lamp-del-empty")

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/lamps",
            json={"config_ids": []},
        )
        assert resp.status_code == 422

    # 2.6 멱등 — 중복 ID
    def test_should_be_idempotent_when_config_ids_have_duplicates(self, client, test_db):
        """중복 config_id → 1회 처리 (멱등)"""
        em = _make_event_mapping(test_db, "EM-lamp-del-dup")
        lp = _make_lamp(test_db, num=9131)
        eml = _attach_lamp_config(test_db, em, lp)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/lamps",
            json={"config_ids": [eml.id, eml.id, eml.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [eml.id]
        assert data["skipped_config_ids"] == []
        assert data["not_found_config_ids"] == []

    # 2.7 config_log
    def test_should_log_config_change_with_config_ids_when_bulk_removed(self, client, test_db):
        """ConfigChangeLog 1건 발행 — before_state에 config_ids 포함"""
        em = _make_event_mapping(test_db, "EM-lamp-del-log")
        lp1 = _make_lamp(test_db, num=9141)
        lp2 = _make_lamp(test_db, num=9142)
        eml1 = _attach_lamp_config(test_db, em, lp1)
        eml2 = _attach_lamp_config(test_db, em, lp2)

        before_log_count = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_LAMP,
            ConfigChangeLog.action == EnumConfigActionType.DELETED,
        ).count()

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/lamps",
            json={"config_ids": [eml1.id, eml2.id]},
        )
        assert resp.status_code == 200

        logs = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_LAMP,
            ConfigChangeLog.action == EnumConfigActionType.DELETED,
        ).all()
        assert len(logs) >= before_log_count + 1
        latest = logs[-1]
        before = latest.before_state
        assert "config_ids" in before
        assert set(before["config_ids"]) == {eml1.id, eml2.id}
