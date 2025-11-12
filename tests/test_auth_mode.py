"""
Test: Authentication Mode Switching (AUTH_MODE environment variable)
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_auth_mode_token_requires_authentication(test_db, monkeypatch):
    """
    Test: When AUTH_MODE=token, endpoints require valid authentication

    Expected to fail initially (Red phase).
    """
    # Set AUTH_MODE to token and reload settings
    monkeypatch.setenv("AUTH_MODE", "token")

    # Force reload settings
    from app import config
    config.settings = config.Settings()

    from app.routers.auth import router as auth_router, get_current_user_optional
    from app.dependencies import get_db

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    # Create a test endpoint that uses optional auth
    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api")

    from fastapi import Depends

    @app.get("/api/test-protected")
    async def test_endpoint(user=Depends(get_current_user_optional)):
        if user is None:
            return {"message": "no auth"}
        return {"message": "authenticated", "username": user.username}

    client = TestClient(app)

    # Request without token should return 401 in token mode
    response = client.get("/api/test-protected")
    assert response.status_code == 401, f"Expected 401 in token mode without auth, got {response.status_code}"


def test_auth_mode_public_allows_no_authentication(test_db, monkeypatch):
    """
    Test: When AUTH_MODE=public, endpoints allow access without authentication

    Expected to fail initially (Red phase).
    """
    # Set AUTH_MODE to public and reload settings
    monkeypatch.setenv("AUTH_MODE", "public")

    # Force reload settings
    from app import config
    config.settings = config.Settings()

    from app.routers.auth import router as auth_router, get_current_user_optional
    from app.dependencies import get_db

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    # Create a test endpoint that uses optional auth
    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api")

    from fastapi import Depends

    @app.get("/api/test-public")
    async def test_endpoint(user=Depends(get_current_user_optional)):
        if user is None:
            return {"message": "no auth"}
        return {"message": "authenticated", "username": user.username}

    client = TestClient(app)

    # Request without token should succeed in public mode
    response = client.get("/api/test-public")
    assert response.status_code == 200, f"Expected 200 in public mode, got {response.status_code}"
    data = response.json()
    assert data["message"] == "no auth", "Should allow access without authentication in public mode"


def test_auth_mode_public_still_accepts_valid_token(test_db, monkeypatch):
    """
    Test: When AUTH_MODE=public, valid tokens are still accepted and processed

    Expected to fail initially (Red phase).
    """
    from app.models.user import User
    from app.utils.auth import hash_password, create_access_token

    # Create a test user FIRST (before any imports that might use settings)
    test_user = User(
        username="publictest",
        hashed_password=hash_password("password123"),
        role="user"
    )
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)

    # Now set AUTH_MODE to public and reload settings
    monkeypatch.setenv("AUTH_MODE", "public")

    # Force reload settings
    from app import config
    config.settings = config.Settings()

    from app.routers.auth import router as auth_router, get_current_user_optional
    from app.dependencies import get_db

    # Create a valid token
    token = create_access_token(data={"sub": "publictest"})

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    # Create a test endpoint that uses optional auth
    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router, prefix="/api")

    from fastapi import Depends

    @app.get("/api/test-public-with-token")
    async def test_endpoint(user=Depends(get_current_user_optional)):
        if user is None:
            return {"message": "no auth"}
        return {"message": "authenticated", "username": user.username}

    client = TestClient(app)

    # Request with valid token should return user data even in public mode
    response = client.get(
        "/api/test-public-with-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["message"] == "authenticated"
    assert data["username"] == "publictest"
