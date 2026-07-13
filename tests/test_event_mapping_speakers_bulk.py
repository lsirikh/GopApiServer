"""
EventMappingSpeaker Bulk Endpoints Tests (TDD - Red Phase)

PRD: PRD_EventMapping_Bulk.md v1.0 (mirrors PRD_DeviceGroup_BulkUnassign.md v1.0)
Endpoints:
  POST   /api/integrations/event-mappings/{mapping_id}/speakers/bulk
         Body: {"items": [{speaker_id, file_group_id?, repeat_count, is_enable, ...}, ...]} (1~100)
         Response 3-way: created / skipped(duplicate) / not_found(speaker/file_group)
  DELETE /api/integrations/event-mappings/{mapping_id}/speakers/bulk
         Body: {"config_ids": [int, ...]} (1~100)
         Response 3-way: removed / skipped(not_belong) / not_found(absent)
"""
import pytest
from app.models.integration import EventMapping, EventMappingSpeaker
from app.models.device import Speaker
from app.models.config_change_log import ConfigChangeLog
from app.utils.enums import (
    EnumMappingEventCategory, EnumDeviceType, EnumDeviceStatus,
    EnumSpeakerType,
    EnumConfigActionType, EnumConfigResourceType,
)


# =============================================================================
# Test fixtures (local helpers — conftest.py의 client/test_db/test_file_group 재사용)
# =============================================================================

def _make_event_mapping(test_db, name="EM-spk-bulk"):
    em = EventMapping(
        name_event=name,
        category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        status=True,
    )
    test_db.add(em)
    test_db.commit()
    test_db.refresh(em)
    return em


def _make_speaker(test_db, num=2401, group=1):
    s = Speaker(
        number_device=num, group_device=group,
        name_device=f"SPK-{num:04d}", type_device=EnumDeviceType.IpSpeaker,
        status=EnumDeviceStatus.ACTIVATED,
        speaker_type=EnumSpeakerType.NORMAL,
    )
    test_db.add(s)
    test_db.commit()
    test_db.refresh(s)
    return s


def _attach_speaker_config(test_db, em, speaker, repeat=1):
    """기존에 등록된 EventMappingSpeaker 매핑 생성 — 벌크 해제 테스트용"""
    ems = EventMappingSpeaker(
        event_mapping_id=em.id,
        speaker_id=speaker.id,
        repeat_count=repeat,
        is_enable=True,
    )
    test_db.add(ems)
    test_db.commit()
    test_db.refresh(ems)
    return ems


# =============================================================================
# TestBulkCreate — POST /api/integrations/event-mappings/{id}/speakers/bulk
# =============================================================================

class TestBulkCreate:
    """POST /api/integrations/event-mappings/{mapping_id}/speakers/bulk 통합 테스트"""

    # 1.1 happy path
    def test_should_create_all_configs_when_all_speakers_valid(self, client, test_db):
        """happy — 모든 speaker_id 유효 → 전부 created"""
        em = _make_event_mapping(test_db, "EM-spk-happy")
        spk1 = _make_speaker(test_db, num=2411)
        spk2 = _make_speaker(test_db, num=2412)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/speakers/bulk",
            json={"items": [
                {"speaker_id": spk1.id, "repeat_count": 1, "is_enable": True},
                {"speaker_id": spk2.id, "repeat_count": 2, "is_enable": True},
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
        # DB 검증
        rows = test_db.query(EventMappingSpeaker).filter(
            EventMappingSpeaker.event_mapping_id == em.id
        ).count()
        assert rows == 2

    # 1.2 partial — 일부 speaker 부재
    def test_should_partial_create_when_some_speakers_not_found(self, client, test_db):
        """partial — 일부 speaker_id 부재 → created + not_found 분리"""
        em = _make_event_mapping(test_db, "EM-spk-partial")
        spk = _make_speaker(test_db, num=2421)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/speakers/bulk",
            json={"items": [
                {"speaker_id": spk.id, "repeat_count": 1, "is_enable": True},
                {"speaker_id": 99999, "repeat_count": 1, "is_enable": True},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["created_ids"]) == 1
        assert data["not_found_config_ids"] == [99999]

    # 1.3 not_found — file_group 부재
    def test_should_classify_not_found_when_file_group_id_absent(self, client, test_db):
        """file_group 부재 → not_found 분류 (404 아님)"""
        em = _make_event_mapping(test_db, "EM-spk-fg")
        spk = _make_speaker(test_db, num=2431)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/speakers/bulk",
            json={"items": [
                {"speaker_id": spk.id, "file_group_id": 88888,
                 "repeat_count": 1, "is_enable": True},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        # file_group 부재로 not_found에 분류됨
        assert data["created_ids"] == []
        assert len(data["not_found_config_ids"]) == 1

    # 1.4 404 — mapping_id 부재
    def test_should_return_404_when_event_mapping_not_found(self, client, test_db):
        """mapping 부재 → 404"""
        resp = client.post(
            "/api/integrations/event-mappings/99999/speakers/bulk",
            json={"items": [{"speaker_id": 1, "repeat_count": 1, "is_enable": True}]},
        )
        assert resp.status_code in (404, 422)

    # 1.5 422 — 빈 배열
    def test_should_return_422_when_items_is_empty(self, client, test_db):
        """빈 배열 → 422 (Pydantic min_length=1)"""
        em = _make_event_mapping(test_db, "EM-spk-empty")

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/speakers/bulk",
            json={"items": []},
        )
        assert resp.status_code == 422

    # 1.6 멱등 — 중복 speaker_id
    def test_should_skip_duplicates_when_speaker_id_repeated(self, client, test_db):
        """중복 speaker_id → 1회만 처리 (멱등, 나머지는 skipped)"""
        em = _make_event_mapping(test_db, "EM-spk-dup")
        spk = _make_speaker(test_db, num=2441)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/speakers/bulk",
            json={"items": [
                {"speaker_id": spk.id, "repeat_count": 1, "is_enable": True},
                {"speaker_id": spk.id, "repeat_count": 1, "is_enable": True},
                {"speaker_id": spk.id, "repeat_count": 1, "is_enable": True},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["created_ids"]) == 1
        assert len(data["skipped_config_ids"]) == 2
        rows = test_db.query(EventMappingSpeaker).filter(
            EventMappingSpeaker.event_mapping_id == em.id
        ).count()
        assert rows == 1

    # 1.7 config_log
    def test_should_log_config_change_with_speaker_ids_when_bulk_created(self, client, test_db):
        """ConfigChangeLog 1건 발행 — after_state에 speaker_ids 포함"""
        em = _make_event_mapping(test_db, "EM-spk-log")
        spk1 = _make_speaker(test_db, num=2451)
        spk2 = _make_speaker(test_db, num=2452)

        before_log_count = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            ConfigChangeLog.action == EnumConfigActionType.CREATED,
        ).count()

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/speakers/bulk",
            json={"items": [
                {"speaker_id": spk1.id, "repeat_count": 1, "is_enable": True},
                {"speaker_id": spk2.id, "repeat_count": 1, "is_enable": True},
            ]},
        )
        assert resp.status_code == 200

        logs = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            ConfigChangeLog.action == EnumConfigActionType.CREATED,
        ).all()
        assert len(logs) >= before_log_count + 1
        latest = logs[-1]
        after = latest.after_state
        assert "config_ids" in after
        assert set(after["speaker_ids"]) == {spk1.id, spk2.id}


# =============================================================================
# TestBulkDelete — DELETE /api/integrations/event-mappings/{id}/speakers/bulk
# =============================================================================

class TestBulkDelete:
    """DELETE /api/integrations/event-mappings/{mapping_id}/speakers/bulk 통합 테스트"""

    # 2.1 happy
    def test_should_remove_all_configs_when_all_belong_to_mapping(self, client, test_db):
        """happy — 모든 config_id가 매핑 소속 → 전부 removed"""
        em = _make_event_mapping(test_db, "EM-spk-del-happy")
        spk1 = _make_speaker(test_db, num=2501)
        spk2 = _make_speaker(test_db, num=2502)
        ems1 = _attach_speaker_config(test_db, em, spk1)
        ems2 = _attach_speaker_config(test_db, em, spk2)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/speakers",
            json={"config_ids": [ems1.id, ems2.id]},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["mapping_id"] == em.id
        assert set(data["removed_config_ids"]) == {ems1.id, ems2.id}
        assert data["skipped_config_ids"] == []
        assert data["not_found_config_ids"] == []
        remaining = test_db.query(EventMappingSpeaker).filter(
            EventMappingSpeaker.event_mapping_id == em.id
        ).count()
        assert remaining == 0

    # 2.2 partial — 다른 mapping 소속
    def test_should_partial_remove_when_some_belong_to_other_mapping(self, client, test_db):
        """부분 — 일부 config가 다른 mapping 소속 → removed + skipped 분리"""
        em1 = _make_event_mapping(test_db, "EM-spk-del-p1")
        em2 = _make_event_mapping(test_db, "EM-spk-del-p2")
        spk1 = _make_speaker(test_db, num=2511)
        spk2 = _make_speaker(test_db, num=2512)
        ems_own = _attach_speaker_config(test_db, em1, spk1)
        ems_other = _attach_speaker_config(test_db, em2, spk2)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em1.id}/speakers",
            json={"config_ids": [ems_own.id, ems_other.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [ems_own.id]
        assert data["skipped_config_ids"] == [ems_other.id]
        assert data["not_found_config_ids"] == []

    # 2.3 not_found — config_id 부재
    def test_should_classify_not_found_when_config_id_absent(self, client, test_db):
        """config 자체 부재 → not_found_config_ids (404 아님)"""
        em = _make_event_mapping(test_db, "EM-spk-del-nf")
        spk = _make_speaker(test_db, num=2521)
        ems = _attach_speaker_config(test_db, em, spk)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/speakers",
            json={"config_ids": [ems.id, 99999]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [ems.id]
        assert data["not_found_config_ids"] == [99999]

    # 2.4 404 — mapping_id 부재
    def test_should_return_404_when_event_mapping_not_found(self, client, test_db):
        """mapping 부재 → 404"""
        resp = client.request(
            "DELETE",
            "/api/integrations/event-mappings/99999/speakers/bulk",
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
        em = _make_event_mapping(test_db, "EM-spk-del-empty")

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/speakers",
            json={"config_ids": []},
        )
        assert resp.status_code == 422

    # 2.6 멱등 — 중복 ID
    def test_should_be_idempotent_when_config_ids_have_duplicates(self, client, test_db):
        """중복 config_id → 1회 처리 (멱등)"""
        em = _make_event_mapping(test_db, "EM-spk-del-dup")
        spk = _make_speaker(test_db, num=2531)
        ems = _attach_speaker_config(test_db, em, spk)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/speakers",
            json={"config_ids": [ems.id, ems.id, ems.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [ems.id]
        assert data["skipped_config_ids"] == []
        assert data["not_found_config_ids"] == []

    # 2.7 config_log
    def test_should_log_config_change_with_config_ids_when_bulk_removed(self, client, test_db):
        """ConfigChangeLog 1건 발행 — before_state에 config_ids 포함"""
        em = _make_event_mapping(test_db, "EM-spk-del-log")
        spk1 = _make_speaker(test_db, num=2541)
        spk2 = _make_speaker(test_db, num=2542)
        ems1 = _attach_speaker_config(test_db, em, spk1)
        ems2 = _attach_speaker_config(test_db, em, spk2)

        before_log_count = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            ConfigChangeLog.action == EnumConfigActionType.DELETED,
        ).count()

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/speakers",
            json={"config_ids": [ems1.id, ems2.id]},
        )
        assert resp.status_code == 200

        logs = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            ConfigChangeLog.action == EnumConfigActionType.DELETED,
        ).all()
        assert len(logs) >= before_log_count + 1
        latest = logs[-1]
        before = latest.before_state
        assert "config_ids" in before
        assert set(before["config_ids"]) == {ems1.id, ems2.id}
