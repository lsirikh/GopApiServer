"""
Test: EventMapping API category_event_mapping field
PRD: PRD_CategoryEvent_Refactoring.md v1.1 - Phase CE-4

Phase CE-4: API 테스트
- ActionItem CE-4.1: EventMapping API 필터링 테스트
- category_event_mapping Query Parameter 필터링 검증
- POST/PATCH에서 category_event_mapping Enum 값 생성/수정 검증
"""
import pytest
from unittest.mock import MagicMock
import asyncio
from app.utils.enums import EnumMappingEventCategory


class TestEventMappingCategoryFilter:
    """CE-4.1: GET /api/integrations/event-mappings?category_event_mapping={value} 필터 테스트"""

    def test_filter_by_category_event_mapping_returns_matching_results(self, test_db):
        """
        Test: GET filter by category_event_mapping returns only matching mappings
        PRD: PRD_CategoryEvent_Refactoring.md v1.1 - Section 6.2
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import get_event_mappings

        # Create test data with different category_event_mapping values
        mapping1 = EventMapping(
            name_event="펜스 센서 전용",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        mapping2 = EventMapping(
            name_event="AI 카메라 전용",
            category_event_mapping=EnumMappingEventCategory.AI_CAMERA_ONLY,
            status=True
        )
        mapping3 = EventMapping(
            name_event="펜스 센서 전용 2",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add_all([mapping1, mapping2, mapping3])
        test_db.commit()

        # Mock current_user
        mock_user = MagicMock()

        # Filter by FENCE_SENSOR_ONLY
        response = asyncio.run(get_event_mappings(
            page=1,
            limit=20,
            name_event=None,
            device_group_id=None,
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        # Verify only FENCE_SENSOR_ONLY mappings returned
        assert response.success is True
        assert len(response.data) == 2
        for mapping in response.data:
            assert mapping.category_event_mapping == EnumMappingEventCategory.FENCE_SENSOR_ONLY

    def test_filter_by_category_event_mapping_ai_camera_only(self, test_db):
        """
        Test: Filter by AI_CAMERA_ONLY returns only AI camera mappings
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import get_event_mappings

        # Create test data
        mapping1 = EventMapping(
            name_event="펜스 센서",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        mapping2 = EventMapping(
            name_event="AI 카메라",
            category_event_mapping=EnumMappingEventCategory.AI_CAMERA_ONLY,
            status=True
        )
        test_db.add_all([mapping1, mapping2])
        test_db.commit()

        mock_user = MagicMock()

        # Filter by AI_CAMERA_ONLY
        response = asyncio.run(get_event_mappings(
            page=1,
            limit=20,
            name_event=None,
            device_group_id=None,
            category_event_mapping=EnumMappingEventCategory.AI_CAMERA_ONLY,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0].category_event_mapping == EnumMappingEventCategory.AI_CAMERA_ONLY

    def test_filter_returns_empty_when_no_match(self, test_db):
        """
        Test: Filter returns empty list when no matching category_event_mapping
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import get_event_mappings

        # Create test data with only FENCE_SENSOR_ONLY
        mapping = EventMapping(
            name_event="펜스 센서",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()

        mock_user = MagicMock()

        # Filter by MULTI_SENSOR_ONLY (no matches)
        response = asyncio.run(get_event_mappings(
            page=1,
            limit=20,
            name_event=None,
            device_group_id=None,
            category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) == 0

    def test_filter_all_enum_values(self, test_db):
        """
        Test: All 8 EnumMappingEventCategory values can be filtered
        PRD: PRD_CategoryEvent_Refactoring.md v1.1 - 8 sensor combination types
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import get_event_mappings

        # Create one mapping for each enum value
        all_categories = [
            EnumMappingEventCategory.NONE,
            EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            EnumMappingEventCategory.FENCE_SENSOR_WITH_MULTI_SENSOR,
            EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            EnumMappingEventCategory.SENSOR_WITH_CAMERA,
            EnumMappingEventCategory.SENSOR_WITH_AI_CAMERA,
            EnumMappingEventCategory.AI_CAMERA_ONLY,
            EnumMappingEventCategory.CAMERA_ONLY,
        ]

        for i, category in enumerate(all_categories):
            mapping = EventMapping(
                name_event=f"Mapping {i}",
                category_event_mapping=category,
                status=True
            )
            test_db.add(mapping)
        test_db.commit()

        mock_user = MagicMock()

        # Test filtering by each category
        for category in all_categories:
            response = asyncio.run(get_event_mappings(
                page=1,
                limit=20,
                name_event=None,
                device_group_id=None,
                category_event_mapping=category,
                status_filter=None,
                current_user=mock_user,
                db=test_db
            ))

            assert response.success is True
            assert len(response.data) == 1
            assert response.data[0].category_event_mapping == category


class TestEventMappingCategoryCreate:
    """CE-4.1: POST /api/integrations/event-mappings category_event_mapping 생성 테스트"""

    def test_create_with_fence_sensor_only(self, test_db):
        """
        Test: Create EventMapping with FENCE_SENSOR_ONLY category_event_mapping
        """
        from app.routers.event_mappings import create_event_mapping
        from app.schemas.integration import EventMappingCreate

        mock_user = MagicMock()

        create_data = EventMappingCreate(
            name_event="펜스 센서 탐지",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            description="펜스 센서 전용 이벤트",
            status=True
        )

        response = asyncio.run(create_event_mapping(
            mapping=create_data,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.category_event_mapping == EnumMappingEventCategory.FENCE_SENSOR_ONLY

    def test_create_with_sensor_with_ai_camera(self, test_db):
        """
        Test: Create EventMapping with SENSOR_WITH_AI_CAMERA category_event_mapping
        """
        from app.routers.event_mappings import create_event_mapping
        from app.schemas.integration import EventMappingCreate

        mock_user = MagicMock()

        create_data = EventMappingCreate(
            name_event="센서 + AI 카메라 탐지",
            category_event_mapping=EnumMappingEventCategory.SENSOR_WITH_AI_CAMERA,
            description="센서와 AI 카메라 조합 이벤트",
            status=True
        )

        response = asyncio.run(create_event_mapping(
            mapping=create_data,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.category_event_mapping == EnumMappingEventCategory.SENSOR_WITH_AI_CAMERA

    def test_create_all_category_event_mapping_values(self, test_db):
        """
        Test: Create EventMapping with all 8 category_event_mapping values
        PRD: PRD_CategoryEvent_Refactoring.md v1.1 - All enum values are valid
        """
        from app.routers.event_mappings import create_event_mapping
        from app.schemas.integration import EventMappingCreate

        mock_user = MagicMock()

        all_categories = [
            EnumMappingEventCategory.NONE,
            EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            EnumMappingEventCategory.FENCE_SENSOR_WITH_MULTI_SENSOR,
            EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            EnumMappingEventCategory.SENSOR_WITH_CAMERA,
            EnumMappingEventCategory.SENSOR_WITH_AI_CAMERA,
            EnumMappingEventCategory.AI_CAMERA_ONLY,
            EnumMappingEventCategory.CAMERA_ONLY,
        ]

        for i, category in enumerate(all_categories):
            create_data = EventMappingCreate(
                name_event=f"Test Mapping {i}",
                category_event_mapping=category,
                status=True
            )

            response = asyncio.run(create_event_mapping(
                mapping=create_data,
                current_user=mock_user,
                db=test_db
            ))

            assert response.success is True
            assert response.data.category_event_mapping == category


class TestEventMappingCategoryUpdate:
    """CE-4.1: PATCH /api/integrations/event-mappings/{id} category_event_mapping 수정 테스트"""

    def test_patch_category_event_mapping_field(self, test_db):
        """
        Test: PATCH update category_event_mapping field
        PRD: PRD_CategoryEvent_Refactoring.md v1.1 - Section 6.2
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import update_event_mapping_partial
        from app.schemas.integration import EventMappingUpdate

        # Create initial mapping
        mapping = EventMapping(
            name_event="테스트 매핑",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        mock_user = MagicMock()

        # Update only category_event_mapping
        update_data = EventMappingUpdate(
            category_event_mapping=EnumMappingEventCategory.AI_CAMERA_ONLY
        )

        response = asyncio.run(update_event_mapping_partial(
            mapping_id=mapping.id,
            mapping=update_data,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.category_event_mapping == EnumMappingEventCategory.AI_CAMERA_ONLY
        # Other fields unchanged
        assert response.data.name_event == "테스트 매핑"
        assert response.data.status is True

    def test_patch_from_none_to_sensor_category(self, test_db):
        """
        Test: Update from NONE to SENSOR_WITH_CAMERA
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import update_event_mapping_partial
        from app.schemas.integration import EventMappingUpdate

        mapping = EventMapping(
            name_event="초기 매핑",
            category_event_mapping=EnumMappingEventCategory.NONE,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        mock_user = MagicMock()

        update_data = EventMappingUpdate(
            category_event_mapping=EnumMappingEventCategory.SENSOR_WITH_CAMERA
        )

        response = asyncio.run(update_event_mapping_partial(
            mapping_id=mapping.id,
            mapping=update_data,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.category_event_mapping == EnumMappingEventCategory.SENSOR_WITH_CAMERA

    def test_patch_to_all_enum_values(self, test_db):
        """
        Test: PATCH can update to all 8 category_event_mapping values
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import update_event_mapping_partial
        from app.schemas.integration import EventMappingUpdate

        mapping = EventMapping(
            name_event="Update Test",
            category_event_mapping=EnumMappingEventCategory.NONE,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        mock_user = MagicMock()

        all_categories = [
            EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            EnumMappingEventCategory.FENCE_SENSOR_WITH_MULTI_SENSOR,
            EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            EnumMappingEventCategory.SENSOR_WITH_CAMERA,
            EnumMappingEventCategory.SENSOR_WITH_AI_CAMERA,
            EnumMappingEventCategory.AI_CAMERA_ONLY,
            EnumMappingEventCategory.CAMERA_ONLY,
            EnumMappingEventCategory.NONE,
        ]

        for category in all_categories:
            update_data = EventMappingUpdate(
                category_event_mapping=category
            )

            response = asyncio.run(update_event_mapping_partial(
                mapping_id=mapping.id,
                mapping=update_data,
                current_user=mock_user,
                db=test_db
            ))

            assert response.success is True
            assert response.data.category_event_mapping == category


class TestEventMappingCategoryResponse:
    """CE-4.1: Response에 category_event_mapping 필드 포함 검증"""

    def test_response_contains_category_event_mapping(self, test_db):
        """
        Test: EventMappingResponse contains category_event_mapping field
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import get_event_mapping

        mapping = EventMapping(
            name_event="응답 테스트",
            category_event_mapping=EnumMappingEventCategory.MULTI_SENSOR_ONLY,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        mock_user = MagicMock()

        response = asyncio.run(get_event_mapping(
            mapping_id=mapping.id,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert hasattr(response.data, 'category_event_mapping')
        assert response.data.category_event_mapping == EnumMappingEventCategory.MULTI_SENSOR_ONLY

    def test_list_response_contains_category_event_mapping(self, test_db):
        """
        Test: List response items contain category_event_mapping field
        """
        from app.models.integration import EventMapping
        from app.routers.event_mappings import get_event_mappings

        mapping = EventMapping(
            name_event="목록 테스트",
            category_event_mapping=EnumMappingEventCategory.CAMERA_ONLY,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()

        mock_user = MagicMock()

        response = asyncio.run(get_event_mappings(
            page=1,
            limit=20,
            name_event=None,
            device_group_id=None,
            category_event_mapping=None,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) >= 1
        for item in response.data:
            assert hasattr(item, 'category_event_mapping')
