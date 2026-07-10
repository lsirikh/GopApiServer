"""
Tests for Servers Router
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
TEST_DATABASE_URL = "sqlite:///./test_servers.db"
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
    if os.path.exists("./test_servers.db"):
        os.remove("./test_servers.db")


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


@pytest.fixture
def sample_category(db):
    """Create sample category for tests"""
    category = ServerCategory(
        name="VMS 서버",
        type_server=EnumServerType.VMS,
        sort_order=1
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


class TestServersGet:
    """Tests for GET /api/servers"""

    def test_get_servers_empty(self, client, db, sample_category):
        """빈 서버 목록 조회"""
        response = client.get("/api/servers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_servers_with_data(self, client, db, sample_category):
        """서버 목록 조회"""
        server = Server(
            category_id=sample_category.id,
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080
        )
        db.add(server)
        db.commit()

        response = client.get("/api/servers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "VMS-ab1120"

    def test_get_servers_filter_by_category(self, client, db, sample_category):
        """카테고리별 서버 필터링"""
        server = Server(
            category_id=sample_category.id,
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080
        )
        db.add(server)
        db.commit()

        response = client.get(f"/api/servers?category_id={sample_category.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    def test_get_servers_filter_by_status(self, client, db, sample_category):
        """상태별 서버 필터링"""
        server1 = Server(
            category_id=sample_category.id,
            name="VMS-001",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080
        )
        server2 = Server(
            category_id=sample_category.id,
            name="VMS-002",
            status=EnumServerStatus.WARNING,
            ip_address="192.168.1.11",
            port=8080
        )
        db.add_all([server1, server2])
        db.commit()

        response = client.get("/api/servers?status=NORMAL")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "NORMAL"


class TestServerGetById:
    """Tests for GET /api/servers/{id}"""

    def test_get_server_by_id(self, client, db, sample_category):
        """서버 상세 조회"""
        server = Server(
            category_id=sample_category.id,
            name="VMS-ab1120",
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
        db.refresh(server)

        response = client.get(f"/api/servers/{server.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "VMS-ab1120"
        assert data["data"]["cpu_usage"] == 45.0
        assert data["data"]["hostname"] == "vms-server-01"

    def test_get_server_not_found(self, client, db, sample_category):
        """존재하지 않는 서버 조회"""
        response = client.get("/api/servers/9999")
        assert response.status_code == 404


class TestServerCreate:
    """Tests for POST /api/servers"""

    def test_create_server(self, client, db, sample_category):
        """서버 생성"""
        payload = {
            "category_id": sample_category.id,
            "name": "VMS-ab1120",
            "status": "NORMAL",
            "ip_address": "192.168.1.10",
            "port": 8080,
            "hostname": "vms-server-01",
            "cpu_usage": 45.0,
            "ram_usage": 62.0,
            "disk_usage": 78.0,
            "network_throughput": "125MB/s"
        }
        response = client.post("/api/servers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "VMS-ab1120"
        assert data["data"]["id"] is not None

    def test_create_server_minimal(self, client, db, sample_category):
        """서버 최소 필드 생성"""
        payload = {
            "category_id": sample_category.id,
            "name": "VMS-ab1121",
            "ip_address": "192.168.1.11",
            "port": 8080
        }
        response = client.post("/api/servers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["status"] == "NORMAL"  # default
        assert data["data"]["hostname"] is None

    def test_create_server_invalid_category(self, client, db, sample_category):
        """존재하지 않는 카테고리로 서버 생성 시 오류"""
        payload = {
            "category_id": 9999,
            "name": "VMS-ab1122",
            "ip_address": "192.168.1.12",
            "port": 8080
        }
        response = client.post("/api/servers", json=payload)
        assert response.status_code == 404


class TestServerUpdate:
    """Tests for PATCH /api/servers/{id}"""

    def test_update_server_partial(self, client, db, sample_category):
        """서버 부분 업데이트 (메트릭 업데이트)"""
        server = Server(
            category_id=sample_category.id,
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080,
            cpu_usage=45.0
        )
        db.add(server)
        db.commit()
        db.refresh(server)

        payload = {
            "status": "WARNING",
            "cpu_usage": 85.0,
            "ram_usage": 78.0
        }
        response = client.patch(f"/api/servers/{server.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "WARNING"
        assert data["data"]["cpu_usage"] == 85.0
        assert data["data"]["ram_usage"] == 78.0
        assert data["data"]["name"] == "VMS-ab1120"  # unchanged

    def test_update_server_not_found(self, client, db, sample_category):
        """존재하지 않는 서버 업데이트"""
        payload = {"status": "ERROR"}
        response = client.patch("/api/servers/9999", json=payload)
        assert response.status_code == 404


class TestServerReplace:
    """Tests for PUT /api/servers/{id}"""

    def test_replace_server(self, client, db, sample_category):
        """서버 전체 교체"""
        server = Server(
            category_id=sample_category.id,
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080
        )
        db.add(server)
        db.commit()
        db.refresh(server)

        payload = {
            "category_id": sample_category.id,
            "name": "VMS-ab1120-updated",
            "status": "WARNING",
            "ip_address": "192.168.1.100",
            "port": 9090,
            "hostname": "new-hostname",
            "cpu_usage": 90.0,
            "ram_usage": 85.0,
            "disk_usage": 95.0,
            "network_throughput": "200MB/s"
        }
        response = client.put(f"/api/servers/{server.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "VMS-ab1120-updated"
        assert data["data"]["ip_address"] == "192.168.1.100"
        assert data["data"]["port"] == 9090


class TestServerDelete:
    """Tests for DELETE /api/servers/{id}"""

    def test_delete_server(self, client, db, sample_category):
        """서버 삭제"""
        server = Server(
            category_id=sample_category.id,
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080
        )
        db.add(server)
        db.commit()
        db.refresh(server)

        response = client.delete(f"/api/servers/{server.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        response = client.get(f"/api/servers/{server.id}")
        assert response.status_code == 404

    def test_delete_server_not_found(self, client, db, sample_category):
        """존재하지 않는 서버 삭제"""
        response = client.delete("/api/servers/9999")
        assert response.status_code == 404
