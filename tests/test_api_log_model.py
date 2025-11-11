"""
Test: API 로그 모델 검증
"""
from datetime import datetime


def test_api_log_model_exists():
    """Test that ApiLog model exists"""
    from app.models.log import ApiLog

    assert ApiLog is not None
    assert hasattr(ApiLog, '__tablename__'), "ApiLog should have __tablename__"
    assert ApiLog.__tablename__ == "api_logs"


def test_api_log_has_required_fields():
    """Test that ApiLog has all required fields"""
    from app.models.log import ApiLog

    # Create instance to check fields
    log = ApiLog(
        timestamp=datetime.now(),
        resource="devices",
        method="POST",
        client_uuid="test-client-uuid",
        request_id="test-request-id",
        description="Create new controller",
        status_code=201,
        user_id=None
    )

    assert log.timestamp is not None
    assert log.resource == "devices"
    assert log.method == "POST"
    assert log.client_uuid == "test-client-uuid"
    assert log.request_id == "test-request-id"
    assert log.description == "Create new controller"
    assert log.status_code == 201


def test_api_log_timestamp_format():
    """Test that timestamp is stored properly"""
    from app.models.log import ApiLog

    now = datetime.now()
    log = ApiLog(
        timestamp=now,
        resource="test",
        method="GET",
        description="test"
    )

    assert isinstance(log.timestamp, datetime)
    assert log.timestamp == now
