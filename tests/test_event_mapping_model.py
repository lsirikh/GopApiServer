"""
Test: EventMapping model
PRD: GOP_Restful_Api_연동설계.md - Section 7.2
PRD: PRD_CategoryEvent_Refactoring.md v1.1 - category_event → category_event_mapping
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime
from app.utils.enums import EnumMappingEventCategory


def test_event_mapping_model_has_required_fields(test_db):
    """
    Test: EventMapping model has all required fields

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping

    # Get table columns
    inspector = inspect(test_db.bind)
    columns = [col['name'] for col in inspector.get_columns('event_mappings')]

    # Check all required fields exist
    assert 'id' in columns
    assert 'name_event' in columns
    assert 'device_group_id' in columns
    assert 'category_event_mapping' in columns
    assert 'description' in columns
    assert 'status' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns


def test_event_mapping_model_timestamps_auto_set(test_db):
    """
    Test: EventMapping model automatically sets timestamps

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping

    # Create event mapping
    mapping = EventMapping(
        name_event="침입 탐지", category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        description="센서 침입 탐지 이벤트 매핑",
        status=True
    )
    test_db.add(mapping)
    test_db.commit()
    test_db.refresh(mapping)

    # Check timestamps are set
    assert mapping.created_at is not None
    assert mapping.updated_at is not None


def test_event_mapping_model_table_name(test_db):
    """
    Test: EventMapping model has correct table name

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping

    assert EventMapping.__tablename__ == "event_mappings"


def test_event_mapping_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve EventMapping

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping

    # Create event mapping
    mapping = EventMapping(
        name_event="장애 발생", category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY,
        description="센서 장애 발생 이벤트 매핑",
        status=True
    )
    test_db.add(mapping)
    test_db.commit()
    test_db.refresh(mapping)

    # Retrieve event mapping
    retrieved = test_db.query(EventMapping).filter(EventMapping.id == mapping.id).first()

    assert retrieved is not None
    assert retrieved.name_event == "장애 발생"
    assert retrieved.device_group_id is None  # No device_group assigned
    assert retrieved.category_event_mapping == EnumMappingEventCategory.MULTI_SENSOR_ONLY
    assert retrieved.description == "센서 장애 발생 이벤트 매핑"
    assert retrieved.status is True
