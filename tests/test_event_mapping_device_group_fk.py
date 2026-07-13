"""
Test: EventMapping device_group_id FK Refactoring
PRD: PRD_Event_ActionEvent_Refactoring.md v2.1
PRD: PRD_CategoryEvent_Refactoring.md v1.1 - category_event → category_event_mapping

Phase 3: EventMapping device_group_id FK Refactoring
- EventMapping has device_group_id field (INTEGER FK to device_groups.id)
- EventMapping does NOT have group_event field
- EventMapping.device_group_id has SET NULL on delete
"""
import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker

from app.models.integration import EventMapping
from app.models.device_group import DeviceGroup
from app.database import Base
from app.utils.enums import EnumMappingEventCategory


# Test database fixture
@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestEventMappingModelStructure:
    """Phase 3.1: EventMapping Model Structure 테스트"""

    def test_event_mapping_has_device_group_id_field(self):
        """Test: EventMapping has device_group_id field (INTEGER FK to device_groups.id)"""
        mapper = inspect(EventMapping)
        column_names = [column.key for column in mapper.columns]

        assert 'device_group_id' in column_names, "EventMapping should have 'device_group_id' field"

    def test_event_mapping_device_group_id_is_fk_to_device_groups(self):
        """Test: EventMapping.device_group_id is FK to device_groups.id"""
        mapper = inspect(EventMapping)

        # Find device_group_id column
        device_group_id_col = None
        for column in mapper.columns:
            if column.key == 'device_group_id':
                device_group_id_col = column
                break

        assert device_group_id_col is not None, "EventMapping should have 'device_group_id' column"

        # Check FK exists
        fk_list = list(device_group_id_col.foreign_keys)
        assert len(fk_list) > 0, "device_group_id should have foreign key"

        # Check FK target
        fk = fk_list[0]
        assert 'device_groups.id' in str(fk.target_fullname), "device_group_id FK should reference device_groups.id"

    def test_event_mapping_does_not_have_group_event(self):
        """Test: EventMapping does NOT have group_event field"""
        mapper = inspect(EventMapping)
        column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in column_names, "EventMapping should NOT have 'group_event' field"

    def test_event_mapping_device_group_id_has_set_null_on_delete(self):
        """Test: EventMapping.device_group_id has SET NULL on delete"""
        mapper = inspect(EventMapping)

        # Find device_group_id column
        device_group_id_col = None
        for column in mapper.columns:
            if column.key == 'device_group_id':
                device_group_id_col = column
                break

        assert device_group_id_col is not None, "EventMapping should have 'device_group_id' column"

        # Check FK exists and ondelete
        fk_list = list(device_group_id_col.foreign_keys)
        assert len(fk_list) > 0, "device_group_id should have foreign key"

        fk = fk_list[0]
        assert fk.ondelete == 'SET NULL', "device_group_id FK should have SET NULL on delete"


class TestEventMappingRelationship:
    """Phase 3.2: EventMapping Relationship 테스트"""

    def test_event_mapping_has_device_group_relationship(self):
        """Test: EventMapping has device_group relationship"""
        mapper = inspect(EventMapping)
        relationships = [rel.key for rel in mapper.relationships]

        assert 'device_group' in relationships, "EventMapping should have 'device_group' relationship"

    def test_device_group_has_event_mappings_relationship(self):
        """Test: DeviceGroup.event_mappings relationship returns EventMapping list"""
        mapper = inspect(DeviceGroup)
        relationships = [rel.key for rel in mapper.relationships]

        assert 'event_mappings' in relationships, "DeviceGroup should have 'event_mappings' relationship"


class TestEventMappingCascadeBehavior:
    """Phase 3.3: EventMapping Cascade Behavior 테스트"""

    def test_event_mapping_device_group_id_becomes_null_when_device_group_deleted(self, test_db):
        """Test: When DeviceGroup is deleted, EventMapping.device_group_id becomes NULL"""
        # Create a DeviceGroup
        device_group = DeviceGroup(
            name="Test Group",
            description="Test group description"
        )
        test_db.add(device_group)
        test_db.commit()
        group_id = device_group.id

        # Create EventMapping referencing the DeviceGroup
        event_mapping = EventMapping(
            name_event="Test Mapping",
            device_group_id=group_id,
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY
        )
        test_db.add(event_mapping)
        test_db.commit()
        mapping_id = event_mapping.id

        # Verify EventMapping has the device_group_id
        assert event_mapping.device_group_id == group_id

        # Delete the DeviceGroup
        test_db.delete(device_group)
        test_db.commit()

        # Refresh EventMapping and verify device_group_id is NULL
        test_db.expire_all()
        event_mapping = test_db.get(EventMapping, mapping_id)
        assert event_mapping is not None, "EventMapping should still exist"
        assert event_mapping.device_group_id is None, "device_group_id should be NULL after DeviceGroup deletion"

    def test_event_mapping_is_not_deleted_when_device_group_deleted(self, test_db):
        """Test: EventMapping is NOT deleted when DeviceGroup is deleted"""
        # Create a DeviceGroup
        device_group = DeviceGroup(
            name="Test Group 2",
            description="Test group description 2"
        )
        test_db.add(device_group)
        test_db.commit()
        group_id = device_group.id

        # Create EventMapping referencing the DeviceGroup
        event_mapping = EventMapping(
            name_event="Test Mapping 2",
            device_group_id=group_id,
            category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY
        )
        test_db.add(event_mapping)
        test_db.commit()
        mapping_id = event_mapping.id

        # Delete the DeviceGroup
        test_db.delete(device_group)
        test_db.commit()

        # Verify EventMapping still exists
        test_db.expire_all()
        event_mapping = test_db.get(EventMapping, mapping_id)
        assert event_mapping is not None, "EventMapping should NOT be deleted when DeviceGroup is deleted"
        assert event_mapping.name_event == "Test Mapping 2", "EventMapping name_event should be preserved"
