"""
Phase 7: Camera Router N:N Groups Tests (TDD)
PRD: PRD_Device_Structure_Refactoring.md - Section 2.3
PRD: PRD_Camera_Urls_JsonB.md v1.0 - Updated to use urls JSONB instead of rtsp_uri/rtsp_port

Tests for:
- POST /api/devices/cameras with group_ids support
- Response with device_groups array
- Backward compatibility with group_device
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.dependencies import get_db
from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType
from app.models.device_group import DeviceGroup, DeviceGroupMapping


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()


@pytest.fixture
def test_groups(db_session):
    """Create test device groups"""
    groups = []
    for i in range(1, 4):
        group = DeviceGroup(
            name=f"Test Group {i}",
            description=f"Test group {i} description"
        )
        db_session.add(group)
        groups.append(group)
    db_session.commit()
    for g in groups:
        db_session.refresh(g)
    return groups


@pytest.fixture
def base_camera_data():
    """Base camera data for tests"""
    return {
        "number_device": 1001,
        "group_device": 1,
        "name_device": "Test Camera",
        "type_device": "IpCamera",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.100",
        "ip_port": 80,
        "user_name": "admin",
        "user_password": "password",
        "urls": {"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}}},
        "mode": "NONE",
        "category": "NONE"
    }


class TestCameraCreateWithGroupIds:
    """Camera POST API with group_ids support"""

    def test_create_camera_with_group_ids(self, db_session, test_groups, base_camera_data):
        """POST: group_ids 배열로 카메라 생성"""
        from app.routers.cameras import router as cameras_router
        from app.routers.auth import get_current_account_user_optional

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
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        client = TestClient(app)

        # Add group_ids to data
        base_camera_data["group_ids"] = [test_groups[0].id, test_groups[1].id]

        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]

        # Check device_groups in response
        assert "device_groups" in data
        assert len(data["device_groups"]) == 2
        group_names = [g["name"] for g in data["device_groups"]]
        assert "Test Group 1" in group_names
        assert "Test Group 2" in group_names

    def test_create_camera_without_group_ids(self, db_session, base_camera_data):
        """POST: group_ids 없이 생성 (하위 호환성)"""
        from app.routers.cameras import router as cameras_router
        from app.routers.auth import get_current_account_user_optional

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
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        client = TestClient(app)

        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]

        # device_groups should be empty (no groups assigned)
        assert "device_groups" in data
        assert data["device_groups"] == []
        # group_device should still be present for backward compatibility
        assert data["group_device"] == 1


class TestCameraGetWithDeviceGroups:
    """Camera GET API with device_groups in response"""

    def test_get_camera_with_device_groups(self, db_session, test_groups):
        """GET: device_groups 배열 포함 단건 조회"""
        from app.routers.cameras import router as cameras_router
        from app.routers.auth import get_current_account_user_optional

        # Create camera with group mappings
        camera = Camera(
            number_device=1001,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}}},
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.NONE
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        # Create mappings
        for group in test_groups[:2]:
            mapping = DeviceGroupMapping(
                device_id=camera.id,
                category_device="camera",
                group_id=group.id
            )
            db_session.add(mapping)
        db_session.commit()

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
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        client = TestClient(app)

        response = client.get(f"/api/devices/cameras/{camera.id}")

        assert response.status_code == 200
        data = response.json()["data"]

        assert "device_groups" in data
        assert len(data["device_groups"]) == 2

    def test_get_cameras_list_with_device_groups(self, db_session, test_groups):
        """GET: device_groups 배열 포함 목록 조회"""
        from app.routers.cameras import router as cameras_router
        from app.routers.auth import get_current_account_user_optional

        # Create cameras
        for i in range(1, 3):
            camera = Camera(
                number_device=1000 + i,
                group_device=1,
                name_device=f"Camera {i}",
                type_device=EnumDeviceType.IpCamera,
                version="1.0.0",
                status=EnumDeviceStatus.ACTIVATED,
                ip_address=f"192.168.1.{100 + i}",
                ip_port=80,
                user_name="admin",
                user_password="password",
                urls={"streams": {"rtsp": {"main": f"rtsp://192.168.1.{100+i}:554/stream1"}}},
                mode=EnumCameraMode.NONE,
                category=EnumCameraType.NONE
            )
            db_session.add(camera)
        db_session.commit()

        # Add some mappings
        cameras = db_session.query(Camera).all()
        for idx, camera in enumerate(cameras):
            mapping = DeviceGroupMapping(
                device_id=camera.id,
                category_device="camera",
                group_id=test_groups[idx].id
            )
            db_session.add(mapping)
        db_session.commit()

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
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        client = TestClient(app)

        response = client.get("/api/devices/cameras")

        assert response.status_code == 200
        data = response.json()["data"]

        assert len(data) == 2
        # Each camera should have device_groups
        for camera_data in data:
            assert "device_groups" in camera_data


class TestCameraUpdateWithGroupIds:
    """Camera PATCH/PUT API with group_ids support"""

    def test_patch_camera_group_ids(self, db_session, test_groups):
        """PATCH: group_ids 수정"""
        from app.routers.cameras import router as cameras_router
        from app.routers.auth import get_current_account_user_optional

        # Create camera
        camera = Camera(
            number_device=1001,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}}},
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.NONE
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        # Add initial mapping
        mapping = DeviceGroupMapping(
            device_id=camera.id,
            category_device="camera",
            group_id=test_groups[0].id
        )
        db_session.add(mapping)
        db_session.commit()

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
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        client = TestClient(app)

        # Update to new groups
        response = client.patch(
            f"/api/devices/cameras/{camera.id}",
            json={"group_ids": [test_groups[1].id, test_groups[2].id]}
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # Should have new groups, not old ones
        assert len(data["device_groups"]) == 2
        group_names = [g["name"] for g in data["device_groups"]]
        assert "Test Group 1" not in group_names
        assert "Test Group 2" in group_names
        assert "Test Group 3" in group_names

    def test_patch_camera_empty_group_ids_removes_all(self, db_session, test_groups):
        """PATCH: group_ids=[] 로 모든 그룹 제거"""
        from app.routers.cameras import router as cameras_router
        from app.routers.auth import get_current_account_user_optional

        # Create camera with mappings
        camera = Camera(
            number_device=1001,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}}},
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.NONE
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        for group in test_groups:
            mapping = DeviceGroupMapping(
                device_id=camera.id,
                category_device="camera",
                group_id=group.id
            )
            db_session.add(mapping)
        db_session.commit()

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
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        client = TestClient(app)

        # Remove all groups
        response = client.patch(
            f"/api/devices/cameras/{camera.id}",
            json={"group_ids": []}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["device_groups"] == []


class TestCameraGroupDeviceBackwardCompatibility:
    """Backward compatibility tests for group_device field"""

    def test_response_includes_group_device(self, db_session, base_camera_data):
        """Response에 group_device 필드 유지"""
        from app.routers.cameras import router as cameras_router
        from app.routers.auth import get_current_account_user_optional

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
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        client = TestClient(app)

        base_camera_data["group_device"] = 999

        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]

        # group_device should be in response for backward compatibility
        assert "group_device" in data
        assert data["group_device"] == 999
