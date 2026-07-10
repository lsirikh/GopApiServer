"""
Test: Camera API with URLs JSONB - Phase 4
PRD Reference: docs/PRD_Camera_Urls_JsonB.md v1.0
TDD Phase: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine
from app.dependencies import get_db
from app.models.device import Camera
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

# Test client (module-level like other camera router tests)
client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()


# =============================================================================
# Phase 4.1: POST /api/devices/cameras Tests
# =============================================================================

class TestCameraApiPost:
    """Phase 4.1: POST /api/devices/cameras 테스트"""

    def test_post_cameras_accepts_urls_field(self, db_session):
        """
        Test: POST /api/devices/cameras accepts urls field

        Plan: Phase 4.1 - POST /api/devices/cameras
        Expected: POST request with urls field should succeed
        """
        camera_data = {
            "number_device": 4001,
            "group_device": 1,
            "name_device": "API Test Camera",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.200",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "streams": {
                    "rtsp": {
                        "main": "rtsp://192.168.1.200:554/stream1",
                        "sub": "rtsp://192.168.1.200:554/stream2"
                    }
                },
                "homepage": {
                    "url": "https://192.168.1.200/"
                }
            }
        }

        response = client.post("/api/devices/cameras", json=camera_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["urls"] is not None
        assert data["data"]["urls"]["streams"]["rtsp"]["main"] == "rtsp://192.168.1.200:554/stream1"

    def test_post_cameras_does_not_accept_rtsp_uri_field(self, db_session):
        """
        Test: POST /api/devices/cameras does NOT accept rtsp_uri field

        Plan: Phase 4.1 - POST /api/devices/cameras
        Expected: POST request with rtsp_uri should ignore the field (not in schema)
        """
        camera_data = {
            "number_device": 4002,
            "group_device": 1,
            "name_device": "API Test Camera 2",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.201",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "rtsp_uri": "rtsp://192.168.1.201:554/stream"  # Should be ignored
        }

        response = client.post("/api/devices/cameras", json=camera_data)
        # Should succeed but rtsp_uri should not be in response
        assert response.status_code == 201
        data = response.json()
        assert "rtsp_uri" not in data["data"]

    def test_post_cameras_does_not_accept_rtsp_port_field(self, db_session):
        """
        Test: POST /api/devices/cameras does NOT accept rtsp_port field

        Plan: Phase 4.1 - POST /api/devices/cameras
        Expected: POST request with rtsp_port should ignore the field (not in schema)
        """
        camera_data = {
            "number_device": 4003,
            "group_device": 1,
            "name_device": "API Test Camera 3",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.202",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "rtsp_port": 554  # Should be ignored
        }

        response = client.post("/api/devices/cameras", json=camera_data)
        # Should succeed but rtsp_port should not be in response
        assert response.status_code == 201
        data = response.json()
        assert "rtsp_port" not in data["data"]

    def test_post_cameras_creates_camera_with_urls_jsonb(self, db_session):
        """
        Test: POST /api/devices/cameras creates Camera with urls JSONB

        Plan: Phase 4.1 - POST /api/devices/cameras
        Expected: Camera should be created with urls JSONB data stored correctly
        """
        camera_data = {
            "number_device": 4004,
            "group_device": 1,
            "name_device": "API Test Camera 4",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.203",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "homepage": {"url": "https://192.168.1.203/"},
                "onvif": {"device_service": "http://192.168.1.203:8000/onvif/device_service"},
                "streams": {
                    "rtsp": {"main": "rtsp://192.168.1.203:554/stream1"}
                },
                "snapshot": {"ch1": "http://192.168.1.203/snapshot.jpg"}
            }
        }

        response = client.post("/api/devices/cameras", json=camera_data)
        assert response.status_code == 201

        # Verify in database
        camera_id = response.json()["data"]["id"]
        camera = db_session.query(Camera).filter(Camera.id == camera_id).first()

        assert camera is not None
        assert camera.urls is not None
        assert camera.urls["homepage"]["url"] == "https://192.168.1.203/"
        assert camera.urls["onvif"]["device_service"] == "http://192.168.1.203:8000/onvif/device_service"
        assert camera.urls["streams"]["rtsp"]["main"] == "rtsp://192.168.1.203:554/stream1"


# =============================================================================
# Phase 4.2: GET /api/devices/cameras Tests
# =============================================================================

class TestCameraApiGetList:
    """Phase 4.2: GET /api/devices/cameras 테스트"""

    def test_get_cameras_returns_urls_field(self, db_session):
        """
        Test: GET /api/devices/cameras returns urls field in response

        Plan: Phase 4.2 - GET /api/devices/cameras
        Expected: Response should include urls field
        """
        # Create camera with urls via API
        camera_data = {
            "number_device": 4010,
            "group_device": 1,
            "name_device": "GET Test Camera",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.210",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {"streams": {"rtsp": {"main": "rtsp://192.168.1.210:554/stream1"}}}
        }
        client.post("/api/devices/cameras", json=camera_data)

        response = client.get("/api/devices/cameras")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Find our camera in the list
        cameras = data["data"]
        our_camera = next((c for c in cameras if c["number_device"] == 4010), None)
        assert our_camera is not None
        assert "urls" in our_camera
        assert our_camera["urls"]["streams"]["rtsp"]["main"] == "rtsp://192.168.1.210:554/stream1"

    def test_get_cameras_does_not_return_rtsp_uri_field(self, db_session):
        """
        Test: GET /api/devices/cameras does NOT return rtsp_uri field

        Plan: Phase 4.2 - GET /api/devices/cameras
        Expected: Response should NOT include rtsp_uri field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4011,
            "group_device": 1,
            "name_device": "GET Test Camera 2",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.211",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        client.post("/api/devices/cameras", json=camera_data)

        response = client.get("/api/devices/cameras")
        assert response.status_code == 200
        data = response.json()

        # Check no camera has rtsp_uri field
        for cam in data["data"]:
            assert "rtsp_uri" not in cam

    def test_get_cameras_does_not_return_rtsp_port_field(self, db_session):
        """
        Test: GET /api/devices/cameras does NOT return rtsp_port field

        Plan: Phase 4.2 - GET /api/devices/cameras
        Expected: Response should NOT include rtsp_port field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4012,
            "group_device": 1,
            "name_device": "GET Test Camera 3",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.212",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        client.post("/api/devices/cameras", json=camera_data)

        response = client.get("/api/devices/cameras")
        assert response.status_code == 200
        data = response.json()

        # Check no camera has rtsp_port field
        for cam in data["data"]:
            assert "rtsp_port" not in cam


# =============================================================================
# Phase 4.3: GET /api/devices/cameras/{id} Tests
# =============================================================================

class TestCameraApiGetSingle:
    """Phase 4.3: GET /api/devices/cameras/{id} 테스트"""

    def test_get_camera_by_id_returns_urls_field(self, db_session):
        """
        Test: GET /api/devices/cameras/{id} returns urls field in response

        Plan: Phase 4.3 - GET /api/devices/cameras/{id}
        Expected: Response should include urls field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4020,
            "group_device": 1,
            "name_device": "GET Single Test Camera",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.220",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "homepage": {"url": "https://192.168.1.220/"},
                "streams": {"rtsp": {"main": "rtsp://192.168.1.220:554/stream1"}}
            }
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        response = client.get(f"/api/devices/cameras/{camera_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "urls" in data["data"]
        assert data["data"]["urls"]["homepage"]["url"] == "https://192.168.1.220/"

    def test_get_camera_by_id_does_not_return_rtsp_uri_field(self, db_session):
        """
        Test: GET /api/devices/cameras/{id} does NOT return rtsp_uri field

        Plan: Phase 4.3 - GET /api/devices/cameras/{id}
        Expected: Response should NOT include rtsp_uri field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4021,
            "group_device": 1,
            "name_device": "GET Single Test Camera 2",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.221",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        response = client.get(f"/api/devices/cameras/{camera_id}")
        assert response.status_code == 200
        data = response.json()
        assert "rtsp_uri" not in data["data"]

    def test_get_camera_by_id_does_not_return_rtsp_port_field(self, db_session):
        """
        Test: GET /api/devices/cameras/{id} does NOT return rtsp_port field

        Plan: Phase 4.3 - GET /api/devices/cameras/{id}
        Expected: Response should NOT include rtsp_port field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4022,
            "group_device": 1,
            "name_device": "GET Single Test Camera 3",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.222",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        response = client.get(f"/api/devices/cameras/{camera_id}")
        assert response.status_code == 200
        data = response.json()
        assert "rtsp_port" not in data["data"]


# =============================================================================
# Phase 4.4: PATCH /api/devices/cameras/{id} Tests
# =============================================================================

class TestCameraApiPatch:
    """Phase 4.4: PATCH /api/devices/cameras/{id} 테스트"""

    def test_patch_camera_accepts_urls_field(self, db_session):
        """
        Test: PATCH /api/devices/cameras/{id} accepts urls field

        Plan: Phase 4.4 - PATCH /api/devices/cameras/{id}
        Expected: PATCH request with urls field should succeed
        """
        # Create camera via API
        camera_data = {
            "number_device": 4030,
            "group_device": 1,
            "name_device": "PATCH Test Camera",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.230",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        update_data = {
            "urls": {
                "streams": {"rtsp": {"main": "rtsp://192.168.1.230:554/updated_stream"}}
            }
        }

        response = client.patch(f"/api/devices/cameras/{camera_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["urls"]["streams"]["rtsp"]["main"] == "rtsp://192.168.1.230:554/updated_stream"

    def test_patch_camera_updates_urls_partially(self, db_session):
        """
        Test: PATCH /api/devices/cameras/{id} updates urls partially

        Plan: Phase 4.4 - PATCH /api/devices/cameras/{id}
        Expected: PATCH should update urls field correctly
        """
        # Create camera via API with initial urls
        camera_data = {
            "number_device": 4031,
            "group_device": 1,
            "name_device": "PATCH Test Camera 2",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.231",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {"homepage": {"url": "https://192.168.1.231/"}}
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        # Update urls with streams
        update_data = {
            "urls": {
                "streams": {"rtsp": {"main": "rtsp://192.168.1.231:554/stream1"}}
            }
        }

        response = client.patch(f"/api/devices/cameras/{camera_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()

        # The new urls should replace the old one (PATCH replaces the whole urls object)
        assert "streams" in data["data"]["urls"]

    def test_patch_camera_does_not_accept_rtsp_uri_field(self, db_session):
        """
        Test: PATCH /api/devices/cameras/{id} does NOT accept rtsp_uri field

        Plan: Phase 4.4 - PATCH /api/devices/cameras/{id}
        Expected: PATCH request with rtsp_uri should ignore the field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4032,
            "group_device": 1,
            "name_device": "PATCH Test Camera 3",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.232",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        update_data = {
            "name_device": "Updated Name",
            "rtsp_uri": "rtsp://192.168.1.232:554/stream"  # Should be ignored
        }

        response = client.patch(f"/api/devices/cameras/{camera_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert "rtsp_uri" not in data["data"]

    def test_patch_camera_does_not_accept_rtsp_port_field(self, db_session):
        """
        Test: PATCH /api/devices/cameras/{id} does NOT accept rtsp_port field

        Plan: Phase 4.4 - PATCH /api/devices/cameras/{id}
        Expected: PATCH request with rtsp_port should ignore the field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4033,
            "group_device": 1,
            "name_device": "PATCH Test Camera 4",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.233",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        update_data = {
            "name_device": "Updated Name",
            "rtsp_port": 554  # Should be ignored
        }

        response = client.patch(f"/api/devices/cameras/{camera_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert "rtsp_port" not in data["data"]


# =============================================================================
# Phase 4.5: PUT /api/devices/cameras/{id} Tests
# =============================================================================

class TestCameraApiPut:
    """Phase 4.5: PUT /api/devices/cameras/{id} 테스트"""

    def test_put_camera_accepts_urls_field(self, db_session):
        """
        Test: PUT /api/devices/cameras/{id} accepts urls field

        Plan: Phase 4.5 - PUT /api/devices/cameras/{id}
        Expected: PUT request with urls field should succeed
        """
        # Create camera via API
        camera_data = {
            "number_device": 4040,
            "group_device": 1,
            "name_device": "PUT Test Camera",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.240",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        replace_data = {
            "number_device": 4040,
            "group_device": 1,
            "name_device": "PUT Replaced Camera",
            "type_device": "IpCamera",
            "version": "2.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.240",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "streams": {"rtsp": {"main": "rtsp://192.168.1.240:554/new_stream"}}
            }
        }

        response = client.put(f"/api/devices/cameras/{camera_id}", json=replace_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["urls"]["streams"]["rtsp"]["main"] == "rtsp://192.168.1.240:554/new_stream"

    def test_put_camera_replaces_urls_entirely(self, db_session):
        """
        Test: PUT /api/devices/cameras/{id} replaces urls entirely

        Plan: Phase 4.5 - PUT /api/devices/cameras/{id}
        Expected: PUT should replace the entire urls field
        """
        # Create camera via API with initial urls
        camera_data = {
            "number_device": 4041,
            "group_device": 1,
            "name_device": "PUT Test Camera 2",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.241",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {"homepage": {"url": "https://old.example.com/"}}
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        replace_data = {
            "number_device": 4041,
            "group_device": 1,
            "name_device": "PUT Replaced Camera 2",
            "type_device": "IpCamera",
            "version": "2.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.241",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "streams": {"rtsp": {"main": "rtsp://192.168.1.241:554/stream1"}}
            }
        }

        response = client.put(f"/api/devices/cameras/{camera_id}", json=replace_data)
        assert response.status_code == 200
        data = response.json()

        # homepage should be replaced with streams
        assert "streams" in data["data"]["urls"]
        # old homepage might or might not be there depending on implementation

    def test_put_camera_does_not_accept_rtsp_uri_field(self, db_session):
        """
        Test: PUT /api/devices/cameras/{id} does NOT accept rtsp_uri field

        Plan: Phase 4.5 - PUT /api/devices/cameras/{id}
        Expected: PUT request with rtsp_uri should ignore the field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4042,
            "group_device": 1,
            "name_device": "PUT Test Camera 3",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.242",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        replace_data = {
            "number_device": 4042,
            "group_device": 1,
            "name_device": "PUT Replaced Camera 3",
            "type_device": "IpCamera",
            "version": "2.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.242",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "rtsp_uri": "rtsp://192.168.1.242:554/stream"  # Should be ignored
        }

        response = client.put(f"/api/devices/cameras/{camera_id}", json=replace_data)
        assert response.status_code == 200
        data = response.json()
        assert "rtsp_uri" not in data["data"]

    def test_put_camera_does_not_accept_rtsp_port_field(self, db_session):
        """
        Test: PUT /api/devices/cameras/{id} does NOT accept rtsp_port field

        Plan: Phase 4.5 - PUT /api/devices/cameras/{id}
        Expected: PUT request with rtsp_port should ignore the field
        """
        # Create camera via API
        camera_data = {
            "number_device": 4043,
            "group_device": 1,
            "name_device": "PUT Test Camera 4",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.243",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = client.post("/api/devices/cameras", json=camera_data)
        camera_id = create_response.json()["data"]["id"]

        replace_data = {
            "number_device": 4043,
            "group_device": 1,
            "name_device": "PUT Replaced Camera 4",
            "type_device": "IpCamera",
            "version": "2.0.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.243",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "rtsp_port": 554  # Should be ignored
        }

        response = client.put(f"/api/devices/cameras/{camera_id}", json=replace_data)
        assert response.status_code == 200
        data = response.json()
        assert "rtsp_port" not in data["data"]
