"""
Test: Device.category_device uses EnumDeviceCategory
PRD: PRD_Device_Inheritance_Structure_Refactoring.md Section 8.1

TDD Phase 4: Red - Write failing tests for Device.category_device ENUM
"""
import pytest
from sqlalchemy import inspect, Enum as SQLEnum


class TestDeviceCategoryEnum:
    """Device.category_device ENUM 적용 테스트"""

    def test_device_category_device_uses_enum(self):
        """Device.category_device가 SQLEnum 타입인지 확인"""
        from app.models.device import Device
        from app.utils.enums import EnumDeviceCategory

        mapper = inspect(Device)
        column = mapper.columns['category_device']

        # SQLEnum 타입인지 확인
        assert isinstance(column.type, SQLEnum), \
            "Device.category_device should use SQLEnum(EnumDeviceCategory)"

    def test_controller_polymorphic_identity_enum(self):
        """Controller의 polymorphic_identity가 EnumDeviceCategory.CONTROLLER인지 확인"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceCategory

        identity = Controller.__mapper_args__.get('polymorphic_identity')
        # ENUM 값 또는 문자열 "controller" 허용
        assert identity == EnumDeviceCategory.CONTROLLER or identity == "controller", \
            f"Controller polymorphic_identity should be EnumDeviceCategory.CONTROLLER, got {identity}"

    def test_sensor_polymorphic_identity_enum(self):
        """Sensor의 polymorphic_identity가 EnumDeviceCategory.SENSOR인지 확인"""
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceCategory

        identity = Sensor.__mapper_args__.get('polymorphic_identity')
        assert identity == EnumDeviceCategory.SENSOR or identity == "sensor", \
            f"Sensor polymorphic_identity should be EnumDeviceCategory.SENSOR, got {identity}"

    def test_camera_polymorphic_identity_enum(self):
        """Camera의 polymorphic_identity가 EnumDeviceCategory.CAMERA인지 확인"""
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceCategory

        identity = Camera.__mapper_args__.get('polymorphic_identity')
        assert identity == EnumDeviceCategory.CAMERA or identity == "camera", \
            f"Camera polymorphic_identity should be EnumDeviceCategory.CAMERA, got {identity}"

    def test_create_controller_with_enum_category(self, db_session):
        """Controller 생성 시 category_device가 EnumDeviceCategory.CONTROLLER로 저장되는지 확인"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        controller = Controller(
            number_device=77777,
            group_device=1,
            name_device="Test Controller ENUM",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.50",
            ip_port=8080,
            version="1.0.0"
        )

        db_session.add(controller)
        db_session.commit()

        assert controller.id is not None
        # category_device가 EnumDeviceCategory.CONTROLLER 또는 "controller"인지 확인
        assert controller.category_device == EnumDeviceCategory.CONTROLLER or \
               controller.category_device == "controller", \
            f"Expected CONTROLLER, got {controller.category_device}"

        # Cleanup
        db_session.delete(controller)
        db_session.commit()

    def test_query_device_by_enum_category(self, db_session):
        """EnumDeviceCategory로 Device 쿼리 가능 여부 테스트"""
        from app.models.device import Device, Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        # Create test controller
        controller = Controller(
            number_device=77776,
            group_device=1,
            name_device="Test Controller Query",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.51",
            ip_port=8080,
            version="1.0.0"
        )
        db_session.add(controller)
        db_session.commit()

        # Query by ENUM value
        result = db_session.query(Device).filter(
            Device.category_device == EnumDeviceCategory.CONTROLLER
        ).first()

        assert result is not None, "Should find controller by EnumDeviceCategory.CONTROLLER"
        assert result.id == controller.id

        # Cleanup
        db_session.delete(controller)
        db_session.commit()
