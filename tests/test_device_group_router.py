"""
DeviceGroup Router Tests (TDD - Red Phase)
PRD: PRD_Device_Structure_Refactoring.md - Phase 6
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import models at module level to ensure they're registered with Base
from app.models.device_group import DeviceGroup, DeviceGroupMapping  # noqa: F401
from app.models.device import Controller  # noqa: F401
from app.database import Base
from tests.conftest import get_test_engine


def get_test_app(test_db):
    """테스트용 FastAPI 앱 생성"""
    from app.routers.device_groups import router as device_groups_router
    from app.dependencies import get_db
    from app.routers.auth import get_current_account_user_optional

    # Get the shared test engine and session factory
    engine, TestingSessionLocal = get_test_engine()

    def override_get_db():
        """Override to use the same shared test database"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_auth():
        return None  # Public mode

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_account_user_optional] = override_auth
    app.include_router(device_groups_router, prefix="/api")

    return TestClient(app)


class TestDeviceGroupList:
    """GET /api/devices/groups 테스트"""

    def test_get_device_groups_empty(self, test_db):
        """빈 목록 반환 테스트"""
        client = get_test_app(test_db)
        response = client.get("/api/devices/groups")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert "pagination" in data

    def test_get_device_groups_with_data(self, test_db):
        """데이터 목록 반환 테스트"""
        from app.models.device_group import DeviceGroup

        # 테스트 그룹 생성
        group1 = DeviceGroup(name="GOP 1구역", description="1구역 그룹")
        group2 = DeviceGroup(name="GOP 2구역", description="2구역 그룹")
        test_db.add_all([group1, group2])
        test_db.commit()

        client = get_test_app(test_db)
        response = client.get("/api/devices/groups")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["name"] in ["GOP 1구역", "GOP 2구역"]


class TestDeviceGroupGet:
    """GET /api/devices/groups/{group_id} 테스트"""

    def test_get_device_group_by_id(self, test_db):
        """ID로 단건 조회 테스트"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="테스트 그룹", description="테스트 설명")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        client = get_test_app(test_db)
        response = client.get(f"/api/devices/groups/{group.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == group.id
        assert data["data"]["name"] == "테스트 그룹"

    def test_get_device_group_not_found(self, test_db):
        """존재하지 않는 그룹 조회 테스트"""
        client = get_test_app(test_db)
        response = client.get("/api/devices/groups/99999")

        assert response.status_code == 404
        data = response.json()
        # FastAPI HTTPException returns detail field, not success
        assert "detail" in data
        assert data["detail"]["success"] is False


class TestDeviceGroupCreate:
    """POST /api/devices/groups 테스트"""

    def test_create_device_group(self, test_db):
        """그룹 생성 테스트"""
        client = get_test_app(test_db)
        response = client.post(
            "/api/devices/groups",
            json={"name": "새 그룹", "description": "새로운 그룹 설명"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "새 그룹"
        assert data["data"]["description"] == "새로운 그룹 설명"
        assert "id" in data["data"]

    def test_create_device_group_without_description(self, test_db):
        """description 없이 그룹 생성 테스트"""
        client = get_test_app(test_db)
        response = client.post(
            "/api/devices/groups",
            json={"name": "그룹만"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == "그룹만"
        assert data["data"]["description"] is None

    def test_create_device_group_duplicate_name(self, test_db):
        """중복 이름 그룹 생성 테스트"""
        from app.models.device_group import DeviceGroup

        existing_group = DeviceGroup(name="중복 이름")
        test_db.add(existing_group)
        test_db.commit()

        client = get_test_app(test_db)
        response = client.post(
            "/api/devices/groups",
            json={"name": "중복 이름"}
        )

        assert response.status_code == 400
        data = response.json()
        # FastAPI HTTPException returns detail field, not success
        assert "detail" in data
        assert data["detail"]["success"] is False


class TestDeviceGroupUpdate:
    """PATCH/PUT /api/devices/groups/{group_id} 테스트"""

    def test_patch_device_group(self, test_db):
        """PATCH 부분 수정 테스트"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="원래 이름", description="원래 설명")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        client = get_test_app(test_db)
        response = client.patch(
            f"/api/devices/groups/{group.id}",
            json={"name": "수정된 이름"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "수정된 이름"
        assert data["data"]["description"] == "원래 설명"  # 변경되지 않음

    def test_put_device_group(self, test_db):
        """PUT 전체 수정 테스트"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="원래 이름", description="원래 설명")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        client = get_test_app(test_db)
        response = client.put(
            f"/api/devices/groups/{group.id}",
            json={"name": "완전히 새 이름", "description": "완전히 새 설명"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "완전히 새 이름"
        assert data["data"]["description"] == "완전히 새 설명"

    def test_update_device_group_not_found(self, test_db):
        """존재하지 않는 그룹 수정 테스트"""
        client = get_test_app(test_db)
        response = client.patch(
            "/api/devices/groups/99999",
            json={"name": "수정"}
        )

        assert response.status_code == 404


class TestDeviceGroupDelete:
    """DELETE /api/devices/groups/{group_id} 테스트"""

    def test_delete_device_group(self, test_db):
        """그룹 삭제 테스트"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="삭제할 그룹")
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        client = get_test_app(test_db)
        response = client.delete(f"/api/devices/groups/{group.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 삭제 확인
        response = client.get(f"/api/devices/groups/{group.id}")
        assert response.status_code == 404

    def test_delete_device_group_not_found(self, test_db):
        """존재하지 않는 그룹 삭제 테스트"""
        client = get_test_app(test_db)
        response = client.delete("/api/devices/groups/99999")

        assert response.status_code == 404


class TestDeviceAssignment:
    """POST/DELETE /api/devices/groups/{group_id}/devices 테스트"""

    def test_assign_devices_to_group(self, test_db):
        """디바이스 그룹 할당 테스트"""
        from app.models.device_group import DeviceGroup
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        group = DeviceGroup(name="할당 테스트 그룹")
        test_db.add(group)

        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="CTL-001",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()
        test_db.refresh(group)
        test_db.refresh(controller)

        client = get_test_app(test_db)
        response = client.post(
            f"/api/devices/groups/{group.id}/devices",
            json={"device_ids": [controller.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert controller.id in data["data"]["assigned_device_ids"]

    def test_remove_device_from_group(self, test_db):
        """디바이스 그룹 제거 테스트"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        group = DeviceGroup(name="제거 테스트 그룹")
        test_db.add(group)

        controller = Controller(
            number_device=1002,
            group_device=1,
            name_device="CTL-002",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.11",
            ip_port=8080
        )
        test_db.add(controller)
        test_db.commit()

        # 매핑 생성
        mapping = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group.id)
        test_db.add(mapping)
        test_db.commit()

        client = get_test_app(test_db)
        response = client.delete(
            f"/api/devices/groups/{group.id}/devices/{controller.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["device_id"] == controller.id

    def test_assign_devices_group_not_found(self, test_db):
        """존재하지 않는 그룹에 디바이스 할당 테스트"""
        client = get_test_app(test_db)
        response = client.post(
            "/api/devices/groups/99999/devices",
            json={"device_ids": [1]}
        )

        assert response.status_code == 404
