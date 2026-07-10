"""
Phase 7: Sensor Router N:N Groups Tests (TDD)
PRD: PRD_Device_Structure_Refactoring.md - Section 2.3

Tests for:
- POST /api/devices/sensors with group_ids support
- Response with device_groups array
- Backward compatibility with group_device
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.dependencies import get_db
from app.models.device import Controller, Sensor, EnumDeviceType, EnumDeviceStatus
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
def test_controller(db_session):
    """Create a test controller for sensors"""
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.1",
        ip_port=502
    )
    db_session.add(controller)
    db_session.commit()
    db_session.refresh(controller)
    return controller


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
def base_sensor_data(test_controller):
    """Base sensor data for tests"""
    return {
        "number_device": 101,
        "group_device": 1,
        "name_device": "Test Sensor",
        "type_device": "Fence",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "controller_id": test_controller.id
    }


class TestSensorCreateWithGroupIds:
    """Sensor POST API with group_ids support"""

    def test_create_sensor_with_group_ids(self, db_session, test_groups, base_sensor_data):
        """POST: group_ids 배열로 센서 생성"""
        from app.routers.sensors import router as sensors_router
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
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        client = TestClient(app)

        # Add group_ids to data
        base_sensor_data["group_ids"] = [test_groups[0].id, test_groups[1].id]

        response = client.post("/api/devices/sensors", json=base_sensor_data)

        assert response.status_code == 201
        data = response.json()["data"]

        # Check device_groups in response
        assert "device_groups" in data
        assert len(data["device_groups"]) == 2
        group_names = [g["name"] for g in data["device_groups"]]
        assert "Test Group 1" in group_names
        assert "Test Group 2" in group_names

    def test_create_sensor_without_group_ids(self, db_session, base_sensor_data):
        """POST: group_ids 없이 생성 (하위 호환성)"""
        from app.routers.sensors import router as sensors_router
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
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        client = TestClient(app)

        response = client.post("/api/devices/sensors", json=base_sensor_data)

        assert response.status_code == 201
        data = response.json()["data"]

        # device_groups should be empty (no groups assigned)
        assert "device_groups" in data
        assert data["device_groups"] == []
        # group_device should still be present for backward compatibility
        assert data["group_device"] == 1


class TestSensorGetWithDeviceGroups:
    """Sensor GET API with device_groups in response"""

    def test_get_sensor_with_device_groups(self, db_session, test_controller, test_groups):
        """GET: device_groups 배열 포함 단건 조회"""
        from app.routers.sensors import router as sensors_router
        from app.routers.auth import get_current_account_user_optional

        # Create sensor with group mappings
        sensor = Sensor(
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device=EnumDeviceType.Fence,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=test_controller.id
        )
        db_session.add(sensor)
        db_session.commit()
        db_session.refresh(sensor)

        # Create mappings
        for group in test_groups[:2]:
            mapping = DeviceGroupMapping(
                device_id=sensor.id,
                category_device="sensor",
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
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        client = TestClient(app)

        response = client.get(f"/api/devices/sensors/{sensor.id}")

        assert response.status_code == 200
        data = response.json()["data"]

        assert "device_groups" in data
        assert len(data["device_groups"]) == 2

    def test_get_sensors_list_with_device_groups(self, db_session, test_controller, test_groups):
        """GET: device_groups 배열 포함 목록 조회"""
        from app.routers.sensors import router as sensors_router
        from app.routers.auth import get_current_account_user_optional

        # Create sensors
        for i in range(1, 3):
            sensor = Sensor(
                number_device=100 + i,
                group_device=1,
                name_device=f"Sensor {i}",
                type_device=EnumDeviceType.Fence,
                version="1.0.0",
                status=EnumDeviceStatus.ACTIVATED,
                controller_id=test_controller.id
            )
            db_session.add(sensor)
        db_session.commit()

        # Add some mappings
        sensors = db_session.query(Sensor).all()
        for idx, sensor in enumerate(sensors):
            mapping = DeviceGroupMapping(
                device_id=sensor.id,
                category_device="sensor",
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
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        client = TestClient(app)

        response = client.get("/api/devices/sensors")

        assert response.status_code == 200
        data = response.json()["data"]

        assert len(data) == 2
        # Each sensor should have device_groups
        for sensor_data in data:
            assert "device_groups" in sensor_data


class TestSensorUpdateWithGroupIds:
    """Sensor PATCH/PUT API with group_ids support"""

    def test_patch_sensor_group_ids(self, db_session, test_controller, test_groups):
        """PATCH: group_ids 수정"""
        from app.routers.sensors import router as sensors_router
        from app.routers.auth import get_current_account_user_optional

        # Create sensor
        sensor = Sensor(
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device=EnumDeviceType.Fence,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=test_controller.id
        )
        db_session.add(sensor)
        db_session.commit()
        db_session.refresh(sensor)

        # Add initial mapping
        mapping = DeviceGroupMapping(
            device_id=sensor.id,
            category_device="sensor",
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
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        client = TestClient(app)

        # Update to new groups
        response = client.patch(
            f"/api/devices/sensors/{sensor.id}",
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

    def test_patch_sensor_empty_group_ids_removes_all(self, db_session, test_controller, test_groups):
        """PATCH: group_ids=[] 로 모든 그룹 제거"""
        from app.routers.sensors import router as sensors_router
        from app.routers.auth import get_current_account_user_optional

        # Create sensor with mappings
        sensor = Sensor(
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device=EnumDeviceType.Fence,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=test_controller.id
        )
        db_session.add(sensor)
        db_session.commit()
        db_session.refresh(sensor)

        for group in test_groups:
            mapping = DeviceGroupMapping(
                device_id=sensor.id,
                category_device="sensor",
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
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        client = TestClient(app)

        # Remove all groups
        response = client.patch(
            f"/api/devices/sensors/{sensor.id}",
            json={"group_ids": []}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["device_groups"] == []


class TestSensorGroupDeviceBackwardCompatibility:
    """Backward compatibility tests for group_device field"""

    def test_response_includes_group_device(self, db_session, base_sensor_data):
        """Response에 group_device 필드 유지"""
        from app.routers.sensors import router as sensors_router
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
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        client = TestClient(app)

        base_sensor_data["group_device"] = 999

        response = client.post("/api/devices/sensors", json=base_sensor_data)

        assert response.status_code == 201
        data = response.json()["data"]

        # group_device should be in response for backward compatibility
        assert "group_device" in data
        assert data["group_device"] == 999
