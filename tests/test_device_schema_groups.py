"""
Phase 5: Device Schema Groups Tests (TDD)
PRD: PRD_Device_Structure_Refactoring.md - Section 2.3

Tests for:
- group_ids array support in Request schemas
- device_groups array in Response schemas
- group_device backward compatibility
"""
import pytest
from pydantic import ValidationError
from datetime import datetime
from typing import List, Optional

from app.schemas.device_group import DeviceGroupResponse
from app.schemas.device import (
    ControllerCreate,
    ControllerResponse,
    ControllerUpdate,
    SensorCreate,
    SensorResponse,
    SensorUpdate,
    CameraCreate,
    CameraResponse,
    CameraUpdate,
)

# Rebuild models to resolve forward references
ControllerResponse.model_rebuild()
SensorResponse.model_rebuild()
CameraResponse.model_rebuild()


class TestControllerSchemaGroupIds:
    """Controller 스키마 group_ids 테스트"""

    def test_controller_create_with_group_device_only(self):
        """ControllerCreate: group_device만 사용 (하위 호환성)"""
        controller = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502
        )
        assert controller.group_device == 1
        assert controller.group_ids is None

    def test_controller_create_with_group_ids(self):
        """ControllerCreate: group_ids 배열 사용"""
        controller = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502,
            group_ids=[1, 2, 3]
        )
        assert controller.group_ids == [1, 2, 3]

    def test_controller_create_group_ids_empty_list(self):
        """ControllerCreate: group_ids 빈 배열"""
        controller = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502,
            group_ids=[]
        )
        assert controller.group_ids == []

    def test_controller_update_with_group_ids(self):
        """ControllerUpdate: group_ids 부분 수정"""
        update = ControllerUpdate(group_ids=[2, 3])
        assert update.group_ids == [2, 3]
        assert update.group_device is None

    def test_controller_response_with_device_groups(self):
        """ControllerResponse: device_groups 배열 포함"""
        # Create mock DeviceGroupResponse objects
        groups = [
            DeviceGroupResponse(
                id=1,
                name="Group 1",
                description="First group",
                device_count=5,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            DeviceGroupResponse(
                id=2,
                name="Group 2",
                description="Second group",
                device_count=3,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        controller = ControllerResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            device_groups=groups
        )
        assert len(controller.device_groups) == 2
        assert controller.device_groups[0].name == "Group 1"

    def test_controller_response_device_groups_default_empty(self):
        """ControllerResponse: device_groups 기본값 빈 배열"""
        controller = ControllerResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert controller.device_groups == []


class TestSensorSchemaGroupIds:
    """Sensor 스키마 group_ids 테스트"""

    def test_sensor_create_with_group_ids(self):
        """SensorCreate: group_ids 배열 사용"""
        sensor = SensorCreate(
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device="Fence",
            version="1.0.0",
            status="ACTIVATED",
            controller_id=1,
            group_ids=[1, 2]
        )
        assert sensor.group_ids == [1, 2]

    def test_sensor_update_with_group_ids(self):
        """SensorUpdate: group_ids 부분 수정"""
        update = SensorUpdate(group_ids=[3, 4, 5])
        assert update.group_ids == [3, 4, 5]

    def test_sensor_response_with_device_groups(self):
        """SensorResponse: device_groups 배열 포함"""
        groups = [
            DeviceGroupResponse(
                id=1,
                name="Sensor Group",
                description="Sensors",
                device_count=10,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        sensor = SensorResponse(
            id=1,
            number_device=101,
            group_device=1,
            name_device="Test Sensor",
            type_device="Fence",
            version="1.0.0",
            status="ACTIVATED",
            controller_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            device_groups=groups
        )
        assert len(sensor.device_groups) == 1
        assert sensor.device_groups[0].name == "Sensor Group"


class TestCameraSchemaGroupIds:
    """Camera 스키마 group_ids 테스트"""

    def test_camera_create_with_group_ids(self):
        """CameraCreate: group_ids 배열 사용"""
        camera = CameraCreate(
            number_device=1001,
            group_device=1,
            name_device="Test Camera",
            type_device="IpCamera",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            rtsp_uri="/stream1",
            rtsp_port=554,
            mode="ONVIF",
            category="PTZ",
            group_ids=[1, 2, 3]
        )
        assert camera.group_ids == [1, 2, 3]

    def test_camera_update_with_group_ids(self):
        """CameraUpdate: group_ids 부분 수정"""
        update = CameraUpdate(group_ids=[4, 5])
        assert update.group_ids == [4, 5]

    def test_camera_response_with_device_groups(self):
        """CameraResponse: device_groups 배열 포함"""
        groups = [
            DeviceGroupResponse(
                id=1,
                name="Camera Zone A",
                description="Zone A cameras",
                device_count=5,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            DeviceGroupResponse(
                id=2,
                name="Camera Zone B",
                description="Zone B cameras",
                device_count=3,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        camera = CameraResponse(
            id=1,
            number_device=1001,
            group_device=1,
            name_device="Test Camera",
            type_device="IpCamera",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            rtsp_uri="/stream1",
            rtsp_port=554,
            mode="ONVIF",
            category="PTZ",
            is_record=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            device_groups=groups
        )
        assert len(camera.device_groups) == 2


class TestGroupIdsPriority:
    """group_ids vs group_device 우선순위 테스트"""

    def test_group_ids_takes_priority_when_both_provided(self):
        """group_ids와 group_device 모두 제공 시 group_ids 우선"""
        controller = ControllerCreate(
            number_device=1,
            group_device=999,  # 이 값은 무시되어야 함
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502,
            group_ids=[1, 2]  # 이 값이 사용되어야 함
        )
        # group_ids가 제공되면 이것을 사용
        assert controller.group_ids == [1, 2]
        # group_device는 하위 호환성을 위해 여전히 존재
        assert controller.group_device == 999


class TestBackwardCompatibility:
    """하위 호환성 테스트"""

    def test_response_includes_group_device_for_compatibility(self):
        """Response에 group_device 필드 유지 (하위 호환성)"""
        controller = ControllerResponse(
            id=1,
            number_device=1,
            group_device=5,  # 기존 필드
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            device_groups=[]  # 신규 필드
        )
        # 기존 group_device 필드 유지
        assert controller.group_device == 5
        # 신규 device_groups 필드도 존재
        assert controller.device_groups == []

    def test_create_without_group_ids_still_works(self):
        """group_ids 없이 생성해도 동작"""
        controller = ControllerCreate(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device="Controller",
            version="1.0.0",
            status="ACTIVATED",
            ip_address="192.168.1.1",
            ip_port=502
            # group_ids 미제공
        )
        assert controller.group_ids is None
        assert controller.group_device == 1
