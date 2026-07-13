"""
Tests for Speaker Schema
PRD: PRD_Speaker_Device.md - Phase 4: Speaker Schema
TDD: Red -> Green -> Refactor
"""
import pytest
from pydantic import ValidationError


class TestSpeakerCreateSchema:
    """Test Speaker Create Schema"""

    def test_speaker_create_schema_exists(self):
        """SpeakerCreate schema should exist"""
        from app.schemas.device import SpeakerCreate
        assert SpeakerCreate is not None

    def test_speaker_create_has_number_device_required(self):
        """SpeakerCreate should require number_device"""
        from app.schemas.device import SpeakerCreate

        with pytest.raises(ValidationError):
            SpeakerCreate(name_device="Test Speaker")  # Missing number_device

    def test_speaker_create_has_name_device_required(self):
        """SpeakerCreate should require name_device"""
        from app.schemas.device import SpeakerCreate

        with pytest.raises(ValidationError):
            SpeakerCreate(number_device=2401)  # Missing name_device

    def test_speaker_create_has_type_device_default_ipspeaker(self):
        """SpeakerCreate type_device should default to IpSpeaker"""
        from app.schemas.device import SpeakerCreate
        from app.utils.enums import EnumDeviceType

        schema = SpeakerCreate(number_device=2401, name_device="VCS_2401")
        assert schema.type_device == EnumDeviceType.IpSpeaker

    def test_speaker_create_has_speaker_type_default_normal(self):
        """SpeakerCreate speaker_type should default to NORMAL"""
        from app.schemas.device import SpeakerCreate
        from app.utils.enums import EnumSpeakerType

        schema = SpeakerCreate(number_device=2401, name_device="VCS_2401")
        assert schema.speaker_type == EnumSpeakerType.NORMAL

    def test_speaker_create_has_server_id_optional(self):
        """SpeakerCreate server_id should be optional"""
        from app.schemas.device import SpeakerCreate

        schema = SpeakerCreate(number_device=2401, name_device="VCS_2401")
        assert schema.server_id is None

    def test_speaker_create_has_description_optional(self):
        """SpeakerCreate description should be optional"""
        from app.schemas.device import SpeakerCreate

        schema = SpeakerCreate(number_device=2401, name_device="VCS_2401")
        assert schema.description is None


class TestSpeakerUpdateSchema:
    """Test Speaker Update Schema"""

    def test_speaker_update_schema_exists(self):
        """SpeakerUpdate schema should exist"""
        from app.schemas.device import SpeakerUpdate
        assert SpeakerUpdate is not None

    def test_speaker_update_all_fields_optional(self):
        """SpeakerUpdate should have all fields optional"""
        from app.schemas.device import SpeakerUpdate

        # Should not raise error with no fields
        schema = SpeakerUpdate()
        assert schema.number_device is None
        assert schema.name_device is None
        assert schema.speaker_type is None
        assert schema.server_id is None
        assert schema.description is None


class TestSpeakerResponseSchema:
    """Test Speaker Response Schema"""

    def test_speaker_response_schema_exists(self):
        """SpeakerResponse schema should exist"""
        from app.schemas.device import SpeakerResponse
        assert SpeakerResponse is not None

    def test_speaker_response_has_device_base_fields(self):
        """SpeakerResponse should have Device base fields"""
        from app.schemas.device import SpeakerResponse
        from datetime import datetime

        # Check field names in model_fields
        fields = SpeakerResponse.model_fields.keys()
        assert 'id' in fields
        assert 'number_device' in fields
        assert 'group_device' in fields
        assert 'name_device' in fields
        assert 'type_device' in fields
        assert 'status' in fields

    def test_speaker_response_category_device_policy(self):
        """
        Test: SpeakerResponse should NOT include category_device field

        SPEC-6.1: category_device는 polymorphic discriminator로
        내부 DB 구조용이며 API 응답에 노출할 필요 없음
        """
        from app.schemas.device import SpeakerResponse

        fields = SpeakerResponse.model_fields.keys()
        assert 'category_device' not in fields, (
            "category_device는 polymorphic discriminator이므로 "
            "API 응답에 노출하지 않음 (SPEC-6.1)"
        )

    def test_speaker_response_has_speaker_type(self):
        """SpeakerResponse should have speaker_type field"""
        from app.schemas.device import SpeakerResponse

        fields = SpeakerResponse.model_fields.keys()
        assert 'speaker_type' in fields

    def test_speaker_response_has_server_nested(self):
        """SpeakerResponse should have server nested object"""
        from app.schemas.device import SpeakerResponse

        fields = SpeakerResponse.model_fields.keys()
        assert 'server' in fields

    def test_speaker_response_excludes_server_id(self):
        """SpeakerResponse should NOT have server_id field"""
        from app.schemas.device import SpeakerResponse

        fields = SpeakerResponse.model_fields.keys()
        assert 'server_id' not in fields

    def test_speaker_response_has_timestamps(self):
        """SpeakerResponse should have created_at and updated_at"""
        from app.schemas.device import SpeakerResponse

        fields = SpeakerResponse.model_fields.keys()
        assert 'created_at' in fields
        assert 'updated_at' in fields


class TestSpeakerNestedResponseSchema:
    """Test Speaker Nested Response Schema"""

    def test_speaker_nested_response_excludes_timestamps(self):
        """SpeakerNestedResponse should NOT have timestamps"""
        from app.schemas.device import SpeakerNestedResponse

        fields = SpeakerNestedResponse.model_fields.keys()
        assert 'created_at' not in fields
        assert 'updated_at' not in fields


class TestServerNestedResponseSchema:
    """Test Server Nested Response Schema"""

    def test_server_nested_response_excludes_timestamps(self):
        """ServerNestedResponse should NOT have timestamps"""
        from app.schemas.server import ServerNestedResponse

        fields = ServerNestedResponse.model_fields.keys()
        assert 'created_at' not in fields
        assert 'updated_at' not in fields
