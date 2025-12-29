"""
Tests for Server Summary (Dashboard) Router
TDD: Test First
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app.models.server import ServerCategory, Server
from app.utils.enums import EnumServerType, EnumServerStatus


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_server_summary.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup test database once for the module"""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("./test_server_summary.db"):
        os.remove("./test_server_summary.db")


@pytest.fixture(scope="function")
def db():
    """Create database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.query(Server).delete()
        session.query(ServerCategory).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db):
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


class TestServerSummary:
    """Tests for GET /api/servers/summary"""

    def test_get_summary_empty(self, client, db):
        """빈 요약 조회"""
        response = client.get("/api/servers/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_summary_with_categories(self, client, db):
        """카테고리별 요약 조회"""
        # Create categories
        vms_category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1
        )
        ai_category = ServerCategory(
            name="AI 분석 서버",
            type_server=EnumServerType.AI_ANALYSIS,
            sort_order=2
        )
        db.add_all([vms_category, ai_category])
        db.commit()
        db.refresh(vms_category)
        db.refresh(ai_category)

        # Create servers
        servers = [
            Server(
                category_id=vms_category.id,
                name="VMS-001",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.10",
                port=8080
            ),
            Server(
                category_id=vms_category.id,
                name="VMS-002",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.11",
                port=8080
            ),
            Server(
                category_id=ai_category.id,
                name="AI-001",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.20",
                port=8080
            ),
            Server(
                category_id=ai_category.id,
                name="AI-002",
                status=EnumServerStatus.WARNING,
                ip_address="192.168.1.21",
                port=8080
            ),
        ]
        db.add_all(servers)
        db.commit()

        response = client.get("/api/servers/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2

        # Check VMS summary
        vms_summary = next(c for c in data["data"] if c["type_server"] == "VMS")
        assert vms_summary["total"] == 2
        assert vms_summary["normal"] == 2
        assert vms_summary["warning"] == 0
        assert vms_summary["error"] == 0
        assert len(vms_summary["servers"]) == 2

        # Check AI summary
        ai_summary = next(c for c in data["data"] if c["type_server"] == "AI_ANALYSIS")
        assert ai_summary["total"] == 2
        assert ai_summary["normal"] == 1
        assert ai_summary["warning"] == 1
        assert ai_summary["error"] == 0

    def test_get_summary_with_error_status(self, client, db):
        """오류 상태 서버 포함 요약"""
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        servers = [
            Server(
                category_id=category.id,
                name="VMS-001",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.10",
                port=8080
            ),
            Server(
                category_id=category.id,
                name="VMS-002",
                status=EnumServerStatus.WARNING,
                ip_address="192.168.1.11",
                port=8080
            ),
            Server(
                category_id=category.id,
                name="VMS-003",
                status=EnumServerStatus.ERROR,
                ip_address="192.168.1.12",
                port=8080
            ),
        ]
        db.add_all(servers)
        db.commit()

        response = client.get("/api/servers/summary")
        assert response.status_code == 200
        data = response.json()

        summary = data["data"][0]
        assert summary["total"] == 3
        assert summary["normal"] == 1
        assert summary["warning"] == 1
        assert summary["error"] == 1

    def test_get_summary_order_by_sort_order(self, client, db):
        """sort_order 순으로 정렬"""
        category2 = ServerCategory(
            name="AI 서버",
            type_server=EnumServerType.AI_ANALYSIS,
            sort_order=2
        )
        category1 = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1
        )
        db.add_all([category2, category1])
        db.commit()

        response = client.get("/api/servers/summary")
        assert response.status_code == 200
        data = response.json()

        # First should be VMS (sort_order=1)
        assert data["data"][0]["type_server"] == "VMS"
        assert data["data"][1]["type_server"] == "AI_ANALYSIS"

    def test_get_summary_includes_server_details(self, client, db):
        """서버 상세 정보 포함"""
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        server = Server(
            category_id=category.id,
            name="VMS-001",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080,
            hostname="vms-server-01",
            cpu_usage=45.0,
            ram_usage=62.0,
            disk_usage=78.0,
            network_throughput="125MB/s"
        )
        db.add(server)
        db.commit()

        response = client.get("/api/servers/summary")
        assert response.status_code == 200
        data = response.json()

        server_data = data["data"][0]["servers"][0]
        assert server_data["name"] == "VMS-001"
        assert server_data["cpu_usage"] == 45.0
        assert server_data["ram_usage"] == 62.0
        assert server_data["disk_usage"] == 78.0
        assert server_data["network_throughput"] == "125MB/s"
