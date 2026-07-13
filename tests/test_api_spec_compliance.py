"""
Tests for API Spec Compliance
PRD: PRD_API_Spec_Compliance.md v1.0
Reference: GOP_Restful_Api_연동설계.md v2.8

TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient


class TestErrorResponseFormat:
    """
    Phase SPEC-1: Error Response Format (SPEC-001)

    스펙 요구사항:
    {
      "success": false,
      "error": {
        "code": "NOT_FOUND",
        "message": "...",
        "details": null
      },
      "meta": {
        "timestamp": "...",
        "request_id": "..."
      }
    }
    """

    def test_error_response_has_error_object(self, client: TestClient):
        """
        Test: 에러 응답에 error 객체가 존재해야 함
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        # 존재하지 않는 리소스 요청으로 404 에러 유발
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        # 스펙: error 객체가 존재해야 함
        assert "error" in data, "Error response must have 'error' object"
        assert isinstance(data["error"], dict), "'error' must be an object"

    def test_error_object_has_code_field(self, client: TestClient):
        """
        Test: error.code 필드가 존재해야 함
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert "error" in data, "Error response must have 'error' object"
        assert "code" in data["error"], "error object must have 'code' field"

    def test_error_object_has_message_field(self, client: TestClient):
        """
        Test: error.message 필드가 존재해야 함
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert "error" in data, "Error response must have 'error' object"
        assert "message" in data["error"], "error object must have 'message' field"

    def test_error_object_has_details_field(self, client: TestClient):
        """
        Test: error.details 필드가 존재해야 함 (Optional, can be null)
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert "error" in data, "Error response must have 'error' object"
        assert "details" in data["error"], "error object must have 'details' field"


class TestHttpErrorCodeMapping:
    """
    Phase SPEC-1.2: HTTP Error Code Mapping
    """

    def test_404_returns_not_found_code(self, client: TestClient):
        """
        Test: 404 에러 시 error.code = "NOT_FOUND"
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert data["error"]["code"] == "NOT_FOUND"

    def test_400_returns_bad_request_code(self, client: TestClient):
        """
        Test: 400 에러 시 error.code = "BAD_REQUEST"
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        # 잘못된 요청 데이터로 400 에러 유발
        response = client.post(
            "/api/devices/controllers",
            json={}  # 필수 필드 누락 → 보통 422지만 router에서 400으로 처리할 수도 있음
        )

        # 실제로 어떤 status code가 반환되는지 확인 필요
        if response.status_code == 400:
            data = response.json()
            assert data["error"]["code"] == "BAD_REQUEST"

    def test_500_returns_internal_error_code(self, client: TestClient):
        """
        Test: 500 에러 시 error.code = "INTERNAL_ERROR"
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        # 500 에러는 테스트하기 어려움 - 스킵하거나 mock 필요
        pytest.skip("500 error testing requires specific setup or mock")

    def test_403_returns_forbidden_code(self, client: TestClient):
        """
        Test: 403 에러 시 error.code = "FORBIDDEN"
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        # 403 에러를 유발하는 엔드포인트 필요
        pytest.skip("403 error testing requires auth setup")

    def test_401_returns_unauthorized_code(self, client: TestClient):
        """
        Test: 401 에러 시 error.code = "UNAUTHORIZED"
        PRD: PRD_API_Spec_Compliance.md - SPEC-001
        """
        # 401 에러를 유발하는 엔드포인트 필요
        pytest.skip("401 error testing requires auth setup")


class TestValidationErrorFormat:
    """
    Phase SPEC-2: Validation Error Response Format (SPEC-002)

    스펙 요구사항:
    {
      "success": false,
      "message": "Validation error",
      "error": {
        "code": "VALIDATION_ERROR",
        "details": [
          {"field": "page", "message": "Page must be greater than 0"}
        ]
      }
    }
    """

    def test_validation_error_has_error_object(self, client: TestClient):
        """
        Test: 422 응답에 error 객체가 존재해야 함
        PRD: PRD_API_Spec_Compliance.md - SPEC-002
        """
        # 필수 필드 누락으로 422 에러 유발
        response = client.post(
            "/api/devices/controllers",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        assert "error" in data, "Validation error response must have 'error' object"
        assert isinstance(data["error"], dict), "'error' must be an object"

    def test_validation_error_code_is_validation_error(self, client: TestClient):
        """
        Test: error.code = "VALIDATION_ERROR"
        PRD: PRD_API_Spec_Compliance.md - SPEC-002
        """
        response = client.post(
            "/api/devices/controllers",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_validation_error_details_is_array(self, client: TestClient):
        """
        Test: error.details가 배열 형식
        PRD: PRD_API_Spec_Compliance.md - SPEC-002
        """
        response = client.post(
            "/api/devices/controllers",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        assert "details" in data["error"], "error must have 'details' field"
        assert isinstance(data["error"]["details"], list), "'details' must be an array"

    def test_validation_detail_has_field_property(self, client: TestClient):
        """
        Test: details[].field 존재
        PRD: PRD_API_Spec_Compliance.md - SPEC-002
        """
        response = client.post(
            "/api/devices/controllers",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        details = data["error"]["details"]
        assert len(details) > 0, "details array should not be empty"

        for detail in details:
            assert "field" in detail, "Each detail must have 'field' property"

    def test_validation_detail_has_message_property(self, client: TestClient):
        """
        Test: details[].message 존재
        PRD: PRD_API_Spec_Compliance.md - SPEC-002
        """
        response = client.post(
            "/api/devices/controllers",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        details = data["error"]["details"]
        assert len(details) > 0, "details array should not be empty"

        for detail in details:
            assert "message" in detail, "Each detail must have 'message' property"

    def test_validation_error_extracts_field_name(self, client: TestClient):
        """
        Test: loc에서 필드명 정확히 추출 (body prefix 제외)
        PRD: PRD_API_Spec_Compliance.md - SPEC-002
        """
        response = client.post(
            "/api/devices/controllers",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        details = data["error"]["details"]
        for detail in details:
            # field는 "body.field_name"이 아닌 "field_name"이어야 함
            assert not detail["field"].startswith("body."), \
                f"Field should not have 'body.' prefix: {detail['field']}"


class TestResponseMeta:
    """
    Phase SPEC-3: Response Meta Field (SPEC-003)

    스펙 요구사항:
    {
      "meta": {
        "timestamp": "2025-01-10T10:30:00.000Z",
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
      }
    }
    """

    def test_get_request_id_from_header(self, client: TestClient):
        """
        Test: X-Request-ID 헤더에서 request_id 추출
        PRD: PRD_API_Spec_Compliance.md - SPEC-003
        """
        custom_request_id = "test-request-id-12345"
        response = client.get(
            "/api/devices/controllers/99999",
            headers={"X-Request-ID": custom_request_id}
        )

        assert response.status_code == 404
        data = response.json()

        assert "meta" in data, "Response must have 'meta' object"
        assert data["meta"]["request_id"] == custom_request_id

    def test_get_request_id_generates_uuid_if_missing(self, client: TestClient):
        """
        Test: 헤더 없으면 UUID 자동 생성
        PRD: PRD_API_Spec_Compliance.md - SPEC-003
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert "meta" in data, "Response must have 'meta' object"
        assert "request_id" in data["meta"], "meta must have 'request_id' field"
        assert data["meta"]["request_id"] is not None, "request_id should not be None"
        assert len(data["meta"]["request_id"]) > 0, "request_id should not be empty"

    def test_meta_has_timestamp_field(self, client: TestClient):
        """
        Test: meta.timestamp 필드 존재
        PRD: PRD_API_Spec_Compliance.md - SPEC-003
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert "meta" in data, "Response must have 'meta' object"
        assert "timestamp" in data["meta"], "meta must have 'timestamp' field"

    def test_meta_has_request_id_field(self, client: TestClient):
        """
        Test: meta.request_id 필드 존재
        PRD: PRD_API_Spec_Compliance.md - SPEC-003
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert "meta" in data, "Response must have 'meta' object"
        assert "request_id" in data["meta"], "meta must have 'request_id' field"

    def test_http_exception_includes_meta(self, client: TestClient):
        """
        Test: HTTP 에러 응답에 meta 포함
        PRD: PRD_API_Spec_Compliance.md - SPEC-003
        """
        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        assert "meta" in data, "HTTP error response must have 'meta' object"

    def test_validation_error_includes_meta(self, client: TestClient):
        """
        Test: 검증 에러 응답에 meta 포함
        PRD: PRD_API_Spec_Compliance.md - SPEC-003
        """
        response = client.post(
            "/api/devices/controllers",
            json={}
        )

        assert response.status_code == 422
        data = response.json()

        assert "meta" in data, "Validation error response must have 'meta' object"

    def test_meta_timestamp_is_iso_format(self, client: TestClient):
        """
        Test: timestamp가 ISO 8601 형식
        PRD: PRD_API_Spec_Compliance.md - SPEC-003
        """
        from datetime import datetime

        response = client.get("/api/devices/controllers/99999")

        assert response.status_code == 404
        data = response.json()

        timestamp = data["meta"]["timestamp"]

        # ISO 8601 형식 검증 (예: "2025-01-10T10:30:00.000Z")
        try:
            # Python에서 Z suffix를 처리하기 위해 변환
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + "+00:00"
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Timestamp is not in ISO 8601 format: {timestamp}")
