"""
Tests for ServerCategories Router
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


# Test database setup - Use file-based SQLite for better session management
TEST_DATABASE_URL = "sqlite:///./test_server_categories.db"
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
    # Clean up test database file
    import os
    if os.path.exists("./test_server_categories.db"):
        os.remove("./test_server_categories.db")


@pytest.fixture(scope="function")
def db():
    """Create database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Clean up data after each test
        session.query(Server).delete()
        session.query(ServerCategory).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db):
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


class TestServerCategoriesGet:
    """Tests for GET /api/servers/categories"""

    def test_get_categories_empty(self, client, db):
        """빈 카테고리 목록 조회"""
        response = client.get("/api/servers/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_categories_with_data(self, client, db):
        """카테고리 목록 조회"""
        # Create test data
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            description="Video Management System",
            sort_order=1
        )
        db.add(category)
        db.commit()

        response = client.get("/api/servers/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "VMS 서버"
        assert data["data"][0]["type_server"] == "VMS"


class TestServerCategoryGetById:
    """Tests for GET /api/servers/categories/{id}"""

    def test_get_category_by_id(self, client, db):
        """카테고리 상세 조회"""
        category = ServerCategory(
            name="AI 분석 서버",
            type_server=EnumServerType.AI_ANALYSIS,
            description="AI Analysis Server",
            sort_order=2
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        response = client.get(f"/api/servers/categories/{category.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "AI 분석 서버"
        assert data["data"]["type_server"] == "AI_ANALYSIS"

    def test_get_category_not_found(self, client, db):
        """존재하지 않는 카테고리 조회"""
        response = client.get("/api/servers/categories/9999")
        assert response.status_code == 404

    def test_get_category_with_servers(self, client, db):
        """카테고리 조회 시 하위 서버 목록 포함"""
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
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080
        )
        db.add(server)
        db.commit()

        response = client.get(f"/api/servers/categories/{category.id}")
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data["data"]
        assert len(data["data"]["servers"]) == 1
        assert data["data"]["servers"][0]["name"] == "VMS-ab1120"


class TestServerCategoryCreate:
    """Tests for POST /api/servers/categories"""

    def test_create_category(self, client, db):
        """카테고리 생성"""
        payload = {
            "name": "VMS 서버",
            "type_server": "VMS",
            "description": "Video Management System",
            "sort_order": 1
        }
        response = client.post("/api/servers/categories", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "VMS 서버"
        assert data["data"]["type_server"] == "VMS"
        assert data["data"]["id"] is not None

    def test_create_category_minimal(self, client, db):
        """카테고리 최소 필드 생성"""
        payload = {
            "name": "AI 분석 서버",
            "type_server": "AI_ANALYSIS"
        }
        response = client.post("/api/servers/categories", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == "AI 분석 서버"
        assert data["data"]["sort_order"] == 0  # default

    def test_create_category_duplicate_type(self, client, db):
        """중복 type_server 생성 시 오류"""
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1
        )
        db.add(category)
        db.commit()

        payload = {
            "name": "VMS 서버 2",
            "type_server": "VMS"
        }
        response = client.post("/api/servers/categories", json=payload)
        assert response.status_code == 409

    def test_create_category_invalid_type(self, client, db):
        """유효하지 않은 type_server 생성 시 오류"""
        payload = {
            "name": "Invalid 서버",
            "type_server": "INVALID_TYPE"
        }
        response = client.post("/api/servers/categories", json=payload)
        assert response.status_code == 422


class TestServerCategoryUpdate:
    """Tests for PATCH /api/servers/categories/{id}"""

    def test_update_category_partial(self, client, db):
        """카테고리 부분 업데이트"""
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            description="Original description",
            sort_order=1
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        payload = {"description": "Updated description"}
        response = client.patch(f"/api/servers/categories/{category.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["description"] == "Updated description"
        assert data["data"]["name"] == "VMS 서버"  # unchanged

    def test_update_category_not_found(self, client, db):
        """존재하지 않는 카테고리 업데이트"""
        payload = {"name": "Updated Name"}
        response = client.patch("/api/servers/categories/9999", json=payload)
        assert response.status_code == 404


class TestServerCategoryReplace:
    """Tests for PUT /api/servers/categories/{id}"""

    def test_replace_category(self, client, db):
        """카테고리 전체 교체"""
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            description="Original",
            sort_order=1
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        payload = {
            "name": "VMS 서버 (수정)",
            "type_server": "VMS",
            "description": "Replaced description",
            "sort_order": 10
        }
        response = client.put(f"/api/servers/categories/{category.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "VMS 서버 (수정)"
        assert data["data"]["sort_order"] == 10


class TestServerCategoryDelete:
    """Tests for DELETE /api/servers/categories/{id}"""

    def test_delete_category(self, client, db):
        """카테고리 삭제"""
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        response = client.delete(f"/api/servers/categories/{category.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        response = client.get(f"/api/servers/categories/{category.id}")
        assert response.status_code == 404

    def test_delete_category_blocked_when_servers_attached(self, client, db):
        """소속 서버가 있으면 카테고리 삭제를 409 로 거부한다 (S4-01, 2026-08-07 계약 변경).

        ★ 계약 변경: 이전에는 FK `ON DELETE CASCADE` 로 **소속 서버가 함께 삭제**되고 200 을 반환했다.
          경고도 삭제 건수도 없어 실사고(VMS 서버 2대 소실)가 발생 → 비우고 지우는 2단계를 강제한다.
        """
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
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080
        )
        db.add(server)
        db.commit()

        response = client.delete(f"/api/servers/categories/{category.id}")
        assert response.status_code == 409

        # 카테고리도 서버도 그대로 남아 있어야 한다
        assert client.get(f"/api/servers/categories/{category.id}").status_code == 200
        assert db.query(Server).filter(Server.category_id == category.id).count() == 1

        # 서버를 먼저 정리하면 삭제된다
        db.delete(server)
        db.commit()
        assert client.delete(f"/api/servers/categories/{category.id}").status_code == 200
        assert client.get(f"/api/servers/categories/{category.id}").status_code == 404

    def test_delete_category_not_found(self, client, db):
        """존재하지 않는 카테고리 삭제"""
        response = client.delete("/api/servers/categories/9999")
        assert response.status_code == 404
