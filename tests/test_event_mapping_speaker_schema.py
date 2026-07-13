"""
Test: EventMappingSpeaker schema

PRD: PRD_EventMappingSpeaker.md v1.0

Phase 2: Schema Tests (TDD - Red Phase)
"""
import pytest
from pydantic import ValidationError


# ============================================================
# Phase 2.1: Create Schema Tests
# ============================================================

class TestEventMappingSpeakerCreateSchema:
    """EventMappingSpeakerCreate Schema Tests"""

    def test_event_mapping_speaker_create_requires_speaker_id(self):
        """Test: EventMappingSpeakerCreate requires speaker_id"""
        from app.schemas.integration import EventMappingSpeakerCreate

        # speaker_id is required
        schema = EventMappingSpeakerCreate(speaker_id=1)
        assert schema.speaker_id == 1

    def test_event_mapping_speaker_create_file_group_id_is_optional(self):
        """Test: EventMappingSpeakerCreate file_group_id is optional"""
        from app.schemas.integration import EventMappingSpeakerCreate

        # Without file_group_id
        schema1 = EventMappingSpeakerCreate(speaker_id=1)
        assert schema1.file_group_id is None

        # With file_group_id
        schema2 = EventMappingSpeakerCreate(speaker_id=1, file_group_id=5)
        assert schema2.file_group_id == 5

    def test_event_mapping_speaker_create_repeat_count_default_is_1(self):
        """Test: EventMappingSpeakerCreate repeat_count default is 1"""
        from app.schemas.integration import EventMappingSpeakerCreate

        schema = EventMappingSpeakerCreate(speaker_id=1)
        assert schema.repeat_count == 1

    def test_event_mapping_speaker_create_repeat_count_validation(self):
        """Test: EventMappingSpeakerCreate repeat_count validation (ge=1)"""
        from app.schemas.integration import EventMappingSpeakerCreate

        # Valid: repeat_count >= 1
        schema = EventMappingSpeakerCreate(speaker_id=1, repeat_count=5)
        assert schema.repeat_count == 5

        # Invalid: repeat_count < 1
        with pytest.raises(ValidationError):
            EventMappingSpeakerCreate(speaker_id=1, repeat_count=0)

        with pytest.raises(ValidationError):
            EventMappingSpeakerCreate(speaker_id=1, repeat_count=-1)

    def test_event_mapping_speaker_create_is_enable_default_is_true(self):
        """Test: EventMappingSpeakerCreate is_enable default is True"""
        from app.schemas.integration import EventMappingSpeakerCreate

        schema = EventMappingSpeakerCreate(speaker_id=1)
        assert schema.is_enable is True

    def test_event_mapping_speaker_create_priority_is_optional(self):
        """Test: EventMappingSpeakerCreate priority is optional"""
        from app.schemas.integration import EventMappingSpeakerCreate

        # Without priority
        schema1 = EventMappingSpeakerCreate(speaker_id=1)
        assert schema1.priority is None

        # With priority
        schema2 = EventMappingSpeakerCreate(speaker_id=1, priority=10)
        assert schema2.priority == 10


# ============================================================
# Phase 2.2: Update Schema Tests (PATCH)
# ============================================================

class TestEventMappingSpeakerUpdateSchema:
    """EventMappingSpeakerUpdate Schema Tests"""

    def test_event_mapping_speaker_update_all_fields_optional(self):
        """Test: EventMappingSpeakerUpdate all fields are optional"""
        from app.schemas.integration import EventMappingSpeakerUpdate

        # Empty update is valid
        schema = EventMappingSpeakerUpdate()
        assert schema.speaker_id is None
        assert schema.file_group_id is None
        assert schema.repeat_count is None
        assert schema.is_enable is None
        assert schema.priority is None

    def test_event_mapping_speaker_update_repeat_count_validation(self):
        """Test: EventMappingSpeakerUpdate repeat_count validation (ge=1)"""
        from app.schemas.integration import EventMappingSpeakerUpdate

        # Valid: repeat_count >= 1
        schema = EventMappingSpeakerUpdate(repeat_count=3)
        assert schema.repeat_count == 3

        # Invalid: repeat_count < 1
        with pytest.raises(ValidationError):
            EventMappingSpeakerUpdate(repeat_count=0)


# ============================================================
# Phase 2.3: Replace Schema Tests (PUT)
# ============================================================

class TestEventMappingSpeakerReplaceSchema:
    """EventMappingSpeakerReplace Schema Tests"""

    def test_event_mapping_speaker_replace_requires_speaker_id(self):
        """Test: EventMappingSpeakerReplace requires speaker_id"""
        from app.schemas.integration import EventMappingSpeakerReplace

        # speaker_id is required
        schema = EventMappingSpeakerReplace(
            speaker_id=1,
            repeat_count=1,
            is_enable=True
        )
        assert schema.speaker_id == 1

        # Missing speaker_id should fail
        with pytest.raises(ValidationError):
            EventMappingSpeakerReplace(repeat_count=1, is_enable=True)

    def test_event_mapping_speaker_replace_requires_repeat_count(self):
        """Test: EventMappingSpeakerReplace requires repeat_count"""
        from app.schemas.integration import EventMappingSpeakerReplace

        # Missing repeat_count should fail
        with pytest.raises(ValidationError):
            EventMappingSpeakerReplace(speaker_id=1, is_enable=True)

    def test_event_mapping_speaker_replace_requires_is_enable(self):
        """Test: EventMappingSpeakerReplace requires is_enable"""
        from app.schemas.integration import EventMappingSpeakerReplace

        # Missing is_enable should fail
        with pytest.raises(ValidationError):
            EventMappingSpeakerReplace(speaker_id=1, repeat_count=1)


# ============================================================
# Phase 2.4: Response Schema Tests
# ============================================================

class TestEventMappingSpeakerResponseSchema:
    """EventMappingSpeakerResponse Schema Tests"""

    def test_event_mapping_speaker_response_includes_all_fields(self):
        """Test: EventMappingSpeakerResponse includes all required fields"""
        from app.schemas.integration import EventMappingSpeakerResponse
        from datetime import datetime

        data = {
            "id": 1,
            "event_mapping_id": 10,
            "speaker": None,
            "file_group": None,
            "repeat_count": 1,
            "is_enable": True,
            "priority": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        schema = EventMappingSpeakerResponse(**data)
        assert schema.id == 1
        assert schema.event_mapping_id == 10
        assert schema.repeat_count == 1
        assert schema.is_enable is True

    def test_event_mapping_speaker_response_includes_nested_speaker(self):
        """Test: EventMappingSpeakerResponse includes nested speaker object"""
        from app.schemas.integration import EventMappingSpeakerResponse

        # Verify schema accepts nested speaker (None for now)
        assert hasattr(EventMappingSpeakerResponse.model_fields, 'speaker') or \
               'speaker' in EventMappingSpeakerResponse.model_fields

    def test_event_mapping_speaker_response_includes_nested_file_group(self):
        """Test: EventMappingSpeakerResponse includes nested file_group object"""
        from app.schemas.integration import EventMappingSpeakerResponse

        # Verify schema accepts nested file_group
        assert hasattr(EventMappingSpeakerResponse.model_fields, 'file_group') or \
               'file_group' in EventMappingSpeakerResponse.model_fields
