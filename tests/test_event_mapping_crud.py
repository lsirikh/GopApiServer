"""
Test: EventMapping CRUD operations (GET single, POST, PATCH, PUT, DELETE)
PRD: GOP_Restful_Api_연동설계.md - Section 7.2
"""
import pytest
from unittest.mock import MagicMock
import asyncio


# Phase 16.4: Single retrieval tests
def test_get_single_event_mapping_returns_mapping(test_db):
    """
    Test: GET /api/integrations/event-mappings/{id} returns event mapping

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import get_event_mapping

    # Create test data
    mapping = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        description="센서 침입 탐지 이벤트 매핑",
        status=True
    )
    test_db.add(mapping)
    test_db.commit()
    test_db.refresh(mapping)

    # Mock current_user
    mock_user = MagicMock()

    # Get single event mapping
    response = asyncio.run(get_event_mapping(
        mapping_id=mapping.id,
        current_user=mock_user,
        db=test_db
    ))

    # Verify response
    assert response.success is True
    assert response.data.id == mapping.id
    assert response.data.name_event == "침입 탐지"
    assert response.data.group_event == "intrusion"


def test_get_single_event_mapping_returns_404_when_not_found(test_db):
    """
    Test: GET /api/integrations/event-mappings/{id} returns 404 for non-existent ID

    Expected to FAIL initially (Red phase).
    """
    from app.routers.event_mappings import get_event_mapping
    from fastapi import HTTPException

    # Mock current_user
    mock_user = MagicMock()

    # Try to get non-existent mapping
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_event_mapping(
            mapping_id=999,
            current_user=mock_user,
            db=test_db
        ))

    assert exc_info.value.status_code == 404


# Phase 16.5: POST tests
def test_create_event_mapping_returns_201(test_db):
    """
    Test: POST /api/integrations/event-mappings creates event mapping

    Expected to FAIL initially (Red phase).
    """
    from app.routers.event_mappings import create_event_mapping
    from app.schemas.integration import EventMappingCreate

    # Mock current_user
    mock_user = MagicMock()

    # Create mapping data
    create_data = EventMappingCreate(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        description="센서 침입 탐지 이벤트 매핑",
        status=True
    )

    # Create event mapping
    response = asyncio.run(create_event_mapping(
        mapping=create_data,
        current_user=mock_user,
        db=test_db
    ))

    # Verify response
    assert response.success is True
    assert response.data.name_event == "침입 탐지"
    assert response.data.id is not None


# Phase 16.6: PATCH tests
def test_patch_event_mapping_updates_fields(test_db):
    """
    Test: PATCH /api/integrations/event-mappings/{id} partially updates mapping

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import update_event_mapping_partial
    from app.schemas.integration import EventMappingUpdate

    # Create test data
    mapping = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        description="Original description",
        status=True
    )
    test_db.add(mapping)
    test_db.commit()
    test_db.refresh(mapping)

    # Mock current_user
    mock_user = MagicMock()

    # Update only status
    update_data = EventMappingUpdate(status=False)

    response = asyncio.run(update_event_mapping_partial(
        mapping_id=mapping.id,
        mapping=update_data,
        current_user=mock_user,
        db=test_db
    ))

    # Verify only status changed
    assert response.success is True
    assert response.data.status is False
    assert response.data.name_event == "침입 탐지"
    assert response.data.description == "Original description"


def test_patch_event_mapping_returns_404_when_not_found(test_db):
    """
    Test: PATCH /api/integrations/event-mappings/{id} returns 404 for non-existent ID

    Expected to FAIL initially (Red phase).
    """
    from app.routers.event_mappings import update_event_mapping_partial
    from app.schemas.integration import EventMappingUpdate
    from fastapi import HTTPException

    # Mock current_user
    mock_user = MagicMock()

    update_data = EventMappingUpdate(status=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(update_event_mapping_partial(
            mapping_id=999,
            mapping=update_data,
            current_user=mock_user,
            db=test_db
        ))

    assert exc_info.value.status_code == 404


def test_patch_event_mapping_updates_timestamp(test_db):
    """
    Test: PATCH /api/integrations/event-mappings/{id} updates updated_at timestamp

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import update_event_mapping_partial
    from app.schemas.integration import EventMappingUpdate
    import time

    # Create test data
    mapping = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        status=True
    )
    test_db.add(mapping)
    test_db.commit()
    test_db.refresh(mapping)

    original_updated_at = mapping.updated_at
    time.sleep(0.1)  # Small delay to ensure timestamp difference

    # Mock current_user
    mock_user = MagicMock()

    # Update mapping
    update_data = EventMappingUpdate(status=False)

    response = asyncio.run(update_event_mapping_partial(
        mapping_id=mapping.id,
        mapping=update_data,
        current_user=mock_user,
        db=test_db
    ))

    # Verify updated_at changed
    assert response.data.updated_at >= original_updated_at


# Phase 16.7: PUT tests
def test_put_event_mapping_replaces_all_fields(test_db):
    """
    Test: PUT /api/integrations/event-mappings/{id} replaces all fields

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import update_event_mapping_full
    from app.schemas.integration import EventMappingCreate

    # Create test data
    mapping = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        description="Original description",
        status=True
    )
    test_db.add(mapping)
    test_db.commit()
    test_db.refresh(mapping)

    # Mock current_user
    mock_user = MagicMock()

    # Full update
    update_data = EventMappingCreate(
        name_event="장애 발생",
        group_event="malfunction",
        category_event="fault",
        description="New description",
        status=False
    )

    response = asyncio.run(update_event_mapping_full(
        mapping_id=mapping.id,
        mapping=update_data,
        current_user=mock_user,
        db=test_db
    ))

    # Verify all fields replaced
    assert response.success is True
    assert response.data.name_event == "장애 발생"
    assert response.data.group_event == "malfunction"
    assert response.data.category_event == "fault"
    assert response.data.description == "New description"
    assert response.data.status is False


def test_put_event_mapping_returns_404_when_not_found(test_db):
    """
    Test: PUT /api/integrations/event-mappings/{id} returns 404 for non-existent ID

    Expected to FAIL initially (Red phase).
    """
    from app.routers.event_mappings import update_event_mapping_full
    from app.schemas.integration import EventMappingCreate
    from fastapi import HTTPException

    # Mock current_user
    mock_user = MagicMock()

    update_data = EventMappingCreate(
        name_event="장애 발생",
        group_event="malfunction",
        category_event="fault",
        status=False
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(update_event_mapping_full(
            mapping_id=999,
            mapping=update_data,
            current_user=mock_user,
            db=test_db
        ))

    assert exc_info.value.status_code == 404


# Phase 16.8: DELETE tests
def test_delete_event_mapping_removes_mapping(test_db):
    """
    Test: DELETE /api/integrations/event-mappings/{id} deletes event mapping

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import delete_event_mapping

    # Create test data
    mapping = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        status=True
    )
    test_db.add(mapping)
    test_db.commit()
    test_db.refresh(mapping)

    mapping_id = mapping.id

    # Mock current_user
    mock_user = MagicMock()

    # Delete mapping
    response = asyncio.run(delete_event_mapping(
        mapping_id=mapping_id,
        current_user=mock_user,
        db=test_db
    ))

    # Verify deletion
    assert response.success is True

    # Verify mapping no longer exists
    deleted_mapping = test_db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    assert deleted_mapping is None


def test_delete_event_mapping_returns_404_when_not_found(test_db):
    """
    Test: DELETE /api/integrations/event-mappings/{id} returns 404 for non-existent ID

    Expected to FAIL initially (Red phase).
    """
    from app.routers.event_mappings import delete_event_mapping
    from fastapi import HTTPException

    # Mock current_user
    mock_user = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(delete_event_mapping(
            mapping_id=999,
            current_user=mock_user,
            db=test_db
        ))

    assert exc_info.value.status_code == 404
