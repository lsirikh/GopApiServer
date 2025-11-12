"""
Test: Controller API endpoints
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_get_controllers_returns_empty_list(test_db):
    """
    Test: GET /api/devices/controllers returns empty list when no data

    Expected to fail initially (Red phase).
    """
    # Import models first to ensure they're registered
    from app.models.device import Controller  # noqa: F401

    from app.routers.controllers import router as controllers_router
    from app.dependencies import get_db
    from app.routers.auth import get_current_user_optional

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    def override_auth():
        return None  # Public mode

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = override_auth
    app.include_router(controllers_router, prefix="/api")

    client = TestClient(app)
    response = client.get("/api/devices/controllers")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []
    assert "pagination" in data


def test_get_controllers_returns_list_with_data(test_db):
    """
    Test: GET /api/devices/controllers returns list of controllers

    Expected to fail initially (Red phase).
    """
    from app.routers.controllers import router as controllers_router
    from app.dependencies import get_db
    from app.routers.auth import get_current_user_optional
    from app.models.device import Controller, EnumDeviceType, EnumDeviceStatus

    # Create test controllers
    controller1 = Controller(
        number_device=1,
        group_device=1,
        name_device="Controller 1",
        type_device=EnumDeviceType.Controller,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.1",
        ip_port=8080
    )
    controller2 = Controller(
        number_device=2,
        group_device=1,
        name_device="Controller 2",
        type_device=EnumDeviceType.Controller,
        version="1.0.0",
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.2",
        ip_port=8080
    )
    test_db.add(controller1)
    test_db.add(controller2)
    test_db.commit()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    def override_auth():
        return None  # Public mode

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = override_auth
    app.include_router(controllers_router, prefix="/api")

    client = TestClient(app)
    response = client.get("/api/devices/controllers")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    assert data["data"][0]["name_device"] == "Controller 1"
    assert data["data"][1]["name_device"] == "Controller 2"


def test_get_controllers_pagination(test_db):
    """
    Test: GET /api/devices/controllers supports pagination

    Expected to fail initially (Red phase).
    """
    from app.routers.controllers import router as controllers_router
    from app.dependencies import get_db
    from app.routers.auth import get_current_user_optional
    from app.models.device import Controller, EnumDeviceType, EnumDeviceStatus

    # Create 5 test controllers
    for i in range(1, 6):
        controller = Controller(
            number_device=i,
            group_device=1,
            name_device=f"Controller {i}",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address=f"192.168.1.{i}",
            ip_port=8080
        )
        test_db.add(controller)
    test_db.commit()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    def override_auth():
        return None  # Public mode

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = override_auth
    app.include_router(controllers_router, prefix="/api")

    client = TestClient(app)

    # Test page 1, limit 3
    response = client.get("/api/devices/controllers?page=1&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["limit"] == 3
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["total_pages"] == 2

    # Test page 2, limit 3
    response = client.get("/api/devices/controllers?page=2&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["page"] == 2
