"""
DeviceGroup Assign/Remove Polymorphic Fix Tests (TDD)

PRD: PRD_DeviceGroup_Assign_Fix.md v1.0
BUG-1: assign_devices_to_group()에서 Controller만 조회 (db.query(Controller))
BUG-2: category_device 항상 CONTROLLER로 저장
BUG-3: remove_device_from_group()에서 CONTROLLER로만 매핑 검색
"""
import pytest
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.models.device import Controller, Sensor, Camera, Speaker, Enclosure, Lamp
from app.utils.enums import (
    EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory,
    EnumSpeakerType, EnumDoorStatus
)


# =============================================================================
# Phase 1: Assign Fix — Device Polymorphic Query
# =============================================================================

class TestAssignSensorToGroup:
    """1.1 TEST: Sensor 디바이스를 그룹에 할당 → assigned_device_ids에 포함"""

    def test_assign_sensor_to_group(self, client, test_db):
        """Sensor를 그룹에 할당하면 assigned_device_ids에 포함되어야 한다"""
        # Arrange: Controller (Sensor의 FK 필요) + Sensor + Group 생성
        controller = Controller(
            number_device=1, group_device=1,
            name_device="CTL-001", type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10", ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        sensor = Sensor(
            number_device=101, group_device=1,
            name_device="SEN-001", type_device=EnumDeviceType.Multi,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id
        )
        test_db.add(sensor)

        group = DeviceGroup(name="Test Group Sensor")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(sensor)
        test_db.refresh(group)

        # Act
        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [sensor.id]}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert sensor.id in data["data"]["assigned_device_ids"]
        assert sensor.id not in data["data"]["skipped_device_ids"]


class TestAssignCameraToGroup:
    """1.2 TEST: Camera 디바이스를 그룹에 할당 → assigned_device_ids에 포함"""

    def test_assign_camera_to_group(self, client, test_db):
        """Camera를 그룹에 할당하면 assigned_device_ids에 포함되어야 한다"""
        camera = Camera(
            number_device=201, group_device=1,
            name_device="CAM-001", type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200", ip_port=80
        )
        test_db.add(camera)

        group = DeviceGroup(name="Test Group Camera")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(camera)
        test_db.refresh(group)

        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [camera.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert camera.id in data["data"]["assigned_device_ids"]
        assert camera.id not in data["data"]["skipped_device_ids"]


class TestAssignSpeakerToGroup:
    """1.3 TEST: Speaker 디바이스를 그룹에 할당 → assigned_device_ids에 포함"""

    def test_assign_speaker_to_group(self, client, test_db):
        """Speaker를 그룹에 할당하면 assigned_device_ids에 포함되어야 한다"""
        speaker = Speaker(
            number_device=301, group_device=1,
            name_device="SPK-001", type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
        )
        test_db.add(speaker)

        group = DeviceGroup(name="Test Group Speaker")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(speaker)
        test_db.refresh(group)

        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [speaker.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert speaker.id in data["data"]["assigned_device_ids"]
        assert speaker.id not in data["data"]["skipped_device_ids"]


class TestAssignEnclosureToGroup:
    """1.4 TEST: Enclosure 디바이스를 그룹에 할당 → assigned_device_ids에 포함"""

    def test_assign_enclosure_to_group(self, client, test_db):
        """Enclosure를 그룹에 할당하면 assigned_device_ids에 포함되어야 한다"""
        enclosure = Enclosure(
            number_device=401, group_device=1,
            name_device="ENC-001", type_device=EnumDeviceType.Enclosure,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        test_db.add(enclosure)

        group = DeviceGroup(name="Test Group Enclosure")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(enclosure)
        test_db.refresh(group)

        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [enclosure.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert enclosure.id in data["data"]["assigned_device_ids"]
        assert enclosure.id not in data["data"]["skipped_device_ids"]


class TestAssignLampToGroup:
    """1.5 TEST: Lamp 디바이스를 그룹에 할당 → assigned_device_ids에 포함"""

    def test_assign_lamp_to_group(self, client, test_db):
        """Lamp를 그룹에 할당하면 assigned_device_ids에 포함되어야 한다"""
        lamp = Lamp(
            number_device=501, group_device=1,
            name_device="LAMP-001", type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.109", ip_port=80
        )
        test_db.add(lamp)

        group = DeviceGroup(name="Test Group Lamp")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(lamp)
        test_db.refresh(group)

        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [lamp.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert lamp.id in data["data"]["assigned_device_ids"]
        assert lamp.id not in data["data"]["skipped_device_ids"]


class TestAssignMixedDevicesToGroup:
    """1.6 TEST: 여러 디바이스 타입 혼합 할당 → 모두 assigned"""

    def test_assign_mixed_device_types_to_group(self, client, test_db):
        """Controller + Sensor + Camera를 동시에 할당하면 모두 assigned_device_ids에 포함"""
        controller = Controller(
            number_device=1, group_device=1,
            name_device="CTL-MIX", type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10", ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        sensor = Sensor(
            number_device=101, group_device=1,
            name_device="SEN-MIX", type_device=EnumDeviceType.Multi,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id
        )
        camera = Camera(
            number_device=201, group_device=1,
            name_device="CAM-MIX", type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200", ip_port=80
        )
        test_db.add_all([sensor, camera])

        group = DeviceGroup(name="Test Group Mixed")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(controller)
        test_db.refresh(sensor)
        test_db.refresh(camera)
        test_db.refresh(group)

        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [controller.id, sensor.id, camera.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assigned = data["data"]["assigned_device_ids"]
        assert controller.id in assigned
        assert sensor.id in assigned
        assert camera.id in assigned
        assert len(data["data"]["skipped_device_ids"]) == 0


# =============================================================================
# Phase 2: Assign Validation — category_device 정확성
# =============================================================================

class TestAssignCategoryDeviceAccuracy:
    """2.1-2.2 TEST: 할당 후 매핑의 category_device가 정확한지 확인"""

    def test_sensor_mapping_has_correct_category(self, client, test_db):
        """2.1: Sensor 할당 후 매핑의 category_device == SENSOR"""
        controller = Controller(
            number_device=1, group_device=1,
            name_device="CTL-CAT", type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10", ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        sensor = Sensor(
            number_device=101, group_device=1,
            name_device="SEN-CAT", type_device=EnumDeviceType.Multi,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id
        )
        group = DeviceGroup(name="Test Category Sensor")
        test_db.add_all([sensor, group])
        test_db.commit()
        test_db.refresh(sensor)
        test_db.refresh(group)

        client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [sensor.id]}
        )

        # DB에서 직접 매핑 확인
        mapping = test_db.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.device_id == sensor.id,
            DeviceGroupMapping.group_id == group.id
        ).first()

        assert mapping is not None
        assert mapping.category_device == EnumDeviceCategory.SENSOR

    def test_camera_mapping_has_correct_category(self, client, test_db):
        """2.2: Camera 할당 후 매핑의 category_device == CAMERA"""
        camera = Camera(
            number_device=201, group_device=1,
            name_device="CAM-CAT", type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200", ip_port=80
        )
        group = DeviceGroup(name="Test Category Camera")
        test_db.add_all([camera, group])
        test_db.commit()
        test_db.refresh(camera)
        test_db.refresh(group)

        client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [camera.id]}
        )

        mapping = test_db.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.device_id == camera.id,
            DeviceGroupMapping.group_id == group.id
        ).first()

        assert mapping is not None
        assert mapping.category_device == EnumDeviceCategory.CAMERA


class TestAssignDuplicateDevice:
    """2.3 TEST: 동일 디바이스 중복 할당 시 skipped 처리"""

    def test_duplicate_assign_is_skipped(self, client, test_db):
        """동일 Sensor를 같은 그룹에 2번 할당하면 두번째는 skipped"""
        controller = Controller(
            number_device=1, group_device=1,
            name_device="CTL-DUP", type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10", ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        sensor = Sensor(
            number_device=101, group_device=1,
            name_device="SEN-DUP", type_device=EnumDeviceType.Multi,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id
        )
        group = DeviceGroup(name="Test Duplicate")
        test_db.add_all([sensor, group])
        test_db.commit()
        test_db.refresh(sensor)
        test_db.refresh(group)

        # 첫번째 할당
        resp1 = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [sensor.id]}
        )
        assert resp1.json()["data"]["assigned_device_ids"] == [sensor.id]

        # 두번째 할당 (중복)
        resp2 = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [sensor.id]}
        )
        data2 = resp2.json()
        assert sensor.id in data2["data"]["skipped_device_ids"]
        assert len(data2["data"]["assigned_device_ids"]) == 0


class TestAssignNonexistentDevice:
    """2.4 TEST: 존재하지 않는 device_id → skipped 처리"""

    def test_nonexistent_device_is_skipped(self, client, test_db):
        """존재하지 않는 device_id는 skipped 처리"""
        group = DeviceGroup(name="Test Nonexistent")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [99999]}
        )

        assert response.status_code == 200
        data = response.json()
        assert 99999 in data["data"]["skipped_device_ids"]
        assert len(data["data"]["assigned_device_ids"]) == 0


# =============================================================================
# Phase 3: Remove Fix — Polymorphic Remove
# =============================================================================

class TestRemoveSensorFromGroup:
    """3.1 TEST: Sensor 디바이스를 그룹에서 제거 → 성공"""

    def test_remove_sensor_from_group(self, client, test_db):
        """Sensor를 그룹에 할당 후 제거하면 성공"""
        controller = Controller(
            number_device=1, group_device=1,
            name_device="CTL-REM", type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10", ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        sensor = Sensor(
            number_device=101, group_device=1,
            name_device="SEN-REM", type_device=EnumDeviceType.Multi,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id
        )
        group = DeviceGroup(name="Test Remove Sensor")
        test_db.add_all([sensor, group])
        test_db.commit()
        test_db.refresh(sensor)
        test_db.refresh(group)

        # Assign first (uses fixed assign)
        mapping = DeviceGroupMapping(
            device_id=sensor.id,
            category_device=EnumDeviceCategory.SENSOR,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        # Remove
        response = client.delete(
            f"/api/devices/groups/{group.id}/devices/{sensor.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["device_id"] == sensor.id


class TestRemoveCameraFromGroup:
    """3.2 TEST: Camera 디바이스를 그룹에서 제거 → 성공"""

    def test_remove_camera_from_group(self, client, test_db):
        """Camera를 그룹에 할당 후 제거하면 성공"""
        camera = Camera(
            number_device=201, group_device=1,
            name_device="CAM-REM", type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200", ip_port=80
        )
        group = DeviceGroup(name="Test Remove Camera")
        test_db.add_all([camera, group])
        test_db.commit()
        test_db.refresh(camera)
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=camera.id,
            category_device=EnumDeviceCategory.CAMERA,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        response = client.delete(
            f"/api/devices/groups/{group.id}/devices/{camera.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["device_id"] == camera.id


class TestRemoveSpeakerFromGroup:
    """3.3 TEST: Speaker 디바이스를 그룹에서 제거 → 성공"""

    def test_remove_speaker_from_group(self, client, test_db):
        """Speaker를 그룹에 할당 후 제거하면 성공"""
        speaker = Speaker(
            number_device=301, group_device=1,
            name_device="SPK-REM", type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
        )
        group = DeviceGroup(name="Test Remove Speaker")
        test_db.add_all([speaker, group])
        test_db.commit()
        test_db.refresh(speaker)
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=speaker.id,
            category_device=EnumDeviceCategory.SPEAKER,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        response = client.delete(
            f"/api/devices/groups/{group.id}/devices/{speaker.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["device_id"] == speaker.id


class TestRemoveNonexistentDevice:
    """3.4 TEST: 존재하지 않는 device_id 제거 시도 → 404"""

    def test_remove_nonexistent_device_returns_404(self, client, test_db):
        """존재하지 않는 device_id를 제거하면 404"""
        group = DeviceGroup(name="Test Remove Nonexistent")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        response = client.delete(
            f"/api/devices/groups/{group.id}/devices/99999"
        )

        assert response.status_code == 404


class TestRemoveUnassignedDevice:
    """3.5 TEST: 그룹에 미할당된 device_id 제거 시도 → 404"""

    def test_remove_unassigned_device_returns_404(self, client, test_db):
        """그룹에 할당되지 않은 device_id를 제거하면 404"""
        camera = Camera(
            number_device=201, group_device=1,
            name_device="CAM-UNASSIGN", type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200", ip_port=80
        )
        group = DeviceGroup(name="Test Remove Unassigned")
        test_db.add_all([camera, group])
        test_db.commit()
        test_db.refresh(camera)
        test_db.refresh(group)

        # 할당하지 않고 바로 제거 시도
        response = client.delete(
            f"/api/devices/groups/{group.id}/devices/{camera.id}"
        )

        assert response.status_code == 404


# =============================================================================
# Phase 4: Group Detail Verification & ConfigChangeLog
# =============================================================================

class TestGroupDetailWithMixedDevices:
    """4.1 TEST: 다양한 타입 할당 후 그룹 상세 조회 → 모든 디바이스 타입 포함"""

    def test_group_detail_shows_all_device_types(self, client, test_db):
        """Controller + Sensor + Camera를 할당 후 그룹 상세 조회하면 모든 타입 포함"""
        controller = Controller(
            number_device=1, group_device=1,
            name_device="CTL-DETAIL", type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10", ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(controller)

        sensor = Sensor(
            number_device=101, group_device=1,
            name_device="SEN-DETAIL", type_device=EnumDeviceType.Multi,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id
        )
        camera = Camera(
            number_device=201, group_device=1,
            name_device="CAM-DETAIL", type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200", ip_port=80
        )
        group = DeviceGroup(name="Test Detail Mixed")
        test_db.add_all([sensor, camera, group])
        test_db.commit()
        test_db.refresh(controller)
        test_db.refresh(sensor)
        test_db.refresh(camera)
        test_db.refresh(group)

        # Assign via API (uses fixed assign)
        client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [controller.id, sensor.id, camera.id]}
        )

        # Get group detail
        response = client.get(f"/api/devices/groups/{group.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        devices = data["data"]["devices"]
        assert len(devices) == 3

        device_names = [d["name_device"] for d in devices]
        assert "CTL-DETAIL" in device_names
        assert "SEN-DETAIL" in device_names
        assert "CAM-DETAIL" in device_names

        device_types = [d["type_device"] for d in devices]
        assert "Controller" in device_types
        assert "Multi" in device_types
        assert "IpCamera" in device_types


class TestAssignConfigChangeLog:
    """4.2 TEST: Assign ConfigChangeLog에 category 정보 포함 확인"""

    def test_assign_logs_config_change_with_categories(self, client, test_db):
        """디바이스 할당 시 ConfigChangeLog에 categories 정보 포함"""
        from app.models.config_change_log import ConfigChangeLog

        sensor_ctl = Controller(
            number_device=1, group_device=1,
            name_device="CTL-LOG", type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10", ip_port=8080
        )
        test_db.add(sensor_ctl)
        test_db.commit()
        test_db.refresh(sensor_ctl)

        sensor = Sensor(
            number_device=101, group_device=1,
            name_device="SEN-LOG", type_device=EnumDeviceType.Multi,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=sensor_ctl.id
        )
        group = DeviceGroup(name="Test Log Assign")
        test_db.add_all([sensor, group])
        test_db.commit()
        test_db.refresh(sensor)
        test_db.refresh(group)

        client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [sensor.id]}
        )

        # ConfigChangeLog 확인
        log = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.action == "ASSIGNED"
        ).order_by(ConfigChangeLog.id.desc()).first()

        assert log is not None
        assert log.after_state is not None
        # categories 정보 포함 확인
        assert "categories" in log.after_state


class TestRemoveConfigChangeLog:
    """4.3 TEST: Remove ConfigChangeLog에 category 정보 포함 확인"""

    def test_remove_logs_config_change_with_category(self, client, test_db):
        """디바이스 제거 시 ConfigChangeLog에 category_device 정보 포함"""
        from app.models.config_change_log import ConfigChangeLog

        camera = Camera(
            number_device=201, group_device=1,
            name_device="CAM-LOG", type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200", ip_port=80
        )
        group = DeviceGroup(name="Test Log Remove")
        test_db.add_all([camera, group])
        test_db.commit()
        test_db.refresh(camera)
        test_db.refresh(group)

        # Assign then remove
        mapping = DeviceGroupMapping(
            device_id=camera.id,
            category_device=EnumDeviceCategory.CAMERA,
            group_id=group.id
        )
        test_db.add(mapping)
        test_db.commit()

        client.delete(
            f"/api/devices/groups/{group.id}/devices/{camera.id}"
        )

        # ConfigChangeLog 확인
        log = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.action == "UNASSIGNED"
        ).order_by(ConfigChangeLog.id.desc()).first()

        assert log is not None
        assert log.before_state is not None
        assert "category_device" in log.before_state
