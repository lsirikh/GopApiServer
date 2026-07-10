"""
Test: Device.version nullable
PRD: PRD_Device_Inheritance_Structure_Refactoring.md v1.2

TDD Phase 2: Red - Write failing tests for Device.version nullable
"""
import pytest
from sqlalchemy import inspect


class TestDeviceVersionNullable:
    """Device.version nullable 테스트"""

    def test_device_version_column_is_nullable(self):
        """Device.version 컬럼이 nullable=True인지 확인"""
        from app.models.device import Device

        mapper = inspect(Device)
        version_column = mapper.columns['version']
        assert version_column.nullable is True, "Device.version should be nullable=True per PRD v1.2"

    def test_create_controller_without_version(self, db_session):
        """version 없이 Controller 생성이 가능한지 테스트"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        controller = Controller(
            number_device=99999,
            group_device=1,
            name_device="Test Controller No Version",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=8080,
            version=None  # version을 None으로 설정
        )

        db_session.add(controller)
        db_session.commit()

        assert controller.id is not None
        assert controller.version is None

        # Cleanup
        db_session.delete(controller)
        db_session.commit()

    def test_create_sensor_without_version(self, db_session):
        """version 없이 Sensor 생성이 가능한지 테스트"""
        from app.models.device import Controller, Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # First create a controller for the sensor
        controller = Controller(
            number_device=99998,
            group_device=1,
            name_device="Test Controller for Sensor",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.101",
            ip_port=8080,
            version="1.0.0"
        )
        db_session.add(controller)
        db_session.commit()

        sensor = Sensor(
            number_device=99997,
            group_device=1,
            name_device="Test Sensor No Version",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id,
            version=None  # version을 None으로 설정
        )

        db_session.add(sensor)
        db_session.commit()

        assert sensor.id is not None
        assert sensor.version is None

        # Cleanup
        db_session.delete(sensor)
        db_session.delete(controller)
        db_session.commit()

    def test_create_camera_without_version(self, db_session):
        """version 없이 Camera 생성이 가능한지 테스트"""
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=99996,
            group_device=1,
            name_device="Test Camera No Version",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.102",
            ip_port=80,
            user_name="admin",
            user_password="password",
            rtsp_uri="rtsp://192.168.1.102/stream",
            rtsp_port=554,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            version=None  # version을 None으로 설정
        )

        db_session.add(camera)
        db_session.commit()

        assert camera.id is not None
        assert camera.version is None

        # Cleanup
        db_session.delete(camera)
        db_session.commit()
