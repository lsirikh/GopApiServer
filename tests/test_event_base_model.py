"""
Test: Event Base Model - Joined Table Inheritance
PRD: PRD_Event_ActionEvent_Refactoring.md v2.1

Phase 1.1: Event Base Model 구조
- Event base model has required fields
- Event base model does NOT have group_event field
- Event.category_event is polymorphic discriminator
- Event.device_id is FK to devices with SET NULL on delete

Phase 1.2: DetectionEvent Child Model
- DetectionEvent inherits from Event
- DetectionEvent.id is FK to events.id with CASCADE on delete
- DetectionEvent has specific fields (action_reported, result)
- DetectionEvent does NOT have group_event field
- DetectionEvent polymorphic_identity is "detection"
"""
import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.event import Event, DetectionEvent, MalfunctionEvent, ConnectionEvent


class TestEventBaseModelStructure:
    """Phase 1.1: Event Base Model 구조 테스트"""

    def test_event_base_model_has_required_fields(self):
        """Test: Event base model has required fields (id, category_event, type_event, device_id, device_description, sequence, created_at, updated_at)"""
        # Get mapper for Event model
        mapper = inspect(Event)
        column_names = [column.key for column in mapper.columns]

        required_fields = [
            'id',
            'category_event',
            'type_event',
            'device_id',
            'device_description',
            'sequence',
            'created_at',
            'updated_at'
        ]

        for field in required_fields:
            assert field in column_names, f"Event model should have '{field}' field"

    def test_event_base_model_does_not_have_group_event(self):
        """Test: Event base model does NOT have group_event field"""
        mapper = inspect(Event)
        column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in column_names, "Event model should NOT have 'group_event' field"

    def test_event_category_event_is_polymorphic_discriminator(self):
        """Test: Event.category_event is polymorphic discriminator"""
        mapper = inspect(Event)

        # Check polymorphic configuration
        assert mapper.polymorphic_on is not None, "Event should have polymorphic_on configured"
        assert mapper.polymorphic_on.key == 'category_event', "Polymorphic discriminator should be 'category_event'"

    def test_event_device_id_is_fk_to_devices(self):
        """Test: Event.device_id is FK to devices with SET NULL on delete"""
        mapper = inspect(Event)

        # Find device_id column
        device_id_col = None
        for column in mapper.columns:
            if column.key == 'device_id':
                device_id_col = column
                break

        assert device_id_col is not None, "Event should have 'device_id' column"

        # Check FK exists
        fk_list = list(device_id_col.foreign_keys)
        assert len(fk_list) > 0, "device_id should have foreign key"

        # Check FK target
        fk = fk_list[0]
        assert 'devices.id' in str(fk.target_fullname), "device_id FK should reference devices.id"

        # Check ondelete SET NULL
        assert fk.ondelete == 'SET NULL', "device_id FK should have SET NULL on delete"

    def test_event_tablename_is_events(self):
        """Test: Event tablename is 'events'"""
        assert Event.__tablename__ == 'events', "Event tablename should be 'events'"

    def test_event_polymorphic_identity_is_event(self):
        """Test: Event polymorphic_identity is 'event' (base)"""
        mapper = inspect(Event)
        assert mapper.polymorphic_identity == 'event', "Event polymorphic_identity should be 'event'"


class TestDetectionEventChildModel:
    """Phase 1.2: DetectionEvent Child Model 테스트"""

    def test_detection_event_inherits_from_event(self):
        """Test: DetectionEvent inherits from Event"""
        assert issubclass(DetectionEvent, Event), "DetectionEvent should inherit from Event"

    def test_detection_event_id_is_fk_to_events(self):
        """Test: DetectionEvent.id is FK to events.id with CASCADE on delete"""
        mapper = inspect(DetectionEvent)

        # Find id column in local columns (not inherited)
        id_col = mapper.local_table.c.get('id')
        assert id_col is not None, "DetectionEvent should have 'id' column"

        # Check FK exists
        fk_list = list(id_col.foreign_keys)
        assert len(fk_list) > 0, "DetectionEvent.id should have foreign key"

        # Check FK target
        fk = fk_list[0]
        assert 'events.id' in str(fk.target_fullname), "DetectionEvent.id FK should reference events.id"

        # Check ondelete CASCADE
        assert fk.ondelete == 'CASCADE', "DetectionEvent.id FK should have CASCADE on delete"

    def test_detection_event_has_specific_fields(self):
        """Test: DetectionEvent has specific fields (action_reported, result)"""
        mapper = inspect(DetectionEvent)
        local_columns = [col.name for col in mapper.local_table.c]

        required_specific_fields = ['action_reported', 'result']

        for field in required_specific_fields:
            assert field in local_columns, f"DetectionEvent should have '{field}' field"

    def test_detection_event_does_not_have_group_event(self):
        """Test: DetectionEvent does NOT have group_event field"""
        mapper = inspect(DetectionEvent)

        # Check all columns (inherited + local)
        all_column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in all_column_names, "DetectionEvent should NOT have 'group_event' field"

    def test_detection_event_polymorphic_identity_is_detection(self):
        """Test: DetectionEvent polymorphic_identity is 'detection'"""
        mapper = inspect(DetectionEvent)
        assert mapper.polymorphic_identity == 'detection', "DetectionEvent polymorphic_identity should be 'detection'"

    def test_detection_event_tablename_is_detection_events(self):
        """Test: DetectionEvent tablename is 'detection_events'"""
        assert DetectionEvent.__tablename__ == 'detection_events', "DetectionEvent tablename should be 'detection_events'"


class TestMalfunctionEventChildModel:
    """Phase 1.3: MalfunctionEvent Child Model 테스트"""

    def test_malfunction_event_inherits_from_event(self):
        """Test: MalfunctionEvent inherits from Event"""
        assert issubclass(MalfunctionEvent, Event), "MalfunctionEvent should inherit from Event"

    def test_malfunction_event_id_is_fk_to_events(self):
        """Test: MalfunctionEvent.id is FK to events.id with CASCADE on delete"""
        mapper = inspect(MalfunctionEvent)

        # Find id column in local columns
        id_col = mapper.local_table.c.get('id')
        assert id_col is not None, "MalfunctionEvent should have 'id' column"

        # Check FK exists
        fk_list = list(id_col.foreign_keys)
        assert len(fk_list) > 0, "MalfunctionEvent.id should have foreign key"

        # Check FK target
        fk = fk_list[0]
        assert 'events.id' in str(fk.target_fullname), "MalfunctionEvent.id FK should reference events.id"

        # Check ondelete CASCADE
        assert fk.ondelete == 'CASCADE', "MalfunctionEvent.id FK should have CASCADE on delete"

    def test_malfunction_event_has_specific_fields(self):
        """Test: MalfunctionEvent has specific fields (action_reported, reason, first_start, first_end, second_start, second_end)"""
        mapper = inspect(MalfunctionEvent)
        local_columns = [col.name for col in mapper.local_table.c]

        required_specific_fields = ['action_reported', 'reason', 'first_start', 'first_end', 'second_start', 'second_end']

        for field in required_specific_fields:
            assert field in local_columns, f"MalfunctionEvent should have '{field}' field"

    def test_malfunction_event_does_not_have_group_event(self):
        """Test: MalfunctionEvent does NOT have group_event field"""
        mapper = inspect(MalfunctionEvent)
        all_column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in all_column_names, "MalfunctionEvent should NOT have 'group_event' field"

    def test_malfunction_event_polymorphic_identity_is_malfunction(self):
        """Test: MalfunctionEvent polymorphic_identity is 'malfunction'"""
        mapper = inspect(MalfunctionEvent)
        assert mapper.polymorphic_identity == 'malfunction', "MalfunctionEvent polymorphic_identity should be 'malfunction'"


class TestConnectionEventChildModel:
    """Phase 1.4: ConnectionEvent Child Model 테스트"""

    def test_connection_event_inherits_from_event(self):
        """Test: ConnectionEvent inherits from Event"""
        assert issubclass(ConnectionEvent, Event), "ConnectionEvent should inherit from Event"

    def test_connection_event_id_is_fk_to_events(self):
        """Test: ConnectionEvent.id is FK to events.id with CASCADE on delete"""
        mapper = inspect(ConnectionEvent)

        # Find id column in local columns
        id_col = mapper.local_table.c.get('id')
        assert id_col is not None, "ConnectionEvent should have 'id' column"

        # Check FK exists
        fk_list = list(id_col.foreign_keys)
        assert len(fk_list) > 0, "ConnectionEvent.id should have foreign key"

        # Check FK target
        fk = fk_list[0]
        assert 'events.id' in str(fk.target_fullname), "ConnectionEvent.id FK should reference events.id"

        # Check ondelete CASCADE
        assert fk.ondelete == 'CASCADE', "ConnectionEvent.id FK should have CASCADE on delete"

    def test_connection_event_does_not_have_additional_specific_fields(self):
        """Test: ConnectionEvent does NOT have additional specific fields (only id in local table)"""
        mapper = inspect(ConnectionEvent)
        local_columns = [col.name for col in mapper.local_table.c]

        # ConnectionEvent should only have 'id' in local table (no additional fields)
        assert 'id' in local_columns, "ConnectionEvent should have 'id' field"
        # Other fields should come from Event base class
        assert len(local_columns) == 1, "ConnectionEvent should only have 'id' in local table (no additional fields)"

    def test_connection_event_does_not_have_group_event(self):
        """Test: ConnectionEvent does NOT have group_event field"""
        mapper = inspect(ConnectionEvent)
        all_column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in all_column_names, "ConnectionEvent should NOT have 'group_event' field"

    def test_connection_event_polymorphic_identity_is_connection(self):
        """Test: ConnectionEvent polymorphic_identity is 'connection'"""
        mapper = inspect(ConnectionEvent)
        assert mapper.polymorphic_identity == 'connection', "ConnectionEvent polymorphic_identity should be 'connection'"
