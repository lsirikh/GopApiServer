"""
Phase 2: Device Base Model Tests (TDD)
PRD: PRD_Device_Structure_Refactoring.md - Section 3.1

Tests for:
- Device Base model with Polymorphic Inheritance (Joined Table)
- category_device discriminator
- Controller, Sensor, Camera inheritance
- DeviceGroupMapping FK to devices.id
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.dependencies import get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()


class TestDeviceBaseModel:
    """Device Base Model Polymorphic Tests"""

    def test_device_base_table_exists(self, db_session):
        """devices 테이블 존재 확인"""
        from app.models.device import Device

        # Device 모델이 존재하고 테이블명이 'devices'인지 확인
        assert Device.__tablename__ == "devices"

    def test_device_has_discriminator_column(self, db_session):
        """category_device discriminator 컬럼 존재 확인"""
        from app.models.device import Device

        # category_device 컬럼이 존재하는지 확인
        assert hasattr(Device, 'category_device')

    def test_controller_inherits_from_device(self, db_session):
        """Controller가 Device를 상속하는지 확인"""
        from app.models.device import Device, Controller

        assert issubclass(Controller, Device)

    def test_sensor_inherits_from_device(self, db_session):
        """Sensor가 Device를 상속하는지 확인"""
        from app.models.device import Device, Sensor

        assert issubclass(Sensor, Device)

    def test_camera_inherits_from_device(self, db_session):
        """Camera가 Device를 상속하는지 확인"""
        from app.models.device import Device, Camera

        assert issubclass(Camera, Device)


class TestDeviceCreation:
    """Device Creation via Inheritance Tests"""

    def test_create_controller_creates_device_record(self, db_session):
        """Controller 생성 시 devices 테이블에도 레코드 생성"""
        from app.models.device import Device, Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()
        db_session.refresh(controller)

        # devices 테이블에서 조회 가능해야 함
        device = db_session.query(Device).filter(Device.id == controller.id).first()
        assert device is not None
        assert device.category_device == "controller"
        assert device.number_device == 1001

    def test_create_sensor_creates_device_record(self, db_session):
        """Sensor 생성 시 devices 테이블에도 레코드 생성"""
        from app.models.device import Device, Controller, Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # First create a controller for the sensor
        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        sensor = Sensor(
            number_device=2001,
            group_device=1,
            name_device="Test Sensor",
            type_device=EnumDeviceType.Fence,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            controller_id=controller.id
        )
        db_session.add(sensor)
        db_session.commit()
        db_session.refresh(sensor)

        # devices 테이블에서 조회 가능해야 함
        device = db_session.query(Device).filter(Device.id == sensor.id).first()
        assert device is not None
        assert device.category_device == "sensor"
        assert device.number_device == 2001

    def test_create_camera_creates_device_record(self, db_session):
        """Camera 생성 시 devices 테이블에도 레코드 생성"""
        from app.models.device import Device, Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=3001,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.NONE
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        # devices 테이블에서 조회 가능해야 함
        device = db_session.query(Device).filter(Device.id == camera.id).first()
        assert device is not None
        assert device.category_device == "camera"
        assert device.number_device == 3001


class TestDevicePolymorphicQuery:
    """Polymorphic Query Tests"""

    def test_query_all_devices(self, db_session):
        """Device로 모든 디바이스 조회"""
        from app.models.device import Device, Controller, Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        # Create controller
        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Controller 1",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)

        # Create camera
        camera = Camera(
            number_device=3001,
            group_device=1,
            name_device="Camera 1",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.NONE
        )
        db_session.add(camera)
        db_session.commit()

        # Query all devices
        devices = db_session.query(Device).all()
        assert len(devices) == 2

    def test_query_devices_by_type(self, db_session):
        """category_device으로 필터링 조회"""
        from app.models.device import Device, Controller, Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        # Create multiple devices
        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Controller 1",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)

        camera = Camera(
            number_device=3001,
            group_device=1,
            name_device="Camera 1",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.NONE
        )
        db_session.add(camera)
        db_session.commit()

        # Query only controllers
        controllers = db_session.query(Device).filter(Device.category_device == "controller").all()
        assert len(controllers) == 1
        assert controllers[0].name_device == "Controller 1"


class TestDeviceGroupMappingWithDeviceBase:
    """DeviceGroupMapping FK to devices.id Tests"""

    def test_device_group_mapping_references_device_id(self, db_session):
        """DeviceGroupMapping.device_id가 devices.id를 참조"""
        from app.models.device import Device, Controller
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # Create group
        group = DeviceGroup(name="Test Group")
        db_session.add(group)
        db_session.commit()

        # Create controller
        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        # Create mapping using device_id (which now refers to devices.id)
        mapping = DeviceGroupMapping(
            device_id=controller.id,
            category_device="controller",
            group_id=group.id
        )
        db_session.add(mapping)
        db_session.commit()

        # Verify the mapping references the device correctly
        assert mapping.device_id == controller.id

        # Should be able to query via Device
        device = db_session.query(Device).filter(Device.id == mapping.device_id).first()
        assert device is not None
        assert device.category_device == "controller"

    def test_device_relationship_to_group_mappings(self, db_session):
        """Device에서 group_mappings relationship 접근"""
        from app.models.device import Device, Controller
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # Create groups
        group1 = DeviceGroup(name="Group 1")
        group2 = DeviceGroup(name="Group 2")
        db_session.add_all([group1, group2])
        db_session.commit()

        # Create controller
        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        # Create mappings
        mapping1 = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group1.id)
        mapping2 = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group2.id)
        db_session.add_all([mapping1, mapping2])
        db_session.commit()

        # Refresh and check relationship
        db_session.refresh(controller)

        # Controller should have group_mappings relationship
        assert hasattr(controller, 'group_mappings')
        assert controller.group_mappings.count() == 2


class TestDeviceNumberUnique:
    """Device number_device UNIQUE constraint Tests"""

    def test_number_device_unique_across_all_devices(self, db_session):
        """number_device가 모든 디바이스 타입에서 UNIQUE"""
        from app.models.device import Controller, Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        # Create controller with number_device=1001
        controller = Controller(
            number_device=1001,
            group_device=1,
            name_device="Controller 1",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        # Try to create camera with same number_device - should fail
        camera = Camera(
            number_device=1001,  # Same as controller!
            group_device=1,
            name_device="Camera 1",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.NONE
        )
        db_session.add(camera)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestDeviceGroupDeviceBackwardCompatibility:
    """group_device 필드 하위 호환성 Tests"""

    def test_group_device_field_still_exists(self, db_session):
        """group_device 필드가 여전히 존재"""
        from app.models.device import Device, Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        controller = Controller(
            number_device=1001,
            group_device=999,  # Legacy field
            name_device="Test Controller",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()
        db_session.refresh(controller)

        assert controller.group_device == 999

        # Also accessible via Device base
        device = db_session.query(Device).filter(Device.id == controller.id).first()
        assert device.group_device == 999
