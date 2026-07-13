"""
Tests for Event Request Schema changes
Phase 5: PRD_Event_Device_Refactoring.md

Event Create Schema에서 device_id를 사용하도록 변경합니다.
- controller, sensor, type_device 필드 제거
- device_id 필드 추가
"""
import pytest
from pydantic import ValidationError


class TestDetectionEventCreateHasDeviceId:
    """DetectionEventCreate device_id 필드 테스트"""

    def test_detection_event_create_has_device_id(self):
        """DetectionEventCreate는 device_id 필드를 가져야 한다"""
        from app.schemas.event import DetectionEventCreate

        schema_fields = DetectionEventCreate.model_fields

        assert 'device_id' in schema_fields, "DetectionEventCreate must have device_id field"

    def test_detection_event_create_no_controller_field(self):
        """DetectionEventCreate는 controller 필드가 없어야 한다"""
        from app.schemas.event import DetectionEventCreate

        schema_fields = DetectionEventCreate.model_fields

        assert 'controller' not in schema_fields, "DetectionEventCreate must not have controller field"

    def test_detection_event_create_no_sensor_field(self):
        """DetectionEventCreate는 sensor 필드가 없어야 한다"""
        from app.schemas.event import DetectionEventCreate

        schema_fields = DetectionEventCreate.model_fields

        assert 'sensor' not in schema_fields, "DetectionEventCreate must not have sensor field"

    def test_detection_event_create_no_type_device_field(self):
        """DetectionEventCreate는 type_device 필드가 없어야 한다"""
        from app.schemas.event import DetectionEventCreate

        schema_fields = DetectionEventCreate.model_fields

        assert 'type_device' not in schema_fields, "DetectionEventCreate must not have type_device field"

    def test_detection_event_create_with_device_id_validation(self):
        """DetectionEventCreate는 device_id로 유효성 검증이 되어야 한다"""
        from app.schemas.event import DetectionEventCreate

        # 유효한 데이터로 생성
        valid_data = {
            'group_event': 'TEST_GROUP',
            'type_event': 'Intrusion',
            'device_id': 1,
            'sequence': 1,
            'action_reported': 'False',
            'result': 'PIR_SENSOR'
        }

        schema = DetectionEventCreate(**valid_data)
        assert schema.device_id == 1


class TestMalfunctionEventCreateHasDeviceId:
    """MalfunctionEventCreate device_id 필드 테스트"""

    def test_malfunction_event_create_has_device_id(self):
        """MalfunctionEventCreate는 device_id 필드를 가져야 한다"""
        from app.schemas.event import MalfunctionEventCreate

        schema_fields = MalfunctionEventCreate.model_fields

        assert 'device_id' in schema_fields, "MalfunctionEventCreate must have device_id field"

    def test_malfunction_event_create_no_legacy_fields(self):
        """MalfunctionEventCreate는 레거시 필드가 없어야 한다"""
        from app.schemas.event import MalfunctionEventCreate

        schema_fields = MalfunctionEventCreate.model_fields

        assert 'controller' not in schema_fields, "MalfunctionEventCreate must not have controller field"
        assert 'sensor' not in schema_fields, "MalfunctionEventCreate must not have sensor field"
        assert 'type_device' not in schema_fields, "MalfunctionEventCreate must not have type_device field"

    def test_malfunction_event_create_with_device_id_validation(self):
        """MalfunctionEventCreate는 device_id로 유효성 검증이 되어야 한다"""
        from app.schemas.event import MalfunctionEventCreate

        valid_data = {
            'group_event': 'TEST_GROUP',
            'type_event': 'Fault',
            'device_id': 1,
            'sequence': 1,
            'action_reported': 'False',
            'reason': 'FAULT_FENCE',
            'first_start': 0,
            'first_end': 100,
            'second_start': 0,
            'second_end': 100
        }

        schema = MalfunctionEventCreate(**valid_data)
        assert schema.device_id == 1


class TestConnectionEventCreateHasDeviceId:
    """ConnectionEventCreate device_id 필드 테스트"""

    def test_connection_event_create_has_device_id(self):
        """ConnectionEventCreate는 device_id 필드를 가져야 한다"""
        from app.schemas.event import ConnectionEventCreate

        schema_fields = ConnectionEventCreate.model_fields

        assert 'device_id' in schema_fields, "ConnectionEventCreate must have device_id field"

    def test_connection_event_create_no_legacy_fields(self):
        """ConnectionEventCreate는 레거시 필드가 없어야 한다"""
        from app.schemas.event import ConnectionEventCreate

        schema_fields = ConnectionEventCreate.model_fields

        assert 'controller' not in schema_fields, "ConnectionEventCreate must not have controller field"
        assert 'sensor' not in schema_fields, "ConnectionEventCreate must not have sensor field"
        assert 'type_device' not in schema_fields, "ConnectionEventCreate must not have type_device field"

    def test_connection_event_create_with_device_id_validation(self):
        """ConnectionEventCreate는 device_id로 유효성 검증이 되어야 한다"""
        from app.schemas.event import ConnectionEventCreate

        valid_data = {
            'group_event': 'TEST_GROUP',
            'type_event': 'Connection',
            'device_id': 1,
            'sequence': 1
        }

        schema = ConnectionEventCreate(**valid_data)
        assert schema.device_id == 1
