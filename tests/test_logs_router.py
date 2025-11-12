"""
Tests for log viewing API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.log import ApiLog

client = TestClient(app)


@pytest.fixture(scope="function")
def test_logs():
    """
    Create test log entries in the database
    """
    db = SessionLocal()
    try:
        # Clear existing logs
        db.query(ApiLog).delete()
        db.commit()

        # Create 15 test logs
        for i in range(15):
            log = ApiLog(
                resource=f"devices/controller{i % 3}",
                method="GET" if i % 2 == 0 else "POST",
                client_uuid=f"client-uuid-{i % 5}",
                request_id=f"req-{i}",
                description=f"Test log entry {i}",
                status_code=200,
                user_id=1
            )
            db.add(log)
        db.commit()

        yield

    finally:
        # Cleanup
        db.query(ApiLog).delete()
        db.commit()
        db.close()


def test_logs_endpoint_exists():
    """
    Test: GET /api/logs endpoint exists and returns 200 status

    This is the first test for Phase 3.4 - verifying the endpoint exists.
    Expected to fail initially (Red phase).
    """
    response = client.get("/api/logs")

    # Should return 200 OK or 401 Unauthorized (if auth required)
    # For now, we expect the endpoint to exist
    assert response.status_code in [200, 401], \
        f"Expected 200 or 401, got {response.status_code}"


def test_logs_pagination(test_logs):
    """
    Test: Logs endpoint supports pagination with skip and limit parameters

    Expected to fail initially (Red phase).
    """
    # Test default pagination (should return first 10 logs)
    response = client.get("/api/logs")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Expected list of logs"
    assert len(data) <= 10, "Default limit should be 10 or less"

    # Test custom limit
    response = client.get("/api/logs?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5, f"Expected 5 logs, got {len(data)}"

    # Test skip parameter
    response = client.get("/api/logs?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5, f"Expected 5 logs (from position 10), got {len(data)}"

    # Verify different data is returned
    response_first = client.get("/api/logs?skip=0&limit=3")
    response_second = client.get("/api/logs?skip=3&limit=3")

    first_ids = [log["id"] for log in response_first.json()]
    second_ids = [log["id"] for log in response_second.json()]

    assert set(first_ids).isdisjoint(set(second_ids)), \
        "Pagination should return different records"


def test_logs_date_range_filtering(test_logs):
    """
    Test: Logs endpoint supports filtering by date range

    Expected to fail initially (Red phase).
    """
    from datetime import datetime, timedelta

    # Get a reference timestamp
    now = datetime.utcnow()
    yesterday = (now - timedelta(days=1)).isoformat()
    tomorrow = (now + timedelta(days=1)).isoformat()

    # Test filtering with date range
    response = client.get(f"/api/logs?start_date={yesterday}&end_date={tomorrow}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Expected list of logs"

    # All returned logs should be within the date range
    for log in data:
        log_time = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
        assert log_time >= datetime.fromisoformat(yesterday), \
            f"Log timestamp {log_time} is before start_date {yesterday}"
        assert log_time <= datetime.fromisoformat(tomorrow), \
            f"Log timestamp {log_time} is after end_date {tomorrow}"

    # Test filtering with only start_date
    response = client.get(f"/api/logs?start_date={yesterday}")
    assert response.status_code == 200
    data = response.json()

    for log in data:
        log_time = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
        assert log_time >= datetime.fromisoformat(yesterday), \
            f"Log timestamp {log_time} is before start_date {yesterday}"

    # Test filtering with only end_date
    response = client.get(f"/api/logs?end_date={tomorrow}")
    assert response.status_code == 200
    data = response.json()

    for log in data:
        log_time = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
        assert log_time <= datetime.fromisoformat(tomorrow), \
            f"Log timestamp {log_time} is after end_date {tomorrow}"


def test_logs_method_filtering(test_logs):
    """
    Test: Logs endpoint supports filtering by HTTP method

    Expected to fail initially (Red phase).
    """
    # Test filtering by GET method
    response = client.get("/api/logs?method=GET")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Expected list of logs"
    assert len(data) > 0, "Expected at least one GET log"

    for log in data:
        assert log["method"] == "GET", f"Expected GET, got {log['method']}"

    # Test filtering by POST method
    response = client.get("/api/logs?method=POST")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0, "Expected at least one POST log"

    for log in data:
        assert log["method"] == "POST", f"Expected POST, got {log['method']}"

    # Verify that different methods return different results
    get_response = client.get("/api/logs?method=GET&limit=100")
    post_response = client.get("/api/logs?method=POST&limit=100")

    get_count = len(get_response.json())
    post_count = len(post_response.json())

    # We created 15 test logs: 8 GET (even indices) and 7 POST (odd indices)
    # But the test requests themselves also get logged, so counts will be higher
    # Just verify that both methods return logs and they're different
    assert get_count >= 8, f"Expected at least 8 GET logs, got {get_count}"
    assert post_count >= 7, f"Expected at least 7 POST logs, got {post_count}"
    assert get_count != post_count, "GET and POST should have different counts"


def test_logs_resource_filtering(test_logs):
    """
    Test: Logs endpoint supports filtering by resource

    Expected to fail initially (Red phase).
    """
    # Test filtering by specific resource
    response = client.get("/api/logs?resource=devices/controller0")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Expected list of logs"
    assert len(data) > 0, "Expected at least one log for controller0"

    for log in data:
        assert log["resource"] == "devices/controller0", \
            f"Expected devices/controller0, got {log['resource']}"

    # Test filtering by another resource
    response = client.get("/api/logs?resource=devices/controller1")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0, "Expected at least one log for controller1"

    for log in data:
        assert log["resource"] == "devices/controller1", \
            f"Expected devices/controller1, got {log['resource']}"

    # Test filtering by controller2
    response = client.get("/api/logs?resource=devices/controller2&limit=100")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 5, "Expected at least 5 logs for controller2"  # indices 2,5,8,11,14

    for log in data:
        assert log["resource"] == "devices/controller2", \
            f"Expected devices/controller2, got {log['resource']}"


def test_logs_client_uuid_filtering(test_logs):
    """
    Test: Logs endpoint supports filtering by client_uuid

    Expected to fail initially (Red phase).
    """
    # Test filtering by specific client UUID
    response = client.get("/api/logs?client_uuid=client-uuid-0")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Expected list of logs"
    assert len(data) > 0, "Expected at least one log for client-uuid-0"

    for log in data:
        assert log["client_uuid"] == "client-uuid-0", \
            f"Expected client-uuid-0, got {log['client_uuid']}"

    # Test filtering by another client UUID
    response = client.get("/api/logs?client_uuid=client-uuid-1")
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0, "Expected at least one log for client-uuid-1"

    for log in data:
        assert log["client_uuid"] == "client-uuid-1", \
            f"Expected client-uuid-1, got {log['client_uuid']}"

    # Test filtering by client-uuid-4
    response = client.get("/api/logs?client_uuid=client-uuid-4&limit=100")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 3, "Expected at least 3 logs for client-uuid-4"  # indices 4,9,14

    for log in data:
        assert log["client_uuid"] == "client-uuid-4", \
            f"Expected client-uuid-4, got {log['client_uuid']}"
