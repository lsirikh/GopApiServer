"""
Test: ActionEvent from_event_id FK Refactoring
PRD: PRD_Event_ActionEvent_Refactoring.md v2.1

Phase 2: ActionEvent from_event_id FK Refactoring
- ActionEvent has from_event_id field (INTEGER FK to events.id)
- ActionEvent does NOT have from_event field
- ActionEvent does NOT have from_type_event field
- ActionEvent.from_event_id has SET NULL on delete
"""
import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker

from app.models.event import ActionEvent, Event, DetectionEvent, MalfunctionEvent, ConnectionEvent
from app.database import Base
from app.utils.enums import EnumDetectionType, EnumFaultType


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


class TestActionEventModelStructure:
    """Phase 2.1: ActionEvent Model Structure 테스트"""

    def test_action_event_has_from_event_id_field(self):
        """Test: ActionEvent has from_event_id field (INTEGER FK to events.id)"""
        mapper = inspect(ActionEvent)
        column_names = [column.key for column in mapper.columns]

        assert 'from_event_id' in column_names, "ActionEvent should have 'from_event_id' field"

    def test_action_event_from_event_id_is_fk_to_events(self):
        """Test: ActionEvent.from_event_id is FK to events.id"""
        mapper = inspect(ActionEvent)

        # Find from_event_id column
        from_event_id_col = None
        for column in mapper.columns:
            if column.key == 'from_event_id':
                from_event_id_col = column
                break

        assert from_event_id_col is not None, "ActionEvent should have 'from_event_id' column"

        # Check FK exists
        fk_list = list(from_event_id_col.foreign_keys)
        assert len(fk_list) > 0, "from_event_id should have foreign key"

        # Check FK target
        fk = fk_list[0]
        assert 'events.id' in str(fk.target_fullname), "from_event_id FK should reference events.id"

    def test_action_event_does_not_have_from_event(self):
        """Test: ActionEvent does NOT have from_event field"""
        mapper = inspect(ActionEvent)
        column_names = [column.key for column in mapper.columns]

        assert 'from_event' not in column_names, "ActionEvent should NOT have 'from_event' field"

    def test_action_event_does_not_have_from_type_event(self):
        """Test: ActionEvent does NOT have from_type_event field"""
        mapper = inspect(ActionEvent)
        column_names = [column.key for column in mapper.columns]

        assert 'from_type_event' not in column_names, "ActionEvent should NOT have 'from_type_event' field"

    def test_action_event_from_event_id_has_set_null_on_delete(self):
        """Test: ActionEvent.from_event_id has SET NULL on delete"""
        mapper = inspect(ActionEvent)

        # Find from_event_id column
        from_event_id_col = None
        for column in mapper.columns:
            if column.key == 'from_event_id':
                from_event_id_col = column
                break

        assert from_event_id_col is not None, "ActionEvent should have 'from_event_id' column"

        # Check FK exists and ondelete
        fk_list = list(from_event_id_col.foreign_keys)
        assert len(fk_list) > 0, "from_event_id should have foreign key"

        fk = fk_list[0]
        assert fk.ondelete == 'SET NULL', "from_event_id FK should have SET NULL on delete"


class TestActionEventRelationship:
    """Phase 2.2: ActionEvent Relationship 테스트"""

    def test_action_event_has_source_event_relationship(self):
        """Test: ActionEvent has source_event relationship"""
        mapper = inspect(ActionEvent)
        relationships = [rel.key for rel in mapper.relationships]

        assert 'source_event' in relationships, "ActionEvent should have 'source_event' relationship"

    def test_event_has_actions_relationship(self):
        """Test: Event has actions relationship"""
        mapper = inspect(Event)
        relationships = [rel.key for rel in mapper.relationships]

        assert 'actions' in relationships, "Event should have 'actions' relationship"

    def test_action_event_source_event_returns_correct_polymorphic_type(self, test_db):
        """Test: ActionEvent.source_event returns correct polymorphic type (DetectionEvent/MalfunctionEvent/ConnectionEvent)"""
        # Create a DetectionEvent
        detection_event = DetectionEvent(
            category_event="detection",
            type_event="Intrusion",
            device_id=None,
            sequence=1,
            action_reported="False",
            result=EnumDetectionType.PIR_SENSOR
        )
        test_db.add(detection_event)
        test_db.commit()
        test_db.refresh(detection_event)

        # Create ActionEvent referencing the DetectionEvent
        action_event = ActionEvent(
            from_event_id=detection_event.id,
            content="Test action",
            user="test_user"
        )
        test_db.add(action_event)
        test_db.commit()
        test_db.refresh(action_event)

        # Verify source_event returns DetectionEvent instance
        assert action_event.source_event is not None, "source_event should not be None"
        assert isinstance(action_event.source_event, DetectionEvent), "source_event should be DetectionEvent instance"
        assert action_event.source_event.id == detection_event.id, "source_event id should match"


class TestActionEventCascadeBehavior:
    """Phase 2.3: ActionEvent Cascade Behavior 테스트"""

    def test_action_event_from_event_id_becomes_null_when_event_deleted(self, test_db):
        """Test: When Event is deleted, ActionEvent.from_event_id becomes NULL"""
        # Create a DetectionEvent
        detection_event = DetectionEvent(
            category_event="detection",
            type_event="Intrusion",
            device_id=None,
            sequence=1,
            action_reported="False",
            result=EnumDetectionType.PIR_SENSOR
        )
        test_db.add(detection_event)
        test_db.commit()
        event_id = detection_event.id

        # Create ActionEvent referencing the DetectionEvent
        action_event = ActionEvent(
            from_event_id=event_id,
            content="Test action",
            user="test_user"
        )
        test_db.add(action_event)
        test_db.commit()
        action_id = action_event.id

        # Verify ActionEvent has the from_event_id
        assert action_event.from_event_id == event_id

        # Delete the Event
        test_db.delete(detection_event)
        test_db.commit()

        # Refresh ActionEvent and verify from_event_id is NULL
        test_db.expire_all()
        action_event = test_db.query(ActionEvent).get(action_id)
        assert action_event is not None, "ActionEvent should still exist"
        assert action_event.from_event_id is None, "from_event_id should be NULL after Event deletion"

    def test_action_event_is_not_deleted_when_source_event_deleted(self, test_db):
        """Test: ActionEvent is NOT deleted when source Event is deleted"""
        # Create a MalfunctionEvent
        malfunction_event = MalfunctionEvent(
            category_event="malfunction",
            type_event="Fault",
            device_id=None,
            sequence=1,
            action_reported="False",
            reason=EnumFaultType.FAULT_CONTROLLER,
            detail={
                "first_start": 0,
                "first_end": 100,
                "second_start": 0,
                "second_end": 100,
            },
        )
        test_db.add(malfunction_event)
        test_db.commit()
        event_id = malfunction_event.id

        # Create ActionEvent referencing the MalfunctionEvent
        action_event = ActionEvent(
            from_event_id=event_id,
            content="Malfunction action",
            user="test_user"
        )
        test_db.add(action_event)
        test_db.commit()
        action_id = action_event.id

        # Delete the Event
        test_db.delete(malfunction_event)
        test_db.commit()

        # Verify ActionEvent still exists
        test_db.expire_all()
        action_event = test_db.query(ActionEvent).get(action_id)
        assert action_event is not None, "ActionEvent should NOT be deleted when source Event is deleted"
        assert action_event.content == "Malfunction action", "ActionEvent content should be preserved"
