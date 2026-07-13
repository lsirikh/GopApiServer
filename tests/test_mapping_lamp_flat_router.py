"""
Test: MappingLamp 독립 List API
PRD: PRD_MappingSubResource_ListAPI.md v1.0

Phase 3: Router Tests (TDD - Red Phase)
Endpoint: GET /api/integrations/mapping-lamps
"""
import pytest
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
def test_event_mapping_lamp(test_db, test_event_mapping, test_lamp):
    """Create a test EventMappingLamp"""
    from app.models.integration import EventMappingLamp

    eml = EventMappingLamp(
        event_mapping_id=test_event_mapping.id,
        lamp_id=test_lamp.id,
        is_enable=True,
        priority=1
    )
    test_db.add(eml)
    test_db.commit()
    test_db.refresh(eml)
    return eml


# ============================================================
# Phase 3.1-3.3: 기본 조회 테스트
# ============================================================

class TestMappingLampFlatList:
    """GET /api/integrations/mapping-lamps Tests"""

    def test_get_mapping_lamps_list_success(self, client, test_event_mapping, test_event_mapping_lamp):
        """Test: GET /api/integrations/mapping-lamps returns 200 with items"""
        response = client.get("/api/integrations/mapping-lamps")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert len(data["data"]["items"]) == 1
        assert data["data"]["total"] == 1

    def test_get_mapping_lamps_list_empty(self, client):
        """Test: GET /api/integrations/mapping-lamps returns empty list when no data"""
        response = client.get("/api/integrations/mapping-lamps")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_get_mapping_lamps_list_includes_nested_objects(self, client, test_event_mapping, test_event_mapping_lamp):
        """Test: Response includes nested event_mapping and lamp objects"""
        response = client.get("/api/integrations/mapping-lamps")

        assert response.status_code == 200
        item = response.json()["data"]["items"][0]

        # Nested event_mapping present
        assert item["event_mapping"] is not None
        assert "id" in item["event_mapping"]
        assert "name_event" in item["event_mapping"]

        # Nested lamp present
        assert item["lamp"] is not None
        assert "id" in item["lamp"]
        assert "name_device" in item["lamp"]
        assert "ip_address" in item["lamp"]

        # Base item HAS timestamps
        assert "created_at" in item
        assert "updated_at" in item


# ============================================================
# Phase 3.6-3.8: 필터 테스트
# ============================================================

class TestMappingLampFlatListFilters:
    """GET /api/integrations/mapping-lamps?filter= Tests"""

    @pytest.fixture
    def second_event_mapping(self, test_db):
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
    def second_lamp(self, test_db):
        from app.models.device import Lamp
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        lamp = Lamp(
            number_device=9002,
            group_device=1,
            name_device="Second Lamp",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.10.51",
            ip_port=80,
        )
        test_db.add(lamp)
        test_db.commit()
        test_db.refresh(lamp)
        return lamp

    @pytest.fixture
    def two_mapping_lamps(self, test_db, test_event_mapping, second_event_mapping, test_lamp, second_lamp):
        from app.models.integration import EventMappingLamp

        eml1 = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        eml2 = EventMappingLamp(
            event_mapping_id=second_event_mapping.id,
            lamp_id=second_lamp.id,
            is_enable=False,
            priority=2
        )
        test_db.add_all([eml1, eml2])
        test_db.commit()
        test_db.refresh(eml1)
        test_db.refresh(eml2)
        return eml1, eml2

    def test_filter_by_event_mapping_id(self, client, two_mapping_lamps, test_event_mapping):
        response = client.get(f"/api/integrations/mapping-lamps?event_mapping_id={test_event_mapping.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["event_mapping"]["id"] == test_event_mapping.id

    def test_filter_by_lamp_id(self, client, two_mapping_lamps, second_lamp):
        response = client.get(f"/api/integrations/mapping-lamps?lamp_id={second_lamp.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1

    def test_filter_by_is_enable(self, client, two_mapping_lamps):
        response = client.get("/api/integrations/mapping-lamps?is_enable=true")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["is_enable"] is True
