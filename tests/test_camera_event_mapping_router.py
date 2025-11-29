"""
TDD Tests for CameraEventMapping Router
Phase 25.3: Router TDD Implementation
"""
import pytest
from unittest.mock import MagicMock
import asyncio


class TestCameraEventMappingListEndpoint:
    """Tests for GET /api/integrations/camera-event-mappings"""

    def test_get_camera_event_mappings_empty_list(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings 빈 목록 조회"""
        from app.routers.camera_event_mappings import get_camera_event_mappings

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=20,
            group_event=None,
            category_event=None,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data == []
        assert response.pagination.total == 0

    def test_get_camera_event_mappings_list(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings 목록 조회"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import get_camera_event_mappings

        # Create test data
        mapping = CameraEventMapping(
            name_event="Test Mapping",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=True
        )
        test_db.add(mapping)
        test_db.commit()

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=20,
            group_event=None,
            category_event=None,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0].name_event == "Test Mapping"

    def test_get_camera_event_mappings_pagination(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings 페이지네이션 검증"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import get_camera_event_mappings

        # Create 25 test mappings
        for i in range(25):
            mapping = CameraEventMapping(
                name_event=f"Test Mapping {i}",
                group_event="Intrusion",  # Plain string
                category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
                status=True
            )
            test_db.add(mapping)
        test_db.commit()

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=10,
            group_event=None,
            category_event=None,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert len(response.data) == 10
        assert response.pagination.total == 25
        assert response.pagination.total_pages == 3

    def test_get_camera_event_mappings_filter_by_group_event(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings?group_event=Intrusion 필터링"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import get_camera_event_mappings

        # Create test data with different group_events (plain strings)
        mapping1 = CameraEventMapping(
            name_event="Intrusion Event",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=True
        )
        mapping2 = CameraEventMapping(
            name_event="Fault Event",
            group_event="Fault",  # Plain string
            category_event=EnumCategoryEvent.AI_CAMERA_ONLY,  # Enum
            status=True
        )
        test_db.add_all([mapping1, mapping2])
        test_db.commit()

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=20,
            group_event="Intrusion",
            category_event=None,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert len(response.data) == 1
        assert response.data[0].group_event == "Intrusion"

    def test_get_camera_event_mappings_filter_by_category_event(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings?category_event=SENSOR_ONLY 필터링"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import get_camera_event_mappings

        # Create test data
        mapping1 = CameraEventMapping(
            name_event="Sensor Only Event",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=True
        )
        mapping2 = CameraEventMapping(
            name_event="AI Detect Event",
            group_event="Fault",  # Plain string
            category_event=EnumCategoryEvent.AI_CAMERA_ONLY,  # Enum
            status=True
        )
        test_db.add_all([mapping1, mapping2])
        test_db.commit()

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=20,
            group_event=None,
            category_event="FENCE_SENSOR_ONLY",  # Filter by enum value
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert len(response.data) == 1
        assert response.data[0].category_event == "FENCE_SENSOR_ONLY"

    def test_get_camera_event_mappings_filter_by_status(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings?status=true 필터링"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import get_camera_event_mappings

        # Create test data
        mapping1 = CameraEventMapping(
            name_event="Active Mapping",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=True
        )
        mapping2 = CameraEventMapping(
            name_event="Inactive Mapping",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=False
        )
        test_db.add_all([mapping1, mapping2])
        test_db.commit()

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=20,
            group_event=None,
            category_event=None,
            status_filter=True,
            current_user=mock_user,
            db=test_db
        ))

        assert len(response.data) == 1
        assert response.data[0].status is True


class TestCameraEventMappingCreateEndpoint:
    """Tests for POST /api/integrations/camera-event-mappings"""

    def test_create_camera_event_mapping_basic(self, test_db):
        """Test: POST /api/integrations/camera-event-mappings 기본 생성"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import CameraEventMappingCreate

        payload = CameraEventMappingCreate(
            name_event="New Mapping",
            group_event="Intrusion",  # Plain string
            category_event="FENCE_SENSOR_ONLY"  # Enum value
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.name_event == "New Mapping"
        assert response.data.group_event == "Intrusion"
        assert response.data.category_event == "FENCE_SENSOR_ONLY"
        assert response.data.status is True
        assert response.data.camera_presets == []

    def test_create_camera_event_mapping_with_presets(self, test_db):
        """Test: POST /api/integrations/camera-event-mappings with presets 생성"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import CameraEventMappingCreate, CameraEventPresetCreate, CameraUrls

        preset1 = CameraEventPresetCreate(
            cam_id=1,
            urls=CameraUrls(
                live="rtsp://192.168.1.100:554/live",
                record="rtsp://192.168.1.100:554/record"
            ),
            category="PTZ",
            preset_id="5",
            preset_time=10,
            home_preset=1,
            home_time=30
        )
        preset2 = CameraEventPresetCreate(
            cam_id=2,
            category="FIXED"
        )

        payload = CameraEventMappingCreate(
            name_event="Mapping with Presets",
            group_event="Intrusion",  # Plain string
            category_event="SENSOR_WITH_CAMERA",  # Enum value
            camera_presets=[preset1, preset2]
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data.camera_presets) == 2
        assert response.data.camera_presets[0].cam_id == 1
        assert response.data.camera_presets[0].preset_time == 10

    def test_create_camera_event_mapping_with_urls_object(self, test_db):
        """Test: POST /api/integrations/camera-event-mappings with urls object (Phase 28.5)"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import CameraEventMappingCreate, CameraEventPresetCreate, CameraUrls

        urls = CameraUrls(
            live="rtsp://192.168.1.100:554/live",
            record="rtsp://192.168.1.100:554/record"
        )
        preset = CameraEventPresetCreate(
            cam_id=1,
            urls=urls,
            category="PTZ",
            preset_time=10
        )
        payload = CameraEventMappingCreate(
            name_event="Test Mapping with URLs",
            group_event="Intrusion",
            category_event="SENSOR_WITH_CAMERA",
            camera_presets=[preset]
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.camera_presets[0].urls is not None
        assert response.data.camera_presets[0].urls.live == "rtsp://192.168.1.100:554/live"
        assert response.data.camera_presets[0].urls.record == "rtsp://192.168.1.100:554/record"


class TestCameraEventMappingDetailEndpoint:
    """Tests for GET /api/integrations/camera-event-mappings/{id}"""

    def test_get_camera_event_mapping_by_id(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings/{id} 상세 조회"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import get_camera_event_mapping

        mapping = CameraEventMapping(
            name_event="Test Mapping",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            description="Test description",
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mapping(
            mapping_id=mapping.id,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.id == mapping.id
        assert response.data.name_event == "Test Mapping"
        assert response.data.description == "Test description"

    def test_get_camera_event_mapping_not_found(self, test_db):
        """Test: GET /api/integrations/camera-event-mappings/{id} 404 처리"""
        from app.routers.camera_event_mappings import get_camera_event_mapping
        from fastapi import HTTPException

        mock_user = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_camera_event_mapping(
                mapping_id=9999,
                current_user=mock_user,
                db=test_db
            ))

        assert exc_info.value.status_code == 404


class TestCameraEventMappingUpdateEndpoint:
    """Tests for PUT/PATCH /api/integrations/camera-event-mappings/{id}"""

    def test_update_camera_event_mapping_put(self, test_db):
        """Test: PUT /api/integrations/camera-event-mappings/{id} 전체 수정"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import update_camera_event_mapping_full
        from app.schemas.integration import CameraEventMappingCreate

        mapping = CameraEventMapping(
            name_event="Original Name",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        payload = CameraEventMappingCreate(
            name_event="Updated Name",
            group_event="Fault",  # Plain string
            category_event="AI_CAMERA_ONLY",  # Enum value
            status=False
        )

        mock_user = MagicMock()
        response = asyncio.run(update_camera_event_mapping_full(
            mapping_id=mapping.id,
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.name_event == "Updated Name"
        assert response.data.group_event == "Fault"
        assert response.data.category_event == "AI_CAMERA_ONLY"
        assert response.data.status is False

    def test_update_camera_event_mapping_patch(self, test_db):
        """Test: PATCH /api/integrations/camera-event-mappings/{id} 부분 수정"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import update_camera_event_mapping_partial
        from app.schemas.integration import CameraEventMappingUpdate

        mapping = CameraEventMapping(
            name_event="Original Name",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        payload = CameraEventMappingUpdate(status=False)

        mock_user = MagicMock()
        response = asyncio.run(update_camera_event_mapping_partial(
            mapping_id=mapping.id,
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.name_event == "Original Name"  # unchanged
        assert response.data.status is False  # updated

    def test_update_camera_event_mapping_presets(self, test_db):
        """Test: PATCH /api/integrations/camera-event-mappings/{id} presets 수정"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import update_camera_event_mapping_partial
        from app.schemas.integration import CameraEventMappingUpdate, CameraEventPresetCreate

        mapping = CameraEventMapping(
            name_event="Mapping with Preset",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.SENSOR_WITH_CAMERA,  # Enum
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        preset = CameraEventPreset(
            mapping_id=mapping.id,
            cam_id=1,
            category="PTZ",
            preset_time=10,
            home_preset=1,
            home_time=30
        )
        test_db.add(preset)
        test_db.commit()

        # Update with new presets (replace all)
        new_preset1 = CameraEventPresetCreate(cam_id=2, category="FIXED")
        new_preset2 = CameraEventPresetCreate(cam_id=3, category="PTZ", preset_id="10")
        payload = CameraEventMappingUpdate(camera_presets=[new_preset1, new_preset2])

        mock_user = MagicMock()
        response = asyncio.run(update_camera_event_mapping_partial(
            mapping_id=mapping.id,
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data.camera_presets) == 2
        assert response.data.camera_presets[0].cam_id == 2


class TestCameraEventMappingDeleteEndpoint:
    """Tests for DELETE /api/integrations/camera-event-mappings/{id}"""

    def test_delete_camera_event_mapping(self, test_db):
        """Test: DELETE /api/integrations/camera-event-mappings/{id} 삭제"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import delete_camera_event_mapping

        mapping = CameraEventMapping(
            name_event="To Delete",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)
        mapping_id = mapping.id

        mock_user = MagicMock()
        response = asyncio.run(delete_camera_event_mapping(
            mapping_id=mapping_id,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True

        # Verify deletion
        deleted = test_db.query(CameraEventMapping).filter(
            CameraEventMapping.id == mapping_id
        ).first()
        assert deleted is None

    def test_delete_camera_event_mapping_cascade_presets(self, test_db):
        """Test: DELETE /api/integrations/camera-event-mappings/{id} cascade presets 삭제 확인"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import delete_camera_event_mapping

        mapping = CameraEventMapping(
            name_event="To Delete with Presets",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.SENSOR_WITH_CAMERA,  # Enum
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        preset = CameraEventPreset(
            mapping_id=mapping.id,
            cam_id=1,
            category="PTZ",
            preset_time=10,
            home_preset=1,
            home_time=30
        )
        test_db.add(preset)
        test_db.commit()

        mapping_id = mapping.id
        preset_id = preset.id

        mock_user = MagicMock()
        response = asyncio.run(delete_camera_event_mapping(
            mapping_id=mapping_id,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True

        # Verify preset is also deleted (cascade)
        deleted_preset = test_db.query(CameraEventPreset).filter(
            CameraEventPreset.id == preset_id
        ).first()
        assert deleted_preset is None

    def test_delete_camera_event_mapping_not_found(self, test_db):
        """Test: DELETE /api/integrations/camera-event-mappings/{id} 404 처리"""
        from app.routers.camera_event_mappings import delete_camera_event_mapping
        from fastapi import HTTPException

        mock_user = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(delete_camera_event_mapping(
                mapping_id=9999,
                current_user=mock_user,
                db=test_db
            ))

        assert exc_info.value.status_code == 404
