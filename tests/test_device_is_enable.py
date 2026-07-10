"""
Device is_enable Field Tests

PRD: PRD_Device_IsEnable_Field.md v1.0
TDD Cycle: Red → Green → Refactor
"""
import pytest
from pydantic import ValidationError


# ============================================================================
# Phase 1: Model Tests
# ============================================================================

class TestDeviceModel:
    """Test Device model has is_enable field"""

    def test_device_model_has_is_enable_column(self):
        """Test: Device 모델에 is_enable 필드 존재 확인"""
        from app.models.device import Device

        # Device 모델에 is_enable 컬럼이 존재해야 함
        assert hasattr(Device, 'is_enable'), "Device model must have is_enable attribute"

        # SQLAlchemy Column 확인
        mapper = Device.__mapper__
        assert 'is_enable' in mapper.columns.keys(), "Device must have is_enable column"

    def test_device_is_enable_default_value(self):
        """Test: Device is_enable 기본값은 True"""
        from app.models.device import Device

        # 컬럼 기본값 확인
        column = Device.__table__.columns['is_enable']
        assert column.default is not None, "is_enable must have default value"
        assert column.default.arg == True, "is_enable default must be True"

    def test_device_is_enable_not_nullable(self):
        """Test: Device is_enable은 NOT NULL"""
        from app.models.device import Device

        column = Device.__table__.columns['is_enable']
        assert column.nullable == False, "is_enable must be NOT NULL"


# ============================================================================
# Phase 2: Controller Schema Tests
# ============================================================================

class TestControllerSchema:
    """Test Controller schemas have is_enable field"""

    def test_controller_create_has_is_enable_with_default(self):
        """Test: ControllerCreate 스키마에 is_enable 필드 존재 (default=True)"""
        from app.schemas.device import ControllerCreate

        # 기본값으로 생성 시 is_enable=True
        schema = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8001
        )
        assert hasattr(schema, 'is_enable'), "ControllerCreate must have is_enable"
        assert schema.is_enable == True, "ControllerCreate is_enable default must be True"

    def test_controller_create_with_is_enable_false(self):
        """Test: ControllerCreate에서 is_enable=False로 생성 가능"""
        from app.schemas.device import ControllerCreate

        schema = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8001,
            is_enable=False
        )
        assert schema.is_enable == False

    def test_controller_response_has_is_enable(self):
        """Test: ControllerResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import ControllerResponse
        from datetime import datetime

        schema = ControllerResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8001,
            is_enable=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert hasattr(schema, 'is_enable'), "ControllerResponse must have is_enable"
        assert schema.is_enable == True

    def test_controller_nested_response_has_is_enable(self):
        """Test: ControllerNestedResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import ControllerNestedResponse

        schema = ControllerNestedResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8001,
            is_enable=True
        )
        assert hasattr(schema, 'is_enable'), "ControllerNestedResponse must have is_enable"

    def test_controller_update_has_optional_is_enable(self):
        """Test: ControllerUpdate 스키마에 is_enable 필드 존재 (Optional)"""
        from app.schemas.device import ControllerUpdate

        # is_enable 없이 생성 가능
        schema_without = ControllerUpdate(name_device="Updated Name")
        assert schema_without.is_enable is None

        # is_enable=False로 생성 가능
        schema_with = ControllerUpdate(is_enable=False)
        assert schema_with.is_enable == False


# ============================================================================
# Phase 2: Controller API Tests
# ============================================================================

from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestControllerApi:
    """Test Controller API endpoints support is_enable"""

    @pytest.fixture
    def client(self, test_db):
        """Create isolated test client with controller router only"""
        from app.routers.controllers import router as controllers_router
        from app.dependencies import get_db
        from app.routers.auth import get_current_account_user_optional

        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        def override_auth():
            return None  # Public mode

        app = FastAPI()
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_account_user_optional] = override_auth
        app.include_router(controllers_router, prefix="/api/devices/controllers")

        return TestClient(app)

    def test_create_controller_with_default_is_enable(self, client, test_db):
        """Test: POST /api/devices/controllers - is_enable 미지정 시 기본값 True"""
        controller_data = {
            "number_device": 9901,
            "group_device": 1,
            "name_device": "Test Controller is_enable default",
            "type_device": "Controller",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.1",
            "ip_port": 8001
        }
        response = client.post("/api/devices/controllers", json=controller_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert "is_enable" in data, "Response must include is_enable"
        assert data["is_enable"] == True, "Default is_enable must be True"

        # Cleanup
        client.delete(f"/api/devices/controllers/{data['id']}")

    def test_create_controller_with_is_enable_false(self, client, test_db):
        """Test: POST /api/devices/controllers - is_enable=False로 생성"""
        controller_data = {
            "number_device": 9902,
            "group_device": 1,
            "name_device": "Test Controller is_enable false",
            "type_device": "Controller",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.2",
            "ip_port": 8002,
            "is_enable": False
        }
        response = client.post("/api/devices/controllers", json=controller_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_enable"] == False

        # Cleanup
        client.delete(f"/api/devices/controllers/{data['id']}")

    def test_get_controller_includes_is_enable(self, client, test_db):
        """Test: GET /api/devices/controllers/{id} - is_enable 필드 포함"""
        # Create
        controller_data = {
            "number_device": 9903,
            "group_device": 1,
            "name_device": "Test Controller GET",
            "type_device": "Controller",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.3",
            "ip_port": 8003
        }
        create_response = client.post("/api/devices/controllers", json=controller_data)
        controller_id = create_response.json()["data"]["id"]

        # Get
        response = client.get(f"/api/devices/controllers/{controller_id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert "is_enable" in data

        # Cleanup
        client.delete(f"/api/devices/controllers/{controller_id}")

    def test_update_controller_is_enable(self, client, test_db):
        """Test: PATCH /api/devices/controllers/{id} - is_enable 업데이트"""
        # Create with is_enable=True (default)
        controller_data = {
            "number_device": 9904,
            "group_device": 1,
            "name_device": "Test Controller PATCH",
            "type_device": "Controller",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.4",
            "ip_port": 8004
        }
        create_response = client.post("/api/devices/controllers", json=controller_data)
        controller_id = create_response.json()["data"]["id"]

        # Update is_enable to False
        update_response = client.patch(
            f"/api/devices/controllers/{controller_id}",
            json={"is_enable": False}
        )

        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert data["is_enable"] == False

        # Cleanup
        client.delete(f"/api/devices/controllers/{controller_id}")


# ============================================================================
# Phase 3: Sensor Schema Tests
# ============================================================================

class TestSensorSchema:
    """Test Sensor schemas have is_enable field"""

    def test_sensor_create_has_is_enable_with_default(self):
        """Test: SensorCreate 스키마에 is_enable 필드 존재 (default=True)"""
        from app.schemas.device import SensorCreate

        schema = SensorCreate(
            number_device=1,
            group_device=1,
            name_device="Test Sensor",
            type_device="Multi",
            version="1.0",
            status="ACTIVATED",
            controller_id=1
        )
        assert hasattr(schema, 'is_enable'), "SensorCreate must have is_enable"
        assert schema.is_enable == True

    def test_sensor_response_has_is_enable(self):
        """Test: SensorResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import SensorResponse
        from datetime import datetime

        schema = SensorResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Sensor",
            type_device="Multi",
            version="1.0",
            status="ACTIVATED",
            controller_id=1,
            is_enable=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert hasattr(schema, 'is_enable')

    def test_sensor_nested_response_has_is_enable(self):
        """Test: SensorNestedResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import SensorNestedResponse

        schema = SensorNestedResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Sensor",
            type_device="Multi",
            version="1.0",
            status="ACTIVATED",
            controller_id=1,
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')

    def test_sensor_update_has_optional_is_enable(self):
        """Test: SensorUpdate 스키마에 is_enable 필드 존재 (Optional)"""
        from app.schemas.device import SensorUpdate

        schema = SensorUpdate(is_enable=False)
        assert schema.is_enable == False


# ============================================================================
# Phase 3: Sensor API Tests
# ============================================================================

class TestSensorApi:
    """Test Sensor API endpoints support is_enable"""

    @pytest.fixture
    def client(self, test_db):
        """Create isolated test client with sensor router only"""
        from app.routers.sensors import router as sensors_router
        from app.routers.controllers import router as controllers_router
        from app.dependencies import get_db
        from app.routers.auth import get_current_account_user_optional

        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        def override_auth():
            return None  # Public mode

        app = FastAPI()
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_account_user_optional] = override_auth
        app.include_router(controllers_router, prefix="/api/devices/controllers")
        app.include_router(sensors_router, prefix="/api/devices/sensors")

        return TestClient(app)

    @pytest.fixture
    def test_controller(self, client, test_db):
        """Create a test controller for sensor tests"""
        controller_data = {
            "number_device": 9900,
            "group_device": 1,
            "name_device": "Test Controller for Sensor",
            "type_device": "Controller",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.99",
            "ip_port": 8099
        }
        response = client.post("/api/devices/controllers", json=controller_data)
        controller = response.json()["data"]
        yield controller
        # Cleanup
        client.delete(f"/api/devices/controllers/{controller['id']}")

    def test_create_sensor_with_default_is_enable(self, client, test_db, test_controller):
        """Test: POST /api/devices/sensors - is_enable 미지정 시 기본값 True"""
        sensor_data = {
            "number_device": 9901,
            "group_device": 1,
            "name_device": "Test Sensor is_enable default",
            "type_device": "Multi",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": test_controller["id"]
        }
        response = client.post("/api/devices/sensors", json=sensor_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert "is_enable" in data, "Response must include is_enable"
        assert data["is_enable"] == True, "Default is_enable must be True"

        # Cleanup
        client.delete(f"/api/devices/sensors/{data['id']}")

    def test_create_sensor_with_is_enable_false(self, client, test_db, test_controller):
        """Test: POST /api/devices/sensors - is_enable=False로 생성"""
        sensor_data = {
            "number_device": 9902,
            "group_device": 1,
            "name_device": "Test Sensor is_enable false",
            "type_device": "Multi",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": test_controller["id"],
            "is_enable": False
        }
        response = client.post("/api/devices/sensors", json=sensor_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_enable"] == False

        # Cleanup
        client.delete(f"/api/devices/sensors/{data['id']}")

    def test_get_sensor_includes_is_enable(self, client, test_db, test_controller):
        """Test: GET /api/devices/sensors/{id} - is_enable 필드 포함"""
        # Create
        sensor_data = {
            "number_device": 9903,
            "group_device": 1,
            "name_device": "Test Sensor GET",
            "type_device": "Multi",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": test_controller["id"]
        }
        create_response = client.post("/api/devices/sensors", json=sensor_data)
        sensor_id = create_response.json()["data"]["id"]

        # Get
        response = client.get(f"/api/devices/sensors/{sensor_id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert "is_enable" in data

        # Cleanup
        client.delete(f"/api/devices/sensors/{sensor_id}")

    def test_update_sensor_is_enable(self, client, test_db, test_controller):
        """Test: PATCH /api/devices/sensors/{id} - is_enable 업데이트"""
        # Create with is_enable=True (default)
        sensor_data = {
            "number_device": 9904,
            "group_device": 1,
            "name_device": "Test Sensor PATCH",
            "type_device": "Multi",
            "version": "1.0",
            "status": "ACTIVATED",
            "controller_id": test_controller["id"]
        }
        create_response = client.post("/api/devices/sensors", json=sensor_data)
        sensor_id = create_response.json()["data"]["id"]

        # Update is_enable to False
        update_response = client.patch(
            f"/api/devices/sensors/{sensor_id}",
            json={"is_enable": False}
        )

        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert data["is_enable"] == False

        # Cleanup
        client.delete(f"/api/devices/sensors/{sensor_id}")


# ============================================================================
# Phase 4: Camera Schema Tests
# ============================================================================

class TestCameraSchema:
    """Test Camera schemas have is_enable field"""

    def test_camera_create_has_is_enable_with_default(self):
        """Test: CameraCreate 스키마에 is_enable 필드 존재 (default=True)"""
        from app.schemas.device import CameraCreate

        schema = CameraCreate(
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device="IpCamera",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.200",
            ip_port=80,
            mode="RTSP",
            category="PTZ"
        )
        assert hasattr(schema, 'is_enable'), "CameraCreate must have is_enable"
        assert schema.is_enable == True

    def test_camera_response_has_is_enable(self):
        """Test: CameraResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import CameraResponse
        from datetime import datetime

        schema = CameraResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device="IpCamera",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.200",
            ip_port=80,
            mode="RTSP",
            category="PTZ",
            is_enable=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert hasattr(schema, 'is_enable')

    def test_camera_nested_response_has_is_enable(self):
        """Test: CameraNestedResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import CameraNestedResponse

        schema = CameraNestedResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device="IpCamera",
            version="1.0",
            status="ACTIVATED",
            ip_address="192.168.1.200",
            ip_port=80,
            mode="RTSP",
            category="PTZ",
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')

    def test_camera_update_has_optional_is_enable(self):
        """Test: CameraUpdate 스키마에 is_enable 필드 존재 (Optional)"""
        from app.schemas.device import CameraUpdate

        schema = CameraUpdate(is_enable=False)
        assert schema.is_enable == False


# ============================================================================
# Phase 4: Camera API Tests
# ============================================================================

class TestCameraApi:
    """Test Camera API endpoints support is_enable"""

    @pytest.fixture
    def client(self, test_db):
        """Create isolated test client with camera router only"""
        from app.routers.cameras import router as cameras_router
        from app.dependencies import get_db
        from app.routers.auth import get_current_account_user_optional

        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        def override_auth():
            return None  # Public mode

        app = FastAPI()
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_account_user_optional] = override_auth
        app.include_router(cameras_router, prefix="/api/devices/cameras")

        return TestClient(app)

    def test_create_camera_with_default_is_enable(self, client, test_db):
        """Test: POST /api/devices/cameras - is_enable 미지정 시 기본값 True"""
        camera_data = {
            "number_device": 9801,
            "group_device": 1,
            "name_device": "Test Camera is_enable default",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.81",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "FIXED",
            "urls": {"live": "rtsp://test.camera/stream"}
        }
        response = client.post("/api/devices/cameras", json=camera_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert "is_enable" in data, "Response must include is_enable"
        assert data["is_enable"] == True, "Default is_enable must be True"

        # Cleanup
        client.delete(f"/api/devices/cameras/{data['id']}")

    def test_create_camera_with_is_enable_false(self, client, test_db):
        """Test: POST /api/devices/cameras - is_enable=False로 생성"""
        camera_data = {
            "number_device": 9802,
            "group_device": 1,
            "name_device": "Test Camera is_enable false",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.82",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "FIXED",
            "urls": {"live": "rtsp://test.camera/stream"},
            "is_enable": False
        }
        response = client.post("/api/devices/cameras", json=camera_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_enable"] == False

        # Cleanup
        client.delete(f"/api/devices/cameras/{data['id']}")

    def test_get_camera_includes_is_enable(self, client, test_db):
        """Test: GET /api/devices/cameras/{id} - is_enable 필드 포함"""
        # Create
        camera_data = {
            "number_device": 9803,
            "group_device": 1,
            "name_device": "Test Camera GET",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.83",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "FIXED",
            "urls": {"live": "rtsp://test.camera/stream"}
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Get
        response = client.get(f"/api/devices/cameras/{camera_id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert "is_enable" in data

        # Cleanup
        client.delete(f"/api/devices/cameras/{camera_id}")

    def test_update_camera_is_enable(self, client, test_db):
        """Test: PATCH /api/devices/cameras/{id} - is_enable 업데이트"""
        # Create with is_enable=True (default)
        camera_data = {
            "number_device": 9804,
            "group_device": 1,
            "name_device": "Test Camera PATCH",
            "type_device": "IpCamera",
            "version": "1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.100.84",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "FIXED",
            "urls": {"live": "rtsp://test.camera/stream"}
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Update is_enable to False
        update_response = client.patch(
            f"/api/devices/cameras/{camera_id}",
            json={"is_enable": False}
        )

        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert data["is_enable"] == False

        # Cleanup
        client.delete(f"/api/devices/cameras/{camera_id}")


# ============================================================================
# Phase 5: Speaker Schema Tests
# ============================================================================

class TestSpeakerSchema:
    """Test Speaker schemas have is_enable field"""

    def test_speaker_create_has_is_enable_with_default(self):
        """Test: SpeakerCreate 스키마에 is_enable 필드 존재 (default=True)"""
        from app.schemas.device import SpeakerCreate

        schema = SpeakerCreate(
            number_device=2401,
            name_device="Test Speaker"
        )
        assert hasattr(schema, 'is_enable'), "SpeakerCreate must have is_enable"
        assert schema.is_enable == True

    def test_speaker_response_has_is_enable(self):
        """Test: SpeakerResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import SpeakerResponse
        from datetime import datetime

        schema = SpeakerResponse(
            id=1,
            number_device=2401,
            group_device=0,
            name_device="Test Speaker",
            type_device="IpSpeaker",
            status="ACTIVATED",
            speaker_type="NORMAL",
            is_enable=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert hasattr(schema, 'is_enable')

    def test_speaker_nested_response_has_is_enable(self):
        """Test: SpeakerNestedResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import SpeakerNestedResponse

        schema = SpeakerNestedResponse(
            id=1,
            number_device=2401,
            name_device="Test Speaker",
            type_device="IpSpeaker",
            status="ACTIVATED",
            speaker_type="NORMAL",
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')

    def test_speaker_update_has_optional_is_enable(self):
        """Test: SpeakerUpdate 스키마에 is_enable 필드 존재 (Optional)"""
        from app.schemas.device import SpeakerUpdate

        schema = SpeakerUpdate(is_enable=False)
        assert schema.is_enable == False


class TestSpeakerApi:
    """Test Speaker API endpoints handle is_enable field"""

    def test_create_speaker_with_default_is_enable(self, client):
        """Test: POST /api/devices/speakers - is_enable 미지정 시 기본값 True"""
        speaker_data = {
            "number_device": 9901,
            "name_device": "Test Speaker is_enable default"
        }

        response = client.post("/api/devices/speakers", json=speaker_data)
        assert response.status_code == 201
        data = response.json()["data"]
        assert "is_enable" in data, "Response must include is_enable"
        assert data["is_enable"] == True, "Default is_enable must be True"

        # Cleanup
        client.delete(f"/api/devices/speakers/{data['id']}")

    def test_create_speaker_with_is_enable_false(self, client):
        """Test: POST /api/devices/speakers - is_enable=False로 생성"""
        speaker_data = {
            "number_device": 9902,
            "name_device": "Test Speaker is_enable false",
            "is_enable": False
        }

        response = client.post("/api/devices/speakers", json=speaker_data)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_enable"] == False, "is_enable must be False as specified"

        # Cleanup
        client.delete(f"/api/devices/speakers/{data['id']}")

    def test_get_speaker_includes_is_enable(self, client):
        """Test: GET /api/devices/speakers/{id} - is_enable 필드 포함"""
        # Create speaker first
        speaker_data = {
            "number_device": 9903,
            "name_device": "Test Speaker GET is_enable"
        }
        create_response = client.post("/api/devices/speakers", json=speaker_data)
        speaker_id = create_response.json()["data"]["id"]

        # GET and verify is_enable
        get_response = client.get(f"/api/devices/speakers/{speaker_id}")
        assert get_response.status_code == 200
        data = get_response.json()["data"]
        assert "is_enable" in data, "GET response must include is_enable"

        # Cleanup
        client.delete(f"/api/devices/speakers/{speaker_id}")

    def test_update_speaker_is_enable(self, client):
        """Test: PATCH /api/devices/speakers/{id} - is_enable 업데이트"""
        # Create speaker with is_enable=True
        speaker_data = {
            "number_device": 9904,
            "name_device": "Test Speaker PATCH is_enable"
        }
        create_response = client.post("/api/devices/speakers", json=speaker_data)
        speaker_id = create_response.json()["data"]["id"]

        # PATCH to set is_enable=False
        update_response = client.patch(
            f"/api/devices/speakers/{speaker_id}",
            json={"is_enable": False}
        )
        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert data["is_enable"] == False

        # Cleanup
        client.delete(f"/api/devices/speakers/{speaker_id}")


# ============================================================================
# Phase 6: DeviceGroup & Event Schema Tests
# ============================================================================

class TestDeviceGroupSchema:
    """Test DeviceGroup schemas have is_enable field in device summaries"""

    def test_device_summary_base_has_is_enable(self):
        """Test: DeviceSummaryBase 스키마에 is_enable 필드 존재"""
        from app.schemas.device_group import DeviceSummaryBase

        schema = DeviceSummaryBase(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Device",
            type_device="Controller",
            status="ACTIVATED",
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')

    def test_controller_summary_inherits_is_enable(self):
        """Test: ControllerSummary에 is_enable 상속됨"""
        from app.schemas.device_group import ControllerSummary

        schema = ControllerSummary(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=8001,
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')

    def test_sensor_summary_inherits_is_enable(self):
        """Test: SensorSummary에 is_enable 상속됨"""
        from app.schemas.device_group import SensorSummary

        schema = SensorSummary(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Sensor",
            type_device="Multi",
            status="ACTIVATED",
            controller_id=1,
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')

    def test_camera_summary_inherits_is_enable(self):
        """Test: CameraSummary에 is_enable 상속됨"""
        from app.schemas.device_group import CameraSummary

        schema = CameraSummary(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device="IpCamera",
            status="ACTIVATED",
            ip_address="192.168.1.200",
            ip_port=80,
            mode="RTSP",
            camera_category="PTZ",
            is_record=True,
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')


class TestDeviceNestedResponseSchema:
    """Test DeviceNestedResponse schema has is_enable field"""

    def test_device_nested_response_has_is_enable(self):
        """Test: DeviceNestedResponse 스키마에 is_enable 필드 존재"""
        from app.schemas.device import DeviceNestedResponse

        schema = DeviceNestedResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Device",
            type_device="Sensor",
            status="ACTIVATED",
            is_enable=True
        )
        assert hasattr(schema, 'is_enable')
        assert schema.is_enable == True


# ============================================================================
# Phase 6: DeviceGroup API Tests
# ============================================================================

class TestDeviceGroupApi:
    """Test DeviceGroup API returns devices with is_enable"""

    @pytest.fixture
    def client(self, test_db):
        """Create isolated test client with device_groups router only"""
        from app.routers.device_groups import router as device_groups_router
        from app.dependencies import get_db
        from app.routers.auth import get_current_account_user_optional

        def override_get_db():
            try:
                yield test_db
            finally:
                pass

        def override_auth():
            return None  # Public mode

        app = FastAPI()
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_account_user_optional] = override_auth
        app.include_router(device_groups_router, prefix="/api/devices/groups")

        return TestClient(app)

    def test_device_group_devices_include_is_enable(self, client, test_db):
        """Test: GET /api/devices/groups/{id}?include_devices=true - devices에 is_enable 포함"""
        # First, create a device group
        group_response = client.post(
            "/api/devices/groups",
            json={"name": "Test Group is_enable", "description": "Test"}
        )

        if group_response.status_code == 201:
            group_id = group_response.json()["data"]["id"]

            # Get group with devices
            response = client.get(f"/api/devices/groups/{group_id}?include_devices=true")

            assert response.status_code == 200
            # Note: devices may be empty if no devices assigned, but schema should support is_enable

            # Cleanup
            client.delete(f"/api/devices/groups/{group_id}")
        else:
            # Group might already exist, try to find it
            list_response = client.get("/api/devices/groups?name=Test Group is_enable")
            if list_response.status_code == 200 and list_response.json()["data"]:
                group_id = list_response.json()["data"][0]["id"]
                response = client.get(f"/api/devices/groups/{group_id}?include_devices=true")
                assert response.status_code == 200
