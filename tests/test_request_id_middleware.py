"""
Test: Request ID 미들웨어 검증
"""
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_request_id_middleware_exists():
    """Test that request_id middleware module exists"""
    from app.middleware.request_id import RequestIDMiddleware

    assert RequestIDMiddleware is not None
    assert callable(RequestIDMiddleware)


def test_request_id_auto_generated_if_missing():
    """Test that X-Request-ID is auto-generated if not provided"""
    from app.middleware.request_id import RequestIDMiddleware

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    # Verify it's a valid UUID
    request_id = response.headers["X-Request-ID"]
    try:
        uuid.UUID(request_id)
        assert True
    except ValueError:
        assert False, "X-Request-ID should be a valid UUID"


def test_request_id_preserved_if_provided():
    """Test that X-Request-ID is preserved if already provided"""
    from app.middleware.request_id import RequestIDMiddleware

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    provided_id = "550e8400-e29b-41d4-a716-446655440000"
    response = client.get("/test", headers={"X-Request-ID": provided_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == provided_id


def test_request_id_added_to_response_headers():
    """Test that X-Request-ID is added to response headers"""
    from app.middleware.request_id import RequestIDMiddleware

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")

    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0
