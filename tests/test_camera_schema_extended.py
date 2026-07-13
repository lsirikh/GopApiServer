"""
Phase 3: Camera Schema Extended Fields Tests (TDD)
PRD: PRD_Device_Structure_Refactoring.md - Section 3.2

Tests for:
- HardwareSpec Pydantic schema validation
- Geolocation Pydantic schema validation
- CameraCreate/CameraUpdate/CameraResponse with extended fields
"""
import pytest
from pydantic import ValidationError
from app.schemas.device import (
    HardwareSpec,
    Geolocation,
    CameraCreate,
    CameraResponse,
    CameraUpdate
)
from datetime import datetime


class TestHardwareSpecSchema:
    """HardwareSpec Pydantic 스키마 테스트"""

    def test_hardware_spec_all_fields(self):
        """HardwareSpec 전체 필드 유효성"""
        spec = HardwareSpec(
            name="Axis P3245-V",
            location="GOP 1구역 전방 초소",
            manufacturer="Axis Communications",
            model="P3245-V",
            hardware="ARTPEC-7",
            firmware="10.12.114",
            device_id="ACCC8E123456",
            mac_address="AC:CC:8E:12:34:56",
            onvif_version="21.06"
        )
        assert spec.name == "Axis P3245-V"
        assert spec.manufacturer == "Axis Communications"
        assert spec.mac_address == "AC:CC:8E:12:34:56"

    def test_hardware_spec_partial_fields(self):
        """HardwareSpec 일부 필드만 (optional)"""
        spec = HardwareSpec(
            name="Simple Camera",
            manufacturer="Generic"
        )
        assert spec.name == "Simple Camera"
        assert spec.model is None
        assert spec.firmware is None

    def test_hardware_spec_empty(self):
        """HardwareSpec 빈 객체"""
        spec = HardwareSpec()
        assert spec.name is None
        assert spec.manufacturer is None

    def test_hardware_spec_to_dict(self):
        """HardwareSpec dict 변환"""
        spec = HardwareSpec(name="Test", manufacturer="TestCo")
        spec_dict = spec.model_dump(exclude_none=True)
        assert spec_dict == {"name": "Test", "manufacturer": "TestCo"}


class TestGeolocationSchema:
    """Geolocation Pydantic 스키마 테스트"""

    def test_geolocation_full(self):
        """Geolocation 전체 필드"""
        geo = Geolocation(
            location="GOP 1구역 전방 초소",
            latitude=37.5665,
            longitude=126.9780,
            altitude=50.0
        )
        assert geo.location == "GOP 1구역 전방 초소"
        assert geo.latitude == 37.5665
        assert geo.longitude == 126.9780
        assert geo.altitude == 50.0

    def test_geolocation_with_location_only(self):
        """Geolocation location만 (좌표 없이)"""
        geo = Geolocation(
            location="GOP 2구역 후방 감시초소"
        )
        assert geo.location == "GOP 2구역 후방 감시초소"
        assert geo.latitude is None
        assert geo.longitude is None
        assert geo.altitude is None

    def test_geolocation_without_altitude(self):
        """Geolocation altitude 없이"""
        geo = Geolocation(
            latitude=37.5665,
            longitude=126.9780
        )
        assert geo.latitude == 37.5665
        assert geo.altitude is None

    def test_geolocation_latitude_range_valid(self):
        """위도 범위 유효 (-90 ~ 90)"""
        geo1 = Geolocation(latitude=-90.0, longitude=0)
        geo2 = Geolocation(latitude=90.0, longitude=0)
        assert geo1.latitude == -90.0
        assert geo2.latitude == 90.0

    def test_geolocation_latitude_range_invalid(self):
        """위도 범위 초과 에러"""
        with pytest.raises(ValidationError):
            Geolocation(latitude=-91.0, longitude=0)
        with pytest.raises(ValidationError):
            Geolocation(latitude=91.0, longitude=0)

    def test_geolocation_longitude_range_valid(self):
        """경도 범위 유효 (-180 ~ 180)"""
        geo1 = Geolocation(latitude=0, longitude=-180.0)
        geo2 = Geolocation(latitude=0, longitude=180.0)
        assert geo1.longitude == -180.0
        assert geo2.longitude == 180.0

    def test_geolocation_longitude_range_invalid(self):
        """경도 범위 초과 에러"""
        with pytest.raises(ValidationError):
            Geolocation(latitude=0, longitude=-181.0)
        with pytest.raises(ValidationError):
            Geolocation(latitude=0, longitude=181.0)


class TestCameraCreateExtended:
    """CameraCreate 확장 필드 테스트"""

    def test_camera_create_with_extended_fields(self):
        """CameraCreate 확장 필드 포함"""
        camera = CameraCreate(
            number_device=1,
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
            is_record=True,
            hardware_spec=HardwareSpec(name="Axis", manufacturer="Axis"),
            geolocation=Geolocation(latitude=37.5, longitude=127.0)
        )
        assert camera.is_record is True
        assert camera.hardware_spec.name == "Axis"
        assert camera.geolocation.latitude == 37.5

    def test_camera_create_default_extended_fields(self):
        """CameraCreate 확장 필드 기본값"""
        camera = CameraCreate(
            number_device=1,
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
            category="PTZ"
        )
        assert camera.is_record is False
        assert camera.hardware_spec is None
        assert camera.geolocation is None


class TestCameraResponseExtended:
    """CameraResponse 확장 필드 테스트"""

    def test_camera_response_with_extended_fields(self):
        """CameraResponse 확장 필드 포함"""
        camera = CameraResponse(
            id=1,
            number_device=1,
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
            is_record=True,
            hardware_spec=HardwareSpec(name="Axis", model="P3245"),
            geolocation=Geolocation(latitude=37.5, longitude=127.0, altitude=100.0),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert camera.is_record is True
        assert camera.hardware_spec.model == "P3245"
        assert camera.geolocation.altitude == 100.0


class TestCameraUpdateExtended:
    """CameraUpdate 확장 필드 테스트"""

    def test_camera_update_only_is_record(self):
        """CameraUpdate is_record만 수정"""
        update = CameraUpdate(is_record=True)
        assert update.is_record is True
        assert update.hardware_spec is None
        assert update.number_device is None

    def test_camera_update_only_hardware_spec(self):
        """CameraUpdate hardware_spec만 수정"""
        update = CameraUpdate(
            hardware_spec=HardwareSpec(firmware="2.0.0")
        )
        assert update.hardware_spec.firmware == "2.0.0"
        assert update.is_record is None

    def test_camera_update_only_geolocation(self):
        """CameraUpdate geolocation만 수정"""
        update = CameraUpdate(
            geolocation=Geolocation(latitude=38.0, longitude=128.0)
        )
        assert update.geolocation.latitude == 38.0
        assert update.is_record is None

    def test_camera_update_all_extended_fields(self):
        """CameraUpdate 모든 확장 필드 수정"""
        update = CameraUpdate(
            is_record=True,
            hardware_spec=HardwareSpec(name="New Name"),
            geolocation=Geolocation(latitude=39.0, longitude=129.0, altitude=200.0)
        )
        assert update.is_record is True
        assert update.hardware_spec.name == "New Name"
        assert update.geolocation.altitude == 200.0
