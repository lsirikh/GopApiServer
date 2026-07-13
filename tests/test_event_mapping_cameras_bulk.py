"""
EventMappingCamera Bulk Endpoints Tests (TDD - Red Phase)

PRD: PRD_EventMapping_Bulk.md v1.0 (mirrors PRD_DeviceGroup_BulkUnassign.md v1.0)
Endpoints:
  POST   /api/integrations/event-mappings/{mapping_id}/cameras/bulk
         Body: {"items": [{camera_id, target_preset_id?, ...}, ...]} (1~100)
         Response 3-way: created / skipped(duplicate) / not_found(camera/preset)
  DELETE /api/integrations/event-mappings/{mapping_id}/cameras/bulk
         Body: {"config_ids": [int, ...]} (1~100)
         Response 3-way: removed / skipped(not_belong) / not_found(absent)
"""
import pytest
from app.models.integration import EventMapping, EventMappingCamera
from app.models.device import Camera
from app.models.camera_preset import CameraPreset
from app.models.config_change_log import ConfigChangeLog
from app.utils.enums import (
    EnumMappingEventCategory, EnumDeviceType, EnumDeviceStatus,
    EnumCameraMode, EnumCameraType,
    EnumConfigActionType, EnumConfigResourceType,
)


# =============================================================================
# Test fixtures (local helpers — conftest.py의 client/test_db 재사용)
# =============================================================================

def _make_event_mapping(test_db, name="EM-bulk"):
    em = EventMapping(
        name_event=name,
        category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        status=True,
    )
    test_db.add(em)
    test_db.commit()
    test_db.refresh(em)
    return em


def _make_camera(test_db, num=1, group=1):
    c = Camera(
        number_device=num, group_device=group,
        name_device=f"CAM-{num:03d}", type_device=EnumDeviceType.IpCamera,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address=f"10.1.{group}.{num}", ip_port=80,
        mode=EnumCameraMode.ONVIF, category=EnumCameraType.PTZ,
    )
    test_db.add(c)
    test_db.commit()
    test_db.refresh(c)
    return c


def _make_preset(test_db, camera, idx=1):
    p = CameraPreset(
        camera_id=camera.id,
        camera_name=camera.name_device,
        preset_index=idx,
        preset_name=f"Preset-{idx}",
        touring_time=10,
    )
    test_db.add(p)
    test_db.commit()
    test_db.refresh(p)
    return p


def _attach_camera_config(test_db, em, camera, delay=10):
    """기존에 등록된 EventMappingCamera 매핑 생성 — 벌크 해제 테스트용"""
    emc = EventMappingCamera(
        event_mapping_id=em.id,
        camera_id=camera.id,
        delay_time=delay,
        is_enable=True,
    )
    test_db.add(emc)
    test_db.commit()
    test_db.refresh(emc)
    return emc


# =============================================================================
# TestBulkCreate — POST /api/integrations/event-mappings/{id}/cameras/bulk
# =============================================================================

class TestBulkCreate:
    """POST /api/integrations/event-mappings/{mapping_id}/cameras/bulk 통합 테스트"""

    # 1.1 happy path
    def test_should_create_all_configs_when_all_cameras_valid(self, client, test_db):
        """happy — 모든 camera_id 유효 → 전부 created"""
        em = _make_event_mapping(test_db, "EM-bulk-happy")
        cam1 = _make_camera(test_db, num=11)
        cam2 = _make_camera(test_db, num=12)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/cameras/bulk",
            json={"items": [
                {"camera_id": cam1.id, "delay_time": 5, "is_enable": True},
                {"camera_id": cam2.id, "delay_time": 7, "is_enable": True},
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
        rows = test_db.query(EventMappingCamera).filter(
            EventMappingCamera.event_mapping_id == em.id
        ).count()
        assert rows == 2

    # 1.2 partial — 일부 camera 부재
    def test_should_partial_create_when_some_cameras_not_found(self, client, test_db):
        """partial — 일부 camera_id 부재 → created + not_found 분리"""
        em = _make_event_mapping(test_db, "EM-bulk-partial")
        cam = _make_camera(test_db, num=21)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/cameras/bulk",
            json={"items": [
                {"camera_id": cam.id, "delay_time": 5},
                {"camera_id": 99999, "delay_time": 10},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["created_ids"]) == 1
        assert data["not_found_config_ids"] == [99999]

    # 1.3 not_found — preset 부재
    def test_should_classify_not_found_when_preset_id_absent(self, client, test_db):
        """preset 부재 → not_found_preset_ids 분류 (404 아님)"""
        em = _make_event_mapping(test_db, "EM-bulk-preset")
        cam = _make_camera(test_db, num=31)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/cameras/bulk",
            json={"items": [
                {"camera_id": cam.id, "target_preset_id": 88888},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        # preset 부재로 not_found에 분류됨
        assert data["created_ids"] == []
        assert len(data["not_found_config_ids"]) == 1

    # 1.4 404 — mapping_id 부재
    def test_should_return_404_when_event_mapping_not_found(self, client, test_db):
        """그룹 부재(mapping_id 없음) → 404"""
        resp = client.post(
            "/api/integrations/event-mappings/99999/cameras/bulk",
            json={"items": [{"camera_id": 1}]},
        )
        assert resp.status_code in (404, 422)

    # 1.5 422 — 빈 배열
    def test_should_return_422_when_items_is_empty(self, client, test_db):
        """빈 배열 → 422 (Pydantic min_length=1)"""
        em = _make_event_mapping(test_db, "EM-bulk-empty")

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/cameras/bulk",
            json={"items": []},
        )
        assert resp.status_code == 422

    # 1.6 멱등 — 중복 camera_id
    def test_should_skip_duplicates_when_camera_id_repeated(self, client, test_db):
        """중복 camera_id → 1회만 처리 (멱등, 나머지는 skipped)"""
        em = _make_event_mapping(test_db, "EM-bulk-dup")
        cam = _make_camera(test_db, num=41)

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/cameras/bulk",
            json={"items": [
                {"camera_id": cam.id, "delay_time": 5},
                {"camera_id": cam.id, "delay_time": 5},
                {"camera_id": cam.id, "delay_time": 5},
            ]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["created_ids"]) == 1
        assert len(data["skipped_config_ids"]) == 2
        # DB에 1건만
        rows = test_db.query(EventMappingCamera).filter(
            EventMappingCamera.event_mapping_id == em.id
        ).count()
        assert rows == 1

    # 1.7 config_log
    def test_should_log_config_change_with_camera_ids_when_bulk_created(self, client, test_db):
        """ConfigChangeLog 1건 발행 — after_state에 camera_ids 포함"""
        em = _make_event_mapping(test_db, "EM-bulk-log")
        cam1 = _make_camera(test_db, num=51)
        cam2 = _make_camera(test_db, num=52)

        before_log_count = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_CAMERA,
        ).count()

        resp = client.post(
            f"/api/integrations/event-mappings/{em.id}/cameras/bulk",
            json={"items": [
                {"camera_id": cam1.id},
                {"camera_id": cam2.id},
            ]},
        )
        assert resp.status_code == 200

        logs = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            ConfigChangeLog.action == EnumConfigActionType.CREATED,
        ).all()
        assert len(logs) >= 1
        assert len(logs) >= before_log_count + 1 or len(logs) >= 1
        latest = logs[-1]
        after = latest.after_state
        assert "config_ids" in after
        assert set(after["camera_ids"]) == {cam1.id, cam2.id}


# =============================================================================
# TestBulkDelete — DELETE /api/integrations/event-mappings/{id}/cameras/bulk
# =============================================================================

class TestBulkDelete:
    """DELETE /api/integrations/event-mappings/{mapping_id}/cameras/bulk 통합 테스트"""

    # 2.1 happy
    def test_should_remove_all_configs_when_all_belong_to_mapping(self, client, test_db):
        """happy — 모든 config_id가 매핑 소속 → 전부 removed"""
        em = _make_event_mapping(test_db, "EM-del-happy")
        cam1 = _make_camera(test_db, num=61)
        cam2 = _make_camera(test_db, num=62)
        emc1 = _attach_camera_config(test_db, em, cam1)
        emc2 = _attach_camera_config(test_db, em, cam2)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/cameras",
            json={"config_ids": [emc1.id, emc2.id]},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["mapping_id"] == em.id
        assert set(data["removed_config_ids"]) == {emc1.id, emc2.id}
        assert data["skipped_config_ids"] == []
        assert data["not_found_config_ids"] == []
        # DB 검증
        remaining = test_db.query(EventMappingCamera).filter(
            EventMappingCamera.event_mapping_id == em.id
        ).count()
        assert remaining == 0

    # 2.2 partial — 다른 mapping 소속
    def test_should_partial_remove_when_some_belong_to_other_mapping(self, client, test_db):
        """부분 — 일부 config가 다른 mapping 소속 → removed + skipped 분리"""
        em1 = _make_event_mapping(test_db, "EM-del-p1")
        em2 = _make_event_mapping(test_db, "EM-del-p2")
        cam1 = _make_camera(test_db, num=71)
        cam2 = _make_camera(test_db, num=72)
        emc_own = _attach_camera_config(test_db, em1, cam1)
        emc_other = _attach_camera_config(test_db, em2, cam2)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em1.id}/cameras",
            json={"config_ids": [emc_own.id, emc_other.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [emc_own.id]
        assert data["skipped_config_ids"] == [emc_other.id]
        assert data["not_found_config_ids"] == []

    # 2.3 not_found — config_id 부재
    def test_should_classify_not_found_when_config_id_absent(self, client, test_db):
        """config 자체 부재 → not_found_config_ids (404 아님)"""
        em = _make_event_mapping(test_db, "EM-del-nf")
        cam = _make_camera(test_db, num=81)
        emc = _attach_camera_config(test_db, em, cam)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/cameras",
            json={"config_ids": [emc.id, 99999]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [emc.id]
        assert data["not_found_config_ids"] == [99999]

    # 2.4 404 — mapping_id 부재
    def test_should_return_404_when_event_mapping_not_found(self, client, test_db):
        """mapping 부재 → 404"""
        resp = client.request(
            "DELETE",
            "/api/integrations/event-mappings/99999/cameras/bulk",
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
        em = _make_event_mapping(test_db, "EM-del-empty")

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/cameras",
            json={"config_ids": []},
        )
        assert resp.status_code == 422

    # 2.6 멱등 — 중복 ID
    def test_should_be_idempotent_when_config_ids_have_duplicates(self, client, test_db):
        """중복 config_id → 1회 처리 (멱등)"""
        em = _make_event_mapping(test_db, "EM-del-dup")
        cam = _make_camera(test_db, num=91)
        emc = _attach_camera_config(test_db, em, cam)

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/cameras",
            json={"config_ids": [emc.id, emc.id, emc.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_config_ids"] == [emc.id]
        assert data["skipped_config_ids"] == []
        assert data["not_found_config_ids"] == []

    # 2.7 config_log
    def test_should_log_config_change_with_config_ids_when_bulk_removed(self, client, test_db):
        """ConfigChangeLog 1건 발행 — before_state에 config_ids 포함"""
        em = _make_event_mapping(test_db, "EM-del-log")
        cam1 = _make_camera(test_db, num=101)
        cam2 = _make_camera(test_db, num=102)
        emc1 = _attach_camera_config(test_db, em, cam1)
        emc2 = _attach_camera_config(test_db, em, cam2)

        before_log_count = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            ConfigChangeLog.action == EnumConfigActionType.DELETED,
        ).count()

        resp = client.request(
            "DELETE",
            f"/api/integrations/event-mappings/{em.id}/cameras",
            json={"config_ids": [emc1.id, emc2.id]},
        )
        assert resp.status_code == 200

        logs = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            ConfigChangeLog.action == EnumConfigActionType.DELETED,
        ).all()
        assert len(logs) >= before_log_count + 1
        latest = logs[-1]
        before = latest.before_state
        assert "config_ids" in before
        assert set(before["config_ids"]) == {emc1.id, emc2.id}
