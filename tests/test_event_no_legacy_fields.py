"""
Tests for Event Legacy Field Removal
Phase 12: PRD_Event_Device_Refactoring.md v1.1

Verifies that legacy fields (controller, sensor, type_device) are removed
from Event models and replaced by device_id FK.
"""
import pytest
from sqlalchemy import inspect


class TestDetectionEventNoLegacyFields:
    """DetectionEvent에서 레거시 필드가 제거되었는지 확인"""

    def test_detection_event_has_device_id(self, test_db):
        """DetectionEvent에 device_id 필드가 있어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'device_id' in columns

    def test_detection_event_has_device_description(self, test_db):
        """DetectionEvent에 device_description 필드가 있어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'device_description' in columns

    # NOTE: Phase 12에서는 아직 legacy 필드가 남아있음
    # 마이그레이션 완료 후 아래 테스트들을 활성화하여 제거 확인
    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_detection_event_no_controller_column(self, test_db):
        """DetectionEvent에 controller 컬럼이 없어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'controller' not in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_detection_event_no_sensor_column(self, test_db):
        """DetectionEvent에 sensor 컬럼이 없어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'sensor' not in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_detection_event_no_type_device_column(self, test_db):
        """DetectionEvent에 type_device 컬럼이 없어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'type_device' not in columns


class TestMalfunctionEventNoLegacyFields:
    """MalfunctionEvent에서 레거시 필드가 제거되었는지 확인"""

    def test_malfunction_event_has_device_id(self, test_db):
        """MalfunctionEvent에 device_id 필드가 있어야 한다"""
        from app.models.event import MalfunctionEvent

        inspector = inspect(MalfunctionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'device_id' in columns

    def test_malfunction_event_has_device_description(self, test_db):
        """MalfunctionEvent에 device_description 필드가 있어야 한다"""
        from app.models.event import MalfunctionEvent

        inspector = inspect(MalfunctionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'device_description' in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_malfunction_event_no_controller_column(self, test_db):
        """MalfunctionEvent에 controller 컬럼이 없어야 한다"""
        from app.models.event import MalfunctionEvent

        inspector = inspect(MalfunctionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'controller' not in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_malfunction_event_no_sensor_column(self, test_db):
        """MalfunctionEvent에 sensor 컬럼이 없어야 한다"""
        from app.models.event import MalfunctionEvent

        inspector = inspect(MalfunctionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'sensor' not in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_malfunction_event_no_type_device_column(self, test_db):
        """MalfunctionEvent에 type_device 컬럼이 없어야 한다"""
        from app.models.event import MalfunctionEvent

        inspector = inspect(MalfunctionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'type_device' not in columns


class TestConnectionEventNoLegacyFields:
    """ConnectionEvent에서 레거시 필드가 제거되었는지 확인"""

    def test_connection_event_has_device_id(self, test_db):
        """ConnectionEvent에 device_id 필드가 있어야 한다"""
        from app.models.event import ConnectionEvent

        inspector = inspect(ConnectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'device_id' in columns

    def test_connection_event_has_device_description(self, test_db):
        """ConnectionEvent에 device_description 필드가 있어야 한다"""
        from app.models.event import ConnectionEvent

        inspector = inspect(ConnectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'device_description' in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_connection_event_no_controller_column(self, test_db):
        """ConnectionEvent에 controller 컬럼이 없어야 한다"""
        from app.models.event import ConnectionEvent

        inspector = inspect(ConnectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'controller' not in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_connection_event_no_sensor_column(self, test_db):
        """ConnectionEvent에 sensor 컬럼이 없어야 한다"""
        from app.models.event import ConnectionEvent

        inspector = inspect(ConnectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'sensor' not in columns

    @pytest.mark.skip(reason="Legacy fields still present for migration compatibility")
    def test_connection_event_no_type_device_column(self, test_db):
        """ConnectionEvent에 type_device 컬럼이 없어야 한다"""
        from app.models.event import ConnectionEvent

        inspector = inspect(ConnectionEvent)
        columns = [col.key for col in inspector.mapper.columns]

        assert 'type_device' not in columns


class TestLegacyFieldsAreNullable:
    """마이그레이션 호환성을 위해 레거시 필드가 nullable인지 확인"""

    @pytest.mark.skip(reason="Legacy column already removed in PRD v2.1; nullable check obsolete")
    def test_detection_event_controller_is_nullable(self, test_db):
        """DetectionEvent.controller가 nullable이어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        for col in inspector.mapper.columns:
            if col.key == 'controller':
                assert col.nullable is True
                return
        pytest.fail("controller column not found")

    @pytest.mark.skip(reason="Legacy column already removed in PRD v2.1; nullable check obsolete")
    def test_detection_event_sensor_is_nullable(self, test_db):
        """DetectionEvent.sensor가 nullable이어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        for col in inspector.mapper.columns:
            if col.key == 'sensor':
                assert col.nullable is True
                return
        pytest.fail("sensor column not found")

    @pytest.mark.skip(reason="Legacy column already removed in PRD v2.1; nullable check obsolete")
    def test_detection_event_type_device_is_nullable(self, test_db):
        """DetectionEvent.type_device가 nullable이어야 한다"""
        from app.models.event import DetectionEvent

        inspector = inspect(DetectionEvent)
        for col in inspector.mapper.columns:
            if col.key == 'type_device':
                assert col.nullable is True
                return
        pytest.fail("type_device column not found")
