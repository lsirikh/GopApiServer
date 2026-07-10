"""
Test: ProxySetting Router (GET/PATCH)
PRD: PRD_Device_Setting.md Section 5.1
"""
import pytest
from app.models.server import Server, ServerCategory
from app.models.device_setting import ProxySetting


class TestProxySettingGet:
    """Tests for GET /api/servers/{server_id}/proxy-settings"""

    def test_get_proxy_settings_server_not_found(self, client, test_db):
        """6.1: 존재하지 않는 서버 → 404"""
        response = client.get("/api/servers/9999/proxy-settings")
        assert response.status_code == 404

    def test_get_proxy_settings_lazy_create(self, client, test_db):
        """6.3: 설정 없을 때 → 기본값 Lazy 생성 후 200"""
        # Create server
        category = ServerCategory(name="Test Category", type_server="VMS")
        test_db.add(category)
        test_db.commit()
        server = Server(name="Test Server", category_id=category.id, ip_address="1.1.1.1", port=8080)
        test_db.add(server)
        test_db.commit()

        response = client.get(f"/api/servers/{server.id}/proxy-settings")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["server_id"] == server.id
        assert data["data"]["operation_mode"] == "NORMAL"
        assert data["data"]["windy_mode"] == "wind0"

    def test_get_proxy_settings_existing(self, client, test_db):
        """6.5: 기존 설정 반환 (중복 생성 안함)"""
        category = ServerCategory(name="Test Category", type_server="VMS")
        test_db.add(category)
        test_db.commit()
        server = Server(name="Test Server", category_id=category.id, ip_address="1.1.1.1", port=8080)
        test_db.add(server)
        test_db.commit()

        # First call creates
        response1 = client.get(f"/api/servers/{server.id}/proxy-settings")
        assert response1.status_code == 200

        # Second call returns same
        response2 = client.get(f"/api/servers/{server.id}/proxy-settings")
        assert response2.status_code == 200
        assert response2.json()["data"]["id"] == response1.json()["data"]["id"]

    def test_get_proxy_settings_api_response_format(self, client, test_db):
        """6.7: ApiResponse 형식 확인"""
        category = ServerCategory(name="Test Category", type_server="VMS")
        test_db.add(category)
        test_db.commit()
        server = Server(name="Test Server", category_id=category.id, ip_address="1.1.1.1", port=8080)
        test_db.add(server)
        test_db.commit()

        response = client.get(f"/api/servers/{server.id}/proxy-settings")
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert data["data"]["id"] is not None
        assert data["data"]["created_at"] is not None
        assert data["data"]["updated_at"] is not None


class TestProxySettingPatch:
    """Tests for PATCH /api/servers/{server_id}/proxy-settings"""

    def _create_server(self, db):
        category = ServerCategory(name="Test Category", type_server="VMS")
        db.add(category)
        db.commit()
        server = Server(name="Test Server", category_id=category.id, ip_address="1.1.1.1", port=8080)
        db.add(server)
        db.commit()
        return server

    def test_patch_proxy_settings_server_not_found(self, client, test_db):
        """7.1: 존재하지 않는 서버 → 404"""
        response = client.patch("/api/servers/9999/proxy-settings", json={"operation_mode": "REGISTER"})
        assert response.status_code == 404

    def test_patch_proxy_settings_upsert(self, client, test_db):
        """7.3: 설정 없을 때 → Upsert (생성 + 요청 필드 적용)"""
        server = self._create_server(test_db)

        response = client.patch(
            f"/api/servers/{server.id}/proxy-settings",
            json={"operation_mode": "REGISTER"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["operation_mode"] == "REGISTER"
        assert data["windy_mode"] == "wind0"  # default preserved

    def test_patch_proxy_settings_partial_update(self, client, test_db):
        """7.5: 기존 설정 부분 업데이트"""
        server = self._create_server(test_db)

        # Create via GET first
        client.get(f"/api/servers/{server.id}/proxy-settings")

        # Update only windy_mode
        response = client.patch(
            f"/api/servers/{server.id}/proxy-settings",
            json={"windy_mode": "wind3"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["windy_mode"] == "wind3"
        assert data["operation_mode"] == "NORMAL"  # unchanged

    def test_patch_proxy_settings_single_field(self, client, test_db):
        """7.7: 단일 필드만 업데이트 (나머지 유지)"""
        server = self._create_server(test_db)

        # Set both fields
        client.patch(
            f"/api/servers/{server.id}/proxy-settings",
            json={"operation_mode": "REGISTER", "windy_mode": "wind2"}
        )

        # Update only operation_mode
        response = client.patch(
            f"/api/servers/{server.id}/proxy-settings",
            json={"operation_mode": "NORMAL"}
        )
        data = response.json()["data"]
        assert data["operation_mode"] == "NORMAL"
        assert data["windy_mode"] == "wind2"  # preserved


class TestProxySettingPut:
    """Tests for PUT /api/servers/{server_id}/proxy-settings"""

    def _create_server(self, db):
        category = ServerCategory(name="Test Category", type_server="VMS")
        db.add(category)
        db.commit()
        server = Server(name="Test Server", category_id=category.id, ip_address="1.1.1.1", port=8080)
        db.add(server)
        db.commit()
        return server

    def test_put_proxy_settings_server_not_found(self, client, test_db):
        """6.1 v1.1: PUT 존재하지 않는 서버 → 404"""
        response = client.put(
            "/api/servers/9999/proxy-settings",
            json={"operation_mode": "NORMAL", "windy_mode": "wind0"}
        )
        assert response.status_code == 404

    def test_put_proxy_settings_upsert(self, client, test_db):
        """6.3 v1.1: PUT 설정 없을 때 → Upsert (생성 + 전체 필드 적용)"""
        server = self._create_server(test_db)

        response = client.put(
            f"/api/servers/{server.id}/proxy-settings",
            json={"operation_mode": "REGISTER", "windy_mode": "wind3"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["operation_mode"] == "REGISTER"
        assert data["windy_mode"] == "wind3"
        assert data["server_id"] == server.id

    def test_put_proxy_settings_full_replace(self, client, test_db):
        """6.5 v1.1: PUT 기존 설정 전체 교체"""
        server = self._create_server(test_db)

        # Create initial settings via GET
        client.get(f"/api/servers/{server.id}/proxy-settings")

        # Replace all fields
        response = client.put(
            f"/api/servers/{server.id}/proxy-settings",
            json={"operation_mode": "REGISTER", "windy_mode": "wind2"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["operation_mode"] == "REGISTER"
        assert data["windy_mode"] == "wind2"

    def test_put_proxy_settings_missing_field_422(self, client, test_db):
        """6.7 v1.1: PUT 필수 필드 누락 → 422 Validation Error"""
        server = self._create_server(test_db)

        # Missing windy_mode
        response = client.put(
            f"/api/servers/{server.id}/proxy-settings",
            json={"operation_mode": "NORMAL"}
        )
        assert response.status_code == 422

        # Empty body
        response = client.put(
            f"/api/servers/{server.id}/proxy-settings",
            json={}
        )
        assert response.status_code == 422

    def test_put_proxy_settings_message(self, client, test_db):
        """6.9 v1.1: PUT message 'Proxy settings replaced successfully' 확인"""
        server = self._create_server(test_db)

        response = client.put(
            f"/api/servers/{server.id}/proxy-settings",
            json={"operation_mode": "NORMAL", "windy_mode": "wind0"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Proxy settings replaced successfully"
