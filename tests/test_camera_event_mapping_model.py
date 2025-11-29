"""
TDD Tests for CameraEventMapping and CameraEventPreset Models
Phase 25.1: Model TDD Implementation
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestEnumCategoryEvent:
    """Tests for EnumCategoryEvent Enum"""

    def test_enum_category_event_exists(self):
        """Test: EnumCategoryEvent Enum이 존재하는지 검증"""
        from app.utils.enums import EnumCategoryEvent
        assert EnumCategoryEvent is not None

    def test_enum_category_event_has_all_values(self):
        """Test: EnumCategoryEvent가 모든 필수 값을 포함하는지 검증 (Phase 31 Updated)"""
        from app.utils.enums import EnumCategoryEvent

        expected_values = [
            "NONE",
            "FENCE_SENSOR_ONLY",
            "FENCE_SENSOR_WITH_MULTI_SENSOR",
            "MULTI_SENSOR_ONLY",
            "SENSOR_WITH_CAMERA",
            "SENSOR_WITH_AI_CAMERA",
            "AI_CAMERA_ONLY",
            "CAMERA_ONLY"
        ]

        actual_values = [e.value for e in EnumCategoryEvent]
        for expected in expected_values:
            assert expected in actual_values, f"Missing value: {expected}"

    def test_enum_category_event_is_string_enum(self):
        """Test: EnumCategoryEvent가 str Enum인지 검증"""
        from app.utils.enums import EnumCategoryEvent

        assert issubclass(EnumCategoryEvent, str)
        assert EnumCategoryEvent.FENCE_SENSOR_ONLY.value == "FENCE_SENSOR_ONLY"


class TestCameraEventMappingModel:
    """Tests for CameraEventMapping Model"""

    def test_camera_event_mapping_model_exists(self):
        """Test: CameraEventMapping 모델 클래스 존재 확인"""
        from app.models.integration import CameraEventMapping
        assert CameraEventMapping is not None

    def test_camera_event_mapping_has_required_fields(self):
        """Test: CameraEventMapping 필수 필드 존재 검증"""
        from app.models.integration import CameraEventMapping

        required_fields = [
            "id", "name_event", "group_event", "category_event",
            "description", "status", "created_at", "updated_at"
        ]

        mapper = CameraEventMapping.__mapper__
        column_names = [col.key for col in mapper.columns]

        for field in required_fields:
            assert field in column_names, f"Missing field: {field}"

    def test_camera_event_mapping_tablename(self):
        """Test: CameraEventMapping 테이블명 검증"""
        from app.models.integration import CameraEventMapping
        assert CameraEventMapping.__tablename__ == "camera_event_mappings"

    def test_camera_event_mapping_create(self, test_db):
        """Test: CameraEventMapping CRUD - 생성 테스트"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent

        mapping = CameraEventMapping(
            name_event="Test Mapping",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,  # Enum (Phase 31)
            description="Test description",
            status=True
        )

        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        assert mapping.id is not None
        assert mapping.name_event == "Test Mapping"
        assert mapping.group_event == "Intrusion"  # Plain string
        assert mapping.category_event == EnumCategoryEvent.FENCE_SENSOR_ONLY
        assert mapping.status is True
        assert mapping.created_at is not None
        assert mapping.updated_at is not None


# ============================================
# Phase 28.4: CameraEventPreset Model URL Columns TDD
# ============================================

class TestCameraEventPresetModel:
    """Tests for CameraEventPreset Model - Phase 28.4"""

    def test_camera_event_preset_model_exists(self):
        """Test: CameraEventPreset 모델 클래스 존재 확인"""
        from app.models.integration import CameraEventPreset
        assert CameraEventPreset is not None

    def test_camera_event_preset_has_url_columns(self):
        """Test: CameraEventPreset에 url_live, url_record 컬럼 존재 확인 (Phase 28.4)"""
        from app.models.integration import CameraEventPreset

        mapper = CameraEventPreset.__mapper__
        column_names = [col.key for col in mapper.columns]

        assert "url_live" in column_names, "Missing column: url_live"
        assert "url_record" in column_names, "Missing column: url_record"

    def test_camera_event_preset_no_rtsp_uri_column(self):
        """Test: CameraEventPreset에 rtsp_uri 컬럼 제거 확인 (Phase 28.4)"""
        from app.models.integration import CameraEventPreset

        mapper = CameraEventPreset.__mapper__
        column_names = [col.key for col in mapper.columns]

        assert "rtsp_uri" not in column_names, "rtsp_uri column should be removed"

    def test_camera_event_preset_has_required_fields(self):
        """Test: CameraEventPreset 필수 필드 존재 검증"""
        from app.models.integration import CameraEventPreset

        required_fields = [
            "id", "mapping_id", "cam_id", "url_live", "url_record", "category",
            "preset_id", "preset_time", "home_preset", "home_time"
        ]

        mapper = CameraEventPreset.__mapper__
        column_names = [col.key for col in mapper.columns]

        for field in required_fields:
            assert field in column_names, f"Missing field: {field}"

    def test_camera_event_preset_tablename(self):
        """Test: CameraEventPreset 테이블명 검증"""
        from app.models.integration import CameraEventPreset
        assert CameraEventPreset.__tablename__ == "camera_event_presets"

    def test_camera_event_preset_create_with_urls(self, test_db):
        """Test: CameraEventPreset CRUD - URL 필드 테스트 (Phase 28.4)"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent

        # Create mapping first
        mapping = CameraEventMapping(
            name_event="Test Mapping",
            group_event="Intrusion",
            category_event=EnumCategoryEvent.SENSOR_WITH_CAMERA,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # Create preset with URL fields
        preset = CameraEventPreset(
            mapping_id=mapping.id,
            cam_id=1,
            url_live="rtsp://192.168.1.100:554/live",
            url_record="rtsp://192.168.1.100:554/record",
            category="PTZ",
            preset_id="5",
            preset_time=10,
            home_preset=1,
            home_time=30
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(preset)

        assert preset.url_live == "rtsp://192.168.1.100:554/live"
        assert preset.url_record == "rtsp://192.168.1.100:554/record"


class TestCameraEventMappingPresetRelationship:
    """Tests for CameraEventMapping ↔ CameraEventPreset Relationship"""

    def test_mapping_preset_relationship(self, test_db):
        """Test: CameraEventMapping ↔ CameraEventPreset 1:N 관계 검증"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent

        # Create mapping
        mapping = CameraEventMapping(
            name_event="Test Mapping",
            group_event="Intrusion",  # Plain string
            category_event=EnumCategoryEvent.SENSOR_WITH_CAMERA,  # Enum
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # Create presets
        preset1 = CameraEventPreset(
            mapping_id=mapping.id,
            cam_id=1,
            url_live="rtsp://192.168.1.100:554/live",
            url_record="rtsp://192.168.1.100:554/record",
            category="PTZ",
            preset_id="5",
            preset_time=10,
            home_preset=1,
            home_time=30
        )
        preset2 = CameraEventPreset(
            mapping_id=mapping.id,
            cam_id=2,
            url_live="rtsp://192.168.1.101:554/live",
            category="FIXED",
            preset_time=0,
            home_preset=0,
            home_time=0
        )

        test_db.add_all([preset1, preset2])
        test_db.commit()

        # Refresh mapping to get relationship
        test_db.refresh(mapping)

        assert len(mapping.camera_presets) == 2
        assert mapping.camera_presets[0].cam_id == 1
        assert mapping.camera_presets[1].cam_id == 2

    def test_cascade_delete(self, test_db):
        """Test: CameraEventMapping 삭제 시 CameraEventPreset 연쇄 삭제 검증"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent

        # Create mapping with presets
        mapping = CameraEventMapping(
            name_event="Test Mapping",
            group_event="Fault",  # Plain string
            category_event=EnumCategoryEvent.AI_CAMERA_ONLY,  # Enum (Phase 31)
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

        # Delete mapping
        test_db.delete(mapping)
        test_db.commit()

        # Verify preset is also deleted (cascade)
        deleted_preset = test_db.query(CameraEventPreset).filter(
            CameraEventPreset.id == preset_id
        ).first()
        assert deleted_preset is None

        deleted_mapping = test_db.query(CameraEventMapping).filter(
            CameraEventMapping.id == mapping_id
        ).first()
        assert deleted_mapping is None
