"""
Tests for Speaker Model
PRD: PRD_Speaker_Device.md - Phase 2: Speaker Model
TDD: Red -> Green -> Refactor
"""
import pytest
from sqlalchemy import inspect


class TestSpeakerModelBasicStructure:
    """Test Speaker Model Basic Structure"""

    def test_speaker_model_exists(self):
        """Speaker model should exist"""
        from app.models.device import Speaker
        assert Speaker is not None

    def test_speaker_table_name_is_speakers(self):
        """Speaker table name should be 'speakers'"""
        from app.models.device import Speaker
        assert Speaker.__tablename__ == "speakers"

    def test_speaker_inherits_from_device(self):
        """Speaker should inherit from Device"""
        from app.models.device import Speaker
        from app.models.device import Device
        assert issubclass(Speaker, Device)

    def test_speaker_has_id_field_as_fk_to_devices(self):
        """Speaker should have id field as FK to devices"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        columns = {c.key: c for c in mapper.columns}
        assert 'id' in columns
        # Check FK reference
        id_col = columns['id']
        fks = list(id_col.foreign_keys)
        assert len(fks) > 0
        fk_target = str(fks[0].target_fullname)
        assert 'devices.id' in fk_target

    def test_speaker_has_speaker_type_field(self):
        """Speaker should have speaker_type field"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        columns = {c.key: c for c in mapper.columns}
        assert 'speaker_type' in columns

    def test_speaker_has_server_id_fk(self):
        """Speaker should have server_id field as FK to servers"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        columns = {c.key: c for c in mapper.columns}
        assert 'server_id' in columns
        # Check FK reference
        server_id_col = columns['server_id']
        fks = list(server_id_col.foreign_keys)
        assert len(fks) > 0
        fk_target = str(fks[0].target_fullname)
        assert 'servers.id' in fk_target

    def test_speaker_has_description_field(self):
        """Speaker should have description field"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        columns = {c.key: c for c in mapper.columns}
        assert 'description' in columns


class TestSpeakerModelPolymorphicIdentity:
    """Test Speaker Model Polymorphic Identity"""

    def test_speaker_polymorphic_identity_is_speaker(self):
        """Speaker polymorphic identity should be SPEAKER enum"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceCategory
        assert Speaker.__mapper_args__['polymorphic_identity'] == EnumDeviceCategory.SPEAKER

    def test_speaker_category_device_is_speaker(self, test_db):
        """Created Speaker should have category_device = 'speaker'"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(
            number_device=2401,
            group_device=0,
            name_device="VCS_2401",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        assert speaker.category_device.value == "speaker"


class TestSpeakerModelDefaultValues:
    """Test Speaker Model Default Values"""

    def test_speaker_type_default_is_normal(self):
        """Speaker.speaker_type default should be NORMAL"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        columns = {c.key: c for c in mapper.columns}
        speaker_type_col = columns['speaker_type']
        # Check default value
        from app.utils.enums import EnumSpeakerType
        assert speaker_type_col.default.arg == EnumSpeakerType.NORMAL

    def test_speaker_server_id_nullable(self):
        """Speaker.server_id should be nullable"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        columns = {c.key: c for c in mapper.columns}
        server_id_col = columns['server_id']
        assert server_id_col.nullable is True

    def test_speaker_description_nullable(self):
        """Speaker.description should be nullable"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        columns = {c.key: c for c in mapper.columns}
        description_col = columns['description']
        assert description_col.nullable is True


class TestSpeakerModelFKBehavior:
    """Test Speaker Model FK Behavior"""

    def test_speaker_server_id_set_null_on_server_delete(self, test_db):
        """When Server is deleted, Speaker.server_id should be set to NULL"""
        from app.models.device import Speaker
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumServerType, EnumServerStatus

        # Create ServerCategory first
        category = ServerCategory(
            name="SPEAKER_API",
            type_server=EnumServerType.SPEAKER_API
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        # Create Server
        server = Server(
            category_id=category.id,
            name="Test Speaker Server",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Create Speaker with server_id
        speaker = Speaker(
            number_device=2401,
            group_device=0,
            name_device="VCS_2401",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL,
            server_id=server.id
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        speaker_id = speaker.id
        assert speaker.server_id == server.id

        # Delete Server
        test_db.delete(server)
        test_db.commit()

        # Refresh Speaker and check server_id is NULL
        test_db.expire_all()
        updated_speaker = test_db.query(Speaker).filter(Speaker.id == speaker_id).first()
        assert updated_speaker is not None
        assert updated_speaker.server_id is None


class TestSpeakerModelRelationship:
    """Test Speaker Model Relationship"""

    def test_speaker_has_server_relationship(self):
        """Speaker should have 'server' relationship"""
        from app.models.device import Speaker
        mapper = inspect(Speaker)
        relationships = {r.key: r for r in mapper.relationships}
        assert 'server' in relationships
