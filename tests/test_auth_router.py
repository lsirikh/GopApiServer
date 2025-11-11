"""
Test: 인증 API 엔드포인트 검증
"""
from fastapi.testclient import TestClient


def test_login_endpoint_exists():
    """Test that POST /api/auth/login endpoint exists"""
    from fastapi import FastAPI
    from app.routers.auth import router as auth_router
    from app.dependencies import get_db

    def override_get_db():
        pass

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api")

    client = TestClient(app)
    response = client.post("/api/auth/login")

    # Should not return 404 (endpoint exists)
    assert response.status_code != 404


def test_login_with_valid_credentials_returns_token(test_db):
    """Test that valid credentials return a token"""
    from fastapi import FastAPI
    from app.routers.auth import router as auth_router
    from app.dependencies import get_db
    from app.models.user import User
    from app.utils.auth import hash_password

    # Create a test user
    test_user = User(
        username="testuser",
        hashed_password=hash_password("testpass123"),
        role="user"
    )
    test_db.add(test_user)
    test_db.commit()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api")

    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_login_with_invalid_credentials_returns_401(test_db):
    """Test that invalid credentials return 401"""
    from fastapi import FastAPI
    from app.routers.auth import router as auth_router
    from app.dependencies import get_db

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api")

    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        data={"username": "nonexistent", "password": "wrongpass"}
    )

    assert response.status_code == 401


def test_login_response_format(test_db):
    """Test that login response has correct format {access_token, token_type}"""
    from fastapi import FastAPI
    from app.routers.auth import router as auth_router
    from app.dependencies import get_db
    from app.models.user import User
    from app.utils.auth import hash_password

    # Create a test user
    test_user = User(
        username="testuser2",
        hashed_password=hash_password("testpass123"),
        role="user"
    )
    test_db.add(test_user)
    test_db.commit()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api")

    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser2", "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["access_token"], str)
    assert data["token_type"] == "bearer"
