"""
Common Pydantic schemas for API responses
"""
from typing import Any, Optional, Dict, Generic, TypeVar, Annotated
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, PlainSerializer, WithJsonSchema, model_validator

from app.utils.datetime import to_display, utc_now

# KST timezone (레거시 상수 — 저장/변환은 to_display/utc_now(DISPLAY_TZ) 사용)
KST = timezone(timedelta(hours=9))


def _kst_isoformat(v: datetime | None) -> str | None:
    """datetime → ISO 8601 in DISPLAY_TZ (datetime-unification: 저장 UTC → 출력 DISPLAY_TZ, DST 자동)."""
    d = to_display(v)
    return d.isoformat() if d is not None else None


# 응답 datetime 필드 공용 타입. WithJsonSchema: PlainSerializer(return_type=str)가 OpenAPI
# 응답 스키마의 format:date-time 을 없애는 회귀 복원(반론 4.5 / V-09).
KSTDatetime = Annotated[
    datetime,
    PlainSerializer(_kst_isoformat, return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "format": "date-time"}, mode="serialization"),
]


def _add_kst_recursive(obj: Any) -> Any:
    """dict/list 구조 내 모든 datetime 을 DISPLAY_TZ 로 변환(aware·naive 모두 — 반론 4.4)."""
    if isinstance(obj, dict):
        return {k: _add_kst_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_add_kst_recursive(v) for v in obj]
    elif isinstance(obj, datetime):
        return to_display(obj)
    return obj

T = TypeVar('T')


class ResponseMeta(BaseModel):
    """Response metadata with timestamp and request ID"""
    timestamp: KSTDatetime = Field(
        default_factory=utc_now,
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
