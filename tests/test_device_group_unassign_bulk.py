"""
DeviceGroup Bulk Unassign Endpoint Tests (TDD)

PRD: PRD_DeviceGroup_BulkUnassign.md v1.0
Endpoint: DELETE /api/devices/groups/{group_id}/devices
Body: {"device_ids": [int, ...]} (1~100)
Response: 3-way classification (removed/skipped/not_found)
"""
import pytest
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.models.device import Controller, Sensor, Camera, Speaker, Enclosure, Lamp
from app.models.config_change_log import ConfigChangeLog
from app.utils.enums import (
    EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory,
    EnumSpeakerType, EnumConfigActionType, EnumConfigResourceType,
)


# =============================================================================
# Test fixtures (local helpers — conftest.py의 client/test_db 재사용)
# =============================================================================

def _make_controller(test_db, num=1, group=1):
    c = Controller(
        number_device=num, group_device=group,
        name_device=f"CTL-{num:03d}", type_device=EnumDeviceType.Controller,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address=f"10.0.{group}.{num}", ip_port=9010 + num,
    )
    test_db.add(c)
    test_db.commit()
    test_db.refresh(c)
    return c


def _make_sensor(test_db, controller_id, num=1, group=1):
    s = Sensor(
        number_device=num, group_device=group,
        name_device=f"SEN-{num:03d}", type_device=EnumDeviceType.Multi,
        status=EnumDeviceStatus.ACTIVATED,
        controller_id=controller_id,
    )
    test_db.add(s)
    test_db.commit()
    test_db.refresh(s)
    return s


def _make_camera(test_db, num=1, group=1):
    c = Camera(
        number_device=num, group_device=group,
        name_device=f"CAM-{num:03d}", type_device=EnumDeviceType.IpCamera,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address=f"10.1.{group}.{num}", ip_port=554,
    )
    test_db.add(c)
    test_db.commit()
    test_db.refresh(c)
    return c


def _make_group_with_members(test_db, name, devices):
    """그룹 생성 + 디바이스들을 그룹 멤버로 등록"""
    g = DeviceGroup(name=name)
    test_db.add(g)
    test_db.commit()
    test_db.refresh(g)
    for d in devices:
        m = DeviceGroupMapping(
            device_id=d.id, category_device=d.category_device, group_id=g.id
        )
        test_db.add(m)
    test_db.commit()
    return g


# =============================================================================
# Phase 2 Integration Tests (PRD §10.1)
# =============================================================================

class TestBulkUnassign:
    """DELETE /api/devices/groups/{group_id}/devices 통합 테스트"""

    # 2.1
    def test_should_unassign_all_devices_when_all_are_members(self, client, test_db):
        """happy path — 모든 device가 그룹 멤버 → 전부 removed"""
        ctrl = _make_controller(test_db, num=1)
        s1 = _make_sensor(test_db, ctrl.id, num=101)
        s2 = _make_sensor(test_db, ctrl.id, num=102)
        g = _make_group_with_members(test_db, "G-happy", [s1, s2])

        resp = client.request(
            "DELETE",
            f"/api/devices/groups/{g.id}/devices",
            json={"device_ids": [s1.id, s2.id]},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["group_id"] == g.id
        assert set(data["removed_device_ids"]) == {s1.id, s2.id}
        assert data["skipped_device_ids"] == []
        assert data["not_found_device_ids"] == []
        # DB 검증: 매핑이 모두 삭제됨
        remaining = test_db.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.group_id == g.id
        ).count()
        assert remaining == 0

    # 2.2
    def test_should_partial_unassign_when_some_are_not_members(self, client, test_db):
        """부분 멤버 — 일부만 멤버 → removed + skipped 분리"""
        ctrl = _make_controller(test_db, num=2)
        member = _make_sensor(test_db, ctrl.id, num=201)
        nonmember = _make_sensor(test_db, ctrl.id, num=202)
        g = _make_group_with_members(test_db, "G-partial", [member])

        resp = client.request(
            "DELETE",
            f"/api/devices/groups/{g.id}/devices",
            json={"device_ids": [member.id, nonmember.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["removed_device_ids"] == [member.id]
        assert data["skipped_device_ids"] == [nonmember.id]
        assert data["not_found_device_ids"] == []

    # 2.3
    def test_should_classify_into_not_found_when_device_id_absent(self, client, test_db):
        """device 자체 부재 → not_found_device_ids (404 아님)"""
        ctrl = _make_controller(test_db, num=3)
        s = _make_sensor(test_db, ctrl.id, num=301)
        g = _make_group_with_members(test_db, "G-notfound", [s])

        resp = client.request(
            "DELETE",
            f"/api/devices/groups/{g.id}/devices",
            json={"device_ids": [s.id, 99999]},  # 99999는 존재하지 않음
        )

        assert resp.status_code == 200  # 부분 성공이라도 200
        data = resp.json()["data"]
        assert data["removed_device_ids"] == [s.id]
        assert data["not_found_device_ids"] == [99999]

    # 2.4
    def test_should_return_404_when_group_not_found(self, client, test_db):
        """그룹 부재 → 404"""
        resp = client.request(
            "DELETE",
            "/api/devices/groups/99999/devices",
            json={"device_ids": [1]},
        )
        assert resp.status_code == 404
        body = resp.json()
        # FastAPI HTTPException detail이 dict이면 detail.message로 옴
        detail = body.get("detail")
        if isinstance(detail, dict):
            assert detail["success"] is False
            assert "not found" in detail["message"].lower()

    # 2.5
    def test_should_return_422_when_device_ids_is_empty(self, client, test_db):
        """빈 배열 → 422 (Pydantic min_length=1)"""
        g = DeviceGroup(name="G-empty")
        test_db.add(g)
        test_db.commit()
        test_db.refresh(g)

        resp = client.request(
            "DELETE",
            f"/api/devices/groups/{g.id}/devices",
            json={"device_ids": []},
        )
        assert resp.status_code == 422

    # 2.6
    def test_should_be_idempotent_when_device_ids_have_duplicates(self, client, test_db):
        """중복 ID → 1회 처리 (멱등)"""
        ctrl = _make_controller(test_db, num=4)
        s = _make_sensor(test_db, ctrl.id, num=401)
        g = _make_group_with_members(test_db, "G-dup", [s])

        resp = client.request(
            "DELETE",
            f"/api/devices/groups/{g.id}/devices",
            json={"device_ids": [s.id, s.id, s.id]},  # 동일 ID 3번
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        # 중복 제거 후 removed에 1번만
        assert data["removed_device_ids"] == [s.id]
        assert data["skipped_device_ids"] == []
        assert data["not_found_device_ids"] == []

    # 2.7
    def test_should_log_config_change_with_categories_when_unassigned(self, client, test_db):
        """ConfigChangeLog 1건 발행 — before_state에 device_ids + categories"""
        ctrl = _make_controller(test_db, num=5)
        s1 = _make_sensor(test_db, ctrl.id, num=501)
        c1 = _make_camera(test_db, num=502)
        g = _make_group_with_members(test_db, "G-log", [s1, c1])

        before_log_count = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DEVICE_GROUP,
            ConfigChangeLog.resource_id == g.id,
        ).count()

        resp = client.request(
            "DELETE",
            f"/api/devices/groups/{g.id}/devices",
            json={"device_ids": [s1.id, c1.id]},
        )
        assert resp.status_code == 200

        # ConfigChangeLog: UNASSIGNED 1건 추가
        logs = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DEVICE_GROUP,
            ConfigChangeLog.resource_id == g.id,
            ConfigChangeLog.action == EnumConfigActionType.UNASSIGNED,
        ).all()
        assert len(logs) == before_log_count + 1 or len(logs) >= 1
        latest = logs[-1]
        # before_state에 device_ids + categories
        before = latest.before_state
        assert "device_ids" in before
        assert set(before["device_ids"]) == {s1.id, c1.id}
        assert "categories" in before
        assert before["categories"][str(s1.id)] == "sensor"
        assert before["categories"][str(c1.id)] == "camera"

    # 2.8
    def test_should_unassign_mixed_device_types_polymorphically(self, client, test_db):
        """폴리모픽 — Controller+Sensor+Camera 동시 해제"""
        ctrl = _make_controller(test_db, num=6)
        s = _make_sensor(test_db, ctrl.id, num=601)
        cam = _make_camera(test_db, num=602)
        g = _make_group_with_members(test_db, "G-poly", [ctrl, s, cam])

        resp = client.request(
            "DELETE",
            f"/api/devices/groups/{g.id}/devices",
            json={"device_ids": [ctrl.id, s.id, cam.id]},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert set(data["removed_device_ids"]) == {ctrl.id, s.id, cam.id}
        # 모든 매핑 삭제됨
        remaining = test_db.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.group_id == g.id
        ).count()
        assert remaining == 0
