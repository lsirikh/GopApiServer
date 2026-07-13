"""
Test: 인증 API 엔드포인트 검증 (AccountUser 기반)

Phase 1 Auth Migration: OAuth2PasswordBearer → HTTPBearer
- POST /api/auth/login: JSON body (login_id, password) for AccountUser
- POST /api/auth/login/oauth2: [DEPRECATED] Form data for legacy User model
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
    app.include_router(auth_router, prefix="/api/auth")

    client = TestClient(app)
    # New login endpoint expects JSON, not form data
    response = client.post("/api/auth/login", json={})

    # Should not return 404 (endpoint exists) - will return 422 for missing fields
    assert response.status_code != 404


def test_login_with_valid_credentials_returns_token(test_db):
    """Test that valid credentials return a token (AccountUser model)"""
    from fastapi import FastAPI
    from app.routers.auth import router as auth_router
    from app.dependencies import get_db
    from app.models.user import AccountUser
    from app.utils.auth import hash_password

    # Create a test AccountUser
    test_user = AccountUser(
        login_id="testuser",
        password_hash=hash_password("testpass123"),
        name="Test User",
        role="OPERATOR",
        is_active=True,
        is_locked=False
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
    app.include_router(auth_router, prefix="/api/auth")

    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"login_id": "testuser", "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "token_type" in data["data"]


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
    app.include_router(auth_router, prefix="/api/auth")

    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"login_id": "nonexistent", "password": "wrongpass"}
    )

    assert response.status_code == 401


def test_login_response_format(test_db):
    """Test that login response has correct format (AccountUser model)"""
    from fastapi import FastAPI
    from app.routers.auth import router as auth_router
    from app.dependencies import get_db
    from app.models.user import AccountUser
    from app.utils.auth import hash_password

    # Create a test AccountUser
    test_user = AccountUser(
        login_id="testuser2",
        password_hash=hash_password("testpass123"),
        name="Test User 2",
        role="OPERATOR",
        is_active=True,
        is_locked=False
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
    app.include_router(auth_router, prefix="/api/auth")

    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"login_id": "testuser2", "password": "testpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"]["access_token"], str)
    assert data["data"]["token_type"] == "bearer"


def test_me_endpoint_with_valid_token(test_db):
    """
    Test: GET /api/auth/me returns authenticated AccountUser info with valid token
    """
    from fastapi import FastAPI
    from app.routers.auth import router as auth_router
    from app.dependencies import get_db
    from app.models.user import AccountUser
    from app.utils.auth import hash_password, create_access_token

    # Create a test AccountUser
    test_user = AccountUser(
        login_id="metest",
        password_hash=hash_password("password123"),
        name="Me Test User",
        role="ADMIN",
        is_active=True,
        is_locked=False
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)

    # Create a valid token
    token = create_access_token(data={"sub": "metest"})

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api/auth")

    client = TestClient(app)
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["login_id"] == "metest"
    assert data["role"] == "ADMIN"
    assert "password_hash" not in data, "Password should not be in response"


def test_me_endpoint_without_token_returns_401(test_db):
    """
    Test: GET /api/auth/me without token returns 401
    """
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
    app.include_router(auth_router, prefix="/api/auth")

    client = TestClient(app)
    response = client.get("/api/auth/me")

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def test_me_endpoint_with_invalid_token_returns_401(test_db):
    """
    Test: GET /api/auth/me with invalid token returns 401
    """
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
    app.include_router(auth_router, prefix="/api/auth")

    client = TestClient(app)
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
