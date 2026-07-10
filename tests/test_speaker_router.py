"""
Tests for Speaker Router (API Endpoints)
PRD: PRD_Speaker_Device.md - Phase 6-9: Speaker Router
TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient


class TestGetSpeakersList:
    """Phase 6.1: Test Speaker List Endpoint"""

    def test_get_speakers_list_success(self, client, test_db):
        """GET /api/devices/speakers should return list of speakers"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        # Create test speaker
        speaker = Speaker(
            number_device=2401,
            group_device=0,
            name_device="VCS_2401",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
        )
        test_db.add(speaker)
        test_db.commit()

        response = client.get("/api/devices/speakers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["number_device"] == 2401

    def test_get_speakers_list_empty(self, client):
        """GET /api/devices/speakers should return empty list when no speakers"""
        response = client.get("/api/devices/speakers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0

    def test_get_speakers_list_with_server_nested(self, client, test_db):
        """GET /api/devices/speakers should include nested server object"""
        from app.models.device import Speaker
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumServerType, EnumServerStatus

        # Create server category
        category = ServerCategory(
            name="SPEAKER_API",
            type_server=EnumServerType.SPEAKER_API
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        # Create server
        server = Server(
            category_id=category.id,
            name="방송서버-01",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Create speaker with server
        speaker = Speaker(
            number_device=2401,
            group_device=0,
            name_device="VCS_2401",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL,
            server_id=server.id
        )
        test_db.add(speaker)
        test_db.commit()

        response = client.get("/api/devices/speakers")
        assert response.status_code == 200
        data = response.json()
        assert data["data"][0]["server"] is not None
        assert data["data"][0]["server"]["name"] == "방송서버-01"
        assert "server_id" not in data["data"][0]  # server_id should not be in response

    def test_get_speakers_list_filter_by_server_id(self, client, test_db):
        """GET /api/devices/speakers?server_id=1 should filter by server_id"""
        from app.models.device import Speaker
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumServerType, EnumServerStatus

        # Create server category
        category = ServerCategory(name="SPEAKER_API", type_server=EnumServerType.SPEAKER_API)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        # Create servers
        server1 = Server(category_id=category.id, name="Server1", status=EnumServerStatus.NORMAL, ip_address="192.168.1.1", port=8080)
        server2 = Server(category_id=category.id, name="Server2", status=EnumServerStatus.NORMAL, ip_address="192.168.1.2", port=8080)
        test_db.add_all([server1, server2])
        test_db.commit()
        test_db.refresh(server1)
        test_db.refresh(server2)

        # Create speakers
        speaker1 = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL, server_id=server1.id)
        speaker2 = Speaker(number_device=2402, group_device=0, name_device="VCS_2402", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL, server_id=server2.id)
        test_db.add_all([speaker1, speaker2])
        test_db.commit()

        response = client.get(f"/api/devices/speakers?server_id={server1.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["number_device"] == 2401

    def test_get_speakers_list_filter_by_status(self, client, test_db):
        """GET /api/devices/speakers?status=ACTIVATED should filter by status"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker1 = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        speaker2 = Speaker(number_device=2402, group_device=0, name_device="VCS_2402", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.DEACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        test_db.add_all([speaker1, speaker2])
        test_db.commit()

        response = client.get("/api/devices/speakers?status=ACTIVATED")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "ACTIVATED"

    def test_get_speakers_list_filter_by_speaker_type(self, client, test_db):
        """GET /api/devices/speakers?speaker_type=ADMIN should filter by speaker_type"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker1 = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        speaker2 = Speaker(number_device=2402, group_device=0, name_device="VCS_2402", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.ADMIN)
        test_db.add_all([speaker1, speaker2])
        test_db.commit()

        response = client.get("/api/devices/speakers?speaker_type=ADMIN")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["speaker_type"] == "ADMIN"

    def test_get_speakers_list_pagination(self, client, test_db):
        """GET /api/devices/speakers?page=1&limit=2 should return paginated results"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        # Create 5 speakers
        for i in range(5):
            speaker = Speaker(number_device=2401+i, group_device=0, name_device=f"VCS_{2401+i}", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
            test_db.add(speaker)
        test_db.commit()

        response = client.get("/api/devices/speakers?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["total_pages"] == 3


class TestGetSpeakerById:
    """Phase 6.2: Test Speaker Get Single Endpoint"""

    def test_get_speaker_by_id_success(self, client, test_db):
        """GET /api/devices/speakers/{id} should return speaker"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.get(f"/api/devices/speakers/{speaker.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == speaker.id
        assert data["data"]["number_device"] == 2401

    def test_get_speaker_by_id_not_found(self, client):
        """GET /api/devices/speakers/{id} should return 404 for non-existent speaker"""
        response = client.get("/api/devices/speakers/9999")
        assert response.status_code == 404

    def test_get_speaker_by_id_includes_server_nested(self, client, test_db):
        """GET /api/devices/speakers/{id} should include nested server object"""
        from app.models.device import Speaker
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumServerType, EnumServerStatus

        category = ServerCategory(name="SPEAKER_API", type_server=EnumServerType.SPEAKER_API)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(category_id=category.id, name="방송서버-01", status=EnumServerStatus.NORMAL, ip_address="192.168.1.100", port=8080)
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL, server_id=server.id)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.get(f"/api/devices/speakers/{speaker.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["server"] is not None
        assert data["data"]["server"]["name"] == "방송서버-01"


class TestCreateSpeaker:
    """Phase 7: Test Speaker Create Endpoint"""

    def test_create_speaker_success(self, client, test_db):
        """POST /api/devices/speakers should create speaker"""
        response = client.post("/api/devices/speakers", json={
            "number_device": 2401,
            "name_device": "VCS_2401"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["number_device"] == 2401
        assert data["data"]["speaker_type"] == "NORMAL"

    def test_create_speaker_with_server_id(self, client, test_db):
        """POST /api/devices/speakers with server_id should link to server"""
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumServerType, EnumServerStatus

        category = ServerCategory(name="SPEAKER_API", type_server=EnumServerType.SPEAKER_API)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(category_id=category.id, name="방송서버-01", status=EnumServerStatus.NORMAL, ip_address="192.168.1.100", port=8080)
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        response = client.post("/api/devices/speakers", json={
            "number_device": 2401,
            "name_device": "VCS_2401",
            "server_id": server.id
        })
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["server"]["id"] == server.id

    def test_create_speaker_server_not_found(self, client):
        """POST /api/devices/speakers with invalid server_id should return 404"""
        response = client.post("/api/devices/speakers", json={
            "number_device": 2401,
            "name_device": "VCS_2401",
            "server_id": 9999
        })
        assert response.status_code == 404

    def test_create_speaker_minimal_fields(self, client):
        """POST /api/devices/speakers with minimal fields should work"""
        response = client.post("/api/devices/speakers", json={
            "number_device": 2401,
            "name_device": "VCS_2401"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["type_device"] == "IpSpeaker"
        assert data["data"]["status"] == "ACTIVATED"
        assert data["data"]["speaker_type"] == "NORMAL"

    def test_create_speaker_all_fields(self, client, test_db):
        """POST /api/devices/speakers with all fields should work"""
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumServerType, EnumServerStatus

        category = ServerCategory(name="SPEAKER_API", type_server=EnumServerType.SPEAKER_API)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(category_id=category.id, name="방송서버-01", status=EnumServerStatus.NORMAL, ip_address="192.168.1.100", port=8080)
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        response = client.post("/api/devices/speakers", json={
            "number_device": 2401,
            "group_device": 1,
            "name_device": "VCS_2401",
            "type_device": "IpSpeaker",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "speaker_type": "ADMIN",
            "server_id": server.id,
            "description": "테스트 스피커"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["speaker_type"] == "ADMIN"
        assert data["data"]["description"] == "테스트 스피커"

    def test_create_speaker_validates_speaker_type(self, client):
        """POST /api/devices/speakers with invalid speaker_type should fail"""
        response = client.post("/api/devices/speakers", json={
            "number_device": 2401,
            "name_device": "VCS_2401",
            "speaker_type": "INVALID_TYPE"
        })
        assert response.status_code == 422


class TestPatchSpeaker:
    """Phase 8.1: Test Speaker PATCH Endpoint"""

    def test_patch_speaker_success(self, client, test_db):
        """PATCH /api/devices/speakers/{id} should update speaker"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.patch(f"/api/devices/speakers/{speaker.id}", json={
            "name_device": "Updated Name"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name_device"] == "Updated Name"

    def test_patch_speaker_not_found(self, client):
        """PATCH /api/devices/speakers/{id} should return 404 for non-existent speaker"""
        response = client.patch("/api/devices/speakers/9999", json={
            "name_device": "Updated Name"
        })
        assert response.status_code == 404

    def test_patch_speaker_partial_update(self, client, test_db):
        """PATCH /api/devices/speakers/{id} should only update provided fields"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL, description="Original")
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.patch(f"/api/devices/speakers/{speaker.id}", json={
            "speaker_type": "ADMIN"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["speaker_type"] == "ADMIN"
        assert data["data"]["description"] == "Original"  # unchanged

    def test_patch_speaker_update_server_id(self, client, test_db):
        """PATCH /api/devices/speakers/{id} should update server_id"""
        from app.models.device import Speaker
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumServerType, EnumServerStatus

        category = ServerCategory(name="SPEAKER_API", type_server=EnumServerType.SPEAKER_API)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(category_id=category.id, name="방송서버-01", status=EnumServerStatus.NORMAL, ip_address="192.168.1.100", port=8080)
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.patch(f"/api/devices/speakers/{speaker.id}", json={
            "server_id": server.id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["server"]["id"] == server.id

    def test_patch_speaker_clear_server_id(self, client, test_db):
        """PATCH /api/devices/speakers/{id} with server_id=null should clear server"""
        from app.models.device import Speaker
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumServerType, EnumServerStatus

        category = ServerCategory(name="SPEAKER_API", type_server=EnumServerType.SPEAKER_API)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(category_id=category.id, name="방송서버-01", status=EnumServerStatus.NORMAL, ip_address="192.168.1.100", port=8080)
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL, server_id=server.id)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.patch(f"/api/devices/speakers/{speaker.id}", json={
            "server_id": None
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["server"] is None


class TestPutSpeaker:
    """Phase 8.2: Test Speaker PUT Endpoint"""

    def test_put_speaker_success(self, client, test_db):
        """PUT /api/devices/speakers/{id} should replace speaker"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.put(f"/api/devices/speakers/{speaker.id}", json={
            "number_device": 2499,
            "name_device": "NEW_NAME"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["number_device"] == 2499
        assert data["data"]["name_device"] == "NEW_NAME"

    def test_put_speaker_replaces_all_fields(self, client, test_db):
        """PUT /api/devices/speakers/{id} should replace all fields"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.ADMIN, description="Original")
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        response = client.put(f"/api/devices/speakers/{speaker.id}", json={
            "number_device": 2499,
            "name_device": "NEW_NAME",
            "speaker_type": "NORMAL"
            # description not provided - should be reset/cleared
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["speaker_type"] == "NORMAL"


class TestDeleteSpeaker:
    """Phase 9: Test Speaker Delete Endpoint"""

    def test_delete_speaker_success(self, client, test_db):
        """DELETE /api/devices/speakers/{id} should delete speaker"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)
        speaker_id = speaker.id

        response = client.delete(f"/api/devices/speakers/{speaker_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deletion
        response = client.get(f"/api/devices/speakers/{speaker_id}")
        assert response.status_code == 404

    def test_delete_speaker_not_found(self, client):
        """DELETE /api/devices/speakers/{id} should return 404 for non-existent speaker"""
        response = client.delete("/api/devices/speakers/9999")
        assert response.status_code == 404

    def test_delete_speaker_cascades_to_device(self, client, test_db):
        """DELETE /api/devices/speakers/{id} should cascade delete Device base"""
        from app.models.device import Speaker
        from app.models.device import Device
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(number_device=2401, group_device=0, name_device="VCS_2401", type_device=EnumDeviceType.IpSpeaker, status=EnumDeviceStatus.ACTIVATED, speaker_type=EnumSpeakerType.NORMAL)
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)
        speaker_id = speaker.id

        # Delete speaker
        response = client.delete(f"/api/devices/speakers/{speaker_id}")
        assert response.status_code == 200

        # Verify Device base is also deleted
        test_db.expire_all()
        device = test_db.query(Device).filter(Device.id == speaker_id).first()
        assert device is None
