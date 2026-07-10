"""
Test: EventMappingLamp schema

PRD: PRD_Lamp_Device.md v1.1

Phase 3.2: Schema Tests (TDD - Red Phase)
"""
import pytest
from pydantic import ValidationError
from datetime import datetime


# ============================================================
# Phase 3.2.1: Create Schema Tests
# ============================================================

class TestEventMappingLampCreateSchema:
    """EventMappingLampCreate Schema Tests"""

    def test_event_mapping_lamp_create_requires_event_mapping_id(self):
        """Test: EventMappingLampCreate requires event_mapping_id"""
        from app.schemas.integration import EventMappingLampCreate

        # event_mapping_id is required
        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.event_mapping_id == 1

        # Missing event_mapping_id should fail
        with pytest.raises(ValidationError):
            EventMappingLampCreate(lamp_id=501)

    def test_event_mapping_lamp_create_requires_lamp_id(self):
        """Test: EventMappingLampCreate requires lamp_id"""
        from app.schemas.integration import EventMappingLampCreate

        # lamp_id is required
        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.lamp_id == 501

        # Missing lamp_id should fail
        with pytest.raises(ValidationError):
            EventMappingLampCreate(event_mapping_id=1)

    def test_event_mapping_lamp_create_color_default_is_red(self):
        """Test: EventMappingLampCreate color default is 'Red'"""
        from app.schemas.integration import EventMappingLampCreate

        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.color == "Red"

    def test_event_mapping_lamp_create_buzzer_time_default_is_5(self):
        """Test: EventMappingLampCreate buzzer_time default is 5"""
        from app.schemas.integration import EventMappingLampCreate

        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.buzzer_time == 5

    def test_event_mapping_lamp_create_buzzer_time_validation(self):
        """Test: EventMappingLampCreate buzzer_time validation (ge=0)"""
        from app.schemas.integration import EventMappingLampCreate

        # Valid: buzzer_time >= 0
        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501, buzzer_time=0)
        assert schema.buzzer_time == 0

        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501, buzzer_time=10)
        assert schema.buzzer_time == 10

        # Invalid: buzzer_time < 0
        with pytest.raises(ValidationError):
            EventMappingLampCreate(event_mapping_id=1, lamp_id=501, buzzer_time=-1)

    def test_event_mapping_lamp_create_buzzer_sound_default_is_pi_pi_pi(self):
        """Test: EventMappingLampCreate buzzer_sound default is 'PI-PI-PI'"""
        from app.schemas.integration import EventMappingLampCreate

        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.buzzer_sound == "PI-PI-PI"

    def test_event_mapping_lamp_create_light_mode_default_is_steady(self):
        """Test: EventMappingLampCreate light_mode default is 'steady'"""
        from app.schemas.integration import EventMappingLampCreate

        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.light_mode == "steady"

    def test_event_mapping_lamp_create_is_enable_default_is_true(self):
        """Test: EventMappingLampCreate is_enable default is True"""
        from app.schemas.integration import EventMappingLampCreate

        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.is_enable is True

    def test_event_mapping_lamp_create_priority_default_is_1(self):
        """Test: EventMappingLampCreate priority default is 1"""
        from app.schemas.integration import EventMappingLampCreate

        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501)
        assert schema.priority == 1

    def test_event_mapping_lamp_create_priority_validation(self):
        """Test: EventMappingLampCreate priority validation (ge=1)"""
        from app.schemas.integration import EventMappingLampCreate

        # Valid: priority >= 1
        schema = EventMappingLampCreate(event_mapping_id=1, lamp_id=501, priority=10)
        assert schema.priority == 10

        # Invalid: priority < 1
        with pytest.raises(ValidationError):
            EventMappingLampCreate(event_mapping_id=1, lamp_id=501, priority=0)

        with pytest.raises(ValidationError):
            EventMappingLampCreate(event_mapping_id=1, lamp_id=501, priority=-1)

    def test_event_mapping_lamp_create_all_fields(self):
        """Test: EventMappingLampCreate with all fields specified"""
        from app.schemas.integration import EventMappingLampCreate

        schema = EventMappingLampCreate(
            event_mapping_id=10,
            lamp_id=501,
            color="Green",
            buzzer_time=10,
            buzzer_sound="Fire A-WANG",
            light_mode="blinking",
            is_enable=False,
            priority=5
        )

        assert schema.event_mapping_id == 10
        assert schema.lamp_id == 501
        assert schema.color == "Green"
        assert schema.buzzer_time == 10
        assert schema.buzzer_sound == "Fire A-WANG"
        assert schema.light_mode == "blinking"
        assert schema.is_enable is False
        assert schema.priority == 5


# ============================================================
# Phase 3.2.2: Update Schema Tests (PATCH)
# ============================================================

class TestEventMappingLampUpdateSchema:
    """EventMappingLampUpdate Schema Tests"""

    def test_event_mapping_lamp_update_all_fields_optional(self):
        """Test: EventMappingLampUpdate all fields are optional"""
        from app.schemas.integration import EventMappingLampUpdate

        # Empty update is valid
        schema = EventMappingLampUpdate()
        assert schema.lamp_id is None
        assert schema.color is None
        assert schema.buzzer_time is None
        assert schema.buzzer_sound is None
        assert schema.light_mode is None
        assert schema.is_enable is None
        assert schema.priority is None

    def test_event_mapping_lamp_update_partial_update(self):
        """Test: EventMappingLampUpdate allows partial updates"""
        from app.schemas.integration import EventMappingLampUpdate

        # Only update color
        schema = EventMappingLampUpdate(color="Blue")
        assert schema.color == "Blue"
        assert schema.lamp_id is None

        # Only update multiple fields
        schema = EventMappingLampUpdate(buzzer_time=15, is_enable=False)
        assert schema.buzzer_time == 15
        assert schema.is_enable is False
        assert schema.color is None

    def test_event_mapping_lamp_update_buzzer_time_validation(self):
        """Test: EventMappingLampUpdate buzzer_time validation (ge=0)"""
        from app.schemas.integration import EventMappingLampUpdate

        # Valid: buzzer_time >= 0
        schema = EventMappingLampUpdate(buzzer_time=0)
        assert schema.buzzer_time == 0

        # Invalid: buzzer_time < 0
        with pytest.raises(ValidationError):
            EventMappingLampUpdate(buzzer_time=-1)

    def test_event_mapping_lamp_update_priority_validation(self):
        """Test: EventMappingLampUpdate priority validation (ge=1)"""
        from app.schemas.integration import EventMappingLampUpdate

        # Valid: priority >= 1
        schema = EventMappingLampUpdate(priority=5)
        assert schema.priority == 5

        # Invalid: priority < 1
        with pytest.raises(ValidationError):
            EventMappingLampUpdate(priority=0)


# ============================================================
# Phase 3.2.3: Replace Schema Tests (PUT)
# ============================================================

class TestEventMappingLampReplaceSchema:
    """EventMappingLampReplace Schema Tests"""

    def test_event_mapping_lamp_replace_requires_all_fields(self):
        """Test: EventMappingLampReplace requires all fields"""
        from app.schemas.integration import EventMappingLampReplace

        # All fields provided
        schema = EventMappingLampReplace(
            event_mapping_id=10,
            lamp_id=501,
            color="Red",
            buzzer_time=5,
            buzzer_sound="PI-PI-PI",
            light_mode="steady",
            is_enable=True,
            priority=1
        )
        assert schema.event_mapping_id == 10
        assert schema.lamp_id == 501

    def test_event_mapping_lamp_replace_requires_event_mapping_id(self):
        """Test: EventMappingLampReplace requires event_mapping_id"""
        from app.schemas.integration import EventMappingLampReplace

        # Missing event_mapping_id should fail
        with pytest.raises(ValidationError):
            EventMappingLampReplace(
                lamp_id=501,
                color="Red",
                buzzer_time=5,
                buzzer_sound="PI-PI-PI",
                light_mode="steady",
                is_enable=True,
                priority=1
            )

    def test_event_mapping_lamp_replace_requires_lamp_id(self):
        """Test: EventMappingLampReplace requires lamp_id"""
        from app.schemas.integration import EventMappingLampReplace

        # Missing lamp_id should fail
        with pytest.raises(ValidationError):
            EventMappingLampReplace(
                event_mapping_id=10,
                color="Red",
                buzzer_time=5,
                buzzer_sound="PI-PI-PI",
                light_mode="steady",
                is_enable=True,
                priority=1
            )

    def test_event_mapping_lamp_replace_requires_color(self):
        """Test: EventMappingLampReplace requires color"""
        from app.schemas.integration import EventMappingLampReplace

        # Missing color should fail
        with pytest.raises(ValidationError):
            EventMappingLampReplace(
                event_mapping_id=10,
                lamp_id=501,
                buzzer_time=5,
                buzzer_sound="PI-PI-PI",
                light_mode="steady",
                is_enable=True,
                priority=1
            )

    def test_event_mapping_lamp_replace_buzzer_time_validation(self):
        """Test: EventMappingLampReplace buzzer_time validation (ge=0)"""
        from app.schemas.integration import EventMappingLampReplace

        # Invalid: buzzer_time < 0
        with pytest.raises(ValidationError):
            EventMappingLampReplace(
                event_mapping_id=10,
                lamp_id=501,
                color="Red",
                buzzer_time=-1,
                buzzer_sound="PI-PI-PI",
                light_mode="steady",
                is_enable=True,
                priority=1
            )

    def test_event_mapping_lamp_replace_priority_validation(self):
        """Test: EventMappingLampReplace priority validation (ge=1)"""
        from app.schemas.integration import EventMappingLampReplace

        # Invalid: priority < 1
        with pytest.raises(ValidationError):
            EventMappingLampReplace(
                event_mapping_id=10,
                lamp_id=501,
                color="Red",
                buzzer_time=5,
                buzzer_sound="PI-PI-PI",
                light_mode="steady",
                is_enable=True,
                priority=0
            )


# ============================================================
# Phase 3.2.4: Response Schema Tests
# ============================================================

class TestEventMappingLampResponseSchema:
    """EventMappingLampResponse Schema Tests"""

    def test_event_mapping_lamp_response_includes_all_fields(self):
        """Test: EventMappingLampResponse includes all required fields"""
        from app.schemas.integration import EventMappingLampResponse, EventMappingNestedResponse

        now = datetime.now()
        event_mapping_nested = EventMappingNestedResponse(
            id=10,
            name_event="Test Event",
            category_event_mapping="FENCE_SENSOR_ONLY"
        )

        data = {
            "id": 1,
            "event_mapping": event_mapping_nested,
            "lamp": None,
            "color": "Red",
            "buzzer_time": 5,
            "buzzer_sound": "PI-PI-PI",
            "light_mode": "steady",
            "is_enable": True,
            "priority": 1,
            "created_at": now,
            "updated_at": now
        }
        schema = EventMappingLampResponse(**data)
        assert schema.id == 1
        assert schema.event_mapping.id == 10
        assert schema.event_mapping.name_event == "Test Event"
        assert schema.color == "Red"
        assert schema.buzzer_time == 5
        assert schema.is_enable is True

    def test_event_mapping_lamp_response_includes_nested_event_mapping(self):
        """Test: EventMappingLampResponse includes nested event_mapping"""
        from app.schemas.integration import EventMappingLampResponse

        # Verify schema has event_mapping field
        assert 'event_mapping' in EventMappingLampResponse.model_fields

    def test_event_mapping_lamp_response_includes_nested_lamp(self):
        """Test: EventMappingLampResponse includes nested lamp (optional)"""
        from app.schemas.integration import EventMappingLampResponse

        # Verify schema has lamp field
        assert 'lamp' in EventMappingLampResponse.model_fields

    def test_event_mapping_lamp_response_lamp_can_be_null(self):
        """Test: EventMappingLampResponse lamp can be null (SET NULL behavior)"""
        from app.schemas.integration import EventMappingLampResponse, EventMappingNestedResponse

        now = datetime.now()
        event_mapping_nested = EventMappingNestedResponse(
            id=10,
            name_event="Test Event",
            category_event_mapping="FENCE_SENSOR_ONLY"
        )

        # lamp is None (Lamp was deleted)
        schema = EventMappingLampResponse(
            id=1,
            event_mapping=event_mapping_nested,
            lamp=None,  # SET NULL behavior
            color="Red",
            buzzer_time=5,
            buzzer_sound="PI-PI-PI",
            light_mode="steady",
            is_enable=True,
            priority=1,
            created_at=now,
            updated_at=now
        )
        assert schema.lamp is None

    def test_event_mapping_lamp_response_includes_timestamps(self):
        """Test: EventMappingLampResponse includes timestamps"""
        from app.schemas.integration import EventMappingLampResponse

        # Verify schema has timestamp fields
        assert 'created_at' in EventMappingLampResponse.model_fields
        assert 'updated_at' in EventMappingLampResponse.model_fields


# ============================================================
# Phase 3.2.5: Nested Response Schema Tests
# ============================================================

class TestLampNestedResponseIntegrationSchema:
    """LampNestedResponseIntegration Schema Tests"""

    def test_lamp_nested_response_integration_includes_all_fields(self):
        """Test: LampNestedResponseIntegration includes all lamp fields"""
        from app.schemas.integration import LampNestedResponseIntegration

        schema = LampNestedResponseIntegration(
            id=501,
            number_device=5001,
            group_device=0,
            name_device="Lamp-A-1",
            type_device="Lamp",
            version="v1.0.0",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80,
            user_name="admin",
            description="GOP 1구역 경광등"
        )

        assert schema.id == 501
        assert schema.number_device == 5001
        assert schema.name_device == "Lamp-A-1"
        assert schema.ip_address == "192.168.1.109"
        assert schema.ip_port == 80

    def test_lamp_nested_response_integration_excludes_timestamps(self):
        """Test: LampNestedResponseIntegration excludes created_at, updated_at (Nested Rule)"""
        from app.schemas.integration import LampNestedResponseIntegration

        # Verify no timestamp fields (per Nested Response rule)
        assert 'created_at' not in LampNestedResponseIntegration.model_fields
        assert 'updated_at' not in LampNestedResponseIntegration.model_fields

    def test_lamp_nested_response_integration_excludes_user_password(self):
        """Test: LampNestedResponseIntegration excludes user_password (sensitive data)"""
        from app.schemas.integration import LampNestedResponseIntegration

        # Verify no user_password field (sensitive data)
        assert 'user_password' not in LampNestedResponseIntegration.model_fields

    def test_lamp_nested_response_integration_optional_fields(self):
        """Test: LampNestedResponseIntegration optional fields can be null"""
        from app.schemas.integration import LampNestedResponseIntegration

        # Minimal required fields only
        schema = LampNestedResponseIntegration(
            id=501,
            number_device=5001,
            group_device=0,
            name_device="Lamp-A-1",
            type_device="Lamp",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.109",
            ip_port=80
        )

        assert schema.version is None
        assert schema.user_name is None
        assert schema.description is None
        assert schema.geolocation is None


class TestEventMappingNestedResponseSchema:
    """EventMappingNestedResponse Schema Tests"""

    def test_event_mapping_nested_response_includes_required_fields(self):
        """Test: EventMappingNestedResponse includes id, name_event, category_event_mapping"""
        from app.schemas.integration import EventMappingNestedResponse

        schema = EventMappingNestedResponse(
            id=10,
            name_event="GOP 1구역 감지 이벤트",
            category_event_mapping="FENCE_SENSOR_ONLY"
        )

        assert schema.id == 10
        assert schema.name_event == "GOP 1구역 감지 이벤트"
        assert schema.category_event_mapping == "FENCE_SENSOR_ONLY"

    def test_event_mapping_nested_response_excludes_timestamps(self):
        """Test: EventMappingNestedResponse excludes timestamps (Nested Rule)"""
        from app.schemas.integration import EventMappingNestedResponse

        # Verify no timestamp fields
        assert 'created_at' not in EventMappingNestedResponse.model_fields
        assert 'updated_at' not in EventMappingNestedResponse.model_fields
