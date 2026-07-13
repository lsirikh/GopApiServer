"""
DeviceGroup Schema Tests (TDD - Red Phase)
PRD: PRD_Device_Structure_Refactoring.md - Phase 4
"""
import pytest
from pydantic import ValidationError


class TestDeviceGroupSchemaCreate:
    """DeviceGroupCreate 스키마 테스트"""

    def test_device_group_create_valid(self):
        """DeviceGroupCreate 유효성 테스트"""
        from app.schemas.device_group import DeviceGroupCreate

        data = DeviceGroupCreate(
            name="GOP 1구역",
            description="1구역 전방 감시 장비 그룹"
        )
        assert data.name == "GOP 1구역"
        assert data.description == "1구역 전방 감시 장비 그룹"

    def test_device_group_create_without_description(self):
        """DeviceGroupCreate description 없이 생성 테스트"""
        from app.schemas.device_group import DeviceGroupCreate

        data = DeviceGroupCreate(name="GOP 2구역")
        assert data.name == "GOP 2구역"
        assert data.description is None

    def test_device_group_create_name_required(self):
        """DeviceGroupCreate name 필수 테스트"""
        from app.schemas.device_group import DeviceGroupCreate

        with pytest.raises(ValidationError) as exc_info:
            DeviceGroupCreate()

        # name 필드 누락 에러 확인
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_device_group_create_name_max_length(self):
        """DeviceGroupCreate name 최대 길이 테스트 (200자)"""
        from app.schemas.device_group import DeviceGroupCreate

        # 200자 이하는 허용
        valid_name = "A" * 200
        data = DeviceGroupCreate(name=valid_name)
        assert len(data.name) == 200

        # 201자는 에러
        with pytest.raises(ValidationError):
            DeviceGroupCreate(name="A" * 201)

    def test_device_group_create_description_max_length(self):
        """DeviceGroupCreate description 최대 길이 테스트 (500자)"""
        from app.schemas.device_group import DeviceGroupCreate

        # 500자 이하는 허용
        valid_desc = "A" * 500
        data = DeviceGroupCreate(name="Test", description=valid_desc)
        assert len(data.description) == 500

        # 501자는 에러
        with pytest.raises(ValidationError):
            DeviceGroupCreate(name="Test", description="A" * 501)


class TestDeviceGroupSchemaUpdate:
    """DeviceGroupUpdate 스키마 테스트"""

    def test_device_group_update_partial(self):
        """DeviceGroupUpdate 부분 수정 테스트"""
        from app.schemas.device_group import DeviceGroupUpdate

        # name만 수정
        data = DeviceGroupUpdate(name="새로운 이름")
        assert data.name == "새로운 이름"
        assert data.description is None

        # description만 수정
        data = DeviceGroupUpdate(description="새로운 설명")
        assert data.name is None
        assert data.description == "새로운 설명"

    def test_device_group_update_all_fields(self):
        """DeviceGroupUpdate 모든 필드 수정 테스트"""
        from app.schemas.device_group import DeviceGroupUpdate

        data = DeviceGroupUpdate(
            name="업데이트된 이름",
            description="업데이트된 설명"
        )
        assert data.name == "업데이트된 이름"
        assert data.description == "업데이트된 설명"

    def test_device_group_update_empty(self):
        """DeviceGroupUpdate 빈 업데이트 허용 테스트"""
        from app.schemas.device_group import DeviceGroupUpdate

        data = DeviceGroupUpdate()
        assert data.name is None
        assert data.description is None


class TestDeviceGroupSchemaResponse:
    """DeviceGroupResponse 스키마 테스트"""

    def test_device_group_response_serialization(self):
        """DeviceGroupResponse 직렬화 테스트"""
        from app.schemas.device_group import DeviceGroupResponse
        from datetime import datetime

        now = datetime.now()
        data = DeviceGroupResponse(
            id=1,
            name="GOP 1구역",
            description="테스트 그룹",
            device_count=5,
            created_at=now,
            updated_at=now
        )
        assert data.id == 1
        assert data.name == "GOP 1구역"
        assert data.description == "테스트 그룹"
        assert data.device_count == 5
        assert data.created_at == now
        assert data.updated_at == now

    def test_device_group_response_device_count_default(self):
        """DeviceGroupResponse device_count 기본값 테스트"""
        from app.schemas.device_group import DeviceGroupResponse
        from datetime import datetime

        now = datetime.now()
        data = DeviceGroupResponse(
            id=1,
            name="GOP 1구역",
            created_at=now,
            updated_at=now
        )
        assert data.device_count == 0

    def test_device_group_response_with_devices(self):
        """DeviceGroupResponse devices 목록 포함 테스트"""
        from app.schemas.device_group import DeviceGroupDetailResponse, DeviceSummary
        from datetime import datetime

        now = datetime.now()
        devices = [
            DeviceSummary(id=1, number_device=1001, name_device="CTL-001", category_device="controller"),
            DeviceSummary(id=2, number_device=1002, name_device="CTL-002", category_device="controller"),
        ]

        data = DeviceGroupDetailResponse(
            id=1,
            name="GOP 1구역",
            description="테스트 그룹",
            device_count=2,
            devices=devices,
            created_at=now,
            updated_at=now
        )
        assert len(data.devices) == 2
        assert data.devices[0].number_device == 1001
        assert data.devices[1].name_device == "CTL-002"


class TestDeviceAssignSchemas:
    """디바이스 할당 관련 스키마 테스트"""

    def test_device_assign_request(self):
        """DeviceAssignRequest 테스트"""
        from app.schemas.device_group import DeviceAssignRequest

        data = DeviceAssignRequest(device_ids=[1, 2, 3])
        assert data.device_ids == [1, 2, 3]

    def test_device_assign_request_empty_list(self):
        """DeviceAssignRequest 빈 목록 테스트"""
        from app.schemas.device_group import DeviceAssignRequest

        with pytest.raises(ValidationError):
            DeviceAssignRequest(device_ids=[])

    def test_device_assign_response(self):
        """DeviceAssignResponse 테스트"""
        from app.schemas.device_group import DeviceAssignResponse

        data = DeviceAssignResponse(
            group_id=1,
            assigned_device_ids=[1, 2, 3],
            skipped_device_ids=[4],  # 이미 할당된 디바이스
            message="3개 디바이스 할당 완료, 1개 건너뜀"
        )
        assert data.group_id == 1
        assert len(data.assigned_device_ids) == 3
        assert data.skipped_device_ids == [4]


class TestDeviceSummarySchema:
    """DeviceSummary 스키마 테스트"""

    def test_device_summary_controller(self):
        """DeviceSummary Controller 타입 테스트"""
        from app.schemas.device_group import DeviceSummary

        data = DeviceSummary(
            id=1,
            number_device=1001,
            name_device="CTL-001",
            category_device="controller"
        )
        assert data.category_device == "controller"

    def test_device_summary_sensor(self):
        """DeviceSummary Sensor 타입 테스트"""
        from app.schemas.device_group import DeviceSummary

        data = DeviceSummary(
            id=2,
            number_device=2001,
            name_device="SNS-001",
            category_device="sensor"
        )
        assert data.category_device == "sensor"

    def test_device_summary_camera(self):
        """DeviceSummary Camera 타입 테스트"""
        from app.schemas.device_group import DeviceSummary

        data = DeviceSummary(
            id=3,
            number_device=3001,
            name_device="CAM-001",
            category_device="camera"
        )
        assert data.category_device == "camera"


class TestDeviceUnassignRequest:
    """DeviceUnassignRequest 스키마 테스트 (PRD_DeviceGroup_BulkUnassign §4.2)"""

    def test_should_pass_validation_when_device_ids_are_valid(self):
        from app.schemas.device_group import DeviceUnassignRequest

        req = DeviceUnassignRequest(device_ids=[1, 2, 3])
        assert req.device_ids == [1, 2, 3]

    def test_should_raise_when_device_ids_is_empty(self):
        from app.schemas.device_group import DeviceUnassignRequest

        with pytest.raises(ValidationError):
            DeviceUnassignRequest(device_ids=[])

    def test_should_raise_when_device_ids_exceeds_max_length(self):
        from app.schemas.device_group import DeviceUnassignRequest

        with pytest.raises(ValidationError):
            DeviceUnassignRequest(device_ids=list(range(1, 102)))  # 101개

    def test_should_pass_when_device_ids_is_exactly_max_length(self):
        from app.schemas.device_group import DeviceUnassignRequest

        req = DeviceUnassignRequest(device_ids=list(range(1, 101)))  # 100개
        assert len(req.device_ids) == 100

    def test_should_raise_when_device_ids_is_missing(self):
        from app.schemas.device_group import DeviceUnassignRequest

        with pytest.raises(ValidationError):
            DeviceUnassignRequest()  # type: ignore[call-arg]


class TestDeviceBulkRemoveResponse:
    """DeviceBulkRemoveResponse 스키마 테스트 (PRD_DeviceGroup_BulkUnassign §4.3)"""

    def test_should_serialize_all_three_classifications(self):
        from app.schemas.device_group import DeviceBulkRemoveResponse

        resp = DeviceBulkRemoveResponse(
            group_id=1,
            removed_device_ids=[1, 101],
            skipped_device_ids=[201],
            not_found_device_ids=[999],
            message="2개 해제 완료, 1개 건너뜀, 1개 없음",
        )
        assert resp.group_id == 1
        assert resp.removed_device_ids == [1, 101]
        assert resp.skipped_device_ids == [201]
        assert resp.not_found_device_ids == [999]

    def test_should_default_lists_to_empty_when_omitted(self):
        from app.schemas.device_group import DeviceBulkRemoveResponse

        resp = DeviceBulkRemoveResponse(group_id=1, message="0개 해제")
        assert resp.removed_device_ids == []
        assert resp.skipped_device_ids == []
        assert resp.not_found_device_ids == []

    def test_should_raise_when_group_id_or_message_missing(self):
        from app.schemas.device_group import DeviceBulkRemoveResponse

        with pytest.raises(ValidationError):
            DeviceBulkRemoveResponse(group_id=1)  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            DeviceBulkRemoveResponse(message="x")  # type: ignore[call-arg]
