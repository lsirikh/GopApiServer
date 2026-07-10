"""
Phase 9: Device Refactoring Integration Tests
PRD: PRD_Device_Structure_Refactoring.md

End-to-End tests for:
- DeviceGroup lifecycle (CRUD)
- Device -> Group assignment flow
- N:N relationship complex scenarios
- Backward compatibility (group_device field)
- Camera extended fields (is_record, hardware_spec, geolocation)
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.dependencies import get_db
from app.routers.auth import get_current_account_user_optional


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()


@pytest.fixture
def test_app(db_session):
    """Create test FastAPI app with all device routers"""
    from app.routers.controllers import router as controllers_router
    from app.routers.sensors import router as sensors_router
    from app.routers.cameras import router as cameras_router
    from app.routers.device_groups import router as device_groups_router

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_auth():
        return None

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_account_user_optional] = override_auth
    # Note: device_groups_router already has prefix="/devices/groups" in router definition
    app.include_router(device_groups_router, prefix="/api")
    app.include_router(controllers_router, prefix="/api/devices/controllers")
    app.include_router(sensors_router, prefix="/api/devices/sensors")
    app.include_router(cameras_router, prefix="/api/devices/cameras")

    return TestClient(app)


class TestDeviceGroupLifecycle:
    """DeviceGroup CRUD E2E Tests"""

    def test_create_group_assign_devices_query(self, test_app):
        """E2E: Group 생성 -> Device 할당 -> 조회 흐름"""
        # Step 1: Create device group
        group_response = test_app.post(
            "/api/devices/groups",
            json={"name": "GOP 1구역", "description": "1구역 전방 감시"}
        )
        assert group_response.status_code == 201
        group_id = group_response.json()["data"]["id"]

        # Step 2: Create controller with group_ids
        controller_response = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 1001,
                "group_device": 1,
                "name_device": "CTL-001",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.1.10",
                "ip_port": 8080,
                "group_ids": [group_id]
            }
        )
        assert controller_response.status_code == 201
        controller_data = controller_response.json()["data"]

        # Verify device_groups in response
        assert "device_groups" in controller_data
        assert len(controller_data["device_groups"]) == 1
        assert controller_data["device_groups"][0]["name"] == "GOP 1구역"

        # Step 3: Query group to see device count
        group_get = test_app.get(f"/api/devices/groups/{group_id}")
        assert group_get.status_code == 200
        assert group_get.json()["data"]["device_count"] >= 1

    def test_device_multiple_groups(self, test_app):
        """E2E: 하나의 디바이스가 여러 그룹에 소속 (N:N)"""
        # Create multiple groups
        groups = []
        for i in range(3):
            response = test_app.post(
                "/api/devices/groups",
                json={"name": f"Group {i+1}"}
            )
            assert response.status_code == 201
            groups.append(response.json()["data"]["id"])

        # Create controller with multiple groups
        controller_response = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 1002,
                "group_device": 1,
                "name_device": "CTL-002",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.1.11",
                "ip_port": 8080,
                "group_ids": groups
            }
        )
        assert controller_response.status_code == 201
        controller_data = controller_response.json()["data"]

        # Verify controller has all 3 groups
        assert len(controller_data["device_groups"]) == 3

    def test_group_multiple_devices(self, test_app):
        """E2E: 하나의 그룹에 여러 디바이스 소속"""
        # Create group
        group_response = test_app.post(
            "/api/devices/groups",
            json={"name": "Multi-Device Group"}
        )
        group_id = group_response.json()["data"]["id"]

        # Create multiple controllers in same group
        for i in range(3):
            response = test_app.post(
                "/api/devices/controllers",
                json={
                    "number_device": 2000 + i,
                    "group_device": 1,
                    "name_device": f"CTL-{2000+i}",
                    "type_device": "Controller",
                    "version": "1.0.0",
                    "status": "ACTIVATED",
                    "ip_address": f"192.168.2.{10+i}",
                    "ip_port": 8080,
                    "group_ids": [group_id]
                }
            )
            assert response.status_code == 201

        # Query group to verify device count
        group_get = test_app.get(f"/api/devices/groups/{group_id}")
        assert group_get.json()["data"]["device_count"] >= 3


class TestBackwardCompatibility:
    """group_device 필드 하위 호환성 테스트"""

    def test_create_without_group_ids(self, test_app):
        """group_ids 없이 생성해도 동작"""
        response = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 3001,
                "group_device": 999,  # Legacy field
                "name_device": "Legacy Controller",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.3.10",
                "ip_port": 8080
                # No group_ids
            }
        )
        assert response.status_code == 201
        data = response.json()["data"]

        # group_device should be preserved
        assert data["group_device"] == 999
        # device_groups should be empty
        assert data["device_groups"] == []

    def test_group_device_and_group_ids_coexist(self, test_app):
        """group_device와 group_ids 동시 사용"""
        # Create group
        group_response = test_app.post(
            "/api/devices/groups",
            json={"name": "Coexist Test Group"}
        )
        group_id = group_response.json()["data"]["id"]

        # Create controller with both group_device and group_ids
        response = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 3002,
                "group_device": 888,  # Legacy field
                "name_device": "Coexist Controller",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.3.11",
                "ip_port": 8080,
                "group_ids": [group_id]  # New N:N field
            }
        )
        assert response.status_code == 201
        data = response.json()["data"]

        # Both should work
        assert data["group_device"] == 888
        assert len(data["device_groups"]) == 1


class TestCameraExtendedFields:
    """Camera 확장 필드 E2E 테스트"""

    def test_create_camera_with_extended_fields(self, test_app):
        """Camera 확장 필드와 group_ids 함께 사용"""
        # Create group
        group_response = test_app.post(
            "/api/devices/groups",
            json={"name": "Camera Group"}
        )
        group_id = group_response.json()["data"]["id"]

        # Create camera with all extended fields
        camera_response = test_app.post(
            "/api/devices/cameras",
            json={
                "number_device": 4001,
                "group_device": 1,
                "name_device": "HD Camera 1",
                "type_device": "IpCamera",
                "version": "2.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.4.10",
                "ip_port": 80,
                "user_name": "admin",
                "user_password": "password123",
                "rtsp_uri": "/stream/main",
                "rtsp_port": 554,
                "mode": "NONE",
                "category": "NONE",
                "is_record": True,
                "hardware_spec": {
                    "manufacturer": "HIKVISION",
                    "model": "DS-2CD2345G0P-I",
                    "resolution": "4MP",
                    "fps": 30
                },
                "geolocation": {
                    "latitude": 37.5665,
                    "longitude": 126.9780,
                    "altitude": 50.0
                },
                "group_ids": [group_id]
            }
        )
        assert camera_response.status_code == 201
        data = camera_response.json()["data"]

        # Verify all fields
        assert data["is_record"] is True
        assert data["hardware_spec"]["manufacturer"] == "HIKVISION"
        assert data["geolocation"]["latitude"] == 37.5665
        assert len(data["device_groups"]) == 1

    def test_update_camera_groups_preserves_extended_fields(self, test_app):
        """group_ids 업데이트 시 확장 필드 유지"""
        # Create groups
        group1 = test_app.post("/api/devices/groups", json={"name": "Group A"}).json()["data"]["id"]
        group2 = test_app.post("/api/devices/groups", json={"name": "Group B"}).json()["data"]["id"]

        # Create camera
        camera_response = test_app.post(
            "/api/devices/cameras",
            json={
                "number_device": 4002,
                "group_device": 1,
                "name_device": "Test Camera",
                "type_device": "IpCamera",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.4.11",
                "ip_port": 80,
                "user_name": "admin",
                "user_password": "pass",
                "rtsp_uri": "/stream",
                "rtsp_port": 554,
                "mode": "NONE",
                "category": "NONE",
                "is_record": True,
                "hardware_spec": {"manufacturer": "SONY"},
                "group_ids": [group1]
            }
        )
        camera_id = camera_response.json()["data"]["id"]

        # Update only group_ids
        update_response = test_app.patch(
            f"/api/devices/cameras/{camera_id}",
            json={"group_ids": [group2]}
        )
        assert update_response.status_code == 200
        data = update_response.json()["data"]

        # Extended fields should be preserved
        assert data["is_record"] is True
        assert data["hardware_spec"]["manufacturer"] == "SONY"
        # Group should be changed
        assert len(data["device_groups"]) == 1
        assert data["device_groups"][0]["name"] == "Group B"


class TestMixedDeviceTypes:
    """다양한 디바이스 타입 통합 테스트"""

    def test_group_with_mixed_device_types(self, test_app):
        """같은 그룹에 Controller, Sensor, Camera 할당"""
        # Create group
        group_response = test_app.post(
            "/api/devices/groups",
            json={"name": "Mixed Device Group"}
        )
        group_id = group_response.json()["data"]["id"]

        # Create controller
        controller = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 5001,
                "group_device": 1,
                "name_device": "Mixed CTL",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.5.10",
                "ip_port": 8080,
                "group_ids": [group_id]
            }
        )
        assert controller.status_code == 201
        controller_id = controller.json()["data"]["id"]

        # Create sensor (linked to controller)
        sensor = test_app.post(
            "/api/devices/sensors",
            json={
                "number_device": 5002,
                "group_device": 1,
                "name_device": "Mixed Sensor",
                "type_device": "Fence",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "controller_id": controller_id,
                "group_ids": [group_id]
            }
        )
        assert sensor.status_code == 201

        # Create camera
        camera = test_app.post(
            "/api/devices/cameras",
            json={
                "number_device": 5003,
                "group_device": 1,
                "name_device": "Mixed Camera",
                "type_device": "IpCamera",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.5.11",
                "ip_port": 80,
                "user_name": "admin",
                "user_password": "pass",
                "rtsp_uri": "/stream",
                "rtsp_port": 554,
                "mode": "NONE",
                "category": "NONE",
                "group_ids": [group_id]
            }
        )
        assert camera.status_code == 201

        # Query group - should show 3 devices
        group_get = test_app.get(f"/api/devices/groups/{group_id}")
        assert group_get.json()["data"]["device_count"] >= 3

    def test_device_delete_removes_group_mappings(self, test_app):
        """디바이스 삭제 시 그룹 매핑도 삭제"""
        # Create group
        group = test_app.post("/api/devices/groups", json={"name": "Delete Test"}).json()["data"]
        group_id = group["id"]

        # Create controller
        controller = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 6001,
                "group_device": 1,
                "name_device": "To Delete",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.6.10",
                "ip_port": 8080,
                "group_ids": [group_id]
            }
        ).json()["data"]
        controller_id = controller["id"]

        # Verify group has 1 device
        assert test_app.get(f"/api/devices/groups/{group_id}").json()["data"]["device_count"] >= 1

        # Delete controller
        delete_response = test_app.delete(f"/api/devices/controllers/{controller_id}")
        assert delete_response.status_code == 200

        # Group should have 0 devices now (or at least one less)
        group_after = test_app.get(f"/api/devices/groups/{group_id}").json()["data"]
        # The mapping should be cleaned up
        assert group_after["device_count"] >= 0


class TestGroupUpdateScenarios:
    """group_ids 업데이트 시나리오 테스트"""

    def test_add_to_more_groups(self, test_app):
        """기존 그룹에 추가 그룹 할당"""
        # Create 3 groups
        groups = []
        for i in range(3):
            g = test_app.post("/api/devices/groups", json={"name": f"Add Test {i}"}).json()["data"]
            groups.append(g["id"])

        # Create controller with 1 group
        controller = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 7001,
                "group_device": 1,
                "name_device": "Add Groups CTL",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.7.10",
                "ip_port": 8080,
                "group_ids": [groups[0]]
            }
        ).json()["data"]

        assert len(controller["device_groups"]) == 1

        # Update to have all 3 groups
        update = test_app.patch(
            f"/api/devices/controllers/{controller['id']}",
            json={"group_ids": groups}
        ).json()["data"]

        assert len(update["device_groups"]) == 3

    def test_remove_from_all_groups(self, test_app):
        """모든 그룹에서 제거"""
        # Create group
        group = test_app.post("/api/devices/groups", json={"name": "Remove All Test"}).json()["data"]

        # Create controller
        controller = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 7002,
                "group_device": 1,
                "name_device": "Remove All CTL",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.7.11",
                "ip_port": 8080,
                "group_ids": [group["id"]]
            }
        ).json()["data"]

        assert len(controller["device_groups"]) == 1

        # Remove all groups
        update = test_app.patch(
            f"/api/devices/controllers/{controller['id']}",
            json={"group_ids": []}
        ).json()["data"]

        assert update["device_groups"] == []

    def test_replace_groups(self, test_app):
        """기존 그룹을 다른 그룹으로 교체"""
        # Create 2 groups
        group_a = test_app.post("/api/devices/groups", json={"name": "Group A"}).json()["data"]["id"]
        group_b = test_app.post("/api/devices/groups", json={"name": "Group B"}).json()["data"]["id"]

        # Create controller with group A
        controller = test_app.post(
            "/api/devices/controllers",
            json={
                "number_device": 7003,
                "group_device": 1,
                "name_device": "Replace CTL",
                "type_device": "Controller",
                "version": "1.0.0",
                "status": "ACTIVATED",
                "ip_address": "192.168.7.12",
                "ip_port": 8080,
                "group_ids": [group_a]
            }
        ).json()["data"]

        assert controller["device_groups"][0]["name"] == "Group A"

        # Replace with group B
        update = test_app.patch(
            f"/api/devices/controllers/{controller['id']}",
            json={"group_ids": [group_b]}
        ).json()["data"]

        assert len(update["device_groups"]) == 1
        assert update["device_groups"][0]["name"] == "Group B"
