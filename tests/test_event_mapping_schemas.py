"""
Test: EventMapping schemas
PRD: GOP_Restful_Api_연동설계.md - Section 7.2
PRD: PRD_CategoryEvent_Refactoring.md v1.1 - category_event → category_event_mapping
"""
import pytest
from datetime import datetime
from app.utils.enums import EnumMappingEventCategory


def test_event_mapping_create_schema_has_required_fields():
    """
    Test: EventMappingCreate schema has all required fields

    Expected to FAIL initially (Red phase).
    """
    from app.schemas.integration import EventMappingCreate

    # Create schema instance (PRD: category_event_mapping)
    mapping_data = {
        "name_event": "침입 탐지",
        "device_group_id": 1,
        "category_event_mapping": EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        "description": "센서 침입 탐지 이벤트 매핑",
        "status": True
    }

    mapping = EventMappingCreate(**mapping_data)

    # Verify all fields are present
    assert mapping.name_event == "침입 탐지"
    assert mapping.device_group_id == 1
    assert mapping.category_event_mapping == EnumMappingEventCategory.FENCE_SENSOR_ONLY
    assert mapping.description == "센서 침입 탐지 이벤트 매핑"
    assert mapping.status is True


def test_event_mapping_create_schema_description_is_optional():
    """
    Test: EventMappingCreate schema allows optional description

    Expected to FAIL initially (Red phase).
    """
    from app.schemas.integration import EventMappingCreate

    # Create schema without description (PRD: category_event_mapping)
    mapping_data = {
        "name_event": "장애 발생",
        "category_event_mapping": EnumMappingEventCategory.MULTI_SENSOR_ONLY,
        "status": True
    }

    mapping = EventMappingCreate(**mapping_data)

    assert mapping.name_event == "장애 발생"
    assert mapping.description is None


def test_event_mapping_response_schema_has_all_fields():
    """
    Test: EventMappingResponse schema includes all fields including timestamps

    Expected to FAIL initially (Red phase).
    """
    from app.schemas.integration import EventMappingResponse

    # Create response schema with all fields (PRD: category_event_mapping)
    now = datetime.now()
    response_data = {
        "id": 1,
        "name_event": "침입 탐지",
        "device_group_id": 1,
        "category_event_mapping": EnumMappingEventCategory.FENCE_SENSOR_ONLY,
        "description": "센서 침입 탐지 이벤트 매핑",
        "status": True,
        "created_at": now,
        "updated_at": now
    }

    response = EventMappingResponse(**response_data)

    # Verify all fields
    assert response.id == 1
    assert response.name_event == "침입 탐지"
    assert response.device_group_id == 1
    assert response.category_event_mapping == EnumMappingEventCategory.FENCE_SENSOR_ONLY
    assert response.description == "센서 침입 탐지 이벤트 매핑"
    assert response.status is True
    assert response.created_at == now
    assert response.updated_at == now


def test_event_mapping_update_schema_all_fields_optional():
    """
    Test: EventMappingUpdate schema has all fields as optional

    Expected to FAIL initially (Red phase).
    """
    from app.schemas.integration import EventMappingUpdate

    # Create update schema with only one field
    update_data = {
        "status": False
    }

    update = EventMappingUpdate(**update_data)

    # Verify only status is set, others are None
    assert update.status is False
    assert update.name_event is None
    assert update.device_group_id is None
    assert update.category_event_mapping is None
    assert update.description is None


def test_event_mapping_update_schema_can_update_multiple_fields():
    """
    Test: EventMappingUpdate schema allows updating multiple fields

    Expected to FAIL initially (Red phase).
    """
    from app.schemas.integration import EventMappingUpdate

    # Create update with multiple fields
    update_data = {
        "name_event": "Updated Name",
        "description": "Updated description",
        "status": False
    }

    update = EventMappingUpdate(**update_data)

    assert update.name_event == "Updated Name"
    assert update.description == "Updated description"
    assert update.status is False
    assert update.device_group_id is None
    assert update.category_event_mapping is None
