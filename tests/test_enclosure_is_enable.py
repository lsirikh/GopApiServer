"""
Tests for Enclosure is_enable Field Consistency
PRD: PRD_API_Spec_Compliance.md v1.0 - SPEC-004
TDD: Red -> Green -> Refactor
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient


class TestEnclosureSchemaIsEnable:
    """
    Phase SPEC-4.1: Enclosure Schema is_enable Field Tests

    다른 Device 타입(Controller, Sensor, Camera, Speaker)은 is_enable 필드를 가지고 있으나
    Enclosure만 is_enable 필드가 없어 일관성 문제 발생.
    """

    def test_enclosure_create_has_is_enable_field(self):
        """
        Test: EnclosureCreate 스키마에 is_enable 필드가 있어야 함
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        from app.schemas.device import EnclosureCreate

        # is_enable 필드가 있어야 함
        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test Enclosure",
            is_enable=True
        )
        assert hasattr(create_data, 'is_enable'), "EnclosureCreate must have 'is_enable' field"
        assert create_data.is_enable is True

    def test_enclosure_create_is_enable_default_true(self):
        """
        Test: EnclosureCreate의 is_enable 기본값은 True
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        from app.schemas.device import EnclosureCreate

        # is_enable 미지정 시 기본값 True
        create_data = EnclosureCreate(
            number_device=101,
            group_device=1,
            name_device="Test Enclosure"
        )
        assert create_data.is_enable is True, "is_enable default value should be True"

    def test_enclosure_update_has_is_enable_field(self):
        """
        Test: EnclosureUpdate 스키마에 is_enable 필드가 있어야 함
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        from app.schemas.device import EnclosureUpdate

        # is_enable 필드로 업데이트 가능해야 함
        update_data = EnclosureUpdate(is_enable=False)
        assert hasattr(update_data, 'is_enable'), "EnclosureUpdate must have 'is_enable' field"
        assert update_data.is_enable is False

    def test_enclosure_update_is_enable_optional(self):
        """
        Test: EnclosureUpdate의 is_enable 필드는 Optional
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        from app.schemas.device import EnclosureUpdate

        # is_enable 미지정 시 None
        update_data = EnclosureUpdate()
        assert update_data.is_enable is None, "is_enable should be None when not provided"

    def test_enclosure_response_has_is_enable_field(self):
        """
        Test: EnclosureResponse 스키마에 is_enable 필드가 있어야 함
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        from app.schemas.device import EnclosureResponse
        from app.utils.enums import EnumDoorStatus, EnumDeviceStatus

        now = datetime.now()
        response = EnclosureResponse(
            id=1,
            number_device=101,
            group_device=1,
            name_device="Test Enclosure",
            type_device="IoController",
            status=EnumDeviceStatus.ACTIVATED,
            door_status=EnumDoorStatus.CLOSED,
            detail_info=None,
            geolocation=None,
            threshold_config=None,
            heater_enabled=False,
            fan_enabled=False,
            is_enable=True,
            created_at=now,
            updated_at=now
        )
        assert hasattr(response, 'is_enable'), "EnclosureResponse must have 'is_enable' field"
        assert response.is_enable is True


class TestEnclosureApiIsEnable:
    """
    Phase SPEC-4.3: Enclosure API is_enable Field Tests
    """

    def test_create_enclosure_with_is_enable(self, client: TestClient):
        """
        Test: POST /api/devices/enclosures - is_enable 필드 포함 생성
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        response = client.post(
            "/api/devices/enclosures",
            json={
                "number_device": 201,
                "group_device": 1,
                "name_device": "Test Enclosure API",
                "is_enable": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_enable"] is True

    def test_create_enclosure_default_is_enable(self, client: TestClient):
        """
        Test: POST /api/devices/enclosures - is_enable 미지정 시 기본값 True
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        response = client.post(
            "/api/devices/enclosures",
            json={
                "number_device": 202,
                "group_device": 1,
                "name_device": "Test Enclosure Default"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_enable"] is True, "Default is_enable should be True"

    def test_update_enclosure_is_enable(self, client: TestClient, test_enclosure):
        """
        Test: PATCH /api/devices/enclosures/{id} - is_enable 필드 수정
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        response = client.patch(
            f"/api/devices/enclosures/{test_enclosure.id}",
            json={"is_enable": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_enable"] is False

    def test_get_enclosure_returns_is_enable(self, client: TestClient, test_enclosure):
        """
        Test: GET /api/devices/enclosures/{id} - is_enable 필드 응답에 포함
        PRD: PRD_API_Spec_Compliance.md - SPEC-004
        """
        response = client.get(f"/api/devices/enclosures/{test_enclosure.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "is_enable" in data["data"], "Response must include 'is_enable' field"
