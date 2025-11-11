"""
Common Pydantic schemas for API responses
"""
from typing import Any, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    """Response metadata with timestamp and request ID"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class ApiResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    message: str
    data: Any
    pagination: Optional[PaginationMeta] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str
    message: str
    details: Optional[str] = None


class ApiErrorResponse(BaseModel):
    """Standard API error response format"""
    success: bool = False
    error: Dict[str, Any]
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
