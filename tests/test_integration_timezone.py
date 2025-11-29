"""
Phase 30: Integration Model Timezone Fix Tests
PRD: docs/Integration-Model-Timezone-Fix-PRD.md

Tests to verify that Integration models use Asia/Seoul timezone consistently.
"""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.models.integration import EventMapping, CameraEventMapping
from app.config import settings

SEOUL_TZ = ZoneInfo("Asia/Seoul")


class TestEventMappingTimezone:
    """EventMapping 타임존 테스트"""

    def test_event_mapping_created_at_uses_seoul_timezone(self, test_db):
        """EventMapping created_at이 Asia/Seoul 타임존 사용"""
        now_seoul = datetime.now(SEOUL_TZ)

        mapping = EventMapping(
            name_event="Test Event",
            group_event="1",
            category_event="SENSOR_ONLY"
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # 생성 시간이 현재 서울 시간과 1분 이내 차이
        created_at_aware = mapping.created_at.replace(tzinfo=SEOUL_TZ)
        time_diff = abs((created_at_aware - now_seoul).total_seconds())
        assert time_diff < 60, f"Time difference too large: {time_diff} seconds"

    def test_event_mapping_updated_at_uses_seoul_timezone(self, test_db):
        """EventMapping updated_at이 Asia/Seoul 타임존 사용"""
        mapping = EventMapping(
            name_event="Test Event",
            group_event="1",
            category_event="SENSOR_ONLY"
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # 업데이트 수행
        now_seoul = datetime.now(SEOUL_TZ)
        mapping.name_event = "Updated Event"
        test_db.commit()
        test_db.refresh(mapping)

        # 수정 시간이 현재 서울 시간과 1분 이내 차이
        updated_at_aware = mapping.updated_at.replace(tzinfo=SEOUL_TZ)
        time_diff = abs((updated_at_aware - now_seoul).total_seconds())
        assert time_diff < 60, f"Time difference too large: {time_diff} seconds"


class TestCameraEventMappingTimezone:
    """CameraEventMapping 타임존 테스트"""

    def test_camera_event_mapping_created_at_uses_seoul_timezone(self, test_db):
        """CameraEventMapping created_at이 Asia/Seoul 타임존 사용"""
        from app.utils.enums import EnumCategoryEvent

        now_seoul = datetime.now(SEOUL_TZ)

        mapping = CameraEventMapping(
            name_event="Test Camera Event",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # 생성 시간이 현재 서울 시간과 1분 이내 차이
        created_at_aware = mapping.created_at.replace(tzinfo=SEOUL_TZ)
        time_diff = abs((created_at_aware - now_seoul).total_seconds())
        assert time_diff < 60, f"Time difference too large: {time_diff} seconds"

    def test_camera_event_mapping_updated_at_uses_seoul_timezone(self, test_db):
        """CameraEventMapping updated_at이 Asia/Seoul 타임존 사용"""
        from app.utils.enums import EnumCategoryEvent

        mapping = CameraEventMapping(
            name_event="Test Camera Event",
            group_event="1",
            category_event=EnumCategoryEvent.FENCE_SENSOR_ONLY
        )
        test_db.add(mapping)
        test_db.commit()
        test_db.refresh(mapping)

        # 업데이트 수행
        now_seoul = datetime.now(SEOUL_TZ)
        mapping.name_event = "Updated Camera Event"
        test_db.commit()
        test_db.refresh(mapping)

        # 수정 시간이 현재 서울 시간과 1분 이내 차이
        updated_at_aware = mapping.updated_at.replace(tzinfo=SEOUL_TZ)
        time_diff = abs((updated_at_aware - now_seoul).total_seconds())
        assert time_diff < 60, f"Time difference too large: {time_diff} seconds"
