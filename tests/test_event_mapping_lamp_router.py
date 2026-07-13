"""
Test: EventMappingLamp Router

PRD: PRD_Lamp_Device.md v1.1

Phase 3.3: Router Tests (TDD - Red Phase)
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
# Phase 3.3.1: GET /event-mappings/{mapping_id}/lamps Tests
# ============================================================

class TestListEventMappingLamps:
    """GET /event-mappings/{mapping_id}/lamps - List Tests"""

    def test_returns_empty_list_when_no_lamps_configured(self, client, test_event_mapping):
        """Test: Returns empty list when no lamps configured"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    def test_returns_list_of_event_mapping_lamps(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Returns list of event mapping lamps"""
        from app.models.integration import EventMappingLamp

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        response = client.get("/api/integrations/event-mappings/99999/lamps")

        assert response.status_code == 404

    def test_response_includes_nested_lamp_object(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Response includes nested lamp object"""
        from app.models.integration import EventMappingLamp

        # Create EventMappingLamp with lamp
        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps")

        assert response.status_code == 200
        data = response.json()
        item = data["data"]["items"][0]
        assert item["lamp"] is not None
        assert item["lamp"]["id"] == test_lamp.id
        assert item["lamp"]["name_device"] == test_lamp.name_device

    def test_response_includes_nested_event_mapping_object(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Response includes nested event_mapping object"""
        from app.models.integration import EventMappingLamp

        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps")

        assert response.status_code == 200
        data = response.json()
        item = data["data"]["items"][0]
        assert item["event_mapping"] is not None
        assert item["event_mapping"]["id"] == test_event_mapping.id
        assert item["event_mapping"]["name_event"] == test_event_mapping.name_event


# ============================================================
# Phase 3.3.2: GET /event-mappings/{mapping_id}/lamps/{config_id} Tests
# ============================================================

class TestGetEventMappingLamp:
    """GET /event-mappings/{mapping_id}/lamps/{config_id} - Single Get Tests"""

    def test_returns_single_event_mapping_lamp(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Returns single event mapping lamp"""
        from app.models.integration import EventMappingLamp

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            color="Green",
            buzzer_time=10,
            is_enable=True,
            priority=5
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == eml.id
        assert data["data"]["color"] == "Green"  # Enum value is "Green"
        assert data["data"]["buzzer_time"] == 10

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        response = client.get("/api/integrations/event-mappings/99999/lamps/1")

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when config not found"""
        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/99999")

        assert response.status_code == 404

    def test_response_includes_nested_objects(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Response includes nested objects"""
        from app.models.integration import EventMappingLamp

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["lamp"] is not None
        assert data["lamp"]["id"] == test_lamp.id
        assert data["event_mapping"] is not None
        assert data["event_mapping"]["id"] == test_event_mapping.id


# ============================================================
# Phase 3.3.3: POST /event-mappings/{mapping_id}/lamps Tests
# ============================================================

class TestCreateEventMappingLamp:
    """POST /event-mappings/{mapping_id}/lamps - Create Tests"""

    def test_creates_event_mapping_lamp_successfully(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Creates event mapping lamp successfully"""
        payload = {
            "event_mapping_id": test_event_mapping.id,
            "lamp_id": test_lamp.id,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 1
        }

        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps",
            json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["lamp"]["id"] == test_lamp.id
        assert data["data"]["color"] == "Red"  # Enum value is "Red"

    def test_returns_404_when_event_mapping_not_found(self, client, test_lamp):
        """Test: Returns 404 when event mapping not found"""
        payload = {
            "event_mapping_id": 99999,
            "lamp_id": test_lamp.id,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 1
        }
        response = client.post("/api/integrations/event-mappings/99999/lamps", json=payload)

        assert response.status_code == 404

    def test_returns_404_when_lamp_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when lamp not found"""
        payload = {
            "event_mapping_id": test_event_mapping.id,
            "lamp_id": 99999,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 1
        }
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_422_when_priority_less_than_1(self, client, test_event_mapping, test_lamp):
        """Test: Returns 422 when priority < 1"""
        payload = {
            "event_mapping_id": test_event_mapping.id,
            "lamp_id": test_lamp.id,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 0  # Invalid
        }
        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps",
            json=payload
        )

        assert response.status_code == 422

    def test_uses_default_values(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Uses default values when not specified"""
        payload = {
            "event_mapping_id": test_event_mapping.id,
            "lamp_id": test_lamp.id
        }

        response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps",
            json=payload
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["color"] == "Red"  # Default (EnumLampColor.RED.value)
        assert data["buzzer_time"] == 5  # Default
        assert data["buzzer_sound"] == "PI-PI-PI"  # Default (EnumBuzzerSound.PI_PI_PI.value)
        assert data["light_mode"] == "steady"  # Default (EnumLightMode.STEADY.value)
        assert data["is_enable"] is True  # Default
        assert data["priority"] == 1  # Default


# ============================================================
# Phase 3.3.4: PATCH /event-mappings/{mapping_id}/lamps/{config_id} Tests
# ============================================================

class TestUpdateEventMappingLamp:
    """PATCH /event-mappings/{mapping_id}/lamps/{config_id} - Update Tests"""

    def test_updates_single_field_successfully(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Updates single field successfully"""
        from app.models.integration import EventMappingLamp

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        # Update only color
        payload = {"color": "Blue"}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["color"] == "Blue"
        assert data["data"]["is_enable"] is True  # unchanged

    def test_updates_multiple_fields_successfully(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Updates multiple fields successfully"""
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

        payload = {"buzzer_time": 15, "is_enable": False, "priority": 10}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["buzzer_time"] == 15
        assert data["is_enable"] is False
        assert data["priority"] == 10

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        payload = {"color": "Green"}
        response = client.patch("/api/integrations/event-mappings/99999/lamps/1", json=payload)

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when config not found"""
        payload = {"color": "Green"}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/99999",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_422_when_priority_less_than_1(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Returns 422 when priority < 1"""
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

        payload = {"priority": 0}
        response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}",
            json=payload
        )

        assert response.status_code == 422


# ============================================================
# Phase 3.3.5: PUT /event-mappings/{mapping_id}/lamps/{config_id} Tests
# ============================================================

class TestReplaceEventMappingLamp:
    """PUT /event-mappings/{mapping_id}/lamps/{config_id} - Replace Tests"""

    def test_replaces_all_fields_successfully(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Replaces all fields successfully"""
        from app.models.integration import EventMappingLamp

        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=5
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        payload = {
            "event_mapping_id": test_event_mapping.id,
            "lamp_id": test_lamp.id,
            "color": "Orange",
            "buzzer_time": 20,
            "buzzer_sound": "Emergency",
            "light_mode": "blinking",
            "is_enable": False,
            "priority": 10
        }
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["color"] == "Orange"
        assert data["buzzer_time"] == 20
        assert data["is_enable"] is False
        assert data["priority"] == 10

    def test_returns_404_when_event_mapping_not_found(self, client, test_lamp):
        """Test: Returns 404 when event mapping not found"""
        payload = {
            "event_mapping_id": 99999,
            "lamp_id": test_lamp.id,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 1
        }
        response = client.put("/api/integrations/event-mappings/99999/lamps/1", json=payload)

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping, test_lamp):
        """Test: Returns 404 when config not found"""
        payload = {
            "event_mapping_id": test_event_mapping.id,
            "lamp_id": test_lamp.id,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 1
        }
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/99999",
            json=payload
        )

        assert response.status_code == 404

    def test_returns_422_when_required_fields_missing(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Returns 422 when required fields missing"""
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

        # Missing required fields
        payload = {"lamp_id": test_lamp.id}
        response = client.put(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}",
            json=payload
        )

        assert response.status_code == 422


# ============================================================
# Phase 3.3.6: DELETE /event-mappings/{mapping_id}/lamps/{config_id} Tests
# ============================================================

class TestDeleteEventMappingLamp:
    """DELETE /event-mappings/{mapping_id}/lamps/{config_id} - Delete Tests"""

    def test_deletes_event_mapping_lamp_successfully(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Deletes event mapping lamp successfully"""
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
        eml_id = eml.id

        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml_id}"
        )

        assert response.status_code == 200

        # Verify deleted
        deleted = test_db.query(EventMappingLamp).filter(EventMappingLamp.id == eml_id).first()
        assert deleted is None

    def test_returns_404_when_event_mapping_not_found(self, client):
        """Test: Returns 404 when event mapping not found"""
        response = client.delete("/api/integrations/event-mappings/99999/lamps/1")

        assert response.status_code == 404

    def test_returns_404_when_config_not_found(self, client, test_event_mapping):
        """Test: Returns 404 when config not found"""
        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/99999"
        )

        assert response.status_code == 404

    def test_returns_success_response_after_deletion(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Returns success response after deletion"""
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

        response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{eml.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower() or "삭제" in data["message"]


# ============================================================
# Phase 3.3.7: Integration Tests
# ============================================================

class TestEventMappingLampIntegration:
    """Integration Tests for EventMappingLamp API"""

    def test_crud_cycle(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Create, Read, Update, Delete cycle"""
        # CREATE
        create_payload = {
            "event_mapping_id": test_event_mapping.id,
            "lamp_id": test_lamp.id,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 3
        }
        create_response = client.post(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps",
            json=create_payload
        )
        assert create_response.status_code == 201
        created_id = create_response.json()["data"]["id"]

        # READ
        read_response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{created_id}"
        )
        assert read_response.status_code == 200
        assert read_response.json()["data"]["priority"] == 3

        # UPDATE
        update_payload = {"priority": 10, "color": "Green"}
        update_response = client.patch(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{created_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["priority"] == 10
        assert update_response.json()["data"]["color"] == "Green"

        # DELETE
        delete_response = client.delete(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{created_id}"
        )
        assert delete_response.status_code == 200

        # VERIFY DELETED
        verify_response = client.get(
            f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps/{created_id}"
        )
        assert verify_response.status_code == 404

    def test_lamp_deletion_sets_lamp_id_to_null(self, test_db, test_event_mapping, test_lamp):
        """Test: Lamp deletion sets lamp_id to NULL"""
        from app.models.integration import EventMappingLamp

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)
        eml_id = eml.id

        # Delete the lamp
        test_db.delete(test_lamp)
        test_db.commit()

        # Verify lamp_id is NULL
        test_db.expire_all()
        updated_eml = test_db.query(EventMappingLamp).filter(EventMappingLamp.id == eml_id).first()
        assert updated_eml is not None
        assert updated_eml.lamp_id is None

    def test_event_mapping_deletion_cascades_to_lamps(self, test_db, test_lamp):
        """Test: EventMapping deletion cascades to lamps"""
        from app.models.integration import EventMapping, EventMappingLamp

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Event For Cascade",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()
        test_db.refresh(event_mapping)

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)
        eml_id = eml.id

        # Delete EventMapping
        test_db.delete(event_mapping)
        test_db.commit()

        # Verify EventMappingLamp is also deleted (CASCADE)
        deleted_eml = test_db.query(EventMappingLamp).filter(EventMappingLamp.id == eml_id).first()
        assert deleted_eml is None

    def test_nested_lamp_excludes_user_password(self, client, test_db, test_event_mapping, test_lamp):
        """Test: Nested lamp response excludes user_password for security"""
        from app.models.integration import EventMappingLamp

        # Update test_lamp to have user_password
        test_lamp.user_password = "secret123"
        test_db.commit()

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=test_event_mapping.id,
            lamp_id=test_lamp.id,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()

        response = client.get(f"/api/integrations/event-mappings/{test_event_mapping.id}/lamps")

        assert response.status_code == 200
        data = response.json()
        lamp_nested = data["data"]["items"][0]["lamp"]
        assert lamp_nested is not None
        assert "user_password" not in lamp_nested
