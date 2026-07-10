"""
Tests for DeviceNestedResponse Schema
Phase 1: PRD_Event_Device_Refactoring.md

DeviceNestedResponse는 Event 응답에서 Device 정보를 nested로 반환하기 위한 폴리모픽 스키마입니다.
Device 타입(Controller, Sensor, Camera)에 따라 다른 필드를 포함합니다.
"""
import pytest
from pydantic import ValidationError


class TestDeviceNestedResponseCommonFields:
    """DeviceNestedResponse 공통 필드 테스트"""

    def test_device_nested_response_has_common_fields(self):
        """DeviceNestedResponse는 모든 Device 타입에 공통인 필드를 가져야 한다"""
        from app.schemas.device import DeviceNestedResponse

        # 필수 공통 필드 목록
        required_common_fields = ['id', 'number_device', 'group_device', 'name_device', 'type_device', 'status']
        optional_common_fields = ['version']

        schema_fields = DeviceNestedResponse.model_fields

        # 필수 공통 필드 존재 확인
        for field in required_common_fields:
            assert field in schema_fields, f"Missing required common field: {field}"

        # 선택적 공통 필드 존재 확인
        for field in optional_common_fields:
            assert field in schema_fields, f"Missing optional common field: {field}"

    def test_device_nested_response_common_fields_validation(self):
        """DeviceNestedResponse 공통 필드 타입 검증"""
        from app.schemas.device import DeviceNestedResponse

        # 유효한 공통 필드로 인스턴스 생성
        data = {
            'id': 1,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Test Device',
            'type_device': 'Controller',
            'version': 'v1.0.0',
            'status': 'ACTIVATED'
        }

        response = DeviceNestedResponse(**data)

        assert response.id == 1
        assert response.number_device == 1
        assert response.group_device == 1
        assert response.name_device == 'Test Device'
        assert response.type_device == 'Controller'
        assert response.version == 'v1.0.0'
        assert response.status == 'ACTIVATED'

    def test_device_nested_response_version_nullable(self):
        """version 필드는 nullable이어야 한다 (PRD v1.2)"""
        from app.schemas.device import DeviceNestedResponse

        data = {
            'id': 1,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Test Device',
            'type_device': 'Controller',
            'version': None,  # nullable
            'status': 'ACTIVATED'
        }

        response = DeviceNestedResponse(**data)
        assert response.version is None


class TestDeviceNestedResponseControllerFields:
    """DeviceNestedResponse Controller 전용 필드 테스트"""

    def test_device_nested_response_controller_fields(self):
        """DeviceNestedResponse는 Controller 전용 필드를 가져야 한다"""
        from app.schemas.device import DeviceNestedResponse

        controller_fields = ['ip_address', 'ip_port']
        schema_fields = DeviceNestedResponse.model_fields

        for field in controller_fields:
            assert field in schema_fields, f"Missing Controller field: {field}"

    def test_device_nested_response_controller_fields_optional(self):
        """Controller 전용 필드는 Optional이어야 한다 (다른 타입에서는 None)"""
        from app.schemas.device import DeviceNestedResponse

        # Controller 타입일 때
        controller_data = {
            'id': 1,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Controller-A',
            'type_device': 'Controller',
            'status': 'ACTIVATED',
            'ip_address': '192.168.1.100',
            'ip_port': 8001
        }

        response = DeviceNestedResponse(**controller_data)
        assert response.ip_address == '192.168.1.100'
        assert response.ip_port == 8001

    def test_device_nested_response_controller_fields_none_for_other_types(self):
        """Controller 필드는 다른 타입에서 None일 수 있다"""
        from app.schemas.device import DeviceNestedResponse

        # Sensor 타입 - Controller 필드 없음
        sensor_data = {
            'id': 101,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Sensor-A-1',
            'type_device': 'Fence',
            'status': 'ACTIVATED',
            'controller_id': 1
        }

        response = DeviceNestedResponse(**sensor_data)
        assert response.ip_address is None
        assert response.ip_port is None


class TestDeviceNestedResponseSensorFields:
    """DeviceNestedResponse Sensor 전용 필드 테스트"""

    def test_device_nested_response_sensor_fields(self):
        """DeviceNestedResponse는 Sensor 전용 필드를 가져야 한다"""
        from app.schemas.device import DeviceNestedResponse

        sensor_fields = ['controller_id']
        schema_fields = DeviceNestedResponse.model_fields

        for field in sensor_fields:
            assert field in schema_fields, f"Missing Sensor field: {field}"

    def test_device_nested_response_sensor_fields_validation(self):
        """Sensor 전용 필드 타입 검증"""
        from app.schemas.device import DeviceNestedResponse

        sensor_data = {
            'id': 101,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Sensor-A-1',
            'type_device': 'Fence',
            'status': 'ACTIVATED',
            'controller_id': 1
        }

        response = DeviceNestedResponse(**sensor_data)
        assert response.controller_id == 1

    def test_device_nested_response_sensor_fields_none_for_other_types(self):
        """Sensor 필드는 다른 타입에서 None일 수 있다"""
        from app.schemas.device import DeviceNestedResponse

        # Controller 타입 - controller_id 없음
        controller_data = {
            'id': 1,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Controller-A',
            'type_device': 'Controller',
            'status': 'ACTIVATED',
            'ip_address': '192.168.1.100',
            'ip_port': 8001
        }

        response = DeviceNestedResponse(**controller_data)
        assert response.controller_id is None


class TestDeviceNestedResponseCameraFields:
    """DeviceNestedResponse Camera 전용 필드 테스트"""

    def test_device_nested_response_camera_fields(self):
        """DeviceNestedResponse는 Camera 전용 필드를 가져야 한다"""
        from app.schemas.device import DeviceNestedResponse

        # Camera는 Controller와 ip_address, ip_port를 공유하고, 추가 필드가 있음
        camera_specific_fields = ['rtsp_uri', 'rtsp_port', 'mode', 'category', 'is_record']
        schema_fields = DeviceNestedResponse.model_fields

        for field in camera_specific_fields:
            assert field in schema_fields, f"Missing Camera field: {field}"

    def test_device_nested_response_camera_fields_validation(self):
        """Camera 전용 필드 타입 검증"""
        from app.schemas.device import DeviceNestedResponse

        camera_data = {
            'id': 201,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Camera-A-1',
            'type_device': 'IpCamera',
            'status': 'ACTIVATED',
            'ip_address': '192.168.1.200',
            'ip_port': 80,
            'rtsp_uri': 'rtsp://192.168.1.200:554/stream1',
            'rtsp_port': 554,
            'mode': 'ONVIF',
            'category': 'PTZ',
            'is_record': True
        }

        response = DeviceNestedResponse(**camera_data)
        assert response.rtsp_uri == 'rtsp://192.168.1.200:554/stream1'
        assert response.rtsp_port == 554
        assert response.mode == 'ONVIF'
        assert response.category == 'PTZ'
        assert response.is_record is True

    def test_device_nested_response_camera_fields_none_for_other_types(self):
        """Camera 필드는 다른 타입에서 None/False일 수 있다"""
        from app.schemas.device import DeviceNestedResponse

        # Sensor 타입 - Camera 필드 없음
        sensor_data = {
            'id': 101,
            'number_device': 1,
            'group_device': 1,
            'name_device': 'Sensor-A-1',
            'type_device': 'Fence',
            'status': 'ACTIVATED',
            'controller_id': 1
        }

        response = DeviceNestedResponse(**sensor_data)
        assert response.rtsp_uri is None
        assert response.rtsp_port is None
        assert response.mode is None
        assert response.category is None
        # is_record의 기본값은 False 또는 None
        assert response.is_record in (None, False)


class TestDeviceNestedResponseFromAttributes:
    """DeviceNestedResponse ORM 모델 변환 테스트"""

    def test_device_nested_response_from_attributes_config(self):
        """DeviceNestedResponse는 from_attributes=True 설정이 있어야 한다"""
        from app.schemas.device import DeviceNestedResponse

        config = DeviceNestedResponse.model_config
        assert config.get('from_attributes') is True, "DeviceNestedResponse must have from_attributes=True"
