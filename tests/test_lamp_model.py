"""
Tests for Lamp Model (TDD)

PRD: PRD_Lamp_Device.md v1.1
Phase 2.1: Lamp Model Tests & Implementation
"""
import pytest
from sqlalchemy.orm import Session

from app.models.device import Lamp, Device
from app.utils.enums import EnumDeviceCategory, EnumDeviceType, EnumDeviceStatus


class TestLampModelCreation:
    """Test Lamp model creation with required fields"""

    def test_lamp_creation_with_required_fields(self, db_session: Session):
        """RED: Lamp should be created with required fields"""
        # Arrange
        lamp = Lamp(
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.50",
            ip_port=80
        )

        # Act
        db_session.add(lamp)
        db_session.commit()
        db_session.refresh(lamp)

        # Assert
        assert lamp.id is not None
        assert lamp.number_device == 1
        assert lamp.group_device == 1
        assert lamp.name_device == "Lamp-A-1"
        assert lamp.type_device == EnumDeviceType.Lamp
        assert lamp.status == EnumDeviceStatus.ACTIVATED
        assert lamp.ip_address == "192.168.1.50"
        assert lamp.ip_port == 80

    def test_lamp_inherits_from_device(self, db_session: Session):
        """RED: Lamp should inherit from Device (polymorphic identity)"""
        # Arrange
        lamp = Lamp(
            number_device=2,
            group_device=1,
            name_device="Lamp-A-2",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.51",
            ip_port=80
        )

        # Act
        db_session.add(lamp)
        db_session.commit()
        db_session.refresh(lamp)

        # Assert - Lamp should be instance of both Lamp and Device
        assert isinstance(lamp, Lamp)
        assert isinstance(lamp, Device)

        # Query by Device base class should also work
        device = db_session.query(Device).filter(Device.id == lamp.id).first()
        assert device is not None
        assert device.category_device == EnumDeviceCategory.LAMP

    def test_lamp_polymorphic_identity(self, db_session: Session):
        """RED: Lamp should have polymorphic_identity = LAMP"""
        # Arrange
        lamp = Lamp(
            number_device=3,
            group_device=1,
            name_device="Lamp-A-3",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.52",
            ip_port=80
        )

        # Act
        db_session.add(lamp)
        db_session.commit()
        db_session.refresh(lamp)

        # Assert
        assert lamp.category_device == EnumDeviceCategory.LAMP

    def test_lamp_geolocation_json_field(self, db_session: Session):
        """RED: Lamp should support geolocation JSON field"""
        # Arrange
        geolocation_data = {
            "location": "GOP 1구역 경광등",
            "latitude": 38.1234,
            "longitude": 127.5678
        }

        lamp = Lamp(
            number_device=4,
            group_device=1,
            name_device="Lamp-A-4",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.53",
            ip_port=80,
            geolocation=geolocation_data
        )

        # Act
        db_session.add(lamp)
        db_session.commit()
        db_session.refresh(lamp)

        # Assert
        assert lamp.geolocation is not None
        assert lamp.geolocation["location"] == "GOP 1구역 경광등"
        assert lamp.geolocation["latitude"] == 38.1234
        assert lamp.geolocation["longitude"] == 127.5678

    def test_lamp_optional_fields(self, db_session: Session):
        """RED: Lamp should support optional fields (user_name, user_password, description)"""
        # Arrange
        lamp = Lamp(
            number_device=5,
            group_device=1,
            name_device="Lamp-A-5",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.54",
            ip_port=8080,
            user_name="admin",
            user_password="secret123",
            description="Test lamp with optional fields"
        )

        # Act
        db_session.add(lamp)
        db_session.commit()
        db_session.refresh(lamp)

        # Assert
        assert lamp.user_name == "admin"
        assert lamp.user_password == "secret123"
        assert lamp.description == "Test lamp with optional fields"

    def test_lamp_default_values(self, db_session: Session):
        """RED: Lamp should have proper default values"""
        # Arrange
        lamp = Lamp(
            number_device=6,
            group_device=1,
            name_device="Lamp-A-6",
            type_device=EnumDeviceType.Lamp,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.55",
            ip_port=80
        )

        # Act
        db_session.add(lamp)
        db_session.commit()
        db_session.refresh(lamp)

        # Assert - default values
        assert lamp.is_enable is True  # Default from Device base
        assert lamp.user_name is None  # Optional, default None
        assert lamp.user_password is None  # Optional, default None
        assert lamp.description is None  # Optional, default None
        assert lamp.geolocation is None  # Optional, default None
