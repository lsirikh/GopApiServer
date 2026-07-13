"""
Test: MappingCamera 독립 List API
PRD: PRD_MappingSubResource_ListAPI.md v1.0

Phase 1: Router Tests (TDD - Red Phase)
Endpoint: GET /api/integrations/mapping-cameras
"""
import pytest
from fastapi.testclient import TestClient
from app.utils.enums import EnumMappingEventCategory


@pytest.fixture
def test_event_mapping(test_db):
    """Create a test EventMapping"""
    from app.models.integration import EventMapping

    event_mapping = EventMapping(
        name_event="Test Event Mapping",
        category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        status=True
    )
    test_db.add(event_mapping)
    test_db.commit()
    test_db.refresh(event_mapping)
    return event_mapping


@pytest.fixture
def test_event_mapping_camera(test_db, test_event_mapping, test_camera, test_preset):
    """Create a test EventMappingCamera"""
    from app.models.integration import EventMappingCamera

    emc = EventMappingCamera(
        event_mapping_id=test_event_mapping.id,
        camera_id=test_camera.id,
        target_preset_id=test_preset.id,
        delay_time=10,
        is_enable=True,
        priority=1
    )
    test_db.add(emc)
    test_db.commit()
    test_db.refresh(emc)
    return emc


# ============================================================
# Phase 1.1: 기본 조회 테스트
# ============================================================

class TestMappingCameraFlatList:
    """GET /api/integrations/mapping-cameras Tests"""

    def test_get_mapping_cameras_list_success(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: GET /api/integrations/mapping-cameras returns 200 with items"""
        response = client.get("/api/integrations/mapping-cameras")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert len(data["data"]["items"]) == 1
        assert data["data"]["total"] == 1

    def test_get_mapping_cameras_list_empty(self, client):
        """Test: GET /api/integrations/mapping-cameras returns empty list when no data"""
        response = client.get("/api/integrations/mapping-cameras")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_get_mapping_cameras_list_includes_nested_camera(self, client, test_event_mapping, test_event_mapping_camera):
        """Test: Response includes nested camera object without timestamps"""
        response = client.get("/api/integrations/mapping-cameras")

        assert response.status_code == 200
        item = response.json()["data"]["items"][0]

        # Nested camera present
        assert item["camera"] is not None
        assert "id" in item["camera"]
        assert "name_device" in item["camera"]
        assert "ip_address" in item["camera"]
        # Nested object should NOT have timestamps
        assert "created_at" not in item["camera"]
        assert "updated_at" not in item["camera"]

        # Nested preset present
        assert item["target_preset"] is not None
        assert "preset_name" in item["target_preset"]

        # Base item HAS timestamps
        assert "created_at" in item
        assert "updated_at" in item


# ============================================================
# Phase 1.6-1.8: 필터 테스트
# ============================================================

class TestMappingCameraFlatListFilters:
    """GET /api/integrations/mapping-cameras?filter= Tests"""

    @pytest.fixture
    def second_event_mapping(self, test_db):
        """Create a second EventMapping"""
        from app.models.integration import EventMapping

        em = EventMapping(
            name_event="Second Event Mapping",
            category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            status=True
        )
        test_db.add(em)
        test_db.commit()
        test_db.refresh(em)
        return em

    @pytest.fixture
    def second_camera(self, test_db):
        """Create a second Camera"""
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=2,
            group_device=1,
            name_device="Second Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.FIXED,
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)
        return camera

    @pytest.fixture
    def two_mapping_cameras(self, test_db, test_event_mapping, second_event_mapping, test_camera, second_camera, test_preset):
        """Create two EventMappingCameras in different mappings"""
        from app.models.integration import EventMappingCamera

        emc1 = EventMappingCamera(
            event_mapping_id=test_event_mapping.id,
            camera_id=test_camera.id,
            target_preset_id=test_preset.id,
            delay_time=5,
            is_enable=True,
            priority=1
        )
        emc2 = EventMappingCamera(
            event_mapping_id=second_event_mapping.id,
            camera_id=second_camera.id,
            delay_time=10,
            is_enable=False,
            priority=2
        )
        test_db.add_all([emc1, emc2])
        test_db.commit()
        test_db.refresh(emc1)
        test_db.refresh(emc2)
        return emc1, emc2

    def test_filter_by_event_mapping_id(self, client, two_mapping_cameras, test_event_mapping):
        """Test: ?event_mapping_id= filters by specific mapping"""
        response = client.get(f"/api/integrations/mapping-cameras?event_mapping_id={test_event_mapping.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["event_mapping_id"] == test_event_mapping.id

    def test_filter_by_camera_id(self, client, two_mapping_cameras, second_camera):
        """Test: ?camera_id= filters by specific camera"""
        response = client.get(f"/api/integrations/mapping-cameras?camera_id={second_camera.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["camera"]["id"] == second_camera.id

    def test_filter_by_is_enable(self, client, two_mapping_cameras):
        """Test: ?is_enable= filters by enabled status"""
        response = client.get("/api/integrations/mapping-cameras?is_enable=true")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["is_enable"] is True
