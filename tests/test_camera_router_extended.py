"""
Phase 3/7: Camera Router Extended Fields API Tests (TDD)
PRD: PRD_Device_Structure_Refactoring.md - Section 3.2

Tests for Camera API with extended fields:
- is_record
- hardware_spec (JSON)
- geolocation (JSON)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import Base, engine
from app.dependencies import get_db
from app.models.device import Camera


# Test client
client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()


@pytest.fixture
def base_camera_data():
    """Base camera data for tests"""
    return {
        "number_device": 9001,
        "group_device": 1,
        "name_device": "Test Camera",
        "type_device": "IpCamera",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.100",
        "ip_port": 80,
        "user_name": "admin",
        "user_password": "password123",
        "rtsp_uri": "/stream1",
        "rtsp_port": 554,
        "mode": "ONVIF",
        "category": "PTZ"
    }


class TestCameraCreateExtendedAPI:
    """Camera POST API with extended fields"""

    def test_create_camera_with_is_record_true(self, db_session, base_camera_data):
        """POST: is_record=True로 카메라 생성"""
        base_camera_data["is_record"] = True

        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_record"] is True

    def test_create_camera_with_is_record_default(self, db_session, base_camera_data):
        """POST: is_record 기본값 False 확인"""
        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_record"] is False

    def test_create_camera_with_hardware_spec(self, db_session, base_camera_data):
        """POST: hardware_spec JSON 포함 생성"""
        base_camera_data["hardware_spec"] = {
            "name": "Axis P3245-V",
            "manufacturer": "Axis Communications",
            "model": "P3245-V",
            "firmware": "10.12.114",
            "mac_address": "AC:CC:8E:12:34:56"
        }

        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["hardware_spec"] is not None
        assert data["hardware_spec"]["name"] == "Axis P3245-V"
        assert data["hardware_spec"]["manufacturer"] == "Axis Communications"

    def test_create_camera_with_geolocation(self, db_session, base_camera_data):
        """POST: geolocation JSON 포함 생성"""
        base_camera_data["geolocation"] = {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "altitude": 50.0
        }

        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["geolocation"] is not None
        assert data["geolocation"]["latitude"] == 37.5665
        assert data["geolocation"]["longitude"] == 126.9780
        assert data["geolocation"]["altitude"] == 50.0

    def test_create_camera_with_all_extended_fields(self, db_session, base_camera_data):
        """POST: 모든 확장 필드 포함 생성"""
        base_camera_data["is_record"] = True
        base_camera_data["hardware_spec"] = {
            "name": "Full Spec Camera",
            "manufacturer": "TestCo",
            "model": "TS-100",
            "firmware": "2.0.0"
        }
        base_camera_data["geolocation"] = {
            "latitude": 38.0,
            "longitude": 127.0
        }

        response = client.post("/api/devices/cameras", json=base_camera_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["is_record"] is True
        assert data["hardware_spec"]["name"] == "Full Spec Camera"
        assert data["geolocation"]["latitude"] == 38.0


class TestCameraGetExtendedAPI:
    """Camera GET API with extended fields"""

    def test_get_camera_with_extended_fields(self, db_session, base_camera_data):
        """GET: 확장 필드 포함 단건 조회"""
        # Create camera with extended fields
        base_camera_data["is_record"] = True
        base_camera_data["hardware_spec"] = {"name": "Test HW"}
        base_camera_data["geolocation"] = {"latitude": 37.0, "longitude": 127.0}

        create_response = client.post("/api/devices/cameras", json=base_camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Get camera
        response = client.get(f"/api/devices/cameras/{camera_id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_record"] is True
        assert data["hardware_spec"]["name"] == "Test HW"
        assert data["geolocation"]["latitude"] == 37.0

    def test_get_cameras_list_with_extended_fields(self, db_session, base_camera_data):
        """GET: 확장 필드 포함 목록 조회"""
        # Create cameras
        base_camera_data["is_record"] = True
        base_camera_data["hardware_spec"] = {"manufacturer": "Brand A"}
        client.post("/api/devices/cameras", json=base_camera_data)

        base_camera_data["number_device"] = 9002
        base_camera_data["is_record"] = False
        base_camera_data["hardware_spec"] = {"manufacturer": "Brand B"}
        client.post("/api/devices/cameras", json=base_camera_data)

        # Get list
        response = client.get("/api/devices/cameras")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        # Check extended fields in list
        assert data[0]["is_record"] is True
        assert data[0]["hardware_spec"]["manufacturer"] == "Brand A"


class TestCameraUpdateExtendedAPI:
    """Camera PATCH API with extended fields"""

    def test_patch_camera_is_record(self, db_session, base_camera_data):
        """PATCH: is_record만 수정"""
        # Create camera
        create_response = client.post("/api/devices/cameras", json=base_camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Patch is_record
        response = client.patch(f"/api/devices/cameras/{camera_id}", json={"is_record": True})

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_record"] is True

    def test_patch_camera_hardware_spec(self, db_session, base_camera_data):
        """PATCH: hardware_spec 수정"""
        # Create camera
        create_response = client.post("/api/devices/cameras", json=base_camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Patch hardware_spec
        new_spec = {"name": "Updated Camera", "firmware": "3.0.0"}
        response = client.patch(f"/api/devices/cameras/{camera_id}", json={"hardware_spec": new_spec})

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["hardware_spec"]["name"] == "Updated Camera"
        assert data["hardware_spec"]["firmware"] == "3.0.0"

    def test_patch_camera_geolocation(self, db_session, base_camera_data):
        """PATCH: geolocation 수정"""
        # Create camera
        create_response = client.post("/api/devices/cameras", json=base_camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Patch geolocation
        new_geo = {"latitude": 35.0, "longitude": 129.0, "altitude": 100.0}
        response = client.patch(f"/api/devices/cameras/{camera_id}", json={"geolocation": new_geo})

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["geolocation"]["latitude"] == 35.0
        assert data["geolocation"]["longitude"] == 129.0
        assert data["geolocation"]["altitude"] == 100.0


class TestCameraReplaceExtendedAPI:
    """Camera PUT API with extended fields"""

    def test_put_camera_with_extended_fields(self, db_session, base_camera_data):
        """PUT: 확장 필드 포함 전체 교체"""
        # Create camera without extended fields
        create_response = client.post("/api/devices/cameras", json=base_camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Replace with extended fields
        base_camera_data["is_record"] = True
        base_camera_data["hardware_spec"] = {"name": "New Hardware", "model": "NH-200"}
        base_camera_data["geolocation"] = {"latitude": 36.0, "longitude": 128.0}

        response = client.put(f"/api/devices/cameras/{camera_id}", json=base_camera_data)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_record"] is True
        assert data["hardware_spec"]["name"] == "New Hardware"
        assert data["geolocation"]["latitude"] == 36.0

    def test_put_camera_clear_extended_fields(self, db_session, base_camera_data):
        """PUT: 확장 필드 제거 (None으로 설정)"""
        # Create camera with extended fields
        base_camera_data["is_record"] = True
        base_camera_data["hardware_spec"] = {"name": "Initial"}
        base_camera_data["geolocation"] = {"latitude": 37.0, "longitude": 127.0}
        create_response = client.post("/api/devices/cameras", json=base_camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Replace without extended fields (defaults)
        base_camera_data["is_record"] = False
        base_camera_data["hardware_spec"] = None
        base_camera_data["geolocation"] = None

        response = client.put(f"/api/devices/cameras/{camera_id}", json=base_camera_data)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_record"] is False
        assert data["hardware_spec"] is None
        assert data["geolocation"] is None
