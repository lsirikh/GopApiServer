"""
Test: 공통 응답 스키마 검증
"""
from pydantic import BaseModel


def test_api_response_schema_exists():
    """Test that ApiResponse schema exists"""
    from app.schemas.common import ApiResponse

    assert issubclass(ApiResponse, BaseModel), "ApiResponse should be a Pydantic model"

    # Test required fields
    response = ApiResponse(success=True, message="Test", data={"test": "value"})
    assert response.success == True
    assert response.message == "Test"
    assert response.data == {"test": "value"}


def test_api_error_response_schema_exists():
    """Test that ApiErrorResponse schema exists"""
    from app.schemas.common import ApiErrorResponse

    assert issubclass(ApiErrorResponse, BaseModel), "ApiErrorResponse should be a Pydantic model"

    # Test structure
    error_response = ApiErrorResponse(
        success=False,
        error={"code": "NOT_FOUND", "message": "Resource not found"}
    )
    assert error_response.success == False
    assert error_response.error["code"] == "NOT_FOUND"


def test_pagination_meta_schema_exists():
    """Test that PaginationMeta schema exists"""
    from app.schemas.common import PaginationMeta

    assert issubclass(PaginationMeta, BaseModel), "PaginationMeta should be a Pydantic model"

    # Test pagination fields
    pagination = PaginationMeta(page=1, limit=20, total=100, total_pages=5)
    assert pagination.page == 1
    assert pagination.limit == 20
    assert pagination.total == 100
    assert pagination.total_pages == 5


def test_response_meta_schema_exists():
    """Test that ResponseMeta schema exists with timestamp and request_id"""
    from app.schemas.common import ResponseMeta
    from datetime import datetime

    assert issubclass(ResponseMeta, BaseModel), "ResponseMeta should be a Pydantic model"

    # Test meta fields
    meta = ResponseMeta(
        timestamp=datetime.now(),
        request_id="550e8400-e29b-41d4-a716-446655440000"
    )
    assert meta.timestamp is not None
    assert meta.request_id == "550e8400-e29b-41d4-a716-446655440000"
