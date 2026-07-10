"""
Test: EventMappingSpeaker Router

PRD: PRD_EventMappingSpeaker.md v1.0

Phase 3: Router Tests (TDD - Red Phase)
"""
import pytest
from app.utils.enums import EnumMappingEventCategory


# ============================================================
# Helper: Create test EventMapping
# ============================================================

@pytest.fixture
def test_event_mapping(test_db):
    """Create a test event mapping for router tests"""
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


# ============================================================
# Phase 3.1: GET /event-mappings/{mapping_id}/speakers Tests
# ============================================================

class TestListEventMappingSpeakers:
    """GET /event-mappings/{mapping_id}/speakers - List Tests"""

    def test_returns_empty_list_when_no_speakers_configured(self, client, test_event_mapping):
        """Test: Returns empty list when no speakers configured"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_returns_list_of_event_mapping_speakers(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Returns list of event mapping speakers"""
        from app.models.integration import EventMappingSpeaker

        # Create EventMappingSpeaker
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=3,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["repeat_count"] == 3

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        response = client.get("/api/integrations/event-mappings/99999/speakers")

        assert response.status_code == 404

    def test_response_includes_nested_speaker_object(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Response includes nested speaker object"""
        from app.models.integration import EventMappingSpeaker

        # Create EventMappingSpeaker with speaker
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers")

        assert response.status_code == 200
        data = response.json()
        item = data["data"]["items"][0]
        assert item["speaker"] is not None
        assert item["speaker"]["id"] == test_speaker.id
        assert item["speaker"]["name_device"] == test_speaker.name_device

    def test_response_includes_nested_file_group_object(self, client, test_db, test_event_mapping, test_file_group):
        """Test: Response includes nested file_group object"""
        from app.models.integration import EventMappingSpeaker

        # Create EventMappingSpeaker with file_group
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            file_group_id=test_file_group.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers")

        assert response.status_code == 200
        data = response.json()
        item = data["data"]["items"][0]
        assert item["file_group"] is not None
        assert item["file_group"]["id"] == test_file_group.id
        assert item["file_group"]["group_name"] == test_file_group.group_name


# ============================================================
# Phase 3.2: GET /event-mappings/{mapping_id}/speakers/{config_id} Tests
# ============================================================

class TestGetEventMappingSpeaker:
    """GET /event-mappings/{mapping_id}/speakers/{config_id} - Single Get Tests"""

    def test_returns_single_event_mapping_speaker(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Returns single event mapping speaker"""
        from app.models.integration import EventMappingSpeaker

        # Create EventMappingSpeaker
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=5,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == ems.id
        assert data["data"]["repeat_count"] == 5

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        response = client.get("/api/integrations/event-mappings/99999/speakers/1")

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when config not found"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/99999")

        assert response.status_code == 404

    def test_response_includes_nested_objects(self, client, test_db, test_event_mapping, test_speaker, test_file_group):
        """Test: Response includes nested objects"""
        from app.models.integration import EventMappingSpeaker

        # Create EventMappingSpeaker with speaker and file_group
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            file_group_id=test_file_group.id,
            repeat_count=2,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["speaker"] is not None
        assert data["speaker"]["id"] == test_speaker.id
        assert data["speaker"]["name_device"] == test_speaker.name_device
        assert data["file_group"] is not None
        assert data["file_group"]["id"] == test_file_group.id
        assert data["file_group"]["group_name"] == test_file_group.group_name


# ============================================================
# Phase 3.3: POST /event-mappings/{mapping_id}/speakers Tests
# ============================================================

class TestCreateEventMappingSpeaker:
    """POST /event-mappings/{mapping_id}/speakers - Create Tests"""

    def test_creates_event_mapping_speaker_successfully(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Creates event mapping speaker successfully"""
        payload = {
            "speaker_id": test_speaker.id,
            "repeat_count": 3,
            "is_enable": True
        }

        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["speaker"]["id"] == test_speaker.id
        assert data["data"]["repeat_count"] == 3

    def test_returns_404_when_event_mapping_not_found(self, client, test_speaker):
        """Test: Returns 404 when event mapping not found"""
        payload = {"speaker_id": test_speaker.id, "repeat_count": 1, "is_enable": True}
        response = client.post("/api/integrations/event-mappings/99999/speakers", json=payload)

        assert response.status_code == 404

    def test_returns_404_when_speaker_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when speaker not found"""
        payload = {"speaker_id": 99999, "repeat_count": 1, "is_enable": True}
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_404_when_file_group_not_found(self, client, test_event_mapping, test_speaker):
        """Test: Returns 404 when file_group not found"""
        payload = {
            "speaker_id": test_speaker.id,
            "file_group_id": 99999,
            "repeat_count": 1,
            "is_enable": True
        }
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_422_when_repeat_count_less_than_1(self, client, test_event_mapping, test_speaker):
        """Test: Returns 422 when repeat_count < 1"""
        payload = {
            "speaker_id": test_speaker.id,
            "repeat_count": 0,
            "is_enable": True
        }
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=payload
        )

        assert response.status_code == 422

    def test_returns_201_with_created_resource(self, client, test_db, test_event_mapping, test_speaker, test_file_group):
        """Test: Returns 201 with created resource"""
        payload = {
            "speaker_id": test_speaker.id,
            "file_group_id": test_file_group.id,
            "repeat_count": 5,
            "is_enable": False,
            "priority": 10
        }

        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["id"] is not None
        assert data["data"]["speaker"]["id"] == test_speaker.id
        assert data["data"]["file_group"]["id"] == test_file_group.id
        assert data["data"]["repeat_count"] == 5
        assert data["data"]["is_enable"] is False
        assert data["data"]["priority"] == 10


# ============================================================
# Phase 3.4: PATCH /event-mappings/{mapping_id}/speakers/{config_id} Tests
# ============================================================

class TestUpdateEventMappingSpeaker:
    """PATCH /event-mappings/{mapping_id}/speakers/{config_id} - Update Tests"""

    def test_updates_single_field_successfully(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Updates single field successfully"""
        from app.models.integration import EventMappingSpeaker

        # Create EventMappingSpeaker
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        # Update only repeat_count
        payload = {"repeat_count": 10}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["repeat_count"] == 10
        assert data["data"]["is_enable"] is True  # unchanged

    def test_updates_multiple_fields_successfully(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Updates multiple fields successfully"""
        from app.models.integration import EventMappingSpeaker

        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        payload = {"repeat_count": 5, "is_enable": False, "priority": 20}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["repeat_count"] == 5
        assert data["is_enable"] is False
        assert data["priority"] == 20

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        payload = {"repeat_count": 5}
        response = client.patch("/api/integrations/event-mappings/99999/speakers/1", json=payload)

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when config not found"""
        payload = {"repeat_count": 5}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/99999",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_422_when_repeat_count_less_than_1(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Returns 422 when repeat_count < 1"""
        from app.models.integration import EventMappingSpeaker

        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        payload = {"repeat_count": 0}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}",
            json=payload
        )

        assert response.status_code == 422


# ============================================================
# Phase 3.5: PUT /event-mappings/{mapping_id}/speakers/{config_id} Tests
# ============================================================

class TestReplaceEventMappingSpeaker:
    """PUT /event-mappings/{mapping_id}/speakers/{config_id} - Replace Tests"""

    def test_replaces_all_fields_successfully(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Replaces all fields successfully"""
        from app.models.integration import EventMappingSpeaker

        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True,
            priority=5
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        payload = {
            "speaker_id": test_speaker.id,
            "repeat_count": 10,
            "is_enable": False
        }
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["repeat_count"] == 10
        assert data["is_enable"] is False
        assert data["priority"] is None  # Not provided, so reset to None

    def test_returns_404_when_event_mapping_not_found(self, client, test_speaker):
        """Test: Returns 404 when event mapping not found"""
        payload = {"speaker_id": test_speaker.id, "repeat_count": 1, "is_enable": True}
        response = client.put("/api/integrations/event-mappings/99999/speakers/1", json=payload)

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping, test_speaker):
        """Test: Returns 404 when config not found"""
        payload = {"speaker_id": test_speaker.id, "repeat_count": 1, "is_enable": True}
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/99999",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_422_when_required_fields_missing(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Returns 422 when required fields missing"""
        from app.models.integration import EventMappingSpeaker

        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        # Missing required fields
        payload = {"speaker_id": test_speaker.id}  # Missing repeat_count and is_enable
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}",
            json=payload
        )

        assert response.status_code == 422


# ============================================================
# Phase 3.6: DELETE /event-mappings/{mapping_id}/speakers/{config_id} Tests
# ============================================================

class TestDeleteEventMappingSpeaker:
    """DELETE /event-mappings/{mapping_id}/speakers/{config_id} - Delete Tests"""

    def test_deletes_event_mapping_speaker_successfully(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Deletes event mapping speaker successfully"""
        from app.models.integration import EventMappingSpeaker

        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)
        ems_id = ems.id

        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems_id}"
        )

        assert response.status_code == 200

        # Verify deleted
        deleted = test_db.query(EventMappingSpeaker).filter(EventMappingSpeaker.id == ems_id).first()
        assert deleted is None

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        response = client.delete("/api/integrations/event-mappings/99999/speakers/1")

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when config not found"""
        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/99999"
        )

        assert response.status_code == 404

    def test_returns_success_response_after_deletion(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Returns success response after deletion"""
        from app.models.integration import EventMappingSpeaker

        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{ems.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower() or "삭제" in data["message"]


# ============================================================
# Phase 4: Integration Tests
# ============================================================

class TestEventMappingSpeakerIntegration:
    """Integration Tests for EventMappingSpeaker API"""

    def test_crud_cycle(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Create, Read, Update, Delete cycle"""
        # CREATE
        create_payload = {
            "speaker_id": test_speaker.id,
            "repeat_count": 3,
            "is_enable": True,
            "priority": 5
        }
        create_response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=create_payload
        )
        assert create_response.status_code == 201
        created_id = create_response.json()["data"]["id"]

        # READ
        read_response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{created_id}"
        )
        assert read_response.status_code == 200
        assert read_response.json()["data"]["repeat_count"] == 3

        # UPDATE
        update_payload = {"repeat_count": 10}
        update_response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{created_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["repeat_count"] == 10

        # DELETE
        delete_response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{created_id}"
        )
        assert delete_response.status_code == 200

        # VERIFY DELETED
        verify_response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers/{created_id}"
        )
        assert verify_response.status_code == 404

    def test_multiple_speakers_for_single_event_mapping(self, client, test_db, test_event_mapping, test_speaker):
        """Test: Multiple speakers for single event mapping"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        # Create second speaker
        speaker2 = Speaker(
            number_device=2402,
            group_device=1,
            name_device="Test Speaker 2",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
        )
        test_db.add(speaker2)
        test_db.commit()
        test_db.refresh(speaker2)

        # Create first mapping
        payload1 = {"speaker_id": test_speaker.id, "repeat_count": 1, "is_enable": True}
        response1 = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=payload1
        )
        assert response1.status_code == 201

        # Create second mapping
        payload2 = {"speaker_id": speaker2.id, "repeat_count": 2, "is_enable": True}
        response2 = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers",
            json=payload2
        )
        assert response2.status_code == 201

        # Verify list returns both
        list_response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/speakers"
        )
        assert list_response.status_code == 200
        assert list_response.json()["data"]["total"] == 2

    def test_speaker_deletion_sets_speaker_id_to_null(self, test_db, test_event_mapping, test_speaker):
        """Test: Speaker deletion sets speaker_id to NULL"""
        from app.models.integration import EventMappingSpeaker
        from app.models.device import Speaker

        # Create EventMappingSpeaker
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)
        ems_id = ems.id

        # Delete the speaker
        test_db.delete(test_speaker)
        test_db.commit()

        # Verify speaker_id is NULL
        test_db.expire_all()
        updated_ems = test_db.query(EventMappingSpeaker).filter(EventMappingSpeaker.id == ems_id).first()
        assert updated_ems is not None
        assert updated_ems.speaker_id is None

    def test_file_group_deletion_sets_file_group_id_to_null(self, test_db, test_event_mapping, test_speaker, test_file_group):
        """Test: FileGroup deletion sets file_group_id to NULL"""
        from app.models.integration import EventMappingSpeaker
        from app.models.file_group import FileGroup

        # Create EventMappingSpeaker with file_group
        ems = EventMappingSpeaker(
            event_mapping_id=test_event_mapping.id,
            speaker_id=test_speaker.id,
            file_group_id=test_file_group.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)
        ems_id = ems.id

        # Delete the file_group
        test_db.delete(test_file_group)
        test_db.commit()

        # Verify file_group_id is NULL
        test_db.expire_all()
        updated_ems = test_db.query(EventMappingSpeaker).filter(EventMappingSpeaker.id == ems_id).first()
        assert updated_ems is not None
        assert updated_ems.file_group_id is None

    def test_event_mapping_deletion_cascades_to_speakers(self, test_db, test_speaker):
        """Test: EventMapping deletion cascades to speakers"""
        from app.models.integration import EventMapping, EventMappingSpeaker
        from app.utils.enums import EnumMappingEventCategory

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Event For Cascade",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()
        test_db.refresh(event_mapping)

        # Create EventMappingSpeaker
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)
        ems_id = ems.id

        # Delete EventMapping
        test_db.delete(event_mapping)
        test_db.commit()

        # Verify EventMappingSpeaker is also deleted (CASCADE)
        deleted_ems = test_db.query(EventMappingSpeaker).filter(EventMappingSpeaker.id == ems_id).first()
        assert deleted_ems is None
