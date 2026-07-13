"""
Test: EventMappingLamp model

PRD: PRD_Lamp_Device.md v1.1 - Section 3.2

Phase 3.1: Model Tests (TDD - Red Phase)
"""
import pytest
from sqlalchemy import inspect
from app.utils.enums import EnumMappingEventCategory, EnumLampColor, EnumBuzzerSound, EnumLightMode


# ============================================================
# Phase 3.1.1: Model Basic Structure Tests
# ============================================================

class TestEventMappingLampModelBasicStructure:
    """Basic Structure Tests"""

    def test_event_mapping_lamp_model_exists(self, test_db):
        """Test: EventMappingLamp model class exists"""
        from app.models.integration import EventMappingLamp
        assert EventMappingLamp is not None

    def test_event_mapping_lamp_table_name(self, test_db):
        """Test: EventMappingLamp has correct table name"""
        from app.models.integration import EventMappingLamp
        assert EventMappingLamp.__tablename__ == "event_mapping_lamps"

    def test_event_mapping_lamp_has_id_field(self, test_db):
        """Test: EventMappingLamp has id primary key field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}

        assert 'id' in columns
        pk_constraint = inspector.get_pk_constraint('event_mapping_lamps')
        pk_columns = pk_constraint['constrained_columns']
        assert 'id' in pk_columns

    def test_event_mapping_lamp_has_event_mapping_id_fk(self, test_db):
        """Test: EventMappingLamp has event_mapping_id FK"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        fks = inspector.get_foreign_keys('event_mapping_lamps')

        assert 'event_mapping_id' in columns
        em_fk = next((fk for fk in fks if 'event_mapping_id' in fk['constrained_columns']), None)
        assert em_fk is not None
        assert em_fk['referred_table'] == 'event_mappings'

    def test_event_mapping_lamp_has_lamp_id_fk(self, test_db):
        """Test: EventMappingLamp has lamp_id FK"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        fks = inspector.get_foreign_keys('event_mapping_lamps')

        assert 'lamp_id' in columns
        lamp_fk = next((fk for fk in fks if 'lamp_id' in fk['constrained_columns']), None)
        assert lamp_fk is not None
        assert lamp_fk['referred_table'] == 'lamps'

    def test_event_mapping_lamp_has_color_field(self, test_db):
        """Test: EventMappingLamp has color field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        assert 'color' in columns

    def test_event_mapping_lamp_has_buzzer_time_field(self, test_db):
        """Test: EventMappingLamp has buzzer_time field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        assert 'buzzer_time' in columns

    def test_event_mapping_lamp_has_buzzer_sound_field(self, test_db):
        """Test: EventMappingLamp has buzzer_sound field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        assert 'buzzer_sound' in columns

    def test_event_mapping_lamp_has_light_mode_field(self, test_db):
        """Test: EventMappingLamp has light_mode field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        assert 'light_mode' in columns

    def test_event_mapping_lamp_has_is_enable_field(self, test_db):
        """Test: EventMappingLamp has is_enable field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        assert 'is_enable' in columns

    def test_event_mapping_lamp_has_priority_field(self, test_db):
        """Test: EventMappingLamp has priority field"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        assert 'priority' in columns

    def test_event_mapping_lamp_has_timestamps(self, test_db):
        """Test: EventMappingLamp has created_at and updated_at fields"""
        inspector = inspect(test_db.bind)
        columns = {col['name']: col for col in inspector.get_columns('event_mapping_lamps')}
        assert 'created_at' in columns
        assert 'updated_at' in columns


# ============================================================
# Phase 3.1.2: Model FK Behavior Tests
# ============================================================

class TestEventMappingLampFKBehavior:
    """EventMappingLamp FK Behavior Tests"""

    def test_event_mapping_lamp_cascade_delete_on_event_mapping(self, test_db):
        """Test: EventMappingLamp CASCADE delete when EventMapping deleted"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()
        test_db.refresh(event_mapping)

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            color=EnumLampColor.RED,
            buzzer_time=5,
            buzzer_sound=EnumBuzzerSound.PI_PI_PI,
            light_mode=EnumLightMode.STEADY,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        eml_id = eml.id

        # Delete EventMapping
        test_db.delete(event_mapping)
        test_db.commit()

        # EventMappingLamp should be deleted (CASCADE)
        deleted_eml = test_db.query(EventMappingLamp).filter(
            EventMappingLamp.id == eml_id
        ).first()
        assert deleted_eml is None

    def test_event_mapping_lamp_set_null_on_lamp_delete(self, test_db, test_lamp):
        """Test: EventMappingLamp.lamp_id SET NULL when Lamp deleted"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp with lamp_id
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            lamp_id=test_lamp.id,
            color=EnumLampColor.RED,
            buzzer_time=5,
            buzzer_sound=EnumBuzzerSound.PI_PI_PI,
            light_mode=EnumLightMode.STEADY,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        eml_id = eml.id

        # Delete Lamp
        test_db.delete(test_lamp)
        test_db.commit()
        test_db.expire_all()

        # EventMappingLamp should still exist with lamp_id=NULL
        updated_eml = test_db.query(EventMappingLamp).filter(
            EventMappingLamp.id == eml_id
        ).first()
        assert updated_eml is not None
        assert updated_eml.lamp_id is None


# ============================================================
# Phase 3.1.3: Model Unique Constraint Tests
# ============================================================

class TestEventMappingLampUniqueConstraint:
    """Unique Constraint Tests"""

    def test_event_mapping_lamp_unique_constraint_exists(self, test_db):
        """Test: EventMappingLamp has unique constraint on (event_mapping_id, lamp_id)"""
        inspector = inspect(test_db.bind)
        unique_constraints = inspector.get_unique_constraints('event_mapping_lamps')

        # Find the constraint
        uq_constraint = next(
            (uc for uc in unique_constraints if 'event_mapping_id' in uc['column_names'] and 'lamp_id' in uc['column_names']),
            None
        )
        assert uq_constraint is not None

    def test_event_mapping_lamp_allows_null_lamp_id_duplicates(self, test_db):
        """Test: Multiple EventMappingLamp with NULL lamp_id allowed (unique constraint excludes NULL)"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create two EventMappingLamp with NULL lamp_id - should be allowed
        eml1 = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            lamp_id=None,
            color=EnumLampColor.RED,
            is_enable=True,
            priority=1
        )
        eml2 = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            lamp_id=None,
            color=EnumLampColor.GREEN,
            is_enable=True,
            priority=2
        )
        test_db.add_all([eml1, eml2])
        test_db.commit()

        # Both should be created
        assert eml1.id is not None
        assert eml2.id is not None


# ============================================================
# Phase 3.1.4: Model Default Values Tests
# ============================================================

class TestEventMappingLampDefaultValues:
    """Default Values Tests"""

    def test_event_mapping_lamp_color_default_red(self, test_db):
        """Test: EventMappingLamp.color defaults to RED"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp without color
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        assert eml.color == EnumLampColor.RED

    def test_event_mapping_lamp_buzzer_time_default_5(self, test_db):
        """Test: EventMappingLamp.buzzer_time defaults to 5"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp without buzzer_time
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        assert eml.buzzer_time == 5

    def test_event_mapping_lamp_buzzer_sound_default_pi_pi_pi(self, test_db):
        """Test: EventMappingLamp.buzzer_sound defaults to PI_PI_PI"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp without buzzer_sound
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        assert eml.buzzer_sound == EnumBuzzerSound.PI_PI_PI

    def test_event_mapping_lamp_light_mode_default_steady(self, test_db):
        """Test: EventMappingLamp.light_mode defaults to STEADY"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp without light_mode
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        assert eml.light_mode == EnumLightMode.STEADY

    def test_event_mapping_lamp_is_enable_default_true(self, test_db):
        """Test: EventMappingLamp.is_enable defaults to True"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp without is_enable
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        assert eml.is_enable is True

    def test_event_mapping_lamp_priority_default_1(self, test_db):
        """Test: EventMappingLamp.priority defaults to 1"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp without priority
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        assert eml.priority == 1


# ============================================================
# Phase 3.1.5: Relationships Tests
# ============================================================

class TestEventMappingLampRelationships:
    """Relationships Tests"""

    def test_event_mapping_has_lamps_relationship(self, test_db):
        """Test: EventMapping has 'lamps' relationship"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()
        test_db.refresh(event_mapping)

        # Create multiple EventMappingLamps
        eml1 = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            color=EnumLampColor.RED,
            is_enable=True,
            priority=1
        )
        eml2 = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            color=EnumLampColor.GREEN,
            is_enable=True,
            priority=2
        )
        test_db.add_all([eml1, eml2])
        test_db.commit()

        # Check relationship
        test_db.refresh(event_mapping)
        assert hasattr(event_mapping, 'lamps')
        lamps_list = list(event_mapping.lamps)
        assert len(lamps_list) == 2

    def test_lamp_has_event_mapping_lamps_relationship(self, test_db, test_lamp):
        """Test: Lamp has 'event_mapping_lamps' relationship"""
        from app.models.integration import EventMappingLamp, EventMapping
        from app.models.device import Lamp

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp linked to test_lamp
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            lamp_id=test_lamp.id,
            color=EnumLampColor.RED,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()

        # Check relationship
        test_db.refresh(test_lamp)
        assert hasattr(test_lamp, 'event_mapping_lamps')

    def test_event_mapping_lamp_has_event_mapping_relationship(self, test_db):
        """Test: EventMappingLamp has 'event_mapping' relationship"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            color=EnumLampColor.RED,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        # Check relationship
        assert hasattr(eml, 'event_mapping')
        assert eml.event_mapping.id == event_mapping.id
        assert eml.event_mapping.name_event == "Test Mapping"

    def test_event_mapping_lamp_has_lamp_relationship(self, test_db, test_lamp):
        """Test: EventMappingLamp has 'lamp' relationship"""
        from app.models.integration import EventMappingLamp, EventMapping

        # Create EventMapping
        event_mapping = EventMapping(
            name_event="Test Mapping",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(event_mapping)
        test_db.commit()

        # Create EventMappingLamp with lamp_id
        eml = EventMappingLamp(
            event_mapping_id=event_mapping.id,
            lamp_id=test_lamp.id,
            color=EnumLampColor.RED,
            is_enable=True,
            priority=1
        )
        test_db.add(eml)
        test_db.commit()
        test_db.refresh(eml)

        # Check relationship
        assert hasattr(eml, 'lamp')
        assert eml.lamp.id == test_lamp.id
        assert eml.lamp.name_device == test_lamp.name_device
