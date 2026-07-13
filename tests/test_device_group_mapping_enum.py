"""
Test: DeviceGroupMapping.category_device uses EnumDeviceCategory
PRD: PRD_Device_Inheritance_Structure_Refactoring.md Section 8.1

TDD Phase 5: Red - Write failing tests for DeviceGroupMapping ENUM
"""
import pytest
from sqlalchemy import inspect, Enum as SQLEnum


class TestDeviceGroupMappingEnum:
    """DeviceGroupMapping.category_device ENUM 적용 테스트"""

    def test_device_group_mapping_category_uses_enum(self):
        """DeviceGroupMapping.category_device가 SQLEnum 타입인지 확인"""
        from app.models.device_group import DeviceGroupMapping
        from app.utils.enums import EnumDeviceCategory

        mapper = inspect(DeviceGroupMapping)
        column = mapper.columns['category_device']

        # SQLEnum 타입인지 확인
        assert isinstance(column.type, SQLEnum), \
            "DeviceGroupMapping.category_device should use SQLEnum(EnumDeviceCategory)"

    def test_create_mapping_with_enum(self, db_session):
        """EnumDeviceCategory로 DeviceGroupMapping 생성 테스트"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        # Create test group
        group = DeviceGroup(
            name="Test Group ENUM",
            description="Test group for ENUM"
        )
        db_session.add(group)
        db_session.commit()

        # Create test controller
        controller = Controller(
            number_device=66666,
            group_device=1,
            name_device="Test Controller Mapping",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.60",
            ip_port=8080,
            version="1.0.0"
        )
        db_session.add(controller)
        db_session.commit()

        # Create mapping with ENUM
        mapping = DeviceGroupMapping(
            device_id=controller.id,
            category_device=EnumDeviceCategory.CONTROLLER,
            group_id=group.id
        )
        db_session.add(mapping)
        db_session.commit()

        assert mapping.id is not None
        assert mapping.category_device == EnumDeviceCategory.CONTROLLER

        # Cleanup
        db_session.delete(mapping)
        db_session.delete(controller)
        db_session.delete(group)
        db_session.commit()

    def test_query_mapping_by_enum(self, db_session):
        """EnumDeviceCategory로 DeviceGroupMapping 쿼리 테스트"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory

        # Create test group
        group = DeviceGroup(
            name="Test Group Query ENUM",
            description="Test group for ENUM query"
        )
        db_session.add(group)
        db_session.commit()

        # Create test controller
        controller = Controller(
            number_device=66665,
            group_device=1,
            name_device="Test Controller Query Mapping",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.61",
            ip_port=8080,
            version="1.0.0"
        )
        db_session.add(controller)
        db_session.commit()

        # Create mapping
        mapping = DeviceGroupMapping(
            device_id=controller.id,
            category_device=EnumDeviceCategory.CONTROLLER,
            group_id=group.id
        )
        db_session.add(mapping)
        db_session.commit()

        # Query by ENUM
        result = db_session.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER
        ).first()

        assert result is not None
        assert result.id == mapping.id

        # Cleanup
        db_session.delete(mapping)
        db_session.delete(controller)
        db_session.delete(group)
        db_session.commit()
