"""
Test: EventMappingSpeaker model

PRD: PRD_EventMappingSpeaker.md v1.0

Phase 1: Model Tests (TDD - Red Phase)
"""
import pytest
from sqlalchemy import inspect
from app.utils.enums import EnumMappingEventCategory


# ============================================================
# Phase 1.1: Model Basic Structure Tests
# ============================================================

class TestEventMappingSpeakerModelBasicStructure:
    """Basic Structure Tests"""

    def test_event_mapping_speaker_model_exists(self, test_db):
        """Test: EventMappingSpeaker model class exists"""
        from app.models.integration import EventMappingSpeaker
        assert EventMappingSpeaker is not None

    def test_event_mapping_speaker_table_name(self, test_db):
        """Test: EventMappingSpeaker has correct table name"""
        from app.models.integration import EventMappingSpeaker
        assert EventMappingSpeaker.__tablename__ == "event_mapping_speakers"

    def test_event_mapping_speaker_has_id_field(self, test_db):
        """Test: EventMappingSpeaker has id primary key field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}

        assert 'id' in columns
        pk_constraint = inspector.get_pk_constraint('event_mapping_speakers')
        pk_columns = pk_constraint['constrained_columns']
        assert 'id' in pk_columns

    def test_event_mapping_speaker_has_event_mapping_id_fk(self, test_db):
        """Test: EventMappingSpeaker has event_mapping_id FK"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}
        fks = inspector.get_foreign_keys('event_mapping_speakers')

        assert 'event_mapping_id' in columns
        em_fk = next((fk for fk in fks if 'event_mapping_id' in fk['constrained_columns']), None)
        assert em_fk is not None
        assert em_fk['referred_table'] == 'event_mappings'

    def test_event_mapping_speaker_has_speaker_id_fk(self, test_db):
        """Test: EventMappingSpeaker has speaker_id FK"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}
        fks = inspector.get_foreign_keys('event_mapping_speakers')

        assert 'speaker_id' in columns
        speaker_fk = next((fk for fk in fks if 'speaker_id' in fk['constrained_columns']), None)
        assert speaker_fk is not None
        assert speaker_fk['referred_table'] == 'speakers'

    def test_event_mapping_speaker_has_file_group_id_fk(self, test_db):
        """Test: EventMappingSpeaker has file_group_id FK"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}
        fks = inspector.get_foreign_keys('event_mapping_speakers')

        assert 'file_group_id' in columns
        fg_fk = next((fk for fk in fks if 'file_group_id' in fk['constrained_columns']), None)
        assert fg_fk is not None
        assert fg_fk['referred_table'] == 'file_groups'

    def test_event_mapping_speaker_has_repeat_count_field(self, test_db):
        """Test: EventMappingSpeaker has repeat_count field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}
        assert 'repeat_count' in columns

    def test_event_mapping_speaker_has_is_enable_field(self, test_db):
        """Test: EventMappingSpeaker has is_enable field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}
        assert 'is_enable' in columns

    def test_event_mapping_speaker_has_priority_field(self, test_db):
        """Test: EventMappingSpeaker has priority field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}
        assert 'priority' in columns

    def test_event_mapping_speaker_has_timestamps(self, test_db):
        """Test: EventMappingSpeaker has created_at and updated_at fields"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_speakers')}
        assert 'created_at' in columns
        assert 'updated_at' in columns


# ============================================================
# Phase 1.2: Model FK Behavior Tests
# ============================================================

class TestEventMappingSpeakerFKBehavior:
    """EventMappingSpeaker FK Behavior Tests"""

    def test_event_mapping_speaker_cascade_delete_on_event_mapping(self, test_db):
        """Test: EventMappingSpeaker CASCADE delete when EventMapping deleted"""
        from app.models.integration import EventMappingSpeaker, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()
        test_db.refresh(event_mapping)

        # Create EventMappingSpeaker
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        ems_id = ems.id

        # Delete EventMapping
        test_db.delete(event_mapping)
        test_db.commit()

        # EventMappingSpeaker should be deleted (CASCADE)
        deleted_ems = test_db.query(EventMappingSpeaker).filter(
            EventMappingSpeaker.id == ems_id
        ).first()
        assert deleted_ems is None

    def test_event_mapping_speaker_set_null_on_speaker_delete(self, test_db, test_speaker):
        """Test: EventMappingSpeaker.speaker_id SET NULL when Speaker deleted"""
        from app.models.integration import EventMappingSpeaker, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingSpeaker with speaker_id
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        ems_id = ems.id

        # Delete Speaker
        test_db.delete(test_speaker)
        test_db.commit()
        test_db.expire_all()

        # EventMappingSpeaker should still exist with speaker_id=NULL
        updated_ems = test_db.query(EventMappingSpeaker).filter(
            EventMappingSpeaker.id == ems_id
        ).first()
        assert updated_ems is not None
        assert updated_ems.speaker_id is None

    def test_event_mapping_speaker_set_null_on_file_group_delete(self, test_db, test_file_group):
        """Test: EventMappingSpeaker.file_group_id SET NULL when FileGroup deleted"""
        from app.models.integration import EventMappingSpeaker, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingSpeaker with file_group_id
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            file_group_id=test_file_group.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()
        ems_id = ems.id

        # Delete FileGroup
        test_db.delete(test_file_group)
        test_db.commit()
        test_db.expire_all()

        # EventMappingSpeaker should still exist with file_group_id=NULL
        updated_ems = test_db.query(EventMappingSpeaker).filter(
            EventMappingSpeaker.id == ems_id
        ).first()
        assert updated_ems is not None
        assert updated_ems.file_group_id is None


# ============================================================
# Phase 1.3: Model Default Values Tests
# ============================================================

class TestEventMappingSpeakerDefaultValues:
    """Default Values Tests"""

    def test_event_mapping_speaker_repeat_count_default_one(self, test_db):
        """Test: EventMappingSpeaker.repeat_count defaults to 1"""
        from app.models.integration import EventMappingSpeaker, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingSpeaker without repeat_count
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        assert ems.repeat_count == 1

    def test_event_mapping_speaker_is_enable_default_true(self, test_db):
        """Test: EventMappingSpeaker.is_enable defaults to True"""
        from app.models.integration import EventMappingSpeaker, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingSpeaker without is_enable
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        assert ems.is_enable is True

    def test_event_mapping_speaker_priority_default_null(self, test_db):
        """Test: EventMappingSpeaker.priority defaults to None (NULL)"""
        from app.models.integration import EventMappingSpeaker, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingSpeaker without priority
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id
        )
        test_db.add(ems)
        test_db.commit()
        test_db.refresh(ems)

        assert ems.priority is None


# ============================================================
# Phase 1.4: Relationships Tests
# ============================================================

class TestEventMappingSpeakerRelationships:
    """Relationships Tests"""

    def test_event_mapping_has_speakers_relationship(self, test_db):
        """Test: EventMapping has 'speakers' relationship"""
        from app.models.integration import EventMappingSpeaker, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()
        test_db.refresh(event_mapping)

        # Create multiple EventMappingSpeakers
        ems1 = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            repeat_count=1,
            is_enable=True
        )
        ems2 = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            repeat_count=2,
            is_enable=True
        )
        test_db.add_all([ems1, ems2])
        test_db.commit()

        # Check relationship
        test_db.refresh(event_mapping)
        assert hasattr(event_mapping, 'speakers')
        speakers_list = list(event_mapping.speakers)
        assert len(speakers_list) == 2

    def test_speaker_has_event_mapping_speakers_relationship(self, test_db, test_speaker):
        """Test: Speaker has 'event_mapping_speakers' relationship"""
        from app.models.integration import EventMappingSpeaker, EventMapping
        from app.models.device import Speaker

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingSpeaker linked to test_speaker
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            speaker_id=test_speaker.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()

        # Check relationship
        test_db.refresh(test_speaker)
        assert hasattr(test_speaker, 'event_mapping_speakers')

    def test_file_group_has_event_mapping_speakers_relationship(self, test_db, test_file_group):
        """Test: FileGroup has 'event_mapping_speakers' relationship"""
        from app.models.integration import EventMappingSpeaker, EventMapping
        from app.models.file_group import FileGroup

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingSpeaker linked to test_file_group
        ems = EventMappingSpeaker(
            event_mapping_id=event_mapping.id,
            file_group_id=test_file_group.id,
            repeat_count=1,
            is_enable=True
        )
        test_db.add(ems)
        test_db.commit()

        # Check relationship
        test_db.refresh(test_file_group)
        assert hasattr(test_file_group, 'event_mapping_speakers')
