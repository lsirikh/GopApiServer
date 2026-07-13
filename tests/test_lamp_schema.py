"""
Tests for Lamp Schema (TDD)

PRD: PRD_Lamp_Device.md v1.1
Phase 2.2: Lamp Schema Tests & Implementation
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.device import (
    LampCreate,
    LampUpdate,
    LampResponse,
    LampNestedResponse,
    DeviceGroupNestedResponse,
    Geolocation
)


class TestLampCreateSchema:
    """Test LampCreate validation (required fields)"""

    def test_lamp_create_with_required_fields(self):
        """RED: LampCreate should validate required fields"""
        lamp = LampCreate(
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            ip_address="192.168.1.50",
            ip_port=80
        )

        assert lamp.number_device == 1
        assert lamp.group_device == 1
        assert lamp.name_device == "Lamp-A-1"
        assert lamp.type_device == "Lamp"
        assert lamp.ip_address == "192.168.1.50"
        assert lamp.ip_port == 80

    def test_lamp_create_missing_required_field_raises_error(self):
        """RED: LampCreate should raise ValidationError for missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            LampCreate(
                number_device=1,
                group_device=1,
                name_device="Lamp-A-1",
                type_device="Lamp"
                # ip_address is missing (required)
            )

        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "ip_address" for e in errors)

    def test_lamp_create_with_optional_fields(self):
        """RED: LampCreate should accept optional fields"""
        lamp = LampCreate(
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            ip_address="192.168.1.50",
            ip_port=8080,
            user_name="admin",
            user_password="secret123",
            description="Test lamp"
        )

        assert lamp.user_name == "admin"
        assert lamp.user_password == "secret123"
        assert lamp.description == "Test lamp"

    def test_lamp_create_with_geolocation(self):
        """RED: LampCreate should accept geolocation JSON"""
        geolocation = Geolocation(
            location="GOP 1구역",
            latitude=38.1234,
            longitude=127.5678
        )

        lamp = LampCreate(
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            ip_address="192.168.1.50",
            ip_port=80,
            geolocation=geolocation
        )

        assert lamp.geolocation is not None
        assert lamp.geolocation.location == "GOP 1구역"


class TestLampUpdateSchema:
    """Test LampUpdate partial update"""

    def test_lamp_update_partial_update(self):
        """RED: LampUpdate should allow partial updates (all fields optional)"""
        # Only update description
        lamp = LampUpdate(description="Updated description")
        assert lamp.description == "Updated description"
        assert lamp.ip_address is None  # Other fields should be None

    def test_lamp_update_empty_is_valid(self):
        """RED: LampUpdate with no fields should be valid (for PATCH)"""
        lamp = LampUpdate()
        # All fields should be None
        assert lamp.ip_address is None
        assert lamp.ip_port is None
        assert lamp.description is None

    def test_lamp_update_multiple_fields(self):
        """RED: LampUpdate should support updating multiple fields"""
        lamp = LampUpdate(
            ip_address="192.168.1.100",
            ip_port=8080,
            is_enable=False
        )

        assert lamp.ip_address == "192.168.1.100"
        assert lamp.ip_port == 8080
        assert lamp.is_enable is False


class TestLampResponseSchema:
    """Test LampResponse includes device_groups"""

    def test_lamp_response_basic_fields(self):
        """RED: LampResponse should include basic fields"""
        now = datetime.now()
        lamp = LampResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            version="v1.0",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.50",
            ip_port=80,
            device_groups=[],
            created_at=now,
            updated_at=now
        )

        assert lamp.id == 1
        assert lamp.name_device == "Lamp-A-1"
        assert lamp.ip_address == "192.168.1.50"

    def test_lamp_response_includes_device_groups(self):
        """RED: LampResponse should include device_groups list"""
        now = datetime.now()
        device_group = DeviceGroupNestedResponse(
            id=1,
            name="GOP 1구역",
            description="1구역 장비 그룹",
            device_count=5
        )

        lamp = LampResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            version="v1.0",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.50",
            ip_port=80,
            device_groups=[device_group],
            created_at=now,
            updated_at=now
        )

        assert len(lamp.device_groups) == 1
        assert lamp.device_groups[0].name == "GOP 1구역"

    def test_lamp_response_includes_optional_fields(self):
        """RED: LampResponse should include optional fields"""
        now = datetime.now()
        geolocation = Geolocation(location="GOP 1구역")
        lamp = LampResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            version="v1.0",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.50",
            ip_port=80,
            user_name="admin",
            user_password="secret",
            description="Test lamp",
            geolocation=geolocation,
            device_groups=[],
            created_at=now,
            updated_at=now
        )

        assert lamp.user_name == "admin"
        assert lamp.description == "Test lamp"
        assert lamp.geolocation.location == "GOP 1구역"


class TestLampNestedResponseSchema:
    """Test LampNestedResponse for DeviceGroup integration"""

    def test_lamp_nested_response_basic_fields(self):
        """RED: LampNestedResponse should include basic lamp fields"""
        lamp = LampNestedResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            version="v1.0",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.50",
            ip_port=80
        )

        assert lamp.id == 1
        assert lamp.name_device == "Lamp-A-1"
        assert lamp.ip_address == "192.168.1.50"

    def test_lamp_nested_response_no_device_groups(self):
        """RED: LampNestedResponse should NOT include device_groups (nested)"""
        lamp = LampNestedResponse(
            id=1,
            number_device=1,
            group_device=1,
            name_device="Lamp-A-1",
            type_device="Lamp",
            version="v1.0",
            status="ACTIVATED",
            is_enable=True,
            ip_address="192.168.1.50",
            ip_port=80
        )

        # LampNestedResponse should not have device_groups attribute
        # (to avoid circular reference in DeviceGroup responses)
        assert not hasattr(lamp, 'device_groups') or getattr(lamp, 'device_groups', None) is None
