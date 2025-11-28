"""
Phase 29: CameraEventMapping API 통합 테스트
PRD: CameraEventMapping-Test-PRD.md
TDD Implementation
"""
import pytest
import asyncio
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


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


# ============================================
# Phase 29.1: POST 생성 테스트 (TC-01 ~ TC-04)
# ============================================

class TestCameraEventMappingIntegrationPost:
    """POST 생성 테스트 - PRD TC-01 ~ TC-04"""

    def test_tc01_create_basic_with_two_cameras(self, test_db):
        """TC-01: 기본 생성 - 이벤트1 (SENSOR_ONLY, 2개 카메라)"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import (
            CameraEventMappingCreate,
            CameraEventPresetCreate,
            CameraUrls
        )

        # PRD 테스트 데이터 - 이벤트1
        preset1 = CameraEventPresetCreate(
            cam_id=1,
            urls=CameraUrls(
                live="rtsp://admin:sensor6500*@123.141.236.253:2554/video1",
                record="rtsp://admin:sensor6500*@123.141.236.253:2554/video1/record"
            ),
            category="PTZ",
            preset_id="2",
            preset_time=3,
            home_preset=1,
            home_time=3
        )
        preset2 = CameraEventPresetCreate(
            cam_id=2,
            urls=CameraUrls(
                live="rtsp://admin:sensor6500*@123.141.236.254:2554/video1",
                record="rtsp://admin:sensor6500*@123.141.236.254:2554/video1/record"
            ),
            category="PTZ",
            preset_id="3",
            preset_time=5,
            home_preset=1,
            home_time=5
        )

        payload = CameraEventMappingCreate(
            name_event="이벤트1",
            group_event="1",
            category_event="FENCE_SENSOR_ONLY",
            description="센서 단독 이벤트 - 테스트용",
            status=True,
            camera_presets=[preset1, preset2]
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        # 검증
        assert response.success is True
        assert response.message == "Camera event mapping created successfully"
        assert response.data.name_event == "이벤트1"
        assert response.data.group_event == "1"
        assert response.data.category_event == "FENCE_SENSOR_ONLY"
        assert response.data.description == "센서 단독 이벤트 - 테스트용"
        assert response.data.status is True
        assert len(response.data.camera_presets) == 2

        # 첫 번째 카메라 프리셋 검증
        preset1_resp = response.data.camera_presets[0]
        assert preset1_resp.cam_id == 1
        assert preset1_resp.urls is not None
        assert preset1_resp.urls.live == "rtsp://admin:sensor6500*@123.141.236.253:2554/video1"
        assert preset1_resp.urls.record == "rtsp://admin:sensor6500*@123.141.236.253:2554/video1/record"
        assert preset1_resp.category == "PTZ"
        assert preset1_resp.preset_id == "2"
        assert preset1_resp.preset_time == 3
        assert preset1_resp.home_preset == 1
        assert preset1_resp.home_time == 3

        # 두 번째 카메라 프리셋 검증
        preset2_resp = response.data.camera_presets[1]
        assert preset2_resp.cam_id == 2
        assert preset2_resp.urls is not None
        assert preset2_resp.urls.live == "rtsp://admin:sensor6500*@123.141.236.254:2554/video1"
        assert preset2_resp.preset_time == 5

    def test_tc02_create_without_presets(self, test_db):
        """TC-02: 프리셋 없이 생성 - 이벤트5 (ETC, 빈 카메라)"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import CameraEventMappingCreate

        payload = CameraEventMappingCreate(
            name_event="이벤트5",
            group_event="5",
            category_event="NONE",
            description="카메라 프리셋 없는 기타 이벤트",
            status=True,
            camera_presets=[]
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.name_event == "이벤트5"
        assert response.data.category_event == "NONE"
        assert len(response.data.camera_presets) == 0

    def test_tc03_create_without_urls(self, test_db):
        """TC-03: urls 없이 생성 (urls optional)"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import CameraEventMappingCreate, CameraEventPresetCreate

        preset = CameraEventPresetCreate(
            cam_id=10,
            category="FIXED"
            # urls is optional, not provided
        )

        payload = CameraEventMappingCreate(
            name_event="URL 없는 이벤트",
            group_event="6",
            category_event="FENCE_SENSOR_ONLY",
            status=True,
            camera_presets=[preset]
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data.camera_presets) == 1
        assert response.data.camera_presets[0].cam_id == 10
        assert response.data.camera_presets[0].urls is None

    def test_tc04_create_with_live_only_urls(self, test_db):
        """TC-04: live만 있는 urls로 생성"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import (
            CameraEventMappingCreate,
            CameraEventPresetCreate,
            CameraUrls
        )

        preset = CameraEventPresetCreate(
            cam_id=11,
            urls=CameraUrls(
                live="rtsp://192.168.1.200:554/live"
                # record is optional, not provided
            ),
            category="PTZ",
            preset_id="1",
            preset_time=5,
            home_preset=1,
            home_time=5
        )

        payload = CameraEventMappingCreate(
            name_event="Live만 있는 이벤트",
            group_event="7",
            category_event="SENSOR_WITH_CAMERA",
            status=True,
            camera_presets=[preset]
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data.camera_presets) == 1
        assert response.data.camera_presets[0].urls is not None
        assert response.data.camera_presets[0].urls.live == "rtsp://192.168.1.200:554/live"
        assert response.data.camera_presets[0].urls.record is None


# ============================================
# Phase 29.2: GET 목록 조회 테스트 (TC-05 ~ TC-10)
# ============================================

class TestCameraEventMappingIntegrationGetList:
    """GET 목록 조회 테스트 - PRD TC-05 ~ TC-10"""

    def _create_test_data(self, test_db):
        """테스트용 데이터 생성 헬퍼"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent

        # 이벤트1 - SENSOR_ONLY
        mapping1 = CameraEventMapping(
            name_event="이벤트1",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
            description="센서 단독",
            status=True
        )
        test_db.add(mapping1)
        test_db.commit()
        test_db.refresh(mapping1)

        preset1 = CameraEventPreset(
            mapping_id=mapping1.id,
            cam_id=1,
            url_live="rtsp://test:pass@192.168.1.1:554/live",
            category="PTZ",
            preset_time=3
        )
        test_db.add(preset1)

        # 이벤트2 - SENSOR_WITH_CAMERA
        mapping2 = CameraEventMapping(
            name_event="이벤트2",
            group_event="2",
            category_event=EnumCategoryEvent.SENSOR_WITH_CAMERA,
            description="센서+카메라",
            status=True
        )
        test_db.add(mapping2)

        # 이벤트3 - SENSOR_ONLY, 비활성
        mapping3 = CameraEventMapping(
            name_event="이벤트3",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
            description="비활성 센서",
            status=False
        )
        test_db.add(mapping3)

        test_db.commit()
        return [mapping1, mapping2, mapping3]

    def test_tc05_get_all_list(self, test_db):
        """TC-05: 전체 목록 조회"""
        from app.routers.camera_event_mappings import get_camera_event_mappings

        self._create_test_data(test_db)

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
        assert len(response.data) == 3
        assert response.pagination.total == 3

    def test_tc06_pagination(self, test_db):
        """TC-06: 페이지네이션 (page=1, limit=2)"""
        from app.routers.camera_event_mappings import get_camera_event_mappings

        self._create_test_data(test_db)

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=2,
            group_event=None,
            category_event=None,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) == 2
        assert response.pagination.total == 3
        assert response.pagination.page == 1
        assert response.pagination.limit == 2
        assert response.pagination.total_pages == 2

    def test_tc07_filter_by_category_event(self, test_db):
        """TC-07: category_event 필터 (SENSOR_ONLY)"""
        from app.routers.camera_event_mappings import get_camera_event_mappings

        self._create_test_data(test_db)

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=20,
            group_event=None,
            category_event="FENCE_SENSOR_ONLY",
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) == 2
        for m in response.data:
            assert m.category_event == "FENCE_SENSOR_ONLY"

    def test_tc08_filter_by_group_event(self, test_db):
        """TC-08: group_event 필터"""
        from app.routers.camera_event_mappings import get_camera_event_mappings

        self._create_test_data(test_db)

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=20,
            group_event="1",
            category_event=None,
            status_filter=None,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) == 2
        for m in response.data:
            assert m.group_event == "1"

    def test_tc09_filter_by_status(self, test_db):
        """TC-09: status 필터"""
        from app.routers.camera_event_mappings import get_camera_event_mappings

        self._create_test_data(test_db)

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

        assert response.success is True
        assert len(response.data) == 2
        for m in response.data:
            assert m.status is True

    def test_tc10_combined_filters(self, test_db):
        """TC-10: 복합 필터"""
        from app.routers.camera_event_mappings import get_camera_event_mappings

        self._create_test_data(test_db)

        mock_user = MagicMock()
        response = asyncio.run(get_camera_event_mappings(
            page=1,
            limit=5,
            group_event="1",
            category_event="FENCE_SENSOR_ONLY",
            status_filter=True,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0].name_event == "이벤트1"
        assert response.data[0].group_event == "1"
        assert response.data[0].category_event == "FENCE_SENSOR_ONLY"
        assert response.data[0].status is True


# ============================================
# Phase 29.3: GET 단일 조회 테스트 (TC-11 ~ TC-12)
# ============================================

class TestCameraEventMappingIntegrationGetDetail:
    """GET 단일 조회 테스트 - PRD TC-11 ~ TC-12"""

    def test_tc11_get_by_id(self, test_db):
        """TC-11: ID로 조회"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import get_camera_event_mapping

        # 데이터 생성
        mapping = CameraEventMapping(
            name_event="테스트 이벤트",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
            description="테스트용",
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        preset = CameraEventPreset(
            mapping_id=mapping.id,
            cam_id=1,
            url_live="rtsp://test@192.168.1.1:554/live",
            url_record="rtsp://test@192.168.1.1:554/record",
            category="PTZ",
            preset_time=5
        )
        test_db.add(preset)
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
        assert response.data.name_event == "테스트 이벤트"
        assert len(response.data.camera_presets) == 1
        assert response.data.camera_presets[0].urls.live == "rtsp://test@192.168.1.1:554/live"

    def test_tc12_get_not_found(self, test_db):
        """TC-12: 존재하지 않는 ID 조회 (404)"""
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


# ============================================
# Phase 29.4: PUT 전체 수정 테스트 (TC-13)
# ============================================

class TestCameraEventMappingIntegrationPut:
    """PUT 전체 수정 테스트 - PRD TC-13"""

    def test_tc13_update_full(self, test_db):
        """TC-13: 전체 필드 수정"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import update_camera_event_mapping_full
        from app.schemas.integration import (
            CameraEventMappingCreate,
            CameraEventPresetCreate,
            CameraUrls
        )

        # 원본 데이터 생성
        mapping = CameraEventMapping(
            name_event="원본 이벤트",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
            description="원본 설명",
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # 수정 데이터
        preset = CameraEventPresetCreate(
            cam_id=100,
            urls=CameraUrls(
                live="rtsp://updated:pass@10.0.0.1:554/live",
                record="rtsp://updated:pass@10.0.0.1:554/record"
            ),
            category="FIXED",
            preset_time=0,
            home_preset=0,
            home_time=0
        )
        update_payload = CameraEventMappingCreate(
            name_event="수정된 이벤트1",
            group_event="1-updated",
            category_event="SENSOR_WITH_CAMERA",
            description="수정된 설명",
            status=False,
            camera_presets=[preset]
        )

        mock_user = MagicMock()
        response = asyncio.run(update_camera_event_mapping_full(
            mapping_id=mapping.id,
            mapping=update_payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.name_event == "수정된 이벤트1"
        assert response.data.group_event == "1-updated"
        assert response.data.category_event == "SENSOR_WITH_CAMERA"
        assert response.data.description == "수정된 설명"
        assert response.data.status is False
        assert len(response.data.camera_presets) == 1
        assert response.data.camera_presets[0].cam_id == 100


# ============================================
# Phase 29.5: PATCH 부분 수정 테스트 (TC-14 ~ TC-16)
# ============================================

class TestCameraEventMappingIntegrationPatch:
    """PATCH 부분 수정 테스트 - PRD TC-14 ~ TC-16"""

    def test_tc14_patch_status_only(self, test_db):
        """TC-14: status만 수정"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import update_camera_event_mapping_partial
        from app.schemas.integration import CameraEventMappingUpdate

        mapping = CameraEventMapping(
            name_event="테스트 이벤트",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        update_payload = CameraEventMappingUpdate(status=False)

        mock_user = MagicMock()
        response = asyncio.run(update_camera_event_mapping_partial(
            mapping_id=mapping.id,
            mapping=update_payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.status is False
        assert response.data.name_event == "테스트 이벤트"  # 변경 안됨

    def test_tc15_patch_description_only(self, test_db):
        """TC-15: description만 수정"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import update_camera_event_mapping_partial
        from app.schemas.integration import CameraEventMappingUpdate

        mapping = CameraEventMapping(
            name_event="테스트 이벤트",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
            description="원본 설명",
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        update_payload = CameraEventMappingUpdate(description="부분 수정된 설명")

        mock_user = MagicMock()
        response = asyncio.run(update_camera_event_mapping_partial(
            mapping_id=mapping.id,
            mapping=update_payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert response.data.description == "부분 수정된 설명"
        assert response.data.status is True  # 변경 안됨

    def test_tc16_patch_camera_presets(self, test_db):
        """TC-16: camera_presets 교체"""
        from app.models.integration import CameraEventMapping, CameraEventPreset
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import update_camera_event_mapping_partial
        from app.schemas.integration import (
            CameraEventMappingUpdate,
            CameraEventPresetCreate,
            CameraUrls
        )

        mapping = CameraEventMapping(
            name_event="테스트 이벤트",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
            status=True
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # 원본 프리셋 추가
        preset = CameraEventPreset(
            mapping_id=mapping.id,
            cam_id=1,
            category="PTZ"
        )
        test_db.add(preset)
        test_db.commit()
        test_db.refresh(mapping)

        # 새 프리셋으로 교체
        new_preset = CameraEventPresetCreate(
            cam_id=99,
            urls=CameraUrls(
                live="rtsp://new:camera@192.168.0.99:554/ch1",
                record="rtsp://new:camera@192.168.0.99:554/ch1/rec"
            ),
            category="PTZ",
            preset_id="10",
            preset_time=15,
            home_preset=5,
            home_time=20
        )
        update_payload = CameraEventMappingUpdate(camera_presets=[new_preset])

        mock_user = MagicMock()
        response = asyncio.run(update_camera_event_mapping_partial(
            mapping_id=mapping.id,
            mapping=update_payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data.camera_presets) == 1
        assert response.data.camera_presets[0].cam_id == 99
        assert response.data.camera_presets[0].preset_time == 15


# ============================================
# Phase 29.6: DELETE 삭제 테스트 (TC-17 ~ TC-18)
# ============================================

class TestCameraEventMappingIntegrationDelete:
    """DELETE 삭제 테스트 - PRD TC-17 ~ TC-18"""

    def test_tc17_delete(self, test_db):
        """TC-17: 삭제"""
        from app.models.integration import CameraEventMapping
        from app.utils.enums import EnumCategoryEvent
        from app.routers.camera_event_mappings import delete_camera_event_mapping

        mapping = CameraEventMapping(
            name_event="삭제할 이벤트",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY,
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
        assert response.message == "Camera event mapping deleted successfully"
        assert response.data["id"] == mapping_id

        # DB에서 삭제 확인
        deleted = test_db.query(CameraEventMapping).filter(
            CameraEventMapping.id == mapping_id
        ).first()
        assert deleted is None

    def test_tc18_delete_not_found(self, test_db):
        """TC-18: 존재하지 않는 ID 삭제 (404)"""
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


# ============================================
# Phase 29.7: 에러 테스트
# ============================================

class TestCameraEventMappingIntegrationError:
    """에러 테스트"""

    def test_invalid_category_event(self, test_db):
        """유효하지 않은 category_event (422)"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import CameraEventMappingCreate
        from fastapi import HTTPException

        payload = CameraEventMappingCreate(
            name_event="잘못된 카테고리",
            group_event="X",
            category_event="INVALID_CATEGORY",
            status=True,
            camera_presets=[]
        )

        mock_user = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(create_camera_event_mapping(
                mapping=payload,
                current_user=mock_user,
                db=test_db
            ))

        assert exc_info.value.status_code == 422


# ============================================
# Phase 29.8: 대량 데이터 테스트
# ============================================

class TestCameraEventMappingIntegrationBulk:
    """대량 데이터 테스트"""

    def test_create_with_five_cameras(self, test_db):
        """다중 프리셋 생성 (5개 카메라)"""
        from app.routers.camera_event_mappings import create_camera_event_mapping
        from app.schemas.integration import (
            CameraEventMappingCreate,
            CameraEventPresetCreate,
            CameraUrls
        )

        presets = []
        for i in range(1, 6):
            preset = CameraEventPresetCreate(
                cam_id=i,
                urls=CameraUrls(
                    live=f"rtsp://admin:pass@10.0.0.{i}:554/ch1",
                    record=f"rtsp://admin:pass@10.0.0.{i}:554/ch1/rec"
                ),
                category="PTZ" if i % 2 == 1 else "FIXED",
                preset_id=str(i) if i % 2 == 1 else None,
                preset_time=5 * i,
                home_preset=i,
                home_time=10 * i
            )
            presets.append(preset)

        payload = CameraEventMappingCreate(
            name_event="대규모 이벤트",
            group_event="LARGE",
            category_event="SENSOR_WITH_AI_CAMERA",
            description="5개 카메라 프리셋 테스트",
            status=True,
            camera_presets=presets
        )

        mock_user = MagicMock()
        response = asyncio.run(create_camera_event_mapping(
            mapping=payload,
            current_user=mock_user,
            db=test_db
        ))

        assert response.success is True
        assert len(response.data.camera_presets) == 5
        for i, preset in enumerate(response.data.camera_presets, 1):
            assert preset.cam_id == i
            assert f"10.0.0.{i}" in preset.urls.live
