"""
Test: MalfunctionEvent Field Normalization
PRD: PRD_Event_Field_Normalization.md v1.0

TDD 테스트: MalfunctionEvent의 케이블 위치 정보(first_start/end, second_start/end)가
별도 컬럼이 아닌 detail JSONB에 저장되도록 정규화

목표 구조:
- reason: 별도 컬럼 (EnumFaultType)
- detail: {"first_start": int, "first_end": int, "second_start": int, "second_end": int}
"""
import pytest
from fastapi.testclient import TestClient


class TestMalfunctionEventSchemaFieldNormalization:
    """Schema 레벨: MalfunctionEventCreate/Response/Update에서 케이블 위치 필드 제거"""

    def test_malfunction_event_create_schema_has_no_cable_position_fields(self):
        """Test: MalfunctionEventCreate에 first_start/end, second_start/end 필드 없음"""
        from app.schemas.event import MalfunctionEventCreate

        schema_fields = MalfunctionEventCreate.model_fields.keys()

        # 케이블 위치 필드가 별도 필드로 존재하지 않아야 함
        assert "first_start" not in schema_fields, \
            "MalfunctionEventCreate should NOT have 'first_start' field (moved to detail)"
        assert "first_end" not in schema_fields, \
            "MalfunctionEventCreate should NOT have 'first_end' field (moved to detail)"
        assert "second_start" not in schema_fields, \
            "MalfunctionEventCreate should NOT have 'second_start' field (moved to detail)"
        assert "second_end" not in schema_fields, \
            "MalfunctionEventCreate should NOT have 'second_end' field (moved to detail)"

        # detail 필드는 있어야 함
        assert "detail" in schema_fields, \
            "MalfunctionEventCreate should have 'detail' field for cable position info"

    def test_malfunction_event_response_schema_has_no_cable_position_fields(self):
        """Test: MalfunctionEventResponse에 first_start/end, second_start/end 필드 없음"""
        from app.schemas.event import MalfunctionEventResponse

        schema_fields = MalfunctionEventResponse.model_fields.keys()

        # 케이블 위치 필드가 별도 필드로 존재하지 않아야 함
        assert "first_start" not in schema_fields, \
            "MalfunctionEventResponse should NOT have 'first_start' field (moved to detail)"
        assert "first_end" not in schema_fields, \
            "MalfunctionEventResponse should NOT have 'first_end' field (moved to detail)"
        assert "second_start" not in schema_fields, \
            "MalfunctionEventResponse should NOT have 'second_start' field (moved to detail)"
        assert "second_end" not in schema_fields, \
            "MalfunctionEventResponse should NOT have 'second_end' field (moved to detail)"

        # reason과 detail 필드는 있어야 함
        assert "reason" in schema_fields, \
            "MalfunctionEventResponse should have 'reason' field (separate field)"
        assert "detail" in schema_fields, \
            "MalfunctionEventResponse should have 'detail' field for cable position info"

    def test_malfunction_event_update_schema_has_no_cable_position_fields(self):
        """Test: MalfunctionEventUpdate에 first_start/end, second_start/end 필드 없음"""
        from app.schemas.event import MalfunctionEventUpdate

        schema_fields = MalfunctionEventUpdate.model_fields.keys()

        # 케이블 위치 필드가 별도 필드로 존재하지 않아야 함
        assert "first_start" not in schema_fields, \
            "MalfunctionEventUpdate should NOT have 'first_start' field (moved to detail)"
        assert "first_end" not in schema_fields, \
            "MalfunctionEventUpdate should NOT have 'first_end' field (moved to detail)"
        assert "second_start" not in schema_fields, \
            "MalfunctionEventUpdate should NOT have 'second_start' field (moved to detail)"
        assert "second_end" not in schema_fields, \
            "MalfunctionEventUpdate should NOT have 'second_end' field (moved to detail)"


class TestMalfunctionEventModelFieldNormalization:
    """Model 레벨: MalfunctionEvent 테이블에서 케이블 위치 컬럼 제거"""

    def test_malfunction_event_model_has_no_cable_position_columns(self):
        """Test: MalfunctionEvent 모델에 first_start/end, second_start/end 컬럼 없음"""
        from app.models.event import MalfunctionEvent

        # 테이블 컬럼 확인
        columns = MalfunctionEvent.__table__.columns.keys()

        # 케이블 위치 컬럼이 존재하지 않아야 함
        assert "first_start" not in columns, \
            "MalfunctionEvent should NOT have 'first_start' column (moved to detail)"
        assert "first_end" not in columns, \
            "MalfunctionEvent should NOT have 'first_end' column (moved to detail)"
        assert "second_start" not in columns, \
            "MalfunctionEvent should NOT have 'second_start' column (moved to detail)"
        assert "second_end" not in columns, \
            "MalfunctionEvent should NOT have 'second_end' column (moved to detail)"

        # reason과 detail 컬럼은 있어야 함
        assert "reason" in columns, \
            "MalfunctionEvent should have 'reason' column (separate column)"
        assert "detail" in columns, \
            "MalfunctionEvent should have 'detail' column for cable position info"


class TestMalfunctionEventAPIFieldNormalization:
    """API 레벨: MalfunctionEvent CRUD 테스트 - detail에 케이블 위치 정보"""

    def test_post_malfunction_event_with_cable_position_in_detail(
        self, client: TestClient, test_db
    ):
        """Test: POST /api/events/malfunctions - detail에 케이블 위치 정보 포함"""
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # Create a test device
        device = Controller(
            number_device=1,
            group_device=1,
            name_device="Test Controller",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.1",
            ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # POST request with cable position in detail
        response = client.post(
            "/api/events/malfunctions",
            json={
                "type_event": "Fault",
                "device_id": device.id,
                "reason": "FAULT_CABLE_CUTTING",
                "detail": {
                    "first_start": 10,
                    "first_end": 15,
                    "second_start": 20,
                    "second_end": 25
                }
            }
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"

        data = response.json()
        assert data["success"] is True

        event_data = data["data"]

        # reason은 별도 필드로 반환
        assert "reason" in event_data
        assert event_data["reason"] == "FAULT_CABLE_CUTTING"

        # 케이블 위치 정보는 detail에 포함
        assert "detail" in event_data
        assert event_data["detail"] is not None
        assert event_data["detail"]["first_start"] == 10
        assert event_data["detail"]["first_end"] == 15
        assert event_data["detail"]["second_start"] == 20
        assert event_data["detail"]["second_end"] == 25

        # 케이블 위치 필드가 별도 필드로 존재하지 않아야 함
        assert "first_start" not in event_data, \
            "Response should NOT have 'first_start' as separate field"
        assert "first_end" not in event_data, \
            "Response should NOT have 'first_end' as separate field"

    def test_get_malfunction_event_returns_cable_position_in_detail(
        self, client: TestClient, test_db
    ):
        """Test: GET /api/events/malfunctions/{id} - detail에서 케이블 위치 정보 반환"""
        from app.models.device import Controller
        from app.models.event import MalfunctionEvent
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumFaultType

        # Create a test device
        device = Controller(
            number_device=2,
            group_device=1,
            name_device="Test Controller 2",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.2",
            ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # Create event with detail containing cable position
        event = MalfunctionEvent(
            category_event="malfunction",
            type_event="Fault",
            device_id=device.id,
            device_description=f"[{device.type_device.value}] {device.name_device}",
            action_reported="False",
            reason=EnumFaultType.FAULT_FENCE,
            detail={
                "first_start": 5,
                "first_end": 10,
                "second_start": 15,
                "second_end": 20
            }
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        # GET single event
        response = client.get(f"/api/events/malfunctions/{event.id}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

        data = response.json()
        event_data = data["data"]

        # reason은 별도 필드
        assert event_data["reason"] == "FAULT_FENCE"

        # 케이블 위치는 detail에서 반환
        assert "detail" in event_data
        assert event_data["detail"]["first_start"] == 5
        assert event_data["detail"]["first_end"] == 10
        assert event_data["detail"]["second_start"] == 15
        assert event_data["detail"]["second_end"] == 20

    def test_patch_malfunction_event_updates_cable_position_in_detail(
        self, client: TestClient, test_db
    ):
        """Test: PATCH /api/events/malfunctions/{id} - detail에서 케이블 위치 수정"""
        from app.models.device import Controller
        from app.models.event import MalfunctionEvent
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumFaultType

        # Create a test device
        device = Controller(
            number_device=3,
            group_device=1,
            name_device="Test Controller 3",
            type_device=EnumDeviceType.Controller,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.3",
            ip_port=8080
        )
        test_db.add(device)
        test_db.commit()
        test_db.refresh(device)

        # Create event with initial detail
        event = MalfunctionEvent(
            category_event="malfunction",
            type_event="Fault",
            device_id=device.id,
            device_description=f"[{device.type_device.value}] {device.name_device}",
            action_reported="False",
            reason=EnumFaultType.FAULT_CONTROLLER,
            detail={
                "first_start": 0,
                "first_end": 0,
                "second_start": 0,
                "second_end": 0
            }
        )
        test_db.add(event)
        test_db.commit()
        test_db.refresh(event)

        # PATCH to update detail
        response = client.patch(
            f"/api/events/malfunctions/{event.id}",
            json={
                "detail": {
                    "first_start": 100,
                    "first_end": 150,
                    "second_start": 200,
                    "second_end": 250
                }
            }
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

        data = response.json()
        event_data = data["data"]

        # detail이 업데이트되었는지 확인
        assert event_data["detail"]["first_start"] == 100
        assert event_data["detail"]["first_end"] == 150
        assert event_data["detail"]["second_start"] == 200
        assert event_data["detail"]["second_end"] == 250
