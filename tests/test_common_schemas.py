"""
Test: 공통 응답 스키마 검증
PRD: CS-2.3 Docstring 품질 검사
"""
import inspect
import os
import importlib
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


# ============================================================
# ApiSingleResponse Tests (PRD_ApiResponse_Split.md)
# ============================================================

def test_api_single_response_has_required_fields():
    """1.1: ApiSingleResponse should have success, message, data, meta fields"""
    from app.schemas.common import ApiSingleResponse

    assert issubclass(ApiSingleResponse, BaseModel), "ApiSingleResponse should be a Pydantic model"

    fields = ApiSingleResponse.model_fields
    assert "success" in fields, "ApiSingleResponse should have 'success' field"
    assert "message" in fields, "ApiSingleResponse should have 'message' field"
    assert "data" in fields, "ApiSingleResponse should have 'data' field"
    assert "meta" in fields, "ApiSingleResponse should have 'meta' field"

    # Functional test
    response = ApiSingleResponse(success=True, message="Test", data={"key": "value"})
    assert response.success is True
    assert response.message == "Test"
    assert response.data == {"key": "value"}
    assert response.meta is not None


def test_api_single_response_no_pagination():
    """1.2: ApiSingleResponse should NOT have pagination field"""
    from app.schemas.common import ApiSingleResponse

    fields = ApiSingleResponse.model_fields
    assert "pagination" not in fields, "ApiSingleResponse should NOT have 'pagination' field"


def test_api_response_still_has_pagination():
    """1.3: ApiResponse should still have pagination field (unchanged)"""
    from app.schemas.common import ApiResponse

    fields = ApiResponse.model_fields
    assert "pagination" in fields, "ApiResponse should still have 'pagination' field"


class TestSchemaPRDReferences:
    """Test: 스키마 클래스에 PRD Reference 포함 여부 확인 (CS-2.3)"""

    def test_schema_files_have_prd_reference_in_module_docstring(self):
        """
        Test: 주요 스키마 파일의 모듈 docstring에 PRD reference 포함 확인

        PRD reference 패턴:
        - PRD: PRD_xxx.md
        - PRD Reference: PRD_xxx.md
        - Based on PRD_xxx.md
        """
        from app.schemas import (
            device, event, integration, report, server,
            system_event, user, device_group, camera_preset,
            audit_log, config_change_log, file_group
        )

        schema_modules = [
            device, event, integration, report, server,
            system_event, user, device_group, camera_preset,
            audit_log, config_change_log, file_group
        ]

        prd_patterns = ['PRD:', 'PRD Reference:', 'Based on PRD', 'PRD_']

        files_with_prd = []
        files_without_prd = []

        for module in schema_modules:
            module_doc = module.__doc__ or ""
            has_prd = any(pattern in module_doc for pattern in prd_patterns)

            if has_prd:
                files_with_prd.append(module.__name__)
            else:
                files_without_prd.append(module.__name__)

        # 80% 이상의 스키마 파일에 PRD reference가 있어야 함
        total = len(schema_modules)
        with_prd = len(files_with_prd)
        coverage = with_prd / total * 100

        assert coverage >= 80, (
            f"PRD reference coverage is {coverage:.1f}% (expected >= 80%)\n"
            f"Files with PRD: {files_with_prd}\n"
            f"Files without PRD: {files_without_prd}"
        )
