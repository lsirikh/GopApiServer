"""
Common Pydantic schemas for API responses
"""
from typing import Any, Optional, Dict, Generic, TypeVar, Annotated
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, PlainSerializer, model_validator

# KST timezone
KST = timezone(timedelta(hours=9))


def _kst_isoformat(v: datetime | None) -> str | None:
    """Serialize datetime to ISO 8601 with +09:00 (KST) timezone offset."""
    if v is None:
        return None
    if v.tzinfo is None:
        v = v.replace(tzinfo=KST)
    return v.isoformat()


# Use this type for all datetime fields in response schemas
KSTDatetime = Annotated[datetime, PlainSerializer(_kst_isoformat, return_type=str, when_used="json")]


def _add_kst_recursive(obj: Any) -> Any:
    """Recursively attach KST timezone to all naive datetimes in a dict/list structure."""
    if isinstance(obj, dict):
        return {k: _add_kst_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_add_kst_recursive(v) for v in obj]
    elif isinstance(obj, datetime) and obj.tzinfo is None:
        return obj.replace(tzinfo=KST)
    return obj

T = TypeVar('T')


class ResponseMeta(BaseModel):
    """Response metadata with timestamp and request ID"""
    timestamp: KSTDatetime = Field(
        default_factory=lambda: datetime.now(KST),
        json_schema_extra={"example": "2025-01-10T10:30:00.000+09:00"}
    )
    request_id: Optional[str] = Field(
        None,
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"}
    )


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1, description="Current page number", json_schema_extra={"example": 1})
    limit: int = Field(..., ge=1, le=100, description="Items per page", json_schema_extra={"example": 20})
    total: int = Field(..., ge=0, description="Total number of items", json_schema_extra={"example": 100})
    total_pages: int = Field(..., ge=0, description="Total number of pages", json_schema_extra={"example": 5})


class ApiSingleResponse(BaseModel, Generic[T]):
    """Standard API response format for single-item endpoints (no pagination)"""
    success: bool = True
    message: str
    data: T
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    @model_validator(mode="before")
    @classmethod
    def _localize_data(cls, values: Any) -> Any:
        if isinstance(values, dict) and "data" in values:
            values["data"] = _add_kst_recursive(values["data"])
        return values


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format for list endpoints (with pagination)"""
    success: bool = True
    message: str
    data: T
    pagination: Optional[PaginationMeta] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    @model_validator(mode="before")
    @classmethod
    def _localize_data(cls, values: Any) -> Any:
        if isinstance(values, dict) and "data" in values:
            values["data"] = _add_kst_recursive(values["data"])
        return values


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str = Field(..., description="에러 코드", json_schema_extra={"example": "NOT_FOUND"})
    message: str = Field(..., description="에러 메시지", json_schema_extra={"example": "Resource not found"})
    details: Optional[str] = Field(None, description="상세 정보", json_schema_extra={"example": "No device exists with the specified ID"})


class ApiErrorResponse(BaseModel):
    """Standard API error response format"""
    success: bool = Field(default=False, json_schema_extra={"example": False})
    error: Dict[str, Any] = Field(
        ...,
        description="에러 정보",
        json_schema_extra={"example": {"code": "NOT_FOUND", "message": "Resource not found", "details": "No device exists with the specified ID"}}
    )
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ValidationFieldError(BaseModel):
    """Validation field error detail"""
    field: str = Field(..., description="필드명", json_schema_extra={"example": "ip_address"})
    message: str = Field(..., description="에러 메시지", json_schema_extra={"example": "Invalid IP address format"})


class ValidationErrorDetail(BaseModel):
    """Validation error detail structure (422 Unprocessable Entity)"""
    code: str = Field(
        default="VALIDATION_ERROR",
        description="에러 코드",
        json_schema_extra={"example": "VALIDATION_ERROR"}
    )
    details: list[ValidationFieldError] = Field(
        ...,
        description="필드별 에러 목록",
        json_schema_extra={"example": [
            {"field": "ip_address", "message": "Invalid IP address format"},
            {"field": "number_device", "message": "Field required"}
        ]}
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response format (422 Unprocessable Entity)

    GOP_Restful_Api_연동설계.md 문서 기준
    """
    success: bool = Field(default=False, json_schema_extra={"example": False})
    message: str = Field(
        default="Validation error",
        description="에러 메시지",
        json_schema_extra={"example": "Validation error"}
    )
    error: ValidationErrorDetail = Field(
        ...,
        description="에러 상세 정보"
    )
