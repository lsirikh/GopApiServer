"""
Pytest fixtures and configuration
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
# Import all models to register them with Base
# v5.3 Phase 1: Legacy User 모델 제거됨 (AccountUser로 통합)
from app.models.user import AccountUser, UserGroup, UserSession, UserLoginLog, UserGroupGrant  # noqa: F401
from app.models.log import ApiLog  # noqa: F401
from app.models.device import Controller, Sensor, Camera, Speaker, Enclosure, Lamp  # noqa: F401
from app.models.device_group import DeviceGroup, DeviceGroupMapping  # noqa: F401
from app.models.event import DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent  # noqa: F401
from app.models.integration import EventMapping, EventMappingCamera, EventMappingSpeaker, EventMappingLamp  # noqa: F401
from app.models.server import ServerCategory, Server  # noqa: F401
from app.models.camera_preset import CameraPreset, ROI, XyPoint  # noqa: F401
from app.models.file_group import FileGroup  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.config_change_log import ConfigChangeLog  # noqa: F401
from app.models.report import ReportGeneration, ReportTemplate  # noqa: F401
from app.models.device_setting import ProxySetting, CameraSetting  # noqa: F401
from app.models.thumbnail import Thumbnail  # noqa: F401
from app.models.tracking import TrackPoint  # noqa: F401
from app.models.token_blacklist import TokenBlacklist  # noqa: F401
from app.models.app_settings import AppSettings  # noqa: F401


def pytest_configure(config):
    """TEST-01 (2026-07-10): 운영 DB 오염 방지 안전장치.

    DATABASE_URL 이 sqlite 가 아닌(=실 DB) 상태에서 테스트를 돌리면 운영 데이터가 파괴될 수 있다.
    비-sqlite DB 대상 실행은 **명시적 opt-in**(ALLOW_DB_TESTS=1) 을 요구해 사고를 구조적으로 차단.
    (전용 test Postgres 로 통합 테스트를 돌릴 때만 의도적으로 설정.)
    """
    import os
    import pytest as _pytest
    url = os.environ.get("DATABASE_URL", "")
    if url and "sqlite" not in url.lower() and os.environ.get("ALLOW_DB_TESTS") != "1":
        raise _pytest.UsageError(
            f"[safety] DATABASE_URL 이 sqlite 가 아닙니다 ({url[:40]}...). "
            "운영 DB 오염 방지 — 통합 테스트는 ALLOW_DB_TESTS=1 을 명시해 opt-in 하세요."
        )


# Global test engine using StaticPool to share connection across all sessions
_test_engine = None
_TestingSessionLocal = None


def get_test_engine():
    """Get or create the shared test engine"""
    global _test_engine, _TestingSessionLocal
    if _test_engine is None:
        # Use StaticPool to ensure all connections share the same in-memory database
        _test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        # Enable foreign key support for SQLite
        @event.listens_for(_test_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        _TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
    return _test_engine, _TestingSessionLocal


@pytest.fixture(scope="function", autouse=True)
def _reset_settings_cache():
    """settings_service 모듈 캐시는 전역이라 함수 스코프 test_db 간 오염될 수 있음.
    각 테스트 전후로 비워 로그인 등이 자기 test_db 값(또는 기본값)을 읽도록 보장."""
    from app.services import settings_service
    settings_service.invalidate_cache()
    yield
    settings_service.invalidate_cache()


@pytest.fixture(scope="function")
def test_db():
    """
    Create a test database for each test function
    """
    engine, TestingSessionLocal = get_test_engine()

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


# Alias for db_session (compatibility)
@pytest.fixture(scope="function")
def db_session(test_db):
    """Alias for test_db fixture"""
    return test_db


@pytest.fixture(scope="function")
def client(test_db, monkeypatch):
    """Create a test client with test database"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.dependencies import get_db
    from app.config import settings
    from app.routers.auth import get_current_account_user, get_current_account_user_optional
    from app.models.user import AccountUser
    from app.utils.auth import hash_password

    # Set AUTH_MODE to public for tests (no authentication required)
    monkeypatch.setattr(settings, "AUTH_MODE", "public")

    # Create and persist a mock admin user for authenticated endpoints
    mock_admin = AccountUser(
        login_id="test_admin",
        password_hash=hash_password("test1234"),
        name="Test Admin",
        role="ADMIN"
    )
    test_db.add(mock_admin)
    test_db.commit()
    test_db.refresh(mock_admin)

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    def override_get_current_account_user():
        return mock_admin

    def override_get_current_account_user_optional():
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_account_user] = override_get_current_account_user
    app.dependency_overrides[get_current_account_user_optional] = override_get_current_account_user_optional
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# Async fixtures — v6.0 async 라우터/서비스 테스트 지원 (dual-stack: sync 유지)
# ============================================================================

@pytest_asyncio.fixture
async def async_db():
    """AsyncSession fixture — v6.0 async 라우터/서비스 테스트 지원.

    실제 Postgres(AsyncSessionLocal) 사용. 각 테스트 후 rollback으로 격리.
    """
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.rollback()


@pytest_asyncio.fixture
async def async_client():
    """httpx.AsyncClient fixture — v6.0 async 엔드포인트 통합 테스트용.

    ASGI 앱 직접 마운트 (네트워크 미사용).
    """
    from app.main import app
    async with AsyncClient(app=app, base_url="https://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(async_client):
    """ADMIN 계정 access_token 발급 fixture — 로그인 필수 엔드포인트 테스트용."""
    resp = await async_client.post(
        "/api/auth/login",
        json={"login_id": "admin", "password": "admin123"},
    )
    return resp.json()["data"]["access_token"]


@pytest.fixture(scope="function")
def test_controller(test_db):
    """Create a test controller for sensor tests"""
    from app.models.device import Controller
    from app.utils.enums import EnumDeviceType, EnumDeviceStatus

    controller = Controller(
        number_device=1,
        group_device=1,
        name_device="Test Controller",
        type_device=EnumDeviceType.IoController,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.1.100",
        ip_port=8080
    )
    test_db.add(controller)
    test_db.commit()
    test_db.refresh(controller)
    return controller


@pytest.fixture(scope="function")
def test_camera(test_db):
    """Create a test camera for preset tests"""
    from app.models.device import Camera
    from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

    camera = Camera(
        # Device base fields
        number_device=1,
        group_device=1,
        name_device="Test Camera",
        type_device=EnumDeviceType.IpCamera,
        status=EnumDeviceStatus.ACTIVATED,
        # Camera-specific fields
        ip_address="192.168.1.100",
        ip_port=80,
        mode=EnumCameraMode.ONVIF,
        category=EnumCameraType.PTZ,
        # PRD_Camera_Urls_JsonB.md: urls JSONB (replaces rtsp_uri/rtsp_port)
        urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}}}
    )
    test_db.add(camera)
    test_db.commit()
    test_db.refresh(camera)
    return camera


@pytest.fixture(scope="function")
def test_preset(test_db, test_camera):
    """Create a test preset for ROI tests"""
    from app.models.camera_preset import CameraPreset

    preset = CameraPreset(
        camera_id=test_camera.id,
        camera_name=test_camera.name_device,
        preset_index=1,
        preset_name="Test Preset",
        touring_time=10
    )
    test_db.add(preset)
    test_db.commit()
    test_db.refresh(preset)
    return preset


@pytest.fixture(scope="function")
def test_roi(test_db, test_preset):
    """Create a test ROI for XyPoint tests"""
    from app.models.camera_preset import ROI

    roi = ROI(
        preset_id=test_preset.id,
        name="Test ROI",
        resolution_width=1920,
        resolution_height=1080,
        is_enable=True
    )
    test_db.add(roi)
    test_db.commit()
    test_db.refresh(roi)
    return roi


@pytest.fixture(scope="function")
def test_enclosure(test_db):
    """Create a test enclosure for enclosure API tests"""
    from app.models.device import Enclosure
    from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumDoorStatus

    enclosure = Enclosure(
        # Device base fields
        number_device=101,
        group_device=1,
        name_device="Test Enclosure",
        type_device=EnumDeviceType.IoController,
        status=EnumDeviceStatus.ACTIVATED,
        # Enclosure-specific fields
        door_status=EnumDoorStatus.CLOSED,
        # detail_info removed → use enclosure_metrics API (PRD_Enclosure_Metrics_Separation.md v1.0)
        geolocation={"location": "GOP 3초소", "latitude": 38.1234, "longitude": 127.5678},
        threshold_config={"temp_high": 40.0, "temp_low": -10.0},
        heater_enabled=False,
        fan_enabled=False
    )
    test_db.add(enclosure)
    test_db.commit()
    test_db.refresh(enclosure)
    return enclosure


@pytest.fixture(scope="function")
def test_speaker(test_db):
    """Create a test speaker for EventMappingSpeaker tests"""
    from app.models.device import Speaker
    from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

    speaker = Speaker(
        number_device=2401,
        group_device=0,
        name_device="Test Speaker",
        type_device=EnumDeviceType.IpSpeaker,
        status=EnumDeviceStatus.ACTIVATED,
        speaker_type=EnumSpeakerType.NORMAL,
        description="Test speaker for unit tests"
    )
    test_db.add(speaker)
    test_db.commit()
    test_db.refresh(speaker)
    return speaker


@pytest.fixture(scope="function")
def test_server(test_db):
    """Create a test server for FileGroup tests"""
    from app.models.server import Server, ServerCategory
    from app.utils.enums import EnumServerType, EnumServerStatus

    # Create server category first
    category = ServerCategory(
        id=10,
        name="Speaker API Server",
        type_server=EnumServerType.SPEAKER_API,
        description="Speaker API Server Category"
    )
    test_db.add(category)
    test_db.commit()

    server = Server(
        category_id=category.id,
        name="Test Speaker Server",
        status=EnumServerStatus.NORMAL,
        ip_address="192.168.1.100",
        port=8080,
        hostname="speaker-srv-01"
    )
    test_db.add(server)
    test_db.commit()
    test_db.refresh(server)
    return server


@pytest.fixture(scope="function")
def test_file_group(test_db, test_server):
    """Create a test file group for EventMappingSpeaker tests"""
    from app.models.file_group import FileGroup

    file_group = FileGroup(
        server_id=test_server.id,
        group_id=1,
        group_name="Test File Group",
        files=["test_audio_01.mp3", "test_audio_02.mp3"]
    )
    test_db.add(file_group)
    test_db.commit()
    test_db.refresh(file_group)
    return file_group


@pytest.fixture(scope="function")
def test_lamp(test_db):
    """Create a test lamp for EventMappingLamp tests"""
    from app.models.device import Lamp
    from app.utils.enums import EnumDeviceType, EnumDeviceStatus

    lamp = Lamp(
        number_device=9001,
        group_device=1,
        name_device="Test Lamp",
        type_device=EnumDeviceType.Lamp,
        status=EnumDeviceStatus.ACTIVATED,
        ip_address="192.168.10.50",
        ip_port=80,
        description="Test lamp for unit tests"
    )
    test_db.add(lamp)
    test_db.commit()
    test_db.refresh(lamp)
    return lamp
