"""
Tests for FileGroup Router
PRD: PRD_Speaker_Device.md - Phase 10-13: FileGroup Router CRUD
TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.server import Server, ServerCategory
from app.models.file_group import FileGroup
from app.utils.enums import EnumServerType, EnumServerStatus


# ============================================
# Phase 10: FileGroup Router - List & Get
# ============================================

class TestGetFileGroupsList:
    """Test GET /api/file-groups endpoint"""

    def test_get_file_groups_list_success(self, client: TestClient, test_db):
        """Should return list of file groups"""
        # Setup: Create server and file group
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
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

        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보",
            files=["fire_alarm.mp3", "evacuate.mp3"]
        )
        test_db.add(file_group)
        test_db.commit()

        response = client.get("/api/file-groups")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_get_file_groups_list_empty(self, client: TestClient, test_db):
        """Should return empty list when no file groups exist"""
        # Clear any existing file groups
        test_db.query(FileGroup).delete()
        test_db.commit()

        response = client.get("/api/file-groups")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_file_groups_list_filter_by_server_id(self, client: TestClient, test_db):
        """Should filter file groups by server_id"""
        # Setup: Create category
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        # Create two servers
        server1 = Server(
            category_id=category.id,
            name="방송서버1",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        server2 = Server(
            category_id=category.id,
            name="방송서버2",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.101",
            port=8080
        )
        test_db.add_all([server1, server2])
        test_db.commit()
        test_db.refresh(server1)
        test_db.refresh(server2)

        # Create file groups for each server
        fg1 = FileGroup(server_id=server1.id, group_id=1, group_name="화재경보")
        fg2 = FileGroup(server_id=server2.id, group_id=1, group_name="긴급방송")
        test_db.add_all([fg1, fg2])
        test_db.commit()

        response = client.get(f"/api/file-groups?server_id={server1.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["server_id"] == server1.id

    def test_get_file_groups_list_pagination(self, client: TestClient, test_db):
        """Should support pagination"""
        # Setup: Create server
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Create multiple file groups
        for i in range(5):
            fg = FileGroup(server_id=server.id, group_id=i+10, group_name=f"그룹{i}")
            test_db.add(fg)
        test_db.commit()

        response = client.get("/api/file-groups?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2


class TestGetFileGroupById:
    """Test GET /api/file-groups/{id} endpoint"""

    def test_get_file_group_by_id_success(self, client: TestClient, test_db):
        """Should return file group by ID"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보",
            files=["fire.mp3"]
        )
        test_db.add(file_group)
        test_db.commit()
        test_db.refresh(file_group)

        response = client.get(f"/api/file-groups/{file_group.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == file_group.id
        assert data["data"]["group_name"] == "화재경보"

    def test_get_file_group_by_id_not_found(self, client: TestClient, test_db):
        """Should return 404 for non-existent file group"""
        response = client.get("/api/file-groups/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


# ============================================
# Phase 11: FileGroup Router - Create
# ============================================

class TestCreateFileGroup:
    """Test POST /api/file-groups endpoint"""

    def test_create_file_group_success(self, client: TestClient, test_db):
        """Should create file group successfully"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        payload = {
            "server_id": server.id,
            "group_id": 100,
            "group_name": "긴급방송"
        }

        response = client.post("/api/file-groups", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["group_name"] == "긴급방송"
        assert data["data"]["group_id"] == 100

    def test_create_file_group_server_not_found(self, client: TestClient, test_db):
        """Should return 404 for non-existent server"""
        payload = {
            "server_id": 99999,
            "group_id": 1,
            "group_name": "화재경보"
        }

        response = client.post("/api/file-groups", json=payload)
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_create_file_group_with_files(self, client: TestClient, test_db):
        """Should create file group with files list"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        payload = {
            "server_id": server.id,
            "group_id": 200,
            "group_name": "화재경보",
            "files": ["fire_alarm.mp3", "evacuate.mp3", "all_clear.mp3"]
        }

        response = client.post("/api/file-groups", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["files"] == ["fire_alarm.mp3", "evacuate.mp3", "all_clear.mp3"]

    def test_create_file_group_duplicate_server_group_id(self, client: TestClient, test_db):
        """Should return error for duplicate server_id + group_id"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Create first file group
        fg = FileGroup(server_id=server.id, group_id=300, group_name="기존그룹")
        test_db.add(fg)
        test_db.commit()

        # Try to create duplicate
        payload = {
            "server_id": server.id,
            "group_id": 300,  # Same group_id
            "group_name": "중복그룹"
        }

        response = client.post("/api/file-groups", json=payload)
        assert response.status_code == 409  # Conflict
        data = response.json()
        assert data["success"] is False


# ============================================
# Phase 12: FileGroup Router - Update (PATCH/PUT)
# ============================================

class TestPatchFileGroup:
    """Test PATCH /api/file-groups/{id} endpoint"""

    def test_patch_file_group_success(self, client: TestClient, test_db):
        """Should update file group with PATCH"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보"
        )
        test_db.add(file_group)
        test_db.commit()
        test_db.refresh(file_group)

        payload = {
            "group_name": "긴급화재경보"
        }

        response = client.patch(f"/api/file-groups/{file_group.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["group_name"] == "긴급화재경보"

    def test_patch_file_group_not_found(self, client: TestClient, test_db):
        """Should return 404 for non-existent file group"""
        payload = {"group_name": "Test"}

        response = client.patch("/api/file-groups/99999", json=payload)
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_patch_file_group_update_files(self, client: TestClient, test_db):
        """Should update files list with PATCH"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보",
            files=["old1.mp3", "old2.mp3"]
        )
        test_db.add(file_group)
        test_db.commit()
        test_db.refresh(file_group)

        payload = {
            "files": ["new1.mp3", "new2.mp3", "new3.mp3"]
        }

        response = client.patch(f"/api/file-groups/{file_group.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["files"] == ["new1.mp3", "new2.mp3", "new3.mp3"]


class TestPutFileGroup:
    """Test PUT /api/file-groups/{id} endpoint"""

    def test_put_file_group_success(self, client: TestClient, test_db):
        """Should replace file group with PUT"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보",
            files=["old.mp3"]
        )
        test_db.add(file_group)
        test_db.commit()
        test_db.refresh(file_group)

        payload = {
            "server_id": server.id,
            "group_id": 1,
            "group_name": "완전변경됨",
            "files": ["completely_new.mp3"]
        }

        response = client.put(f"/api/file-groups/{file_group.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["group_name"] == "완전변경됨"
        assert data["data"]["files"] == ["completely_new.mp3"]

    def test_put_file_group_replaces_all_fields(self, client: TestClient, test_db):
        """PUT should replace all fields including nulling optional ones"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보",
            files=["fire.mp3", "evacuate.mp3"]
        )
        test_db.add(file_group)
        test_db.commit()
        test_db.refresh(file_group)

        # PUT without files (should clear them)
        payload = {
            "server_id": server.id,
            "group_id": 1,
            "group_name": "새그룹"
            # files not provided - should become null
        }

        response = client.put(f"/api/file-groups/{file_group.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["group_name"] == "새그룹"
        assert data["data"]["files"] is None


# ============================================
# Phase 13: FileGroup Router - Delete
# ============================================

class TestDeleteFileGroup:
    """Test DELETE /api/file-groups/{id} endpoint"""

    def test_delete_file_group_success(self, client: TestClient, test_db):
        """Should delete file group successfully"""
        # Setup
        category = ServerCategory(name="방송서버", type_server=EnumServerType.MEDIA, description="방송 서버")
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        server = Server(
            category_id=category.id,
            name="방송서버",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="삭제될그룹"
        )
        test_db.add(file_group)
        test_db.commit()
        test_db.refresh(file_group)
        fg_id = file_group.id

        response = client.delete(f"/api/file-groups/{fg_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        deleted_fg = test_db.query(FileGroup).filter(FileGroup.id == fg_id).first()
        assert deleted_fg is None

    def test_delete_file_group_not_found(self, client: TestClient, test_db):
        """Should return 404 for non-existent file group"""
        response = client.delete("/api/file-groups/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
