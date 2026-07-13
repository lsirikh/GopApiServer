"""
Phase 3: Camera Extended Fields Tests (TDD - Red Phase)
PRD: PRD_Device_Structure_Refactoring.md - Section 3.2
PRD: PRD_Camera_Urls_JsonB.md v1.0 - Updated to use urls JSONB instead of rtsp_uri/rtsp_port

Tests for:
- is_record: Boolean field (default False)
- hardware_spec: JSON field (HardwareSpec composite type)
- geolocation: JSON field (Geolocation composite type)
"""
import pytest
from sqlalchemy.orm import Session
from app.models.device import Camera
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType


class TestCameraIsRecordField:
    """is_record 필드 테스트"""

    def test_camera_is_record_default_false(self, db_session: Session):
        """is_record 필드 기본값은 False"""
        camera = Camera(
            number_device=9001,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.is_record is False

    def test_camera_is_record_set_true(self, db_session: Session):
        """is_record 필드를 True로 설정"""
        camera = Camera(
            number_device=9002,
            group_device=1,
            name_device="Recording Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.101",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            is_record=True
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.is_record is True


class TestCameraHardwareSpecField:
    """hardware_spec JSON 필드 테스트"""

    def test_camera_hardware_spec_default_none(self, db_session: Session):
        """hardware_spec 필드 기본값은 None"""
        camera = Camera(
            number_device=9003,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.102",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.hardware_spec is None

    def test_camera_hardware_spec_full_data(self, db_session: Session):
        """hardware_spec 전체 필드 저장/조회"""
        hardware_spec = {
            "name": "Axis P3245-V",
            "location": "GOP 1구역 전방 초소",
            "manufacturer": "Axis Communications",
            "model": "P3245-V",
            "hardware": "ARTPEC-7",
            "firmware": "10.12.114",
            "device_id": "ACCC8E123456",
            "mac_address": "AC:CC:8E:12:34:56",
            "onvif_version": "21.06"
        }

        camera = Camera(
            number_device=9004,
            group_device=1,
            name_device="Full Spec Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.103",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            hardware_spec=hardware_spec
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.hardware_spec is not None
        assert camera.hardware_spec["name"] == "Axis P3245-V"
        assert camera.hardware_spec["manufacturer"] == "Axis Communications"
        assert camera.hardware_spec["mac_address"] == "AC:CC:8E:12:34:56"

    def test_camera_hardware_spec_partial_data(self, db_session: Session):
        """hardware_spec 일부 필드만 저장 (optional 필드)"""
        hardware_spec = {
            "name": "Simple Camera",
            "manufacturer": "Generic"
        }

        camera = Camera(
            number_device=9005,
            group_device=1,
            name_device="Partial Spec Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.104",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.FIXED,
            hardware_spec=hardware_spec
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.hardware_spec["name"] == "Simple Camera"
        assert camera.hardware_spec["manufacturer"] == "Generic"
        assert camera.hardware_spec.get("model") is None


class TestCameraGeolocationField:
    """geolocation JSON 필드 테스트"""

    def test_camera_geolocation_default_none(self, db_session: Session):
        """geolocation 필드 기본값은 None"""
        camera = Camera(
            number_device=9006,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.105",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.geolocation is None

    def test_camera_geolocation_full_data(self, db_session: Session):
        """geolocation 전체 필드 저장/조회 (latitude, longitude, altitude)"""
        geolocation = {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "altitude": 50.0
        }

        camera = Camera(
            number_device=9007,
            group_device=1,
            name_device="Geolocated Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.106",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            geolocation=geolocation
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.geolocation is not None
        assert camera.geolocation["latitude"] == 37.5665
        assert camera.geolocation["longitude"] == 126.9780
        assert camera.geolocation["altitude"] == 50.0

    def test_camera_geolocation_without_altitude(self, db_session: Session):
        """geolocation altitude 없이 저장 (optional)"""
        geolocation = {
            "latitude": 38.1234,
            "longitude": 127.5678
        }

        camera = Camera(
            number_device=9008,
            group_device=1,
            name_device="2D Geolocated Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.107",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.FIXED,
            geolocation=geolocation
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.geolocation["latitude"] == 38.1234
        assert camera.geolocation["longitude"] == 127.5678
        assert camera.geolocation.get("altitude") is None


class TestCameraAllExtendedFields:
    """모든 확장 필드 조합 테스트"""

    def test_camera_all_extended_fields(self, db_session: Session):
        """is_record, hardware_spec, geolocation 모두 설정"""
        camera = Camera(
            number_device=9009,
            group_device=1,
            name_device="Full Featured Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.108",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            is_record=True,
            hardware_spec={
                "name": "Premium Camera",
                "manufacturer": "Premium Brand",
                "model": "Premium-X1",
                "firmware": "2.0.0",
                "mac_address": "AA:BB:CC:DD:EE:FF"
            },
            geolocation={
                "latitude": 37.5000,
                "longitude": 127.0000,
                "altitude": 100.5
            }
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        assert camera.is_record is True
        assert camera.hardware_spec["name"] == "Premium Camera"
        assert camera.hardware_spec["manufacturer"] == "Premium Brand"
        assert camera.geolocation["latitude"] == 37.5000
        assert camera.geolocation["altitude"] == 100.5

    def test_camera_update_extended_fields(self, db_session: Session):
        """확장 필드 업데이트 테스트"""
        camera = Camera(
            number_device=9010,
            group_device=1,
            name_device="Updateable Camera",
            type_device=EnumDeviceType.IpCamera,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.109",
            ip_port=80,
            user_name="admin",
            user_password="password",
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.FIXED,
            is_record=False,
            hardware_spec={"name": "Old Name"},
            geolocation={"latitude": 0.0, "longitude": 0.0}
        )
        db_session.add(camera)
        db_session.commit()

        # Update fields
        camera.is_record = True
        camera.hardware_spec = {"name": "New Name", "firmware": "3.0.0"}
        camera.geolocation = {"latitude": 37.1234, "longitude": 127.5678, "altitude": 75.0}
        db_session.commit()
        db_session.refresh(camera)

        assert camera.is_record is True
        assert camera.hardware_spec["name"] == "New Name"
        assert camera.hardware_spec["firmware"] == "3.0.0"
        assert camera.geolocation["latitude"] == 37.1234
        assert camera.geolocation["altitude"] == 75.0
