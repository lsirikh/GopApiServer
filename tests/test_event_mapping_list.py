"""
Test: EventMapping GET list endpoint
PRD: GOP_Restful_Api_연동설계.md - Section 7.2
"""
import pytest
from unittest.mock import MagicMock
import asyncio


def test_get_event_mappings_returns_empty_list_when_no_data(test_db):
    """
    Test: GET /api/integrations/event-mappings returns empty list

    Expected to FAIL initially (Red phase).
    """
    from app.routers.event_mappings import get_event_mappings

    # Mock current_user
    mock_user = MagicMock()

    # Get event mappings (should be empty)
    response = asyncio.run(get_event_mappings(
        page=1,
        limit=20,
        name_event=None,
        group_event=None,
        category_event=None,
        status=None,
        current_user=mock_user,
        db=test_db
    ))

    # Verify response
    assert response.success is True
    assert response.data == []
    assert response.pagination.page == 1
    assert response.pagination.limit == 20
    assert response.pagination.total == 0
    assert response.pagination.total_pages == 1


def test_get_event_mappings_returns_data_when_exists(test_db):
    """
    Test: GET /api/integrations/event-mappings returns event mappings

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import get_event_mappings

    # Create test data
    mapping1 = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        description="센서 침입 탐지 이벤트 매핑",
        status=True
    )
    mapping2 = EventMapping(
        name_event="장애 발생",
        group_event="malfunction",
        category_event="fault",
        description="센서 장애 발생 이벤트 매핑",
        status=True
    )
    test_db.add_all([mapping1, mapping2])
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get event mappings
    response = asyncio.run(get_event_mappings(
        page=1,
        limit=20,
        name_event=None,
        group_event=None,
        category_event=None,
        status=None,
        current_user=mock_user,
        db=test_db
    ))

    # Verify response
    assert response.success is True
    assert len(response.data) == 2
    assert response.pagination.total == 2


def test_get_event_mappings_filters_by_name_event(test_db):
    """
    Test: GET /api/integrations/event-mappings?name_event=침입 filters by name_event

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import get_event_mappings

    # Create test data
    mapping1 = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        status=True
    )
    mapping2 = EventMapping(
        name_event="장애 발생",
        group_event="malfunction",
        category_event="fault",
        status=True
    )
    test_db.add_all([mapping1, mapping2])
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get event mappings filtered by name_event
    response = asyncio.run(get_event_mappings(
        page=1,
        limit=20,
        name_event="침입 탐지",
        group_event=None,
        category_event=None,
        status=None,
        current_user=mock_user,
        db=test_db
    ))

    # Verify only matching records returned
    assert response.success is True
    assert len(response.data) == 1
    assert response.data[0].name_event == "침입 탐지"


def test_get_event_mappings_filters_by_group_event(test_db):
    """
    Test: GET /api/integrations/event-mappings?group_event=intrusion filters by group_event

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import get_event_mappings

    # Create test data
    mapping1 = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        status=True
    )
    mapping2 = EventMapping(
        name_event="장애 발생",
        group_event="malfunction",
        category_event="fault",
        status=True
    )
    test_db.add_all([mapping1, mapping2])
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get event mappings filtered by group_event
    response = asyncio.run(get_event_mappings(
        page=1,
        limit=20,
        name_event=None,
        group_event="intrusion",
        category_event=None,
        status=None,
        current_user=mock_user,
        db=test_db
    ))

    # Verify only matching records returned
    assert response.success is True
    assert len(response.data) == 1
    assert response.data[0].group_event == "intrusion"


def test_get_event_mappings_filters_by_category_event(test_db):
    """
    Test: GET /api/integrations/event-mappings?category_event=detection filters by category_event

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import get_event_mappings

    # Create test data
    mapping1 = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        status=True
    )
    mapping2 = EventMapping(
        name_event="장애 발생",
        group_event="malfunction",
        category_event="fault",
        status=True
    )
    test_db.add_all([mapping1, mapping2])
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get event mappings filtered by category_event
    response = asyncio.run(get_event_mappings(
        page=1,
        limit=20,
        name_event=None,
        group_event=None,
        category_event="detection",
        status=None,
        current_user=mock_user,
        db=test_db
    ))

    # Verify only matching records returned
    assert response.success is True
    assert len(response.data) == 1
    assert response.data[0].category_event == "detection"


def test_get_event_mappings_filters_by_status(test_db):
    """
    Test: GET /api/integrations/event-mappings?status=true filters by status

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import get_event_mappings

    # Create test data
    mapping1 = EventMapping(
        name_event="침입 탐지",
        group_event="intrusion",
        category_event="detection",
        status=True
    )
    mapping2 = EventMapping(
        name_event="장애 발생",
        group_event="malfunction",
        category_event="fault",
        status=False
    )
    test_db.add_all([mapping1, mapping2])
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get event mappings filtered by status=True
    response = asyncio.run(get_event_mappings(
        page=1,
        limit=20,
        name_event=None,
        group_event=None,
        category_event=None,
        status=True,
        current_user=mock_user,
        db=test_db
    ))

    # Verify only active records returned
    assert response.success is True
    assert len(response.data) == 1
    assert response.data[0].status is True


def test_get_event_mappings_pagination_works(test_db):
    """
    Test: GET /api/integrations/event-mappings?page=2&limit=2 pagination works

    Expected to FAIL initially (Red phase).
    """
    from app.models.integration import EventMapping
    from app.routers.event_mappings import get_event_mappings

    # Create 5 test records
    for i in range(5):
        mapping = EventMapping(
            name_event=f"Event {i+1}",
            group_event="test",
            category_event="test",
            status=True
        )
        test_db.add(mapping)
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get page 2 with limit 2
    response = asyncio.run(get_event_mappings(
        page=2,
        limit=2,
        name_event=None,
        group_event=None,
        category_event=None,
        status=None,
        current_user=mock_user,
        db=test_db
    ))

    # Verify pagination
    assert response.success is True
    assert len(response.data) == 2
    assert response.pagination.page == 2
    assert response.pagination.limit == 2
    assert response.pagination.total == 5
    assert response.pagination.total_pages == 3
