"""
TDD Tests: DeviceGroup support completion for Speaker, Enclosure, Lamp
PRD: PRD_DeviceGroup_Support_Completion.md v1.0
"""
import pytest
from datetime import datetime


# ============================================================================
# Phase 1-1: Speaker Schema Tests
# ============================================================================

class TestSpeakerDeviceGroupSchema:
    """Phase 1-1: Speaker 스키마에 DeviceGroup 필드 존재 확인"""

    def test_speaker_create_has_group_ids_field(self):
        """SpeakerCreate should have optional group_ids field"""
        from app.schemas.device import SpeakerCreate

        create = SpeakerCreate(
            number_device=2401,
            name_device="VCS_2401",
            type_device="IpSpeaker",
            status="ACTIVATED",
            group_ids=[1, 2]
        )
        assert create.group_ids == [1, 2]

    def test_speaker_create_group_ids_optional(self):
        """SpeakerCreate group_ids should default to None"""
        from app.schemas.device import SpeakerCreate

        create = SpeakerCreate(
            number_device=2401,
            name_device="VCS_2401",
            type_device="IpSpeaker",
            status="ACTIVATED",
        )
        assert create.group_ids is None

    def test_speaker_update_has_group_ids_field(self):
        """SpeakerUpdate should have optional group_ids field"""
        from app.schemas.device import SpeakerUpdate

        update = SpeakerUpdate(group_ids=[3])
        assert update.group_ids == [3]

    def test_speaker_update_group_ids_optional(self):
        """SpeakerUpdate group_ids should default to None"""
        from app.schemas.device import SpeakerUpdate

        update = SpeakerUpdate()
        assert update.group_ids is None

    def test_speaker_response_has_device_groups_field(self):
        """SpeakerResponse should have device_groups field"""
        from app.schemas.device import SpeakerResponse

        now = datetime.now()
        response = SpeakerResponse(
            id=1, number_device=2401, group_device=0,
            name_device="VCS_2401", type_device="IpSpeaker",
            status="ACTIVATED", is_enable=True,
            speaker_type="NORMAL",
            created_at=now, updated_at=now,
            device_groups=[]
        )
        assert response.device_groups == []

    def test_speaker_response_device_groups_with_data(self):
        """SpeakerResponse should accept device_groups with nested data"""
        from app.schemas.device import SpeakerResponse, DeviceGroupNestedResponse

        now = datetime.now()
        response = SpeakerResponse(
            id=1, number_device=2401, group_device=0,
            name_device="VCS_2401", type_device="IpSpeaker",
            status="ACTIVATED", is_enable=True,
            speaker_type="NORMAL",
            created_at=now, updated_at=now,
            device_groups=[
                DeviceGroupNestedResponse(id=1, name="GOP 1구역", description="테스트", device_count=5)
            ]
        )
        assert len(response.device_groups) == 1
        assert response.device_groups[0].name == "GOP 1구역"


# ============================================================================
# Phase 1-2: Speaker Router Tests
# ============================================================================

class TestSpeakerDeviceGroupRouter:
    """Phase 1-2: Speaker 라우터 DeviceGroup 지원 확인"""

    def test_create_speaker_with_group_ids(self, client, test_db):
        """POST /api/devices/speakers with group_ids should create group mappings"""
        from app.models.device_group import DeviceGroup

        # Create device groups first
        g1 = DeviceGroup(name="GOP 1구역", description="1구역")
        g2 = DeviceGroup(name="GOP 2구역", description="2구역")
        test_db.add_all([g1, g2])
        test_db.commit()
        test_db.refresh(g1)
        test_db.refresh(g2)

        response = client.post("/api/devices/speakers", json={
            "number_device": 2401,
            "name_device": "VCS_2401",
            "type_device": "IpSpeaker",
            "status": "ACTIVATED",
            "group_ids": [g1.id, g2.id]
        })
        assert response.status_code == 201
        data = response.json()["data"]
        assert len(data["device_groups"]) == 2

    def test_get_speaker_includes_device_groups(self, client, test_db):
        """GET /api/devices/speakers/{id} should include device_groups"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumDeviceCategory

        # Create speaker
        speaker = Speaker(
            number_device=2401, group_device=0, name_device="VCS_2401",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        # Create group and mapping
        group = DeviceGroup(name="Test Group", description="test")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=speaker.id,
            group_id=group.id,
            category_device=EnumDeviceCategory.SPEAKER
        )
        test_db.add(mapping)
        test_db.commit()

        response = client.get(f"/api/devices/speakers/{speaker.id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "device_groups" in data
        assert len(data["device_groups"]) == 1
        assert data["device_groups"][0]["name"] == "Test Group"

    def test_patch_speaker_group_ids(self, client, test_db):
        """PATCH /api/devices/speakers/{id} with group_ids should update mappings"""
        from app.models.device_group import DeviceGroup
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(
            number_device=2401, group_device=0, name_device="VCS_2401",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        group = DeviceGroup(name="New Group", description="new")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        response = client.patch(f"/api/devices/speakers/{speaker.id}", json={
            "group_ids": [group.id]
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["device_groups"]) == 1
        assert data["device_groups"][0]["name"] == "New Group"


# ============================================================================
# Phase 2-1: Enclosure Schema Tests
# ============================================================================

class TestEnclosureDeviceGroupSchema:
    """Phase 2-1: Enclosure 스키마에 DeviceGroup 필드 존재 확인"""

    def test_enclosure_create_has_group_ids_field(self):
        """EnclosureCreate should have optional group_ids field"""
        from app.schemas.device import EnclosureCreate

        create = EnclosureCreate(
            number_device=3001,
            name_device="ENC_3001",
            group_ids=[1, 2]
        )
        assert create.group_ids == [1, 2]

    def test_enclosure_create_group_ids_optional(self):
        """EnclosureCreate group_ids should default to None"""
        from app.schemas.device import EnclosureCreate

        create = EnclosureCreate(
            number_device=3001,
            name_device="ENC_3001",
        )
        assert create.group_ids is None

    def test_enclosure_update_has_group_ids_field(self):
        """EnclosureUpdate should have optional group_ids field"""
        from app.schemas.device import EnclosureUpdate

        update = EnclosureUpdate(group_ids=[3])
        assert update.group_ids == [3]

    def test_enclosure_update_group_ids_optional(self):
        """EnclosureUpdate group_ids should default to None"""
        from app.schemas.device import EnclosureUpdate

        update = EnclosureUpdate()
        assert update.group_ids is None

    def test_enclosure_response_has_device_groups_field(self):
        """EnclosureResponse should have device_groups field"""
        from app.schemas.device import EnclosureResponse

        now = datetime.now()
        response = EnclosureResponse(
            id=1, number_device=3001, group_device=0,
            name_device="ENC_3001", type_device="IoController",
            status="ACTIVATED", is_enable=True,
            door_status="CLOSED",
            heater_enabled=False, fan_enabled=False,
            created_at=now, updated_at=now,
            device_groups=[]
        )
        assert response.device_groups == []

    def test_enclosure_response_device_groups_with_data(self):
        """EnclosureResponse should accept device_groups with nested data"""
        from app.schemas.device import EnclosureResponse, DeviceGroupNestedResponse

        now = datetime.now()
        response = EnclosureResponse(
            id=1, number_device=3001, group_device=0,
            name_device="ENC_3001", type_device="IoController",
            status="ACTIVATED", is_enable=True,
            door_status="CLOSED",
            heater_enabled=False, fan_enabled=False,
            created_at=now, updated_at=now,
            device_groups=[
                DeviceGroupNestedResponse(id=1, name="GOP 1구역", description="테스트", device_count=5)
            ]
        )
        assert len(response.device_groups) == 1
        assert response.device_groups[0].name == "GOP 1구역"


# ============================================================================
# Phase 2-2: Enclosure Router Tests
# ============================================================================

class TestEnclosureDeviceGroupRouter:
    """Phase 2-2: Enclosure 라우터 DeviceGroup 지원 확인"""

    def test_create_enclosure_with_group_ids(self, client, test_db):
        """POST /api/devices/enclosures with group_ids should create group mappings"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="GOP 1구역", description="1구역")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        response = client.post("/api/devices/enclosures", json={
            "number_device": 3001,
            "name_device": "ENC_3001",
            "group_ids": [group.id]
        })
        assert response.status_code == 201
        data = response.json()["data"]
        assert len(data["device_groups"]) == 1

    def test_get_enclosure_includes_device_groups(self, client, test_db):
        """GET /api/devices/enclosures/{id} should include device_groups"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus, EnumDeviceCategory

        enclosure = Enclosure(
            number_device=3001, group_device=0, name_device="ENC_3001",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        test_db.add(enclosure)
        test_db.commit()
        test_db.refresh(enclosure)

        group = DeviceGroup(name="Test Group", description="test")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=enclosure.id,
            group_id=group.id,
            category_device=EnumDeviceCategory.ENCLOSURE
        )
        test_db.add(mapping)
        test_db.commit()

        response = client.get(f"/api/devices/enclosures/{enclosure.id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "device_groups" in data
        assert len(data["device_groups"]) == 1
        assert data["device_groups"][0]["name"] == "Test Group"

    def test_patch_enclosure_group_ids(self, client, test_db):
        """PATCH /api/devices/enclosures/{id} with group_ids should update mappings"""
        from app.models.device_group import DeviceGroup
        from app.models.device import Enclosure
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

        enclosure = Enclosure(
            number_device=3001, group_device=0, name_device="ENC_3001",
            type_device=EnumDeviceType.IoController,
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED
        )
        test_db.add(enclosure)
        test_db.commit()
        test_db.refresh(enclosure)

        group = DeviceGroup(name="New Group", description="new")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        response = client.patch(f"/api/devices/enclosures/{enclosure.id}", json={
            "group_ids": [group.id]
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["device_groups"]) == 1
        assert data["device_groups"][0]["name"] == "New Group"


# ============================================================================
# Phase 3-1: Lamp Schema Tests
# ============================================================================

class TestLampDeviceGroupSchema:
    """Phase 3-1: Lamp 스키마에 group_ids 필드 존재 확인"""

    def test_lamp_create_has_group_ids_field(self):
        """LampCreate should have optional group_ids field"""
        from app.schemas.device import LampCreate

        create = LampCreate(
            number_device=5001,
            name_device="Lamp-A-1",
            ip_address="192.168.1.109",
            group_ids=[1, 2]
        )
        assert create.group_ids == [1, 2]

    def test_lamp_create_group_ids_optional(self):
        """LampCreate group_ids should default to None"""
        from app.schemas.device import LampCreate

        create = LampCreate(
            number_device=5001,
            name_device="Lamp-A-1",
            ip_address="192.168.1.109",
        )
        assert create.group_ids is None

    def test_lamp_update_has_group_ids_field(self):
        """LampUpdate should have optional group_ids field"""
        from app.schemas.device import LampUpdate

        update = LampUpdate(group_ids=[3])
        assert update.group_ids == [3]

    def test_lamp_update_group_ids_optional(self):
        """LampUpdate group_ids should default to None"""
        from app.schemas.device import LampUpdate

        update = LampUpdate()
        assert update.group_ids is None


# ============================================================================
# Phase 3-2: Lamp Router Tests
# ============================================================================

class TestLampDeviceGroupRouter:
    """Phase 3-2: Lamp 라우터 DeviceGroup 지원 확인 (깨진 코드 수정 포함)"""

    def test_create_lamp_with_group_ids(self, client, test_db):
        """POST /api/devices/lamps with group_ids should create group mappings"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="GOP 1구역", description="1구역")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        response = client.post("/api/devices/lamps", json={
            "number_device": 5001,
            "name_device": "Lamp-A-1",
            "ip_address": "192.168.1.109",
            "group_ids": [group.id]
        })
        assert response.status_code == 201
        data = response.json()["data"]
        assert len(data["device_groups"]) == 1

    def test_get_lamp_includes_device_groups(self, client, test_db):
        """GET /api/devices/lamps/{id} should include device_groups"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Lamp
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        lamp = Lamp(
            number_device=5001, group_device=0, name_device="Lamp-A-1",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.109", ip_port=80
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        group = DeviceGroup(name="Test Group", description="test")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        mapping = DeviceGroupMapping(
            device_id=lamp.id,
            group_id=group.id,
            category_device=EnumDeviceCategory.LAMP
        )
        test_db.add(mapping)
        test_db.commit()

        response = client.get(f"/api/devices/lamps/{lamp.id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "device_groups" in data
        assert len(data["device_groups"]) == 1
        assert data["device_groups"][0]["name"] == "Test Group"

    def test_patch_lamp_group_ids(self, client, test_db):
        """PATCH /api/devices/lamps/{id} with group_ids should update mappings"""
        from app.models.device_group import DeviceGroup
        from app.models.device import Lamp
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        lamp = Lamp(
            number_device=5001, group_device=0, name_device="Lamp-A-1",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.109", ip_port=80
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)

        group = DeviceGroup(name="New Group", description="new")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        response = client.patch(f"/api/devices/lamps/{lamp.id}", json={
            "group_ids": [group.id]
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["device_groups"]) == 1
        assert data["device_groups"][0]["name"] == "New Group"
