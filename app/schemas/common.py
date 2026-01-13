"""
Common Pydantic schemas for API responses
"""
from typing import Any, Optional, Dict, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar('T')


class ResponseMeta(BaseModel):
    """Response metadata with timestamp and request ID"""
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        json_schema_extra={"example": "2025-01-10T10:30:00.000Z"}
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


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format"""
    success: bool = True
    message: str
    data: T
    pagination: Optional[PaginationMeta] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


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
