"""
Test: MappingSpeaker 독립 List API
PRD: PRD_MappingSubResource_ListAPI.md v1.0

Phase 2: Router Tests (TDD - Red Phase)
Endpoint: GET /api/integrations/mapping-speakers
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
def test_event_mapping_speaker(test_db, test_event_mapping, test_speaker, test_file_group):
    """Create a test EventMappingSpeaker"""
    from app.models.integration import EventMappingSpeaker

    ems = EventMappingSpeaker(
        event_mapping_id=test_event_mapping.id,
        speaker_id=test_speaker.id,
        file_group_id=test_file_group.id,
        repeat_count=3,
        is_enable=True,
        priority=1
    )
    test_db.add(ems)
    test_db.commit()
    test_db.refresh(ems)
    return ems


# ============================================================
# Phase 2.1-2.3: 기본 조회 테스트
# ============================================================

class TestMappingSpeakerFlatList:
    """GET /api/integrations/mapping-speakers Tests"""

    def test_get_mapping_speakers_list_success(self, client, test_event_mapping, test_event_mapping_speaker):
        """Test: GET /api/integrations/mapping-speakers returns 200 with items"""
        response = client.get("/api/integrations/mapping-speakers")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert len(data["data"]["items"]) == 1
        assert data["data"]["total"] == 1

    def test_get_mapping_speakers_list_empty(self, client):
        """Test: GET /api/integrations/mapping-speakers returns empty list when no data"""
        response = client.get("/api/integrations/mapping-speakers")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_get_mapping_speakers_list_includes_nested_speaker(self, client, test_event_mapping, test_event_mapping_speaker):
        """Test: Response includes nested speaker/file_group without timestamps"""
        response = client.get("/api/integrations/mapping-speakers")

        assert response.status_code == 200
        item = response.json()["data"]["items"][0]

        # Nested speaker present
        assert item["speaker"] is not None
        assert "id" in item["speaker"]
        assert "name_device" in item["speaker"]
        assert "speaker_type" in item["speaker"]
        assert "created_at" not in item["speaker"]
        assert "updated_at" not in item["speaker"]

        # Nested file_group present
        assert item["file_group"] is not None
        assert "group_name" in item["file_group"]

        # Base item HAS timestamps
        assert "created_at" in item
        assert "updated_at" in item


# ============================================================
# Phase 2.6-2.8: 필터 테스트
# ============================================================

class TestMappingSpeakerFlatListFilters:
    """GET /api/integrations/mapping-speakers?filter= Tests"""

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
    def second_speaker(self, test_db):
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(
            number_device=2402,
            group_device=0,
            name_device="Second Speaker",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.ADMIN,
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)
        return speaker

    @pytest.fixture
    def two_mapping_speakers(self, test_db, test_event_mapping, second_event_mapping, test_speaker, second_speaker, test_file_group):
        from app.models.integration import EventMappingSpeaker

        ems1 = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            file_group_id=test_file_group.id,
            repeat_count=2,
            is_enable=True,
            priority=1
        )
        ems2 = EventMappingSpeaker(
            event_mapping_id=second_event_mapping.id,
            speaker_id=second_speaker.id,
            repeat_count=1,
            is_enable=False,
            priority=2
        )
        test_db.add_all([ems1, ems2])
        test_db.commit()
        test_db.refresh(ems1)
        test_db.refresh(ems2)
        return ems1, ems2

    def test_filter_by_event_mapping_id(self, client, two_mapping_speakers, test_event_mapping):
        response = client.get(f"/api/integrations/mapping-speakers?event_mapping_id={test_event_mapping.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["event_mapping_id"] == test_event_mapping.id

    def test_filter_by_speaker_id(self, client, two_mapping_speakers, second_speaker):
        response = client.get(f"/api/integrations/mapping-speakers?speaker_id={second_speaker.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1

    def test_filter_by_is_enable(self, client, two_mapping_speakers):
        response = client.get("/api/integrations/mapping-speakers?is_enable=false")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["is_enable"] is False
