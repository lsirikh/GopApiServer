"""
Test: group_event Field Removal
PRD: PRD_Event_ActionEvent_Refactoring.md v2.1

Phase 4: group_event Field Removal
- Event models do NOT have group_event column
- Event schemas do NOT accept group_event field
- EventMapping model does NOT have group_event column
"""
import pytest
from sqlalchemy import inspect

from app.models.event import Event, DetectionEvent, MalfunctionEvent, ConnectionEvent
from app.models.integration import EventMapping


class TestEventModelsGroupEventRemoval:
    """Phase 4.1: Event Models - group_event Removal 테스트"""

    def test_detection_event_model_does_not_have_group_event_column(self):
        """Test: DetectionEvent model does NOT have group_event column"""
        mapper = inspect(DetectionEvent)
        all_column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in all_column_names, "DetectionEvent should NOT have 'group_event' column"

    def test_malfunction_event_model_does_not_have_group_event_column(self):
        """Test: MalfunctionEvent model does NOT have group_event column"""
        mapper = inspect(MalfunctionEvent)
        all_column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in all_column_names, "MalfunctionEvent should NOT have 'group_event' column"

    def test_connection_event_model_does_not_have_group_event_column(self):
        """Test: ConnectionEvent model does NOT have group_event column"""
        mapper = inspect(ConnectionEvent)
        all_column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in all_column_names, "ConnectionEvent should NOT have 'group_event' column"


class TestEventSchemasGroupEventRemoval:
    """Phase 4.2: Event Schemas - group_event Removal 테스트"""

    def test_detection_event_create_schema_does_not_accept_group_event(self):
        """Test: DetectionEventCreate schema does NOT accept group_event field"""
        from app.schemas.event import DetectionEventCreate

        # Get model fields
        field_names = list(DetectionEventCreate.model_fields.keys())
        assert 'group_event' not in field_names, "DetectionEventCreate should NOT have 'group_event' field"

    def test_malfunction_event_create_schema_does_not_accept_group_event(self):
        """Test: MalfunctionEventCreate schema does NOT accept group_event field"""
        from app.schemas.event import MalfunctionEventCreate

        field_names = list(MalfunctionEventCreate.model_fields.keys())
        assert 'group_event' not in field_names, "MalfunctionEventCreate should NOT have 'group_event' field"

    def test_connection_event_create_schema_does_not_accept_group_event(self):
        """Test: ConnectionEventCreate schema does NOT accept group_event field"""
        from app.schemas.event import ConnectionEventCreate

        field_names = list(ConnectionEventCreate.model_fields.keys())
        assert 'group_event' not in field_names, "ConnectionEventCreate should NOT have 'group_event' field"


class TestEventMappingGroupEventRemoval:
    """Phase 4.3: EventMapping - group_event Removal 테스트"""

    def test_event_mapping_model_does_not_have_group_event_column(self):
        """Test: EventMapping model does NOT have group_event column"""
        mapper = inspect(EventMapping)
        column_names = [column.key for column in mapper.columns]

        assert 'group_event' not in column_names, "EventMapping should NOT have 'group_event' column"

    def test_event_mapping_create_schema_does_not_accept_group_event(self):
        """Test: EventMappingCreate schema does NOT accept group_event field"""
        from app.schemas.integration import EventMappingCreate

        field_names = list(EventMappingCreate.model_fields.keys())
        assert 'group_event' not in field_names, "EventMappingCreate should NOT have 'group_event' field"

    def test_event_mapping_create_schema_requires_device_group_id(self):
        """Test: EventMappingCreate schema requires device_group_id field"""
        from app.schemas.integration import EventMappingCreate

        field_names = list(EventMappingCreate.model_fields.keys())
        assert 'device_group_id' in field_names, "EventMappingCreate should have 'device_group_id' field"
