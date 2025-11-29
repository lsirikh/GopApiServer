"""
Test: Controller API with include_sensors parameter
PRD: GOP_Restful_Api_연동설계.md - Section 5.1
"""
import pytest
from datetime import datetime


def test_get_controllers_list_includes_sensors_when_flag_is_true(test_db):
    """
    Test: GET /api/devices/controllers?include_sensors=true returns sensors

    Expected to FAIL initially (Red phase).
    """
    from app.models.device import Controller, Sensor, EnumDeviceType, EnumDeviceStatus
    from app.routers.controllers import get_controllers
    from app.schemas.device import SensorResponse
    from unittest.mock import MagicMock
    import asyncio

    # Create a controller
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=8080
    )
    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    # Create sensors for this controller
    sensor1 = Sensor(
        number_device=1,
        controller_id=controller.id,
        group_device=1,
        name_device="Sensor 1",
        type_device=EnumDeviceType.PIR,
        version="1.0",
        status=EnumDeviceStatus.ACTIVATED
    )
    sensor2 = Sensor(
        number_device=2,
        controller_id=controller.id,
        group_device=1,
        name_device="Sensor 2",
        type_device=EnumDeviceType.Contact,
        version="1.0",
        status=EnumDeviceStatus.ACTIVATED
    )
    test_db.add_all([sensor1, sensor2])
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get controllers with include_sensors=True
    response = asyncio.run(get_controllers(
        page=1,
        limit=20,
        group_device=None,
        status=None,
        include_sensors=True,
        current_user=mock_user,
        db=test_db
    ))

    # Verify response structure
    assert response.success is True
    assert response.data is not None
    assert len(response.data) == 1

    # Verify sensors are included
    controller_response = response.data[0]
    assert hasattr(controller_response, 'sensors')
    assert controller_response.sensors is not None
    assert len(controller_response.sensors) == 2
    assert isinstance(controller_response.sensors[0], SensorResponse)
    assert controller_response.sensors[0].number_device in [1, 2]
    assert controller_response.sensors[1].number_device in [1, 2]


def test_get_controllers_list_excludes_sensors_when_flag_is_false(test_db):
    """
    Test: GET /api/devices/controllers?include_sensors=false excludes sensors

    Expected to FAIL initially (Red phase).
    """
    from app.models.device import Controller, Sensor, EnumDeviceType, EnumDeviceStatus
    from app.routers.controllers import get_controllers
    from unittest.mock import MagicMock
    import asyncio

    # Create a controller with sensors
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=8080
    )
    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    sensor = Sensor(
        number_device=1,
        controller_id=controller.id,
        group_device=1,
        name_device="Sensor 1",
        type_device=EnumDeviceType.PIR,
        version="1.0",
        status=EnumDeviceStatus.ACTIVATED
    )
    test_db.add(sensor)
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get controllers with include_sensors=False (default)
    response = asyncio.run(get_controllers(
        page=1,
        limit=20,
        group_device=None,
        status=None,
        include_sensors=False,
        current_user=mock_user,
        db=test_db
    ))

    # Verify sensors are NOT included
    assert response.success is True
    controller_response = response.data[0]
    assert controller_response.sensors is None or controller_response.sensors == []


def test_get_single_controller_includes_sensors_when_flag_is_true(test_db):
    """
    Test: GET /api/devices/controllers/{id}?include_sensors=true returns sensors

    Expected to FAIL initially (Red phase).
    """
    from app.models.device import Controller, Sensor, EnumDeviceType, EnumDeviceStatus
    from app.routers.controllers import get_controller
    from app.schemas.device import SensorResponse
    from unittest.mock import MagicMock
    import asyncio

    # Create a controller
    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.Controller,
        version="1.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=8080
    )
    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)

    # Create sensors
    sensor1 = Sensor(
        number_device=1,
        controller_id=controller.id,
        group_device=1,
        name_device="Sensor 1",
        type_device=EnumDeviceType.PIR,
        version="1.0",
        status=EnumDeviceStatus.ACTIVATED
    )
    test_db.add(sensor1)
    test_db.commit()

    # Mock current_user
    mock_user = MagicMock()

    # Get single controller with include_sensors=True
    response = asyncio.run(get_controller(
        controller_id=controller.id,
        include_sensors=True,
        current_user=mock_user,
        db=test_db
    ))

    # Verify sensors are included
    assert response.success is True
    assert response.data.sensors is not None
    assert len(response.data.sensors) == 1
    assert isinstance(response.data.sensors[0], SensorResponse)
