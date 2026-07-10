"""
Tests for Event Response Schema changes
Phase 6: PRD_Event_Device_Refactoring.md

Event Response Schema에서 device nested 객체와 device_description을 반환합니다.
- device: Optional[DeviceNestedResponse] = None (Device 삭제 시 null)
- device_description: Optional[str] = None (Device 정보 스냅샷)
"""
import pytest
from typing import get_type_hints, get_origin, get_args, Union
from pydantic import ValidationError


class TestDetectionEventResponseHasDevice:
    """DetectionEventResponse device 필드 테스트"""

    def test_detection_event_response_has_device(self):
        """DetectionEventResponse는 device 필드를 가져야 한다"""
        from app.schemas.event import DetectionEventResponse

        schema_fields = DetectionEventResponse.model_fields

        assert 'device' in schema_fields, "DetectionEventResponse must have device field"

    def test_detection_event_response_has_device_description(self):
        """DetectionEventResponse는 device_description 필드를 가져야 한다"""
        from app.schemas.event import DetectionEventResponse

        schema_fields = DetectionEventResponse.model_fields

        assert 'device_description' in schema_fields, "DetectionEventResponse must have device_description field"

    def test_detection_event_response_device_is_optional(self):
        """device 필드는 Optional이어야 한다 (Device 삭제 시 null)"""
        from app.schemas.event import DetectionEventResponse
        from app.schemas.device import DeviceNestedResponse

        # device 필드가 Optional인지 확인
        device_field = DetectionEventResponse.model_fields['device']
        # annotation이 Optional[DeviceNestedResponse] 또는 Union[DeviceNestedResponse, None]이어야 함
        assert device_field.default is None, "device field must default to None"

    def test_detection_event_response_device_description_is_optional(self):
        """device_description 필드는 Optional이어야 한다"""
        from app.schemas.event import DetectionEventResponse

        desc_field = DetectionEventResponse.model_fields['device_description']
        assert desc_field.default is None, "device_description field must default to None"


class TestMalfunctionEventResponseHasDevice:
    """MalfunctionEventResponse device 필드 테스트"""

    def test_malfunction_event_response_has_device(self):
        """MalfunctionEventResponse는 device 필드를 가져야 한다"""
        from app.schemas.event import MalfunctionEventResponse

        schema_fields = MalfunctionEventResponse.model_fields

        assert 'device' in schema_fields, "MalfunctionEventResponse must have device field"

    def test_malfunction_event_response_has_device_description(self):
        """MalfunctionEventResponse는 device_description 필드를 가져야 한다"""
        from app.schemas.event import MalfunctionEventResponse

        schema_fields = MalfunctionEventResponse.model_fields

        assert 'device_description' in schema_fields, "MalfunctionEventResponse must have device_description field"


class TestConnectionEventResponseHasDevice:
    """ConnectionEventResponse device 필드 테스트"""

    def test_connection_event_response_has_device(self):
        """ConnectionEventResponse는 device 필드를 가져야 한다"""
        from app.schemas.event import ConnectionEventResponse

        schema_fields = ConnectionEventResponse.model_fields

        assert 'device' in schema_fields, "ConnectionEventResponse must have device field"

    def test_connection_event_response_has_device_description(self):
        """ConnectionEventResponse는 device_description 필드를 가져야 한다"""
        from app.schemas.event import ConnectionEventResponse

        schema_fields = ConnectionEventResponse.model_fields

        assert 'device_description' in schema_fields, "ConnectionEventResponse must have device_description field"


class TestEventResponseValidation:
    """Event Response 유효성 검증 테스트"""

    def test_detection_event_response_with_device(self):
        """DetectionEventResponse는 device nested 객체를 포함할 수 있다"""
        from app.schemas.event import DetectionEventResponse
        from datetime import datetime

        # Device가 있는 경우
        # PRD v2.1: group_event, controller, sensor, type_device 필드 제거됨
        valid_data = {
            'id': 1,
            'category_event': 'detection',
            'type_event': 'Intrusion',
            'device_id': 101,
            'sequence': 1,
            'action_reported': 'False',
            'result': 'PIR_SENSOR',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'device': {
                'id': 101,
                'number_device': 1,
                'group_device': 1,
                'name_device': 'Sensor-A-1',
                'type_device': 'Fence',
                'status': 'ACTIVATED'
            },
            'device_description': '[Fence] Sensor-A-1 (number: 1, id: 101)'
        }

        response = DetectionEventResponse(**valid_data)
        assert response.device is not None
        assert response.device.id == 101
        assert response.device_description == '[Fence] Sensor-A-1 (number: 1, id: 101)'

    def test_detection_event_response_without_device(self):
        """DetectionEventResponse는 device가 null일 수 있다 (Device 삭제 후)"""
        from app.schemas.event import DetectionEventResponse
        from datetime import datetime

        # Device가 삭제된 경우
        # PRD v2.1: group_event, controller, sensor, type_device 필드 제거됨
        valid_data = {
            'id': 1,
            'category_event': 'detection',
            'type_event': 'Intrusion',
            'device_id': None,  # Device 삭제됨
            'sequence': 1,
            'action_reported': 'False',
            'result': 'PIR_SENSOR',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'device': None,  # Device 삭제됨
            'device_description': '[Fence] Sensor-A-1 (number: 1, id: 101)'  # 스냅샷은 유지
        }

        response = DetectionEventResponse(**valid_data)
        assert response.device is None
        assert response.device_description == '[Fence] Sensor-A-1 (number: 1, id: 101)'
