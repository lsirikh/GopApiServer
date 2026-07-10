"""
Integration Tests for Speaker and FileGroup
PRD: PRD_Speaker_Device.md - Phase 14: Integration Tests
TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.server import Server, ServerCategory
from app.models.device import Speaker
from app.models.file_group import FileGroup
from app.utils.enums import (
    EnumServerType, EnumServerStatus, EnumDeviceCategory,
    EnumDeviceType, EnumDeviceStatus, EnumSpeakerType
)


# ============================================
# Phase 14.1: Speaker Server Relationship
# ============================================

class TestSpeakerServerRelationship:
    """Test Speaker and Server FK relationships"""

    def test_delete_server_sets_speaker_server_id_null(self, client: TestClient, test_db):
        """When server is deleted, speaker.server_id should be SET NULL"""
        # Setup: Create server and speaker
        category = ServerCategory(
            name="SPEAKER_API",
            type_server=EnumServerType.SPEAKER_API,
            description="방송 서버"
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버1",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

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
        test_db.refresh(speaker)
        speaker_id = speaker.id

        # Verify speaker has server_id
        assert speaker.server_id == server.id

        # Delete server
        test_db.delete(server)
        test_db.commit()

        # Verify speaker still exists but server_id is NULL
        test_db.expire_all()
        updated_speaker = test_db.query(Speaker).filter(Speaker.id == speaker_id).first()
        assert updated_speaker is not None
        assert updated_speaker.server_id is None

    def test_speaker_with_null_server_response_format(self, client: TestClient, test_db):
        """Speaker with null server_id should have server: null in response"""
        # Setup: Create speaker without server
        speaker = Speaker(
            number_device=2402,
            group_device=0,
            name_device="VCS_2402",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL,
            server_id=None  # No server
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        # Get speaker via API
        response = client.get(f"/api/devices/speakers/{speaker.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["server"] is None


# ============================================
# Phase 14.2: FileGroup Server Relationship
# ============================================

class TestFileGroupServerRelationship:
    """Test FileGroup and Server FK relationships"""

    def test_delete_server_cascades_to_file_groups(self, client: TestClient, test_db):
        """When server is deleted, file_groups should be CASCADE deleted"""
        # Setup: Create server and file groups
        category = ServerCategory(
            name="SPEAKER_API",
            type_server=EnumServerType.SPEAKER_API,
            description="방송 서버"
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버1",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Create multiple file groups
        fg1 = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보"
        )
        fg2 = FileGroup(
            server_id=server.id,
            group_id=2,
            group_name="긴급방송"
        )
        test_db.add_all([fg1, fg2])
        test_db.commit()
        fg1_id = fg1.id
        fg2_id = fg2.id

        # Verify file groups exist
        assert test_db.query(FileGroup).filter(FileGroup.id == fg1_id).first() is not None
        assert test_db.query(FileGroup).filter(FileGroup.id == fg2_id).first() is not None

        # Delete server
        test_db.delete(server)
        test_db.commit()

        # Verify file groups are deleted (CASCADE)
        test_db.expire_all()
        assert test_db.query(FileGroup).filter(FileGroup.id == fg1_id).first() is None
        assert test_db.query(FileGroup).filter(FileGroup.id == fg2_id).first() is None


# ============================================
# Phase 14.3: Full Flow Tests
# ============================================

class TestFullFlowTests:
    """End-to-end integration tests"""

    def test_full_flow_create_speaker_with_server(self, client: TestClient, test_db):
        """Full flow: Create server category -> server -> speaker with server_id"""
        # Step 1: Create server via API (first need category)
        category = ServerCategory(
            name="방송서버",
            type_server=EnumServerType.SPEAKER_API,
            description="방송 서버"
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버1",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Step 2: Create speaker with server_id via API
        speaker_payload = {
            "number_device": 2403,
            "name_device": "VCS_2403",
            "server_id": server.id,
            "speaker_type": "NORMAL",
            "description": "테스트 스피커"
        }
        response = client.post("/api/devices/speakers", json=speaker_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["server"] is not None
        assert data["data"]["server"]["id"] == server.id
        assert data["data"]["server"]["name"] == "방송서버1"

    def test_full_flow_speaker_nested_response_structure(self, client: TestClient, test_db):
        """Verify speaker response has correct nested server structure"""
        # Setup
        category = ServerCategory(
            name="방송서버",
            type_server=EnumServerType.SPEAKER_API,
            description="방송 서버"
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버1",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080,
            hostname="broadcast-server-1",
            user_name="admin",
            user_password="secret123"
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        speaker = Speaker(
            number_device=2404,
            group_device=0,
            name_device="VCS_2404",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.ADMIN,
            server_id=server.id,
            description="관리자 스피커"
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        # Get speaker via API
        response = client.get(f"/api/devices/speakers/{speaker.id}")
        assert response.status_code == 200
        data = response.json()

        # Verify speaker fields
        speaker_data = data["data"]
        assert speaker_data["id"] == speaker.id
        # SPEC-6.1: category_device는 polymorphic discriminator로 API 응답에 포함하지 않음
        assert "category_device" not in speaker_data
        assert speaker_data["number_device"] == 2404
        assert speaker_data["name_device"] == "VCS_2404"
        assert speaker_data["type_device"] == "IpSpeaker"
        assert speaker_data["status"] == "ACTIVATED"
        assert speaker_data["speaker_type"] == "ADMIN"
        assert speaker_data["description"] == "관리자 스피커"
        assert "created_at" in speaker_data
        assert "updated_at" in speaker_data

        # Verify nested server structure (ServerNestedResponse)
        server_nested = speaker_data["server"]
        assert server_nested is not None
        assert server_nested["id"] == server.id
        assert server_nested["name"] == "방송서버1"
        assert server_nested["status"] == "NORMAL"
        assert server_nested["ip_address"] == "192.168.1.100"
        assert server_nested["port"] == 8080
        assert server_nested["hostname"] == "broadcast-server-1"
        assert server_nested["user_name"] == "admin"
        assert server_nested["user_password"] == "secret123"
        # ServerNestedResponse should NOT have timestamps
        assert "created_at" not in server_nested
        assert "updated_at" not in server_nested
