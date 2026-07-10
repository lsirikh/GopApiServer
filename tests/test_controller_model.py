"""
Tests for Controller model
"""
import pytest
from datetime import datetime


def test_controller_model_has_required_fields(test_db):
    """
    Test: Controller model has all required fields

    Expected to fail initially (Red phase).
    """
    from app.models.device import Controller

    # Test that the model class exists and has required attributes
    assert hasattr(Controller, 'id')
    assert hasattr(Controller, 'number_device')
    assert hasattr(Controller, 'group_device')
    assert hasattr(Controller, 'name_device')
    assert hasattr(Controller, 'type_device')
    assert hasattr(Controller, 'version')
    assert hasattr(Controller, 'status')
    assert hasattr(Controller, 'ip_address')
    assert hasattr(Controller, 'ip_port')
    assert hasattr(Controller, 'created_at')
    assert hasattr(Controller, 'updated_at')


def test_controller_model_timestamps_auto_set(test_db):
    """
    Test: created_at and updated_at are automatically set

    Expected to fail initially (Red phase).
    """
    from app.models.device import Controller
    from app.models.device import EnumDeviceType, EnumDeviceStatus

    # Create a controller without setting timestamps
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=8080
    )

    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    # Verify timestamps were set automatically
    assert controller.created_at is not None
    assert controller.updated_at is not None
    assert isinstance(controller.created_at, datetime)
    assert isinstance(controller.updated_at, datetime)


def test_controller_model_table_name(test_db):
    """
    Test: Controller model uses 'controllers' as table name

    Expected to fail initially (Red phase).
    """
    from app.models.device import Controller

    assert Controller.__tablename__ == 'controllers'


def test_controller_model_create_and_retrieve(test_db):
    """
    Test: Can create and retrieve a Controller from database

    Expected to fail initially (Red phase).
    """
    from app.models.device import Controller
    from app.models.device import EnumDeviceType, EnumDeviceStatus

    # Create a controller
    controller = Controller(
        number_device=100,
        group_device=5,
        name_device="Main Gate Controller",
        type_device=EnumDeviceType.Controller,
        version="2.1.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="10.0.0.50",
        ip_port=9000
    )

    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    # Retrieve the controller
    retrieved = test_db.query(Controller).filter(
        Controller.number_device == 100
    ).first()

    assert retrieved is not None
    assert retrieved.id == controller.id
    assert retrieved.number_device == 100
    assert retrieved.group_device == 5
    assert retrieved.name_device == "Main Gate Controller"
    assert retrieved.type_device == EnumDeviceType.Controller
    assert retrieved.version == "2.1.0"
    assert retrieved.status == EnumDeviceStatus.ACTIVATED
    assert retrieved.ip_address == "10.0.0.50"
    assert retrieved.ip_port == 9000
