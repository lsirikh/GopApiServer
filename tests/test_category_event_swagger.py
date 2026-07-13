"""
Test: Swagger/OpenAPI documentation for category_event_mapping
PRD: PRD_CategoryEvent_Refactoring.md v1.1 - Phase CE-5

Phase CE-5: Swagger 문서 검증
- ActionItem CE-5.1: Swagger UI 확인
- GET Query Parameter에 Enum 값 목록 표시 검증
- POST/PATCH Request Body에 Enum 값 목록 표시 검증
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.enums import EnumMappingEventCategory


@pytest.fixture
def client():
    """Test client for OpenAPI schema verification"""
    return TestClient(app)


class TestOpenApiSchemaEnumMappingEventCategory:
    """CE-5.1: OpenAPI schema contains EnumMappingEventCategory"""

    def test_openapi_schema_contains_enum_mapping_event_category(self, client):
        """
        Test: OpenAPI schema includes EnumMappingEventCategory definition
        PRD: PRD_CategoryEvent_Refactoring.md v1.1 - Section 6.3
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_schema = response.json()

        # Check that components/schemas exists
        assert "components" in openapi_schema
        assert "schemas" in openapi_schema["components"]

        schemas = openapi_schema["components"]["schemas"]

        # Verify EnumMappingEventCategory is in schemas
        assert "EnumMappingEventCategory" in schemas

        enum_schema = schemas["EnumMappingEventCategory"]
        assert "enum" in enum_schema

        # Verify all 8 enum values are present
        expected_values = [
            "NONE",
            "FENCE_SENSOR_ONLY",
            "FENCE_SENSOR_WITH_MULTI_SENSOR",
            "MULTI_SENSOR_ONLY",
            "SENSOR_WITH_CAMERA",
            "SENSOR_WITH_AI_CAMERA",
            "AI_CAMERA_ONLY",
            "CAMERA_ONLY",
        ]

        for value in expected_values:
            assert value in enum_schema["enum"], f"Missing enum value: {value}"

    def test_openapi_event_mapping_create_schema_has_category_event_mapping(self, client):
        """
        Test: EventMappingCreate schema has category_event_mapping field
        """
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        schemas = openapi_schema["components"]["schemas"]

        assert "EventMappingCreate" in schemas
        create_schema = schemas["EventMappingCreate"]

        # Check properties
        assert "properties" in create_schema
        assert "category_event_mapping" in create_schema["properties"]

        # Verify reference to EnumMappingEventCategory
        category_prop = create_schema["properties"]["category_event_mapping"]
        # Can be direct ref or allOf
        if "$ref" in category_prop:
            assert "EnumMappingEventCategory" in category_prop["$ref"]
        elif "allOf" in category_prop:
            refs = [item.get("$ref", "") for item in category_prop["allOf"]]
            assert any("EnumMappingEventCategory" in ref for ref in refs)

    def test_openapi_event_mapping_response_schema_has_category_event_mapping(self, client):
        """
        Test: EventMappingResponse schema has category_event_mapping field
        """
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        schemas = openapi_schema["components"]["schemas"]

        assert "EventMappingResponse" in schemas
        response_schema = schemas["EventMappingResponse"]

        assert "properties" in response_schema
        assert "category_event_mapping" in response_schema["properties"]

    def test_openapi_event_mapping_update_schema_has_category_event_mapping(self, client):
        """
        Test: EventMappingUpdate schema has category_event_mapping field
        """
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        schemas = openapi_schema["components"]["schemas"]

        assert "EventMappingUpdate" in schemas
        update_schema = schemas["EventMappingUpdate"]

        assert "properties" in update_schema
        assert "category_event_mapping" in update_schema["properties"]


class TestOpenApiQueryParameterEnum:
    """CE-5.1: Query Parameter에 Enum 값 목록 표시"""

    def test_get_event_mappings_query_parameter_has_enum(self, client):
        """
        Test: GET /api/integrations/event-mappings has category_event_mapping query parameter with enum
        PRD: PRD_CategoryEvent_Refactoring.md v1.1 - Section 6.3
        """
        response = client.get("/openapi.json")
        openapi_schema = response.json()

        # Find the GET endpoint for event-mappings
        paths = openapi_schema.get("paths", {})
        event_mappings_path = paths.get("/api/integrations/event-mappings", {})
        get_operation = event_mappings_path.get("get", {})

        assert "parameters" in get_operation

        # Find category_event_mapping parameter
        category_param = None
        for param in get_operation["parameters"]:
            if param.get("name") == "category_event_mapping":
                category_param = param
                break

        assert category_param is not None, "category_event_mapping query parameter not found"
        assert category_param.get("in") == "query"

        # Verify schema reference or enum values
        if "schema" in category_param:
            schema = category_param["schema"]
            # Can be anyOf with null, or direct ref
            if "anyOf" in schema:
                refs = [item.get("$ref", "") for item in schema["anyOf"] if "$ref" in item]
                assert any("EnumMappingEventCategory" in ref for ref in refs)
            elif "$ref" in schema:
                assert "EnumMappingEventCategory" in schema["$ref"]


class TestEnumValuesMatchModel:
    """CE-5.1: OpenAPI Enum values match Python Enum"""

    def test_openapi_enum_values_match_python_enum(self, client):
        """
        Test: OpenAPI EnumMappingEventCategory values match Python EnumMappingEventCategory
        """
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        schemas = openapi_schema["components"]["schemas"]

        enum_schema = schemas["EnumMappingEventCategory"]
        openapi_values = set(enum_schema["enum"])

        # Get Python enum values
        python_values = set(e.value for e in EnumMappingEventCategory)

        assert openapi_values == python_values, (
            f"OpenAPI values {openapi_values} do not match Python values {python_values}"
        )

    def test_all_8_enum_values_in_openapi(self, client):
        """
        Test: All 8 EnumMappingEventCategory values are in OpenAPI schema
        PRD: PRD_CategoryEvent_Refactoring.md v1.1 - 8 sensor combination types
        """
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        schemas = openapi_schema["components"]["schemas"]

        enum_schema = schemas["EnumMappingEventCategory"]
        openapi_values = enum_schema["enum"]

        assert len(openapi_values) == 8, f"Expected 8 enum values, got {len(openapi_values)}"

        expected = [
            "NONE",
            "FENCE_SENSOR_ONLY",
            "FENCE_SENSOR_WITH_MULTI_SENSOR",
            "MULTI_SENSOR_ONLY",
            "SENSOR_WITH_CAMERA",
            "SENSOR_WITH_AI_CAMERA",
            "AI_CAMERA_ONLY",
            "CAMERA_ONLY",
        ]

        for expected_value in expected:
            assert expected_value in openapi_values, f"Missing: {expected_value}"
