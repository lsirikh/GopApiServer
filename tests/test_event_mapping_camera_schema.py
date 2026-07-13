"""
Test: EventMappingCamera schemas
PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 6

Phase 2: Schema Tests (TDD - Red Phase)
"""
import pytest
from pydantic import ValidationError


# ============================================================
# Phase 2.1: Create Schema Tests
# ============================================================

class TestEventMappingCameraCreateSchema:
    """EventMappingCameraCreate Schema Tests"""

    def test_event_mapping_camera_create_schema_exists(self):
        """Test: EventMappingCameraCreate schema class exists"""
        from app.schemas.integration import EventMappingCameraCreate
        assert EventMappingCameraCreate is not None

    def test_event_mapping_camera_create_camera_id_required(self):
        """Test: EventMappingCameraCreate.camera_id is required"""
        from app.schemas.integration import EventMappingCameraCreate

        # Should raise ValidationError without camera_id
        with pytest.raises(ValidationError):
            EventMappingCameraCreate()

        # Should work with camera_id
        schema = EventMappingCameraCreate(camera_id=1)
        assert schema.camera_id == 1

    def test_event_mapping_camera_create_target_preset_id_optional(self):
        """Test: EventMappingCameraCreate.target_preset_id is optional"""
        from app.schemas.integration import EventMappingCameraCreate

        # Without target_preset_id (should be None)
        schema = EventMappingCameraCreate(camera_id=1)
        assert schema.target_preset_id is None

        # With target_preset_id
        schema = EventMappingCameraCreate(camera_id=1, target_preset_id=5)
        assert schema.target_preset_id == 5

    def test_event_mapping_camera_create_home_preset_id_optional(self):
        """Test: EventMappingCameraCreate.home_preset_id is optional"""
        from app.schemas.integration import EventMappingCameraCreate

        # Without home_preset_id (should be None)
        schema = EventMappingCameraCreate(camera_id=1)
        assert schema.home_preset_id is None

        # With home_preset_id
        schema = EventMappingCameraCreate(camera_id=1, home_preset_id=6)
        assert schema.home_preset_id == 6

    def test_event_mapping_camera_create_delay_time_default(self):
        """Test: EventMappingCameraCreate.delay_time defaults to 0"""
        from app.schemas.integration import EventMappingCameraCreate

        schema = EventMappingCameraCreate(camera_id=1)
        assert schema.delay_time == 0

    def test_event_mapping_camera_create_is_enable_default(self):
        """Test: EventMappingCameraCreate.is_enable defaults to True"""
        from app.schemas.integration import EventMappingCameraCreate

        schema = EventMappingCameraCreate(camera_id=1)
        assert schema.is_enable is True

    def test_event_mapping_camera_create_priority_optional(self):
        """Test: EventMappingCameraCreate.priority is optional (defaults to None)"""
        from app.schemas.integration import EventMappingCameraCreate

        # Without priority (should be None)
        schema = EventMappingCameraCreate(camera_id=1)
        assert schema.priority is None

        # With priority
        schema = EventMappingCameraCreate(camera_id=1, priority=1)
        assert schema.priority == 1


# ============================================================
# Phase 2.2: Update Schema Tests
# ============================================================

class TestEventMappingCameraUpdateSchema:
    """EventMappingCameraUpdate Schema Tests"""

    def test_event_mapping_camera_update_schema_exists(self):
        """Test: EventMappingCameraUpdate schema class exists"""
        from app.schemas.integration import EventMappingCameraUpdate
        assert EventMappingCameraUpdate is not None

    def test_event_mapping_camera_update_all_fields_optional(self):
        """Test: EventMappingCameraUpdate all fields are optional (for PATCH)"""
        from app.schemas.integration import EventMappingCameraUpdate

        # Empty schema should be valid
        schema = EventMappingCameraUpdate()
        assert schema.camera_id is None
        assert schema.target_preset_id is None
        assert schema.home_preset_id is None
        assert schema.delay_time is None
        assert schema.is_enable is None
        assert schema.priority is None

        # Partial update
        schema = EventMappingCameraUpdate(delay_time=30)
        assert schema.delay_time == 30
        assert schema.camera_id is None


# ============================================================
# Phase 2.3: Response Schema Tests
# ============================================================

class TestEventMappingCameraResponseSchema:
    """EventMappingCameraResponse Schema Tests"""

    def test_event_mapping_camera_response_schema_exists(self):
        """Test: EventMappingCameraResponse schema class exists"""
        from app.schemas.integration import EventMappingCameraResponse
        assert EventMappingCameraResponse is not None

    def test_event_mapping_camera_response_has_camera_nested(self):
        """Test: EventMappingCameraResponse has camera field (Optional nested)"""
        from app.schemas.integration import EventMappingCameraResponse
        from typing import get_type_hints, Optional

        hints = get_type_hints(EventMappingCameraResponse)
        assert 'camera' in hints

    def test_event_mapping_camera_response_has_target_preset_nested(self):
        """Test: EventMappingCameraResponse has target_preset field (Optional nested)"""
        from app.schemas.integration import EventMappingCameraResponse
        from typing import get_type_hints

        hints = get_type_hints(EventMappingCameraResponse)
        assert 'target_preset' in hints

    def test_event_mapping_camera_response_has_home_preset_nested(self):
        """Test: EventMappingCameraResponse has home_preset field (Optional nested)"""
        from app.schemas.integration import EventMappingCameraResponse
        from typing import get_type_hints

        hints = get_type_hints(EventMappingCameraResponse)
        assert 'home_preset' in hints

    def test_event_mapping_camera_response_has_timestamps(self):
        """Test: EventMappingCameraResponse has created_at and updated_at"""
        from app.schemas.integration import EventMappingCameraResponse
        from typing import get_type_hints

        hints = get_type_hints(EventMappingCameraResponse)
        assert 'created_at' in hints
        assert 'updated_at' in hints


# ============================================================
# Phase 2.4: Nested Response Schema Tests
# ============================================================

class TestNestedResponseSchemas:
    """EventMappingCameraResponse Schema Tests"""

    def test_camera_nested_response_excludes_timestamps(self):
        """Test: CameraNestedResponse does NOT have created_at/updated_at"""
        from app.schemas.integration import CameraNestedResponseIntegration as CameraNestedResponse
        from typing import get_type_hints

        hints = get_type_hints(CameraNestedResponse)
        assert 'created_at' not in hints
        assert 'updated_at' not in hints

    def test_preset_nested_response_excludes_timestamps(self):
        """Test: PresetNestedResponse does NOT have created_at/updated_at"""
        from app.schemas.integration import PresetNestedResponse
        from typing import get_type_hints

        hints = get_type_hints(PresetNestedResponse)
        assert 'created_at' not in hints
        assert 'updated_at' not in hints
