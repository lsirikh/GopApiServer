"""
TDD Tests for CameraEventMapping and CameraEventPreset Schemas
Phase 25.2: Schema TDD Implementation
Phase 28: URL Schema Refactor (rtsp_uri → urls)
"""
import pytest
from pydantic import ValidationError


# ============================================
# Phase 28.1: CameraUrls Schema TDD
# ============================================

class TestCameraUrlsSchema:
    """Tests for CameraUrls Schema - Phase 28.1"""

    def test_camera_urls_schema_exists(self):
        """Test: CameraUrls 스키마 클래스 존재 확인"""
        from app.schemas.integration import CameraUrls
        assert CameraUrls is not None

    def test_camera_urls_has_live_and_record_fields(self):
        """Test: CameraUrls에 live, record 필드 포함"""
        from app.schemas.integration import CameraUrls

        urls = CameraUrls(
            live="rtsp://192.168.1.100:554/live",
            record="rtsp://192.168.1.100:554/record"
        )
        assert urls.live == "rtsp://192.168.1.100:554/live"
        assert urls.record == "rtsp://192.168.1.100:554/record"

    def test_camera_urls_all_fields_optional(self):
        """Test: CameraUrls 모든 필드 optional"""
        from app.schemas.integration import CameraUrls

        urls = CameraUrls()
        assert urls.live is None
        assert urls.record is None

    def test_camera_urls_partial_fields(self):
        """Test: CameraUrls 부분 필드만 설정 가능"""
        from app.schemas.integration import CameraUrls

        # Only live
        urls_live_only = CameraUrls(live="rtsp://live")
        assert urls_live_only.live == "rtsp://live"
        assert urls_live_only.record is None

        # Only record
        urls_record_only = CameraUrls(record="rtsp://record")
        assert urls_record_only.live is None
        assert urls_record_only.record == "rtsp://record"


# ============================================
# Phase 28.2: CameraEventPresetCreate Schema TDD
# ============================================

class TestCameraEventPresetCreateSchema:
    """Tests for CameraEventPresetCreate Schema - Phase 28.2"""

    def test_camera_event_preset_create_schema_exists(self):
        """Test: CameraEventPresetCreate 스키마 클래스 존재 확인"""
        from app.schemas.integration import CameraEventPresetCreate
        assert CameraEventPresetCreate is not None

    def test_camera_event_preset_create_has_required_fields(self):
        """Test: CameraEventPresetCreate 필수 필드 검증"""
        from app.schemas.integration import CameraEventPresetCreate

        # Should work with minimal required fields
        preset = CameraEventPresetCreate(
            cam_id=1,
            category="PTZ"
        )
        assert preset.cam_id == 1
        assert preset.category == "PTZ"

    def test_camera_event_preset_create_has_urls_field(self):
        """Test: CameraEventPresetCreate에 urls 필드 포함 확인 (Phase 28.2)"""
        from app.schemas.integration import CameraEventPresetCreate, CameraUrls

        urls = CameraUrls(
            live="rtsp://192.168.1.100:554/live",
            record="rtsp://192.168.1.100:554/record"
        )
        preset = CameraEventPresetCreate(
            cam_id=1,
            urls=urls,
            category="PTZ"
        )
        assert preset.urls is not None
        assert preset.urls.live == "rtsp://192.168.1.100:554/live"
        assert preset.urls.record == "rtsp://192.168.1.100:554/record"

    def test_camera_event_preset_create_urls_optional(self):
        """Test: CameraEventPresetCreate urls 필드 optional (Phase 28.2)"""
        from app.schemas.integration import CameraEventPresetCreate

        preset = CameraEventPresetCreate(
            cam_id=1,
            category="PTZ"
        )
        assert preset.urls is None

    def test_camera_event_preset_create_default_values(self):
        """Test: CameraEventPresetCreate 기본값 검증"""
        from app.schemas.integration import CameraEventPresetCreate

        preset = CameraEventPresetCreate(
            cam_id=1,
            category="PTZ"
        )
        assert preset.urls is None  # Changed from rtsp_uri
        assert preset.preset_id is None
        assert preset.preset_time == 0
        assert preset.home_preset == 0
        assert preset.home_time == 0

    def test_camera_event_preset_create_all_fields(self):
        """Test: CameraEventPresetCreate 모든 필드 설정"""
        from app.schemas.integration import CameraEventPresetCreate, CameraUrls

        urls = CameraUrls(
            live="rtsp://192.168.1.100:554/live",
            record="rtsp://192.168.1.100:554/record"
        )
        preset = CameraEventPresetCreate(
            cam_id=1,
            urls=urls,  # Changed from rtsp_uri
            category="PTZ",
            preset_id="5",
            preset_time=10,
            home_preset=1,
            home_time=30
        )
        assert preset.cam_id == 1
        assert preset.urls.live == "rtsp://192.168.1.100:554/live"
        assert preset.urls.record == "rtsp://192.168.1.100:554/record"
        assert preset.category == "PTZ"
        assert preset.preset_id == "5"
        assert preset.preset_time == 10
        assert preset.home_preset == 1
        assert preset.home_time == 30


# ============================================
# Phase 28.3: CameraEventPresetResponse Schema TDD
# ============================================

class TestCameraEventPresetResponseSchema:
    """Tests for CameraEventPresetResponse Schema - Phase 28.3"""

    def test_camera_event_preset_response_schema_exists(self):
        """Test: CameraEventPresetResponse 스키마 클래스 존재 확인"""
        from app.schemas.integration import CameraEventPresetResponse
        assert CameraEventPresetResponse is not None

    def test_camera_event_preset_response_has_urls_field(self):
        """Test: CameraEventPresetResponse에 urls 필드 포함 확인 (Phase 28.3)"""
        from app.schemas.integration import CameraEventPresetResponse, CameraUrls

        urls = CameraUrls(
            live="rtsp://192.168.1.100:554/live",
            record="rtsp://192.168.1.100:554/record"
        )
        preset = CameraEventPresetResponse(
            id=1,
            cam_id=1,
            urls=urls,
            category="PTZ",
            preset_id=None,
            preset_time=0,
            home_preset=0,
            home_time=0
        )
        assert preset.id == 1
        assert preset.urls is not None
        assert preset.urls.live == "rtsp://192.168.1.100:554/live"
        assert preset.urls.record == "rtsp://192.168.1.100:554/record"

    def test_camera_event_preset_response_urls_can_be_none(self):
        """Test: CameraEventPresetResponse urls 필드 None 허용"""
        from app.schemas.integration import CameraEventPresetResponse

        preset = CameraEventPresetResponse(
            id=1,
            cam_id=1,
            urls=None,
            category="PTZ",
            preset_id=None,
            preset_time=0,
            home_preset=0,
            home_time=0
        )
        assert preset.urls is None

    def test_camera_event_preset_response_from_attributes(self):
        """Test: CameraEventPresetResponse from_attributes 설정 확인"""
        from app.schemas.integration import CameraEventPresetResponse

        # Check model_config has from_attributes=True
        assert CameraEventPresetResponse.model_config.get("from_attributes") is True


class TestCameraEventMappingCreateSchema:
    """Tests for CameraEventMappingCreate Schema"""

    def test_camera_event_mapping_create_schema_exists(self):
        """Test: CameraEventMappingCreate 스키마 클래스 존재 확인"""
        from app.schemas.integration import CameraEventMappingCreate
        assert CameraEventMappingCreate is not None

    def test_camera_event_mapping_create_has_required_fields(self):
        """Test: CameraEventMappingCreate 필수 필드 검증"""
        from app.schemas.integration import CameraEventMappingCreate

        mapping = CameraEventMappingCreate(
            name_event="Test Event",
            group_event="Intrusion",  # Plain string
            category_event="FENCE_SENSOR_ONLY"  # Enum value string
        )
        assert mapping.name_event == "Test Event"
        assert mapping.group_event == "Intrusion"
        assert mapping.category_event == "FENCE_SENSOR_ONLY"

    def test_camera_event_mapping_create_default_values(self):
        """Test: CameraEventMappingCreate 기본값 검증 (status=True, camera_presets=[])"""
        from app.schemas.integration import CameraEventMappingCreate

        mapping = CameraEventMappingCreate(
            name_event="Test Event",
            group_event="Intrusion",  # Plain string
            category_event="FENCE_SENSOR_ONLY"  # Enum value string
        )
        assert mapping.status is True
        assert mapping.camera_presets == []
        assert mapping.description is None

    def test_camera_event_mapping_create_with_presets(self):
        """Test: CameraEventMappingCreate with nested presets"""
        from app.schemas.integration import CameraEventMappingCreate, CameraEventPresetCreate

        preset1 = CameraEventPresetCreate(cam_id=1, category="PTZ")
        preset2 = CameraEventPresetCreate(cam_id=2, category="FIXED")

        mapping = CameraEventMappingCreate(
            name_event="Test Event",
            group_event="Intrusion",  # Plain string
            category_event="SENSOR_WITH_CAMERA",  # Enum value string
            camera_presets=[preset1, preset2]
        )
        assert len(mapping.camera_presets) == 2
        assert mapping.camera_presets[0].cam_id == 1
        assert mapping.camera_presets[1].cam_id == 2


class TestCameraEventMappingResponseSchema:
    """Tests for CameraEventMappingResponse Schema"""

    def test_camera_event_mapping_response_schema_exists(self):
        """Test: CameraEventMappingResponse 스키마 클래스 존재 확인"""
        from app.schemas.integration import CameraEventMappingResponse
        assert CameraEventMappingResponse is not None

    def test_camera_event_mapping_response_has_all_fields(self):
        """Test: CameraEventMappingResponse 모든 필드 검증"""
        from app.schemas.integration import CameraEventMappingResponse
        from datetime import datetime

        now = datetime.now()
        mapping = CameraEventMappingResponse(
            id=1,
            name_event="Test Event",
            group_event="Intrusion",  # Plain string
            category_event="FENCE_SENSOR_ONLY",  # Enum value string
            description="Test description",
            status=True,
            camera_presets=[],
            created_at=now,
            updated_at=now
        )
        assert mapping.id == 1
        assert mapping.name_event == "Test Event"
        assert mapping.camera_presets == []
        assert mapping.created_at == now

    def test_camera_event_mapping_response_with_nested_presets(self):
        """Test: CameraEventMappingResponse with nested presets"""
        from app.schemas.integration import CameraEventMappingResponse, CameraEventPresetResponse, CameraUrls
        from datetime import datetime

        now = datetime.now()
        preset = CameraEventPresetResponse(
            id=1,
            cam_id=1,
            urls=CameraUrls(live="rtsp://live", record="rtsp://record"),
            category="PTZ",
            preset_id="5",
            preset_time=10,
            home_preset=1,
            home_time=30
        )

        mapping = CameraEventMappingResponse(
            id=1,
            name_event="Test Event",
            group_event="Intrusion",  # Plain string
            category_event="SENSOR_WITH_CAMERA",  # Enum value string
            description=None,
            status=True,
            camera_presets=[preset],
            created_at=now,
            updated_at=now
        )
        assert len(mapping.camera_presets) == 1
        assert mapping.camera_presets[0].cam_id == 1

    def test_camera_event_mapping_response_from_attributes(self):
        """Test: CameraEventMappingResponse from_attributes 설정 확인"""
        from app.schemas.integration import CameraEventMappingResponse

        assert CameraEventMappingResponse.model_config.get("from_attributes") is True


class TestCameraEventMappingUpdateSchema:
    """Tests for CameraEventMappingUpdate Schema"""

    def test_camera_event_mapping_update_schema_exists(self):
        """Test: CameraEventMappingUpdate 스키마 클래스 존재 확인"""
        from app.schemas.integration import CameraEventMappingUpdate
        assert CameraEventMappingUpdate is not None

    def test_camera_event_mapping_update_all_fields_optional(self):
        """Test: CameraEventMappingUpdate 모든 필드가 optional인지 검증"""
        from app.schemas.integration import CameraEventMappingUpdate

        # Empty update should work
        update = CameraEventMappingUpdate()
        assert update.name_event is None
        assert update.group_event is None
        assert update.category_event is None
        assert update.description is None
        assert update.status is None
        assert update.camera_presets is None

    def test_camera_event_mapping_update_partial_fields(self):
        """Test: CameraEventMappingUpdate 부분 필드 설정"""
        from app.schemas.integration import CameraEventMappingUpdate

        update = CameraEventMappingUpdate(
            status=False,
            description="Updated description"
        )
        assert update.status is False
        assert update.description == "Updated description"
        assert update.name_event is None

    def test_camera_event_mapping_update_with_presets(self):
        """Test: CameraEventMappingUpdate with presets"""
        from app.schemas.integration import CameraEventMappingUpdate, CameraEventPresetCreate

        preset = CameraEventPresetCreate(cam_id=1, category="PTZ")
        update = CameraEventMappingUpdate(
            camera_presets=[preset]
        )
        assert len(update.camera_presets) == 1
