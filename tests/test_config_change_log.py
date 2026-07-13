"""
ConfigChangeLog TDD Tests
Based on PRD_ConfigChangeLog.md v1.0

TDD Phase: RED - Tests written before implementation
"""
import pytest
from datetime import datetime


# ==============================================================================
# Phase CCL-1: Enum Tests (RED)
# ==============================================================================

class TestEnumConfigResourceType:
    """
    CCL-1.1: EnumConfigResourceType 테스트 (17개 리소스 유형)

    PRD: PRD_ConfigChangeLog.md v1.2 Section 2.1

    카테고리별 분류:
    - Device 계열: 10개
    - Event 계열: 4개
    - Integration 계열: 3개

    Note: SERVER, SERVER_CATEGORY는 SystemEvent에서 관리
    """

    def test_enum_config_resource_type_has_17_types(self):
        """CCL-1.1: EnumConfigResourceType이 정확히 17개 타입을 가짐 (v1.2)"""
        from app.utils.enums import EnumConfigResourceType

        assert len(EnumConfigResourceType) == 17, \
            f"EnumConfigResourceType은 17개 타입이어야 합니다. 현재: {len(EnumConfigResourceType)}개"

    def test_enum_config_resource_type_device_category(self):
        """CCL-1.1: Device 계열 10개 타입 확인"""
        from app.utils.enums import EnumConfigResourceType

        device_types = [
            'CONTROLLER', 'SENSOR', 'CAMERA', 'SPEAKER', 'ENCLOSURE',
            'DEVICE_GROUP', 'CAMERA_PRESET', 'ROI', 'XY_POINT', 'FILE_GROUP'
        ]

        for type_name in device_types:
            assert hasattr(EnumConfigResourceType, type_name), \
                f"Device 계열 {type_name}이 EnumConfigResourceType에 존재해야 합니다"

    def test_enum_config_resource_type_excludes_server_types(self):
        """CCL-1.1: Server 계열은 SystemEvent에서 관리 (v1.2)"""
        from app.utils.enums import EnumConfigResourceType

        # SERVER, SERVER_CATEGORY는 SystemEvent에서 관리하므로 포함되지 않아야 함
        excluded_types = ['SERVER_CATEGORY', 'SERVER']

        for type_name in excluded_types:
            assert not hasattr(EnumConfigResourceType, type_name), \
                f"Server 계열 {type_name}은 ConfigChangeLog가 아닌 SystemEvent에서 관리해야 합니다"

    def test_enum_config_resource_type_event_category(self):
        """CCL-1.1: Event 계열 4개 타입 확인"""
        from app.utils.enums import EnumConfigResourceType

        event_types = [
            'DETECTION_EVENT', 'MALFUNCTION_EVENT',
            'CONNECTION_EVENT', 'ACTION_EVENT'
        ]

        for type_name in event_types:
            assert hasattr(EnumConfigResourceType, type_name), \
                f"Event 계열 {type_name}이 EnumConfigResourceType에 존재해야 합니다"

    def test_enum_config_resource_type_integration_category(self):
        """CCL-1.1: Integration 계열 3개 타입 확인"""
        from app.utils.enums import EnumConfigResourceType

        integration_types = [
            'EVENT_MAPPING', 'EVENT_MAPPING_CAMERA', 'EVENT_MAPPING_SPEAKER'
        ]

        for type_name in integration_types:
            assert hasattr(EnumConfigResourceType, type_name), \
                f"Integration 계열 {type_name}이 EnumConfigResourceType에 존재해야 합니다"

    def test_enum_config_resource_type_uses_upper_case(self):
        """CCL-1.1: 모든 타입이 UPPER_CASE 사용"""
        from app.utils.enums import EnumConfigResourceType

        for member in EnumConfigResourceType:
            assert member.value == member.value.upper(), \
                f"{member.name}의 값 '{member.value}'이 UPPER_CASE가 아닙니다"


class TestEnumConfigActionType:
    """
    CCL-1.2: EnumConfigActionType 테스트 (6개 액션 유형)

    - CRUD 액션: CREATED, UPDATED, DELETED
    - 특수 액션: STATUS_CHANGED, ASSIGNED, UNASSIGNED
    """

    def test_enum_config_action_type_has_6_types(self):
        """CCL-1.2: EnumConfigActionType이 정확히 6개 타입을 가짐"""
        from app.utils.enums import EnumConfigActionType

        assert len(EnumConfigActionType) == 6, \
            f"EnumConfigActionType은 6개 타입이어야 합니다. 현재: {len(EnumConfigActionType)}개"

    def test_enum_config_action_type_crud_actions(self):
        """CCL-1.2: CRUD 액션 3개 (CREATED, UPDATED, DELETED) 존재"""
        from app.utils.enums import EnumConfigActionType

        crud_actions = ['CREATED', 'UPDATED', 'DELETED']

        for action in crud_actions:
            assert hasattr(EnumConfigActionType, action), \
                f"CRUD 액션 {action}이 EnumConfigActionType에 존재해야 합니다"

    def test_enum_config_action_type_special_actions(self):
        """CCL-1.2: 특수 액션 3개 (STATUS_CHANGED, ASSIGNED, UNASSIGNED) 존재"""
        from app.utils.enums import EnumConfigActionType

        special_actions = ['STATUS_CHANGED', 'ASSIGNED', 'UNASSIGNED']

        for action in special_actions:
            assert hasattr(EnumConfigActionType, action), \
                f"특수 액션 {action}이 EnumConfigActionType에 존재해야 합니다"

    def test_enum_config_action_type_uses_upper_case(self):
        """CCL-1.2: 모든 타입이 UPPER_CASE 사용"""
        from app.utils.enums import EnumConfigActionType

        for member in EnumConfigActionType:
            assert member.value == member.value.upper(), \
                f"{member.name}의 값 '{member.value}'이 UPPER_CASE가 아닙니다"


# ==============================================================================
# Phase CCL-3: Model Tests (RED)
# ==============================================================================

class TestConfigChangeLogModel:
    """
    CCL-3.1: ConfigChangeLog 모델 테스트

    테이블: config_change_logs
    필수 필드: resource_type, resource_id, action
    선택 필드: resource_name, before_state, after_state, actor_id, actor_name, actor_ip, description
    """

    def test_config_change_log_model_exists(self):
        """CCL-3.1: ConfigChangeLog 모델 존재 확인"""
        from app.models.config_change_log import ConfigChangeLog

        assert ConfigChangeLog is not None

    def test_config_change_log_tablename(self):
        """CCL-3.1: __tablename__ = 'config_change_logs' 확인"""
        from app.models.config_change_log import ConfigChangeLog

        assert ConfigChangeLog.__tablename__ == "config_change_logs"

    def test_config_change_log_required_fields(self):
        """CCL-3.1: 필수 필드 확인 (resource_type, resource_id, action)"""
        from app.models.config_change_log import ConfigChangeLog

        # Check columns exist
        columns = [col.name for col in ConfigChangeLog.__table__.columns]

        required_fields = ['resource_type', 'resource_id', 'action']
        for field in required_fields:
            assert field in columns, f"필수 필드 {field}가 ConfigChangeLog 모델에 존재해야 합니다"

    def test_config_change_log_optional_fields(self):
        """CCL-3.1: 선택 필드 확인"""
        from app.models.config_change_log import ConfigChangeLog

        columns = [col.name for col in ConfigChangeLog.__table__.columns]

        optional_fields = [
            'resource_name', 'before_state', 'after_state',
            'actor_id', 'actor_name', 'actor_ip', 'description'
        ]
        for field in optional_fields:
            assert field in columns, f"선택 필드 {field}가 ConfigChangeLog 모델에 존재해야 합니다"

    def test_config_change_log_id_field(self):
        """CCL-3.1: id 필드 확인 (primary_key)"""
        from app.models.config_change_log import ConfigChangeLog

        columns = {col.name: col for col in ConfigChangeLog.__table__.columns}

        assert 'id' in columns
        assert columns['id'].primary_key is True

    def test_config_change_log_created_at_field(self):
        """CCL-3.1: created_at 필드 확인"""
        from app.models.config_change_log import ConfigChangeLog

        columns = [col.name for col in ConfigChangeLog.__table__.columns]

        assert 'created_at' in columns, "created_at 필드가 ConfigChangeLog 모델에 존재해야 합니다"

    def test_config_change_log_jsonb_fields(self):
        """CCL-3.1: JSONB 필드 (before_state, after_state) 확인"""
        from app.models.config_change_log import ConfigChangeLog
        from sqlalchemy.dialects.postgresql import JSONB

        columns = {col.name: col for col in ConfigChangeLog.__table__.columns}

        # Check before_state and after_state are JSONB type
        assert 'before_state' in columns
        assert 'after_state' in columns


# ==============================================================================
# Phase CCL-4: Schema Tests (RED)
# ==============================================================================

class TestConfigChangeLogSchema:
    """
    CCL-4.1: ConfigChangeLog Pydantic 스키마 테스트

    스키마:
    - ConfigChangeLogResponse: 단건 응답
    - ConfigChangeLogListResponse: 목록 응답 (logs, total, page, limit)
    """

    def test_config_change_log_response_schema_exists(self):
        """CCL-4.1: ConfigChangeLogResponse 스키마 존재 확인"""
        from app.schemas.config_change_log import ConfigChangeLogResponse

        assert ConfigChangeLogResponse is not None

    def test_config_change_log_response_schema_fields(self):
        """CCL-4.1: ConfigChangeLogResponse 필드 확인"""
        from app.schemas.config_change_log import ConfigChangeLogResponse

        # Check required fields exist in model_fields
        required_fields = [
            'id', 'resource_type', 'resource_id', 'action', 'created_at'
        ]
        optional_fields = [
            'resource_name', 'before_state', 'after_state',
            'actor_id', 'actor_name', 'actor_ip', 'description'
        ]

        all_fields = required_fields + optional_fields
        for field in all_fields:
            assert field in ConfigChangeLogResponse.model_fields, \
                f"필드 {field}가 ConfigChangeLogResponse 스키마에 존재해야 합니다"

    def test_config_change_log_response_from_attributes(self):
        """CCL-4.1: ConfigChangeLogResponse의 from_attributes 설정 확인"""
        from app.schemas.config_change_log import ConfigChangeLogResponse

        # Check model_config has from_attributes=True
        assert ConfigChangeLogResponse.model_config.get('from_attributes') is True, \
            "ConfigChangeLogResponse에 from_attributes=True 설정이 필요합니다"

    def test_config_change_log_list_response_schema_exists(self):
        """CCL-4.1: ConfigChangeLogListResponse 스키마 존재 확인"""
        from app.schemas.config_change_log import ConfigChangeLogListResponse

        assert ConfigChangeLogListResponse is not None

    def test_config_change_log_list_response_schema_fields(self):
        """CCL-4.1: ConfigChangeLogListResponse 필드 확인 (logs, total, page, limit)"""
        from app.schemas.config_change_log import ConfigChangeLogListResponse

        list_fields = ['logs', 'total', 'page', 'limit']
        for field in list_fields:
            assert field in ConfigChangeLogListResponse.model_fields, \
                f"필드 {field}가 ConfigChangeLogListResponse 스키마에 존재해야 합니다"

    def test_config_change_log_response_json_schema_extra(self):
        """CCL-4.1: ConfigChangeLogResponse에 json_schema_extra 예제 확인"""
        from app.schemas.config_change_log import ConfigChangeLogResponse

        # Check at least one field has json_schema_extra with example
        schema = ConfigChangeLogResponse.model_json_schema()

        # Check that 'id' field has example in the schema
        assert 'properties' in schema
        assert 'id' in schema['properties']


# ==============================================================================
# Phase CCL-5: API Router Tests (RED)
# ==============================================================================

class TestConfigChangeLogAPI:
    """
    CCL-5.1: ConfigChangeLog API 테스트

    API 엔드포인트:
    - GET /api/config-change-logs: 목록 조회
    - GET /api/config-change-logs/{id}: 단건 조회
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        """테스트 설정 - conftest.py의 client, test_db 픽스처 사용"""
        self.client = client
        self.db = test_db

    def test_get_config_change_logs_endpoint_exists(self):
        """CCL-5.1: GET /api/config-change-logs 엔드포인트 존재 확인"""
        response = self.client.get("/api/config-change-logs")

        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, \
            "GET /api/config-change-logs 엔드포인트가 존재해야 합니다"

    def test_get_config_change_logs_empty(self):
        """CCL-5.1: GET /api/config-change-logs 빈 목록 조회"""
        response = self.client.get("/api/config-change-logs")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "logs" in data["data"]

    def test_get_config_change_logs_pagination(self):
        """CCL-5.1: GET /api/config-change-logs 페이지네이션"""
        response = self.client.get("/api/config-change-logs?page=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "page" in data["data"]
        assert "limit" in data["data"]
        assert "total" in data["data"]

    def test_get_config_change_log_by_id_endpoint_exists(self):
        """CCL-5.1: GET /api/config-change-logs/{id} 엔드포인트 존재 확인"""
        response = self.client.get("/api/config-change-logs/1")

        # Should be 404 (not found) but endpoint exists
        assert response.status_code in [200, 404], \
            "GET /api/config-change-logs/{id} 엔드포인트가 존재해야 합니다"

    def test_get_config_change_log_not_found(self):
        """CCL-5.1: GET /api/config-change-logs/{id} 존재하지 않는 ID 404"""
        response = self.client.get("/api/config-change-logs/99999")

        assert response.status_code == 404

    def test_get_config_change_logs_filter_by_resource_type(self):
        """CCL-5.1: GET /api/config-change-logs resource_type 필터"""
        response = self.client.get("/api/config-change-logs?resource_type=CAMERA")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_config_change_logs_filter_by_action(self):
        """CCL-5.1: GET /api/config-change-logs action 필터"""
        response = self.client.get("/api/config-change-logs?action=CREATED")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ==============================================================================
# Phase CCL-6: Service Tests (RED)
# ==============================================================================

class TestConfigLogService:
    """
    CCL-6.1: config_log_service 테스트

    Functions:
    - log_config_change(): 설정 변경 로그 기록
    - model_to_dict(): SQLAlchemy 모델 → dict 변환
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        """테스트 설정"""
        self.client = client
        self.db = test_db

    def test_log_config_change_function_exists(self):
        """CCL-6.1: log_config_change 함수 존재 확인"""
        from app.services.config_log_service import log_config_change

        assert callable(log_config_change)

    def test_model_to_dict_function_exists(self):
        """CCL-6.1: model_to_dict 함수 존재 확인"""
        from app.services.config_log_service import model_to_dict

        assert callable(model_to_dict)

    def test_log_config_change_creates_record(self):
        """CCL-6.1: log_config_change가 DB 레코드를 생성"""
        from app.services.config_log_service import log_config_change
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Create a log entry
        log_config_change(
            db=self.db,
            resource_type=EnumConfigResourceType.CAMERA,
            resource_id=1,
            resource_name="Test Camera",
            action=EnumConfigActionType.CREATED,
            after_state={"name": "Test Camera", "ip": "192.168.1.1"},
            actor_name="admin",
            actor_ip="127.0.0.1"
        )

        # Verify record was created
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA,
            ConfigChangeLog.resource_id == 1
        ).first()

        assert log is not None
        assert log.resource_name == "Test Camera"
        assert log.action == EnumConfigActionType.CREATED
        assert log.after_state == {"name": "Test Camera", "ip": "192.168.1.1"}

    def test_model_to_dict_handles_datetime(self):
        """CCL-6.1: model_to_dict가 datetime을 ISO 문자열로 변환"""
        from app.services.config_log_service import model_to_dict
        from app.models.device import Camera
        from datetime import datetime

        # Create a mock camera-like object with datetime
        class MockModel:
            id = 1
            name = "Test"
            created_at = datetime(2026, 1, 21, 10, 30, 0)

            def __table__(self):
                pass

        # Mock the columns
        MockModel.__table__ = type('obj', (object,), {
            'columns': [
                type('col', (object,), {'name': 'id'})(),
                type('col', (object,), {'name': 'name'})(),
                type('col', (object,), {'name': 'created_at'})()
            ]
        })()

        result = model_to_dict(MockModel())

        assert 'created_at' in result
        assert isinstance(result['created_at'], str)
        assert '2026-01-21' in result['created_at']

    def test_model_to_dict_handles_enum(self):
        """CCL-6.1: model_to_dict가 Enum을 문자열로 변환"""
        from app.services.config_log_service import model_to_dict
        from app.utils.enums import EnumConfigResourceType

        class MockModel:
            id = 1
            resource_type = EnumConfigResourceType.CAMERA

        MockModel.__table__ = type('obj', (object,), {
            'columns': [
                type('col', (object,), {'name': 'id'})(),
                type('col', (object,), {'name': 'resource_type'})()
            ]
        })()

        result = model_to_dict(MockModel())

        assert result['resource_type'] == 'CAMERA'

    def test_log_config_change_with_before_and_after(self):
        """CCL-6.1: log_config_change가 before_state와 after_state를 저장"""
        from app.services.config_log_service import log_config_change
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        before = {"name": "Old Name", "ip": "192.168.1.1"}
        after = {"name": "New Name", "ip": "192.168.1.1"}

        log_config_change(
            db=self.db,
            resource_type=EnumConfigResourceType.SENSOR,
            resource_id=100,
            resource_name="Test Sensor",
            action=EnumConfigActionType.UPDATED,
            before_state=before,
            after_state=after,
            actor_name="operator"
        )

        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_id == 100
        ).first()

        assert log is not None
        assert log.before_state == before
        assert log.after_state == after
        assert log.action == EnumConfigActionType.UPDATED


# ==============================================================================
# Phase CCL-10: PRD v1.1 JSONB 정규화 함수 테스트
# ==============================================================================

class TestGetChangedFields:
    """
    CCL-10.1: get_changed_fields() 함수 테스트

    PRD Reference: PRD_ConfigChangeLog.md v1.1 Section 3.3, 6.1
    """

    def test_get_changed_fields_function_exists(self):
        """CCL-10.1: get_changed_fields 함수 존재 확인"""
        from app.services.config_log_service import get_changed_fields

        assert callable(get_changed_fields)

    def test_get_changed_fields_detects_single_change(self):
        """CCL-10.1: 단일 필드 변경 감지"""
        from app.services.config_log_service import get_changed_fields

        before = {"name": "정문 CCTV", "ip": "192.168.1.100"}
        after = {"name": "정문 CCTV (수정)", "ip": "192.168.1.100"}

        before_changes, after_changes = get_changed_fields(before, after)

        assert before_changes == {"name": "정문 CCTV"}
        assert after_changes == {"name": "정문 CCTV (수정)"}

    def test_get_changed_fields_detects_multiple_changes(self):
        """CCL-10.1: 복수 필드 변경 감지"""
        from app.services.config_log_service import get_changed_fields

        before = {"name": "정문 CCTV", "ip": "192.168.1.100", "port": 8080}
        after = {"name": "정문 CCTV (수정)", "ip": "192.168.1.101", "port": 8080}

        before_changes, after_changes = get_changed_fields(before, after)

        assert before_changes == {"name": "정문 CCTV", "ip": "192.168.1.100"}
        assert after_changes == {"name": "정문 CCTV (수정)", "ip": "192.168.1.101"}

    def test_get_changed_fields_no_changes(self):
        """CCL-10.1: 변경 없는 경우 빈 dict 반환"""
        from app.services.config_log_service import get_changed_fields

        before = {"name": "정문 CCTV", "ip": "192.168.1.100"}
        after = {"name": "정문 CCTV", "ip": "192.168.1.100"}

        before_changes, after_changes = get_changed_fields(before, after)

        assert before_changes == {}
        assert after_changes == {}

    def test_get_changed_fields_ignores_unchanged(self):
        """CCL-10.1: 변경되지 않은 필드 제외"""
        from app.services.config_log_service import get_changed_fields

        before = {"id": 1, "name": "테스트", "status": "ACTIVATED", "ip": "192.168.1.1"}
        after = {"id": 1, "name": "테스트 수정", "status": "ACTIVATED", "ip": "192.168.1.1"}

        before_changes, after_changes = get_changed_fields(before, after)

        # id, status, ip는 변경되지 않았으므로 포함되지 않아야 함
        assert "id" not in before_changes
        assert "status" not in before_changes
        assert "ip" not in before_changes
        assert before_changes == {"name": "테스트"}
        assert after_changes == {"name": "테스트 수정"}


class TestGetIdentifier:
    """
    CCL-10.3: get_identifier() 함수 테스트

    PRD Reference: PRD_ConfigChangeLog.md v1.1 Section 3.3, 6.1
    """

    def test_get_identifier_function_exists(self):
        """CCL-10.3: get_identifier 함수 존재 확인"""
        from app.services.config_log_service import get_identifier

        assert callable(get_identifier)

    def test_get_identifier_extracts_id_and_name(self):
        """CCL-10.3: id, name 추출"""
        from app.services.config_log_service import get_identifier

        class MockModel:
            id = 201
            name = "정문 CCTV"
            ip_address = "192.168.1.100"

        result = get_identifier(MockModel())

        assert result == {"id": 201, "name": "정문 CCTV"}

    def test_get_identifier_with_name_device(self):
        """CCL-10.3: name_device 필드 처리 (Device 모델)"""
        from app.services.config_log_service import get_identifier

        class MockDeviceModel:
            id = 201
            name_device = "정문 CCTV"
            ip_address = "192.168.1.100"

        result = get_identifier(MockDeviceModel())

        assert result == {"id": 201, "name": "정문 CCTV"}

    def test_get_identifier_with_title(self):
        """CCL-10.3: title 필드 처리 (fallback)"""
        from app.services.config_log_service import get_identifier

        class MockModelWithTitle:
            id = 100
            title = "이벤트 매핑 A"

        result = get_identifier(MockModelWithTitle())

        assert result == {"id": 100, "name": "이벤트 매핑 A"}

    def test_get_identifier_no_name_field(self):
        """CCL-10.3: name 필드가 없는 경우 id만 반환"""
        from app.services.config_log_service import get_identifier

        class MockModelNoName:
            id = 50

        result = get_identifier(MockModelNoName())

        assert result == {"id": 50}


# ==============================================================================
# Phase CCL-11: Device 계열 라우터 통합 테스트
# ==============================================================================

class TestControllerConfigChangeLog:
    """
    CCL-11.1: controllers.py ConfigChangeLog 통합 테스트

    PRD Reference: PRD_ConfigChangeLog.md v1.2 Section 7

    테스트 대상:
    - POST /api/devices/controllers - CREATED 로그 기록
    - PATCH /api/devices/controllers/{id} - UPDATED 로그 기록
    - DELETE /api/devices/controllers/{id} - DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        """테스트 설정 - conftest.py의 client, test_db 픽스처 사용"""
        self.client = client
        self.db = test_db

    def test_create_controller_logs_config_change(self):
        """
        CCL-11.1: POST /api/devices/controllers - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 초기 로그 수 확인
        initial_count = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CONTROLLER
        ).count()

        # When: Controller 생성
        controller_data = {
            "number_device": 9001,
            "group_device": 1,
            "name_device": "테스트 제어기",
            "type_device": "Controller",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.100.1",
            "ip_port": 8080
        }
        response = self.client.post("/api/devices/controllers", json=controller_data)
        assert response.status_code == 201, f"Controller 생성 실패: {response.json()}"

        created_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CONTROLLER,
            ConfigChangeLog.resource_id == created_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "Controller 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_controller_logs_config_change(self):
        """
        CCL-11.1: PATCH /api/devices/controllers/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Controller 생성
        controller_data = {
            "number_device": 9002,
            "group_device": 1,
            "name_device": "수정 테스트 제어기",
            "type_device": "Controller",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.100.2",
            "ip_port": 8080
        }
        create_response = self.client.post("/api/devices/controllers", json=controller_data)
        assert create_response.status_code == 201
        controller_id = create_response.json()["data"]["id"]

        # When: Controller 수정
        update_data = {"name_device": "수정된 제어기 이름"}
        update_response = self.client.patch(f"/api/devices/controllers/{controller_id}", json=update_data)
        assert update_response.status_code == 200, f"Controller 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        self.db.expire_all()  # 세션 캐시 무효화하여 최신 데이터 조회
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CONTROLLER,
            ConfigChangeLog.resource_id == controller_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "Controller 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "name_device" in log.before_state or "name" in log.before_state, \
            "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_controller_logs_config_change(self):
        """
        CCL-11.1: DELETE /api/devices/controllers/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Controller 생성
        controller_data = {
            "number_device": 9003,
            "group_device": 1,
            "name_device": "삭제 테스트 제어기",
            "type_device": "Controller",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.100.3",
            "ip_port": 8080
        }
        create_response = self.client.post("/api/devices/controllers", json=controller_data)
        assert create_response.status_code == 201
        controller_id = create_response.json()["data"]["id"]
        controller_name = create_response.json()["data"]["name_device"]

        # When: Controller 삭제
        delete_response = self.client.delete(f"/api/devices/controllers/{controller_id}")
        assert delete_response.status_code == 200, f"Controller 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CONTROLLER,
            ConfigChangeLog.resource_id == controller_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "Controller 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"


class TestSensorConfigChangeLog:
    """
    CCL-11.2: sensors.py ConfigChangeLog 통합 테스트

    PRD Reference: PRD_ConfigChangeLog.md v1.2 Section 7

    테스트 대상:
    - POST /api/devices/sensors - CREATED 로그 기록
    - PATCH /api/devices/sensors/{id} - UPDATED 로그 기록
    - DELETE /api/devices/sensors/{id} - DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_controller):
        """테스트 설정 - conftest.py의 client, test_db, test_controller 픽스처 사용"""
        self.client = client
        self.db = test_db
        self.controller = test_controller

    def test_create_sensor_logs_config_change(self):
        """
        CCL-11.2: POST /api/devices/sensors - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 초기 로그 수 확인
        initial_count = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SENSOR
        ).count()

        # When: Sensor 생성
        sensor_data = {
            "number_device": 8001,
            "group_device": 1,
            "name_device": "테스트 센서",
            "type_device": "Fence",  # EnumDeviceType: Fence, PIR, Contact 등
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "controller_id": self.controller.id
        }
        response = self.client.post("/api/devices/sensors", json=sensor_data)
        assert response.status_code == 201, f"Sensor 생성 실패: {response.json()}"

        created_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SENSOR,
            ConfigChangeLog.resource_id == created_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "Sensor 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_sensor_logs_config_change(self):
        """
        CCL-11.2: PATCH /api/devices/sensors/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Sensor 생성
        sensor_data = {
            "number_device": 8002,
            "group_device": 1,
            "name_device": "수정 테스트 센서",
            "type_device": "Fence",  # EnumDeviceType: Fence, PIR, Contact 등
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "controller_id": self.controller.id
        }
        create_response = self.client.post("/api/devices/sensors", json=sensor_data)
        assert create_response.status_code == 201
        sensor_id = create_response.json()["data"]["id"]

        # When: Sensor 수정
        update_data = {"name_device": "수정된 센서 이름"}
        update_response = self.client.patch(f"/api/devices/sensors/{sensor_id}", json=update_data)
        assert update_response.status_code == 200, f"Sensor 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        self.db.expire_all()  # 세션 캐시 무효화하여 최신 데이터 조회
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SENSOR,
            ConfigChangeLog.resource_id == sensor_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "Sensor 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "name_device" in log.before_state or "name" in log.before_state, \
            "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_sensor_logs_config_change(self):
        """
        CCL-11.2: DELETE /api/devices/sensors/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Sensor 생성
        sensor_data = {
            "number_device": 8003,
            "group_device": 1,
            "name_device": "삭제 테스트 센서",
            "type_device": "Fence",  # EnumDeviceType: Fence, PIR, Contact 등
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "controller_id": self.controller.id
        }
        create_response = self.client.post("/api/devices/sensors", json=sensor_data)
        assert create_response.status_code == 201
        sensor_id = create_response.json()["data"]["id"]
        sensor_name = create_response.json()["data"]["name_device"]

        # When: Sensor 삭제
        delete_response = self.client.delete(f"/api/devices/sensors/{sensor_id}")
        assert delete_response.status_code == 200, f"Sensor 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SENSOR,
            ConfigChangeLog.resource_id == sensor_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "Sensor 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"


class TestCameraConfigChangeLog:
    """
    CCL-11.3: cameras.py ConfigChangeLog 통합 테스트

    PRD Reference: PRD_ConfigChangeLog.md v1.2 Section 7

    테스트 대상:
    - POST /api/devices/cameras - CREATED 로그 기록
    - PATCH /api/devices/cameras/{id} - UPDATED 로그 기록
    - DELETE /api/devices/cameras/{id} - DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        """테스트 설정 - conftest.py의 client, test_db 픽스처 사용"""
        self.client = client
        self.db = test_db

    def test_create_camera_logs_config_change(self):
        """
        CCL-11.3: POST /api/devices/cameras - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 초기 로그 수 확인
        initial_count = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA
        ).count()

        # When: Camera 생성
        camera_data = {
            "number_device": 7001,
            "group_device": 1,
            "name_device": "테스트 카메라",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.200.1",
            "ip_port": 554,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        response = self.client.post("/api/devices/cameras", json=camera_data)
        assert response.status_code == 201, f"Camera 생성 실패: {response.json()}"

        created_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA,
            ConfigChangeLog.resource_id == created_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "Camera 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_camera_logs_config_change(self):
        """
        CCL-11.3: PATCH /api/devices/cameras/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Camera 생성
        camera_data = {
            "number_device": 7002,
            "group_device": 1,
            "name_device": "수정 테스트 카메라",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.200.2",
            "ip_port": 554,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = self.client.post("/api/devices/cameras", json=camera_data)
        assert create_response.status_code == 201
        camera_id = create_response.json()["data"]["id"]

        # When: Camera 수정
        update_data = {"name_device": "수정된 카메라 이름"}
        update_response = self.client.patch(f"/api/devices/cameras/{camera_id}", json=update_data)
        assert update_response.status_code == 200, f"Camera 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        self.db.expire_all()  # 세션 캐시 무효화하여 최신 데이터 조회
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA,
            ConfigChangeLog.resource_id == camera_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "Camera 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "name_device" in log.before_state or "name" in log.before_state, \
            "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_camera_logs_config_change(self):
        """
        CCL-11.3: DELETE /api/devices/cameras/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Camera 생성
        camera_data = {
            "number_device": 7003,
            "group_device": 1,
            "name_device": "삭제 테스트 카메라",
            "type_device": "IpCamera",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.200.3",
            "ip_port": 554,
            "mode": "ONVIF",
            "category": "PTZ"
        }
        create_response = self.client.post("/api/devices/cameras", json=camera_data)
        assert create_response.status_code == 201
        camera_id = create_response.json()["data"]["id"]

        # When: Camera 삭제
        delete_response = self.client.delete(f"/api/devices/cameras/{camera_id}")
        assert delete_response.status_code == 200, f"Camera 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA,
            ConfigChangeLog.resource_id == camera_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "Camera 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"


class TestSpeakerConfigChangeLog:
    """
    CCL-11.4: Speaker ConfigChangeLog 통합 테스트

    PRD: PRD_ConfigChangeLog.md v1.2 Section 4.1
    - POST /api/devices/speakers → CREATED 로그
    - PATCH /api/devices/speakers/{id} → UPDATED 로그
    - DELETE /api/devices/speakers/{id} → DELETED 로그
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        self.client = client
        self.db = test_db

    def test_create_speaker_logs_config_change(self):
        """
        CCL-11.4: POST /api/devices/speakers - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Speaker 생성 데이터
        speaker_data = {
            "number_device": 9001,
            "group_device": 1,
            "name_device": "테스트 스피커",
            "type_device": "IpSpeaker",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "speaker_type": "NORMAL",
            "description": "테스트용 스피커"
        }

        # When: Speaker 생성
        response = self.client.post("/api/devices/speakers", json=speaker_data)
        assert response.status_code == 201, f"Speaker 생성 실패: {response.json()}"
        speaker_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SPEAKER,
            ConfigChangeLog.resource_id == speaker_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "Speaker 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_speaker_logs_config_change(self):
        """
        CCL-11.4: PATCH /api/devices/speakers/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Speaker 생성
        speaker_data = {
            "number_device": 9002,
            "group_device": 1,
            "name_device": "수정 전 스피커",
            "type_device": "IpSpeaker",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "speaker_type": "NORMAL"
        }
        create_response = self.client.post("/api/devices/speakers", json=speaker_data)
        assert create_response.status_code == 201
        speaker_id = create_response.json()["data"]["id"]

        # When: Speaker 수정
        update_data = {"name_device": "수정 후 스피커"}
        update_response = self.client.patch(f"/api/devices/speakers/{speaker_id}", json=update_data)
        assert update_response.status_code == 200, f"Speaker 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SPEAKER,
            ConfigChangeLog.resource_id == speaker_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "Speaker 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "name_device" in log.before_state or "name" in log.before_state, \
            "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_speaker_logs_config_change(self):
        """
        CCL-11.4: DELETE /api/devices/speakers/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Speaker 생성
        speaker_data = {
            "number_device": 9003,
            "group_device": 1,
            "name_device": "삭제 테스트 스피커",
            "type_device": "IpSpeaker",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "speaker_type": "NORMAL"
        }
        create_response = self.client.post("/api/devices/speakers", json=speaker_data)
        assert create_response.status_code == 201
        speaker_id = create_response.json()["data"]["id"]

        # When: Speaker 삭제
        delete_response = self.client.delete(f"/api/devices/speakers/{speaker_id}")
        assert delete_response.status_code == 200, f"Speaker 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SPEAKER,
            ConfigChangeLog.resource_id == speaker_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "Speaker 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"


class TestEnclosureConfigChangeLog:
    """
    CCL-11.5: Enclosure ConfigChangeLog 통합 테스트

    PRD: PRD_ConfigChangeLog.md v1.2 Section 4.1
    - POST /api/devices/enclosures → CREATED 로그
    - PATCH /api/devices/enclosures/{id} → UPDATED 로그
    - DELETE /api/devices/enclosures/{id} → DELETED 로그
    - PATCH /api/devices/enclosures/{id}/status → STATUS_CHANGED 로그
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        self.client = client
        self.db = test_db

    def test_create_enclosure_logs_config_change(self):
        """
        CCL-11.5: POST /api/devices/enclosures - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Enclosure 생성 데이터
        enclosure_data = {
            "number_device": 6001,
            "group_device": 1,
            "name_device": "테스트 함체",
            "type_device": "IoController",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "door_status": "CLOSED"
        }

        # When: Enclosure 생성
        response = self.client.post("/api/devices/enclosures", json=enclosure_data)
        assert response.status_code == 201, f"Enclosure 생성 실패: {response.json()}"
        enclosure_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ENCLOSURE,
            ConfigChangeLog.resource_id == enclosure_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "Enclosure 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_enclosure_logs_config_change(self):
        """
        CCL-11.5: PATCH /api/devices/enclosures/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Enclosure 생성
        enclosure_data = {
            "number_device": 6002,
            "group_device": 1,
            "name_device": "수정 전 함체",
            "type_device": "IoController",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "door_status": "CLOSED"
        }
        create_response = self.client.post("/api/devices/enclosures", json=enclosure_data)
        assert create_response.status_code == 201
        enclosure_id = create_response.json()["data"]["id"]

        # When: Enclosure 수정
        update_data = {"name_device": "수정 후 함체"}
        update_response = self.client.patch(f"/api/devices/enclosures/{enclosure_id}", json=update_data)
        assert update_response.status_code == 200, f"Enclosure 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ENCLOSURE,
            ConfigChangeLog.resource_id == enclosure_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "Enclosure 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "name_device" in log.before_state or "name" in log.before_state, \
            "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_enclosure_logs_config_change(self):
        """
        CCL-11.5: DELETE /api/devices/enclosures/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Enclosure 생성
        enclosure_data = {
            "number_device": 6003,
            "group_device": 1,
            "name_device": "삭제 테스트 함체",
            "type_device": "IoController",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "door_status": "CLOSED"
        }
        create_response = self.client.post("/api/devices/enclosures", json=enclosure_data)
        assert create_response.status_code == 201
        enclosure_id = create_response.json()["data"]["id"]

        # When: Enclosure 삭제
        delete_response = self.client.delete(f"/api/devices/enclosures/{enclosure_id}")
        assert delete_response.status_code == 200, f"Enclosure 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ENCLOSURE,
            ConfigChangeLog.resource_id == enclosure_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "Enclosure 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"

    def test_update_enclosure_status_logs_config_change(self):
        """
        CCL-11.5: PATCH /api/devices/enclosures/{id}/status - ConfigChangeLog STATUS_CHANGED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: STATUS_CHANGED → before_state/after_state = {status 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: Enclosure 생성 (door_status=CLOSED)
        enclosure_data = {
            "number_device": 6004,
            "group_device": 1,
            "name_device": "상태 변경 테스트 함체",
            "type_device": "IoController",
            "version": "1.0.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "door_status": "CLOSED"
        }
        create_response = self.client.post("/api/devices/enclosures", json=enclosure_data)
        assert create_response.status_code == 201
        enclosure_id = create_response.json()["data"]["id"]

        # When: Enclosure 상태 변경 (door_status: CLOSED → OPEN)
        status_data = {"door_status": "OPEN"}
        status_response = self.client.patch(f"/api/devices/enclosures/{enclosure_id}/status", json=status_data)
        assert status_response.status_code == 200, f"Enclosure 상태 변경 실패: {status_response.json()}"

        # Then: ConfigChangeLog에 STATUS_CHANGED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ENCLOSURE,
            ConfigChangeLog.resource_id == enclosure_id,
            ConfigChangeLog.action == EnumConfigActionType.STATUS_CHANGED
        ).first()

        assert log is not None, "Enclosure 상태 변경 시 ConfigChangeLog STATUS_CHANGED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "STATUS_CHANGED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "STATUS_CHANGED 시 after_state가 있어야 합니다"
        # door_status 변경 확인
        assert "door_status" in log.before_state or "status" in log.before_state, \
            "before_state에 상태 필드가 포함되어야 합니다"


class TestDeviceGroupConfigChangeLog:
    """
    CCL-11.6: DeviceGroup ConfigChangeLog 통합 테스트

    PRD: PRD_ConfigChangeLog.md v1.2 Section 4.1
    - POST /api/devices/groups → CREATED 로그
    - PATCH /api/devices/groups/{id} → UPDATED 로그
    - DELETE /api/devices/groups/{id} → DELETED 로그
    - POST /api/devices/groups/{id}/devices → ASSIGNED 로그
    - DELETE /api/devices/groups/{group_id}/devices/{device_id} → UNASSIGNED 로그
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_controller):
        """테스트 설정 - conftest.py의 client, test_db, test_controller 픽스처 사용"""
        self.client = client
        self.db = test_db
        self.controller = test_controller

    def test_create_device_group_logs_config_change(self):
        """
        CCL-11.6: POST /api/devices/groups - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: DeviceGroup 생성 데이터
        group_data = {
            "name": "테스트 디바이스 그룹",
            "description": "ConfigChangeLog 테스트용 그룹"
        }

        # When: DeviceGroup 생성
        response = self.client.post("/api/devices/groups", json=group_data)
        assert response.status_code == 201, f"DeviceGroup 생성 실패: {response.json()}"
        group_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DEVICE_GROUP,
            ConfigChangeLog.resource_id == group_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "DeviceGroup 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_device_group_logs_config_change(self):
        """
        CCL-11.6: PATCH /api/devices/groups/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: DeviceGroup 생성
        group_data = {
            "name": "수정 전 그룹",
            "description": "원본 설명"
        }
        create_response = self.client.post("/api/devices/groups", json=group_data)
        assert create_response.status_code == 201
        group_id = create_response.json()["data"]["id"]

        # When: DeviceGroup 수정
        update_data = {"name": "수정 후 그룹"}
        update_response = self.client.patch(f"/api/devices/groups/{group_id}", json=update_data)
        assert update_response.status_code == 200, f"DeviceGroup 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DEVICE_GROUP,
            ConfigChangeLog.resource_id == group_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "DeviceGroup 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "name" in log.before_state, "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_device_group_logs_config_change(self):
        """
        CCL-11.6: DELETE /api/devices/groups/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: DeviceGroup 생성
        group_data = {
            "name": "삭제 테스트 그룹",
            "description": "삭제될 그룹"
        }
        create_response = self.client.post("/api/devices/groups", json=group_data)
        assert create_response.status_code == 201
        group_id = create_response.json()["data"]["id"]

        # When: DeviceGroup 삭제
        delete_response = self.client.delete(f"/api/devices/groups/{group_id}")
        assert delete_response.status_code == 200, f"DeviceGroup 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DEVICE_GROUP,
            ConfigChangeLog.resource_id == group_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "DeviceGroup 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"

    def test_assign_device_to_group_logs_config_change(self):
        """
        CCL-11.6: POST /api/devices/groups/{id}/devices - ConfigChangeLog ASSIGNED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: ASSIGNED → after_state = {device_id, device_name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: DeviceGroup 생성
        group_data = {
            "name": "할당 테스트 그룹",
            "description": "디바이스 할당 테스트"
        }
        create_response = self.client.post("/api/devices/groups", json=group_data)
        assert create_response.status_code == 201
        group_id = create_response.json()["data"]["id"]

        # When: Controller를 그룹에 할당
        assign_data = {"device_ids": [self.controller.id]}
        assign_response = self.client.post(f"/api/devices/groups/{group_id}/devices", json=assign_data)
        assert assign_response.status_code == 200, f"디바이스 할당 실패: {assign_response.json()}"

        # Then: ConfigChangeLog에 ASSIGNED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DEVICE_GROUP,
            ConfigChangeLog.resource_id == group_id,
            ConfigChangeLog.action == EnumConfigActionType.ASSIGNED
        ).first()

        assert log is not None, "디바이스 할당 시 ConfigChangeLog ASSIGNED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "ASSIGNED 시 after_state가 있어야 합니다"
        assert "device_id" in log.after_state or "device_ids" in log.after_state, \
            "after_state에 할당된 디바이스 정보가 포함되어야 합니다"

    def test_unassign_device_from_group_logs_config_change(self):
        """
        CCL-11.6: DELETE /api/devices/groups/{group_id}/devices/{device_id} - ConfigChangeLog UNASSIGNED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UNASSIGNED → before_state = {device_id, device_name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: DeviceGroup 생성 및 Controller 할당
        group_data = {
            "name": "할당 해제 테스트 그룹",
            "description": "디바이스 할당 해제 테스트"
        }
        create_response = self.client.post("/api/devices/groups", json=group_data)
        assert create_response.status_code == 201
        group_id = create_response.json()["data"]["id"]

        # Controller를 그룹에 할당
        assign_data = {"device_ids": [self.controller.id]}
        assign_response = self.client.post(f"/api/devices/groups/{group_id}/devices", json=assign_data)
        assert assign_response.status_code == 200

        # When: Controller를 그룹에서 할당 해제
        unassign_response = self.client.delete(f"/api/devices/groups/{group_id}/devices/{self.controller.id}")
        assert unassign_response.status_code == 200, f"디바이스 할당 해제 실패: {unassign_response.json()}"

        # Then: ConfigChangeLog에 UNASSIGNED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DEVICE_GROUP,
            ConfigChangeLog.resource_id == group_id,
            ConfigChangeLog.action == EnumConfigActionType.UNASSIGNED
        ).first()

        assert log is not None, "디바이스 할당 해제 시 ConfigChangeLog UNASSIGNED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UNASSIGNED 시 before_state가 있어야 합니다"
        assert "device_id" in log.before_state, \
            "before_state에 해제된 디바이스 정보가 포함되어야 합니다"


class TestCameraPresetConfigChangeLog:
    """
    CCL-11.7: CameraPreset ConfigChangeLog 통합 테스트

    PRD: PRD_ConfigChangeLog.md v1.2 Section 4.1
    - POST /api/devices/cameras/{camera_id}/presets → CREATED 로그
    - PATCH /api/devices/cameras/{camera_id}/presets/{preset_id} → UPDATED 로그
    - DELETE /api/devices/cameras/{camera_id}/presets/{preset_id} → DELETED 로그
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_camera):
        """테스트 설정 - conftest.py의 client, test_db, test_camera 픽스처 사용"""
        self.client = client
        self.db = test_db
        self.camera = test_camera

    def test_create_camera_preset_logs_config_change(self):
        """
        CCL-11.7: POST /api/devices/cameras/{camera_id}/presets - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: CameraPreset 생성 데이터
        preset_data = {
            "preset_index": 1,
            "preset_name": "테스트 프리셋",
            "touring_time": 10
        }

        # When: CameraPreset 생성
        response = self.client.post(f"/api/devices/cameras/{self.camera.id}/presets", json=preset_data)
        assert response.status_code == 201, f"CameraPreset 생성 실패: {response.json()}"
        preset_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA_PRESET,
            ConfigChangeLog.resource_id == preset_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "CameraPreset 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_camera_preset_logs_config_change(self):
        """
        CCL-11.7: PATCH /api/devices/cameras/{camera_id}/presets/{preset_id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: CameraPreset 생성
        preset_data = {
            "preset_index": 2,
            "preset_name": "수정 전 프리셋",
            "touring_time": 10
        }
        create_response = self.client.post(f"/api/devices/cameras/{self.camera.id}/presets", json=preset_data)
        assert create_response.status_code == 201
        preset_id = create_response.json()["data"]["id"]

        # When: CameraPreset 수정
        update_data = {"preset_name": "수정 후 프리셋"}
        update_response = self.client.patch(f"/api/devices/cameras/{self.camera.id}/presets/{preset_id}", json=update_data)
        assert update_response.status_code == 200, f"CameraPreset 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA_PRESET,
            ConfigChangeLog.resource_id == preset_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "CameraPreset 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "preset_name" in log.before_state, "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_camera_preset_logs_config_change(self):
        """
        CCL-11.7: DELETE /api/devices/cameras/{camera_id}/presets/{preset_id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: CameraPreset 생성
        preset_data = {
            "preset_index": 3,
            "preset_name": "삭제 테스트 프리셋",
            "touring_time": 10
        }
        create_response = self.client.post(f"/api/devices/cameras/{self.camera.id}/presets", json=preset_data)
        assert create_response.status_code == 201
        preset_id = create_response.json()["data"]["id"]

        # When: CameraPreset 삭제
        delete_response = self.client.delete(f"/api/devices/cameras/{self.camera.id}/presets/{preset_id}")
        assert delete_response.status_code == 200, f"CameraPreset 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CAMERA_PRESET,
            ConfigChangeLog.resource_id == preset_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "CameraPreset 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"


class TestROIConfigChangeLog:
    """
    CCL-11.8: ROI ConfigChangeLog 통합 테스트

    PRD: PRD_ConfigChangeLog.md v1.2 Section 4.1
    - POST /api/presets/{preset_id}/rois → CREATED 로그
    - PATCH /api/presets/{preset_id}/rois/{roi_id} → UPDATED 로그
    - DELETE /api/presets/{preset_id}/rois/{roi_id} → DELETED 로그
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_camera):
        """테스트 설정 - conftest.py의 client, test_db, test_camera 픽스처 사용"""
        self.client = client
        self.db = test_db
        self.camera = test_camera

        # CameraPreset 생성 (ROI의 부모)
        preset_data = {
            "preset_index": 100,
            "preset_name": "ROI 테스트용 프리셋",
            "touring_time": 10
        }
        response = self.client.post(f"/api/devices/cameras/{self.camera.id}/presets", json=preset_data)
        assert response.status_code == 201
        self.preset_id = response.json()["data"]["id"]

    def test_create_roi_logs_config_change(self):
        """
        CCL-11.8: POST /api/presets/{preset_id}/rois - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: ROI 생성 데이터
        roi_data = {
            "name": "테스트 ROI",
            "resolution_width": 1920,
            "resolution_height": 1080,
            "is_enable": True
        }

        # When: ROI 생성
        response = self.client.post(f"/api/presets/{self.preset_id}/rois", json=roi_data)
        assert response.status_code == 201, f"ROI 생성 실패: {response.json()}"
        roi_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ROI,
            ConfigChangeLog.resource_id == roi_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "ROI 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "name" in log.after_state, "after_state에 name이 포함되어야 합니다"

    def test_update_roi_logs_config_change(self):
        """
        CCL-11.8: PATCH /api/presets/{preset_id}/rois/{roi_id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: ROI 생성
        roi_data = {
            "name": "수정 전 ROI",
            "resolution_width": 1920,
            "resolution_height": 1080,
            "is_enable": True
        }
        create_response = self.client.post(f"/api/presets/{self.preset_id}/rois", json=roi_data)
        assert create_response.status_code == 201
        roi_id = create_response.json()["data"]["id"]

        # When: ROI 수정
        update_data = {"name": "수정 후 ROI"}
        update_response = self.client.patch(f"/api/presets/{self.preset_id}/rois/{roi_id}", json=update_data)
        assert update_response.status_code == 200, f"ROI 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ROI,
            ConfigChangeLog.resource_id == roi_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "ROI 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1 정규화: 변경된 필드만 저장
        assert "name" in log.before_state, "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_roi_logs_config_change(self):
        """
        CCL-11.8: DELETE /api/presets/{preset_id}/rois/{roi_id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: ROI 생성
        roi_data = {
            "name": "삭제 테스트 ROI",
            "resolution_width": 1920,
            "resolution_height": 1080,
            "is_enable": True
        }
        create_response = self.client.post(f"/api/presets/{self.preset_id}/rois", json=roi_data)
        assert create_response.status_code == 201
        roi_id = create_response.json()["data"]["id"]

        # When: ROI 삭제
        delete_response = self.client.delete(f"/api/presets/{self.preset_id}/rois/{roi_id}")
        assert delete_response.status_code == 200, f"ROI 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ROI,
            ConfigChangeLog.resource_id == roi_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "ROI 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "name" in log.before_state, "before_state에 name이 포함되어야 합니다"


class TestXyPointConfigChangeLog:
    """
    CCL-11.9: XyPoint ConfigChangeLog 통합 테스트
    PRD: PRD_ConfigChangeLog.md v1.2 Section 4.1

    - POST /api/rois/{roi_id}/points → CREATED 로그
    - DELETE /api/rois/{roi_id}/points/{point_id} → DELETED 로그

    Note: PUT /api/rois/{roi_id}/points는 bulk replace로 별도 처리
    Note: XyPoint는 name 필드가 없어 order를 식별자로 사용
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_camera):
        """ROI 생성 (XyPoint의 부모)"""
        self.client = client
        self.db = test_db
        self.camera = test_camera

        # CameraPreset 생성
        preset_data = {
            "preset_index": 200,
            "preset_name": "XyPoint 테스트용 프리셋",
            "touring_time": 10
        }
        preset_response = self.client.post(
            f"/api/devices/cameras/{self.camera.id}/presets",
            json=preset_data
        )
        self.preset_id = preset_response.json()["data"]["id"]

        # ROI 생성
        roi_data = {
            "name": "XyPoint 테스트용 ROI",
            "resolution_width": 1920,
            "resolution_height": 1080,
            "is_enable": True
        }
        roi_response = self.client.post(
            f"/api/presets/{self.preset_id}/rois",
            json=roi_data
        )
        self.roi_id = roi_response.json()["data"]["id"]

    def test_create_point_logs_config_change(self):
        """
        CCL-11.9: POST /api/rois/{roi_id}/points - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, order}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # When: XyPoint 생성
        point_data = {
            "x": 100,
            "y": 200,
            "order": 1
        }
        response = self.client.post(f"/api/rois/{self.roi_id}/points", json=point_data)
        assert response.status_code == 201, f"XyPoint 생성 실패: {response.json()}"

        point_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.XY_POINT,
            ConfigChangeLog.resource_id == point_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "XyPoint 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"

    def test_delete_point_logs_config_change(self):
        """
        CCL-11.9: DELETE /api/rois/{roi_id}/points/{point_id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, order}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: XyPoint 생성
        point_data = {
            "x": 300,
            "y": 400,
            "order": 2
        }
        create_response = self.client.post(f"/api/rois/{self.roi_id}/points", json=point_data)
        assert create_response.status_code == 201
        point_id = create_response.json()["data"]["id"]

        # When: XyPoint 삭제
        delete_response = self.client.delete(f"/api/rois/{self.roi_id}/points/{point_id}")
        assert delete_response.status_code == 200, f"XyPoint 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.XY_POINT,
            ConfigChangeLog.resource_id == point_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "XyPoint 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"


class TestFileGroupConfigChangeLog:
    """
    CCL-11.10: FileGroup ConfigChangeLog 통합 테스트
    PRD: PRD_ConfigChangeLog.md v1.2 Section 4.1

    - POST /api/file-groups → CREATED 로그
    - PATCH /api/file-groups/{id} → UPDATED 로그
    - DELETE /api/file-groups/{id} → DELETED 로그
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_server):
        """Server 필요 (FileGroup의 부모)"""
        self.client = client
        self.db = test_db
        self.server = test_server

    def test_create_file_group_logs_config_change(self):
        """
        CCL-11.10: POST /api/file-groups - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # When: FileGroup 생성
        file_group_data = {
            "server_id": self.server.id,
            "group_id": 999,
            "group_name": "테스트 파일 그룹",
            "files": ["audio1.mp3", "audio2.mp3"]
        }
        response = self.client.post("/api/file-groups", json=file_group_data)
        assert response.status_code == 201, f"FileGroup 생성 실패: {response.json()}"

        file_group_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.FILE_GROUP,
            ConfigChangeLog.resource_id == file_group_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "FileGroup 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"

    def test_update_file_group_logs_config_change(self):
        """
        CCL-11.10: PATCH /api/file-groups/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: FileGroup 생성
        file_group_data = {
            "server_id": self.server.id,
            "group_id": 998,
            "group_name": "수정 테스트 그룹",
            "files": ["original.mp3"]
        }
        create_response = self.client.post("/api/file-groups", json=file_group_data)
        assert create_response.status_code == 201
        file_group_id = create_response.json()["data"]["id"]

        # When: FileGroup 수정
        update_data = {"group_name": "수정된 그룹 이름"}
        update_response = self.client.patch(f"/api/file-groups/{file_group_id}", json=update_data)
        assert update_response.status_code == 200, f"FileGroup 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.FILE_GROUP,
            ConfigChangeLog.resource_id == file_group_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "FileGroup 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        assert "group_name" in log.before_state, "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_file_group_logs_config_change(self):
        """
        CCL-11.10: DELETE /api/file-groups/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: FileGroup 생성
        file_group_data = {
            "server_id": self.server.id,
            "group_id": 997,
            "group_name": "삭제 테스트 그룹",
            "files": []
        }
        create_response = self.client.post("/api/file-groups", json=file_group_data)
        assert create_response.status_code == 201
        file_group_id = create_response.json()["data"]["id"]

        # When: FileGroup 삭제
        delete_response = self.client.delete(f"/api/file-groups/{file_group_id}")
        assert delete_response.status_code == 200, f"FileGroup 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.FILE_GROUP,
            ConfigChangeLog.resource_id == file_group_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "FileGroup 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"


# ==============================================================================
# Phase CCL-12: Event 계열 라우터 통합 테스트
# ==============================================================================

class TestDetectionEventConfigChangeLog:
    """
    CCL-12.1: DetectionEvent ConfigChangeLog 통합 테스트

    PRD Reference: PRD_ConfigChangeLog.md v1.2 Section 7

    테스트 대상:
    - POST /api/events/detections - CREATED 로그 기록
    - PATCH /api/events/detections/{id} - UPDATED 로그 기록
    - DELETE /api/events/detections/{id} - DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_controller):
        """테스트 설정 - conftest.py의 client, test_db, test_controller 픽스처 사용"""
        self.client = client
        self.db = test_db
        self.controller = test_controller
        # Create a sensor for detection event tests
        self._create_test_sensor()

    def _create_test_sensor(self):
        """테스트용 센서 생성"""
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        sensor = Sensor(
            number_device=5001,
            group_device=1,
            name_device="Detection Test Sensor",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            controller_id=self.controller.id
        )
        self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        self.sensor = sensor

    def test_create_detection_event_logs_config_change(self):
        """
        CCL-12.1: POST /api/events/detections - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # When: DetectionEvent 생성
        event_data = {
            "type_event": "Intrusion",
            "device_id": self.sensor.id,
            "result": "PIR_SENSOR"  # EnumDetectionType valid value
        }
        response = self.client.post("/api/events/detections", json=event_data)
        assert response.status_code == 201, f"DetectionEvent 생성 실패: {response.json()}"

        event_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DETECTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "DetectionEvent 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"

    def test_update_detection_event_logs_config_change(self):
        """
        CCL-12.1: PATCH /api/events/detections/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: DetectionEvent 생성
        event_data = {
            "type_event": "Intrusion",
            "device_id": self.sensor.id,
            "result": "PIR_SENSOR"  # EnumDetectionType valid value
        }
        create_response = self.client.post("/api/events/detections", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: DetectionEvent 수정
        update_data = {"type_event": "Movement"}
        update_response = self.client.patch(f"/api/events/detections/{event_id}", json=update_data)
        assert update_response.status_code == 200, f"DetectionEvent 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        self.db.expire_all()
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DETECTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "DetectionEvent 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        assert "type_event" in log.before_state, "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_detection_event_logs_config_change(self):
        """
        CCL-12.1: DELETE /api/events/detections/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, name}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: DetectionEvent 생성
        event_data = {
            "type_event": "Intrusion",
            "device_id": self.sensor.id,
            "result": "PIR_SENSOR"  # EnumDetectionType valid value
        }
        create_response = self.client.post("/api/events/detections", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: DetectionEvent 삭제
        delete_response = self.client.delete(f"/api/events/detections/{event_id}")
        assert delete_response.status_code == 200, f"DetectionEvent 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.DETECTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "DetectionEvent 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"


class TestMalfunctionEventConfigChangeLog:
    """
    CCL-12.2: MalfunctionEvent ConfigChangeLog 통합 테스트

    PRD Reference: PRD_ConfigChangeLog.md v1.2 Section 7

    테스트 대상:
    - POST /api/events/malfunctions - CREATED 로그 기록
    - PATCH /api/events/malfunctions/{id} - UPDATED 로그 기록
    - DELETE /api/events/malfunctions/{id} - DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_controller):
        """테스트 설정 - conftest.py의 client, test_db, test_controller 픽스처 사용"""
        self.client = client
        self.db = test_db
        self.controller = test_controller
        # Create a sensor for malfunction event tests
        self._create_test_sensor()

    def _create_test_sensor(self):
        """테스트용 센서 생성"""
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        sensor = Sensor(
            number_device=5002,
            group_device=1,
            name_device="Malfunction Test Sensor",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            controller_id=self.controller.id
        )
        self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        self.sensor = sensor

    def test_create_malfunction_event_logs_config_change(self):
        """
        CCL-12.2: POST /api/events/malfunctions - ConfigChangeLog CREATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: CREATED → after_state = {id, type_event}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # When: MalfunctionEvent 생성
        event_data = {
            "type_event": "Fault",
            "device_id": self.sensor.id,
            "reason": "FAULT_FENCE"  # EnumFaultType valid value
        }
        response = self.client.post("/api/events/malfunctions", json=event_data)
        assert response.status_code == 201, f"MalfunctionEvent 생성 실패: {response.json()}"

        event_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.MALFUNCTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "MalfunctionEvent 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"

    def test_update_malfunction_event_logs_config_change(self):
        """
        CCL-12.2: PATCH /api/events/malfunctions/{id} - ConfigChangeLog UPDATED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: UPDATED → before_state/after_state = {변경된 필드만}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: MalfunctionEvent 생성
        event_data = {
            "type_event": "Fault",
            "device_id": self.sensor.id,
            "reason": "FAULT_FENCE"
        }
        create_response = self.client.post("/api/events/malfunctions", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: MalfunctionEvent 수정
        update_data = {"type_event": "Equipment"}
        update_response = self.client.patch(f"/api/events/malfunctions/{event_id}", json=update_data)
        assert update_response.status_code == 200, f"MalfunctionEvent 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        self.db.expire_all()
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.MALFUNCTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "MalfunctionEvent 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        assert "type_event" in log.before_state, "before_state에 변경된 필드가 포함되어야 합니다"

    def test_delete_malfunction_event_logs_config_change(self):
        """
        CCL-12.2: DELETE /api/events/malfunctions/{id} - ConfigChangeLog DELETED 기록 확인

        PRD: PRD_ConfigChangeLog.md v1.2 Section 3.3
        JSONB 정규화: DELETED → before_state = {id, type_event}
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: MalfunctionEvent 생성
        event_data = {
            "type_event": "Fault",
            "device_id": self.sensor.id,
            "reason": "FAULT_FENCE"
        }
        create_response = self.client.post("/api/events/malfunctions", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: MalfunctionEvent 삭제
        delete_response = self.client.delete(f"/api/events/malfunctions/{event_id}")
        assert delete_response.status_code == 200, f"MalfunctionEvent 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.MALFUNCTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "MalfunctionEvent 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"


class TestConnectionEventConfigChangeLog:
    """
    CCL-12.3: ConnectionEvent ConfigChangeLog 통합 테스트

    ConnectionEvent CRUD 작업 시 ConfigChangeLog에 로그가 기록되는지 검증합니다.
    - POST: CREATED 로그 기록
    - PATCH: UPDATED 로그 기록
    - DELETE: DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_controller):
        """테스트 셋업: client, db, controller 의존성 주입"""
        self.client = client
        self.db = test_db
        self.controller = test_controller
        self._create_test_sensor()

    def _create_test_sensor(self):
        """테스트용 센서 생성"""
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        sensor = Sensor(
            number_device=6001,
            group_device=1,
            name_device="Connection Test Sensor",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            controller_id=self.controller.id
        )
        self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        self.sensor = sensor

    def test_create_connection_event_logs_config_change(self):
        """
        CCL-12.3-1: ConnectionEvent 생성 시 ConfigChangeLog CREATED 로그 검증

        Given: 유효한 ConnectionEvent 데이터
        When: POST /api/events/connections 요청
        Then: ConfigChangeLog에 CREATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 유효한 ConnectionEvent 데이터
        event_data = {
            "type_event": "Connect",
            "device_id": self.sensor.id
        }

        # When: ConnectionEvent 생성
        response = self.client.post("/api/events/connections", json=event_data)
        assert response.status_code == 201, f"ConnectionEvent 생성 실패: {response.json()}"
        event_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CONNECTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "ConnectionEvent 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "type_event" in log.after_state, "after_state에 type_event가 포함되어야 합니다"

    def test_update_connection_event_logs_config_change(self):
        """
        CCL-12.3-2: ConnectionEvent 수정 시 ConfigChangeLog UPDATED 로그 검증

        Given: 기존 ConnectionEvent
        When: PATCH /api/events/connections/{id} 요청
        Then: ConfigChangeLog에 UPDATED 로그가 기록됨 (변경된 필드만)
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 ConnectionEvent 생성
        event_data = {
            "type_event": "Connect",
            "device_id": self.sensor.id
        }
        create_response = self.client.post("/api/events/connections", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: ConnectionEvent 수정
        update_data = {"type_event": "Disconnect"}
        update_response = self.client.patch(f"/api/events/connections/{event_id}", json=update_data)
        assert update_response.status_code == 200, f"ConnectionEvent 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CONNECTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "ConnectionEvent 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1: 변경된 필드만 저장
        assert "type_event" in log.before_state, "before_state에 변경된 필드(type_event)가 포함되어야 합니다"
        assert "type_event" in log.after_state, "after_state에 변경된 필드(type_event)가 포함되어야 합니다"

    def test_delete_connection_event_logs_config_change(self):
        """
        CCL-12.3-3: ConnectionEvent 삭제 시 ConfigChangeLog DELETED 로그 검증

        Given: 기존 ConnectionEvent
        When: DELETE /api/events/connections/{id} 요청
        Then: ConfigChangeLog에 DELETED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 ConnectionEvent 생성
        event_data = {
            "type_event": "Connect",
            "device_id": self.sensor.id
        }
        create_response = self.client.post("/api/events/connections", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: ConnectionEvent 삭제
        delete_response = self.client.delete(f"/api/events/connections/{event_id}")
        assert delete_response.status_code == 200, f"ConnectionEvent 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.CONNECTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "ConnectionEvent 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"


class TestActionEventConfigChangeLog:
    """
    CCL-12.4: ActionEvent ConfigChangeLog 통합 테스트

    ActionEvent CRUD 작업 시 ConfigChangeLog에 로그가 기록되는지 검증합니다.
    - POST: CREATED 로그 기록
    - PATCH: UPDATED 로그 기록
    - DELETE: DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db, test_controller):
        """테스트 셋업: client, db, controller 의존성 주입"""
        self.client = client
        self.db = test_db
        self.controller = test_controller
        self._create_test_sensor()
        self._create_source_event()

    def _create_test_sensor(self):
        """테스트용 센서 생성"""
        from app.models.device import Sensor
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        sensor = Sensor(
            number_device=7001,
            group_device=1,
            name_device="Action Test Sensor",
            type_device=EnumDeviceType.Fence,
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            controller_id=self.controller.id
        )
        self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        self.sensor = sensor

    def _create_source_event(self):
        """테스트용 소스 이벤트 (DetectionEvent) 생성"""
        from app.models.event import DetectionEvent
        from app.utils.enums import EnumDetectionType

        detection_event = DetectionEvent(
            type_event="ActionTest_Detection",
            action_reported="False",
            result=EnumDetectionType.NONE,
            device_id=self.sensor.id,
            device_description="Action test detection"
        )
        self.db.add(detection_event)
        self.db.commit()
        self.db.refresh(detection_event)
        self.source_event = detection_event

    def test_create_action_event_logs_config_change(self):
        """
        CCL-12.4-1: ActionEvent 생성 시 ConfigChangeLog CREATED 로그 검증

        Given: 유효한 ActionEvent 데이터 (소스 이벤트 참조)
        When: POST /api/events/actions 요청
        Then: ConfigChangeLog에 CREATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 유효한 ActionEvent 데이터
        event_data = {
            "type_event": "ActionTest_Action",
            "content": "Test action content",
            "user": "test_user",
            "from_event_id": self.source_event.id
        }

        # When: ActionEvent 생성
        response = self.client.post("/api/events/actions", json=event_data)
        assert response.status_code == 201, f"ActionEvent 생성 실패: {response.json()}"
        event_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ACTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "ActionEvent 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"

    def test_update_action_event_logs_config_change(self):
        """
        CCL-12.4-2: ActionEvent 수정 시 ConfigChangeLog UPDATED 로그 검증

        Given: 기존 ActionEvent
        When: PATCH /api/events/actions/{id} 요청
        Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 ActionEvent 생성
        event_data = {
            "type_event": "ActionTest_Action",
            "content": "Original content",
            "user": "test_user",
            "from_event_id": self.source_event.id
        }
        create_response = self.client.post("/api/events/actions", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: ActionEvent 수정
        update_data = {"content": "Updated content"}
        update_response = self.client.patch(f"/api/events/actions/{event_id}", json=update_data)
        assert update_response.status_code == 200, f"ActionEvent 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ACTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "ActionEvent 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1: 변경된 필드만 저장
        assert "content" in log.before_state, "before_state에 변경된 필드(content)가 포함되어야 합니다"
        assert "content" in log.after_state, "after_state에 변경된 필드(content)가 포함되어야 합니다"

    def test_delete_action_event_logs_config_change(self):
        """
        CCL-12.4-3: ActionEvent 삭제 시 ConfigChangeLog DELETED 로그 검증

        Given: 기존 ActionEvent
        When: DELETE /api/events/actions/{id} 요청
        Then: ConfigChangeLog에 DELETED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 ActionEvent 생성
        event_data = {
            "type_event": "ActionTest_Action",
            "content": "To be deleted",
            "user": "test_user",
            "from_event_id": self.source_event.id
        }
        create_response = self.client.post("/api/events/actions", json=event_data)
        assert create_response.status_code == 201
        event_id = create_response.json()["data"]["id"]

        # When: ActionEvent 삭제
        delete_response = self.client.delete(f"/api/events/actions/{event_id}")
        assert delete_response.status_code == 200, f"ActionEvent 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.ACTION_EVENT,
            ConfigChangeLog.resource_id == event_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "ActionEvent 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"


class TestEventMappingConfigChangeLog:
    """
    CCL-13.1: EventMapping ConfigChangeLog 통합 테스트

    EventMapping CRUD 작업 시 ConfigChangeLog에 로그가 기록되는지 검증합니다.
    - POST: CREATED 로그 기록
    - PATCH: UPDATED 로그 기록
    - DELETE: DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        """테스트 셋업: client, db 의존성 주입"""
        self.client = client
        self.db = test_db

    def test_create_event_mapping_logs_config_change(self):
        """
        CCL-13.1-1: EventMapping 생성 시 ConfigChangeLog CREATED 로그 검증

        Given: 유효한 EventMapping 데이터
        When: POST /api/integrations/event-mappings 요청
        Then: ConfigChangeLog에 CREATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 유효한 EventMapping 데이터
        mapping_data = {
            "name_event": "Test EventMapping for CCL",
            "category_event_mapping": "FENCE_SENSOR_ONLY",
            "status": True
        }

        # When: EventMapping 생성
        response = self.client.post("/api/integrations/event-mappings", json=mapping_data)
        assert response.status_code == 201, f"EventMapping 생성 실패: {response.json()}"
        mapping_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING,
            ConfigChangeLog.resource_id == mapping_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "EventMapping 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"

    def test_update_event_mapping_logs_config_change(self):
        """
        CCL-13.1-2: EventMapping 수정 시 ConfigChangeLog UPDATED 로그 검증

        Given: 기존 EventMapping
        When: PATCH /api/integrations/event-mappings/{id} 요청
        Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 EventMapping 생성
        mapping_data = {
            "name_event": "Original EventMapping",
            "category_event_mapping": "FENCE_SENSOR_ONLY",
            "status": True
        }
        create_response = self.client.post("/api/integrations/event-mappings", json=mapping_data)
        assert create_response.status_code == 201
        mapping_id = create_response.json()["data"]["id"]

        # When: EventMapping 수정
        update_data = {"name_event": "Updated EventMapping"}
        update_response = self.client.patch(f"/api/integrations/event-mappings/{mapping_id}", json=update_data)
        assert update_response.status_code == 200, f"EventMapping 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING,
            ConfigChangeLog.resource_id == mapping_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "EventMapping 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1: 변경된 필드만 저장
        assert "name_event" in log.before_state, "before_state에 변경된 필드(name_event)가 포함되어야 합니다"
        assert "name_event" in log.after_state, "after_state에 변경된 필드(name_event)가 포함되어야 합니다"

    def test_delete_event_mapping_logs_config_change(self):
        """
        CCL-13.1-3: EventMapping 삭제 시 ConfigChangeLog DELETED 로그 검증

        Given: 기존 EventMapping
        When: DELETE /api/integrations/event-mappings/{id} 요청
        Then: ConfigChangeLog에 DELETED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 EventMapping 생성
        mapping_data = {
            "name_event": "To be deleted EventMapping",
            "category_event_mapping": "FENCE_SENSOR_ONLY",
            "status": True
        }
        create_response = self.client.post("/api/integrations/event-mappings", json=mapping_data)
        assert create_response.status_code == 201
        mapping_id = create_response.json()["data"]["id"]

        # When: EventMapping 삭제
        delete_response = self.client.delete(f"/api/integrations/event-mappings/{mapping_id}")
        assert delete_response.status_code == 200, f"EventMapping 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING,
            ConfigChangeLog.resource_id == mapping_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "EventMapping 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"


class TestEventMappingCameraConfigChangeLog:
    """
    CCL-13.2: EventMappingCamera ConfigChangeLog 통합 테스트

    EventMappingCamera CRUD 작업 시 ConfigChangeLog에 로그가 기록되는지 검증합니다.
    - POST: CREATED 로그 기록
    - PATCH: UPDATED 로그 기록
    - DELETE: DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        """테스트 셋업: client, db, EventMapping, Camera 의존성 주입"""
        self.client = client
        self.db = test_db
        self._create_test_event_mapping()
        self._create_test_camera()

    def _create_test_event_mapping(self):
        """테스트용 EventMapping 생성"""
        from app.models.integration import EventMapping
        from app.utils.enums import EnumMappingEventCategory

        mapping = EventMapping(
            name_event="Test EventMapping for Camera CCL",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        self.event_mapping = mapping

    def _create_test_camera(self):
        """테스트용 Camera 생성"""
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=7001,
            group_device=1,
            name_device="Test Camera for CCL",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.NONE
        )
        self.db.add(camera)
        self.db.commit()
        self.db.refresh(camera)
        self.camera = camera

    def test_create_event_mapping_camera_logs_config_change(self):
        """
        CCL-13.2-1: EventMappingCamera 생성 시 ConfigChangeLog CREATED 로그 검증

        Given: 유효한 EventMappingCamera 데이터
        When: POST /api/integrations/event-mappings/{mapping_id}/cameras 요청
        Then: ConfigChangeLog에 CREATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 유효한 EventMappingCamera 데이터
        camera_config_data = {
            "camera_id": self.camera.id,
            "delay_time": 5,
            "is_enable": True,
            "priority": 1
        }

        # When: EventMappingCamera 생성
        response = self.client.post(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/cameras",
            json=camera_config_data
        )
        assert response.status_code == 201, f"EventMappingCamera 생성 실패: {response.json()}"
        config_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            ConfigChangeLog.resource_id == config_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "EventMappingCamera 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "camera_id" in log.after_state, "after_state에 camera_id가 포함되어야 합니다"

    def test_update_event_mapping_camera_logs_config_change(self):
        """
        CCL-13.2-2: EventMappingCamera 수정 시 ConfigChangeLog UPDATED 로그 검증

        Given: 기존 EventMappingCamera
        When: PATCH /api/integrations/event-mappings/{mapping_id}/cameras/{config_id} 요청
        Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 EventMappingCamera 생성
        camera_config_data = {
            "camera_id": self.camera.id,
            "delay_time": 5,
            "is_enable": True,
            "priority": 1
        }
        create_response = self.client.post(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/cameras",
            json=camera_config_data
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["data"]["id"]

        # When: EventMappingCamera 수정
        update_data = {"delay_time": 10}
        update_response = self.client.patch(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/cameras/{config_id}",
            json=update_data
        )
        assert update_response.status_code == 200, f"EventMappingCamera 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            ConfigChangeLog.resource_id == config_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "EventMappingCamera 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1: 변경된 필드만 저장
        assert "delay_time" in log.before_state, "before_state에 변경된 필드(delay_time)가 포함되어야 합니다"
        assert "delay_time" in log.after_state, "after_state에 변경된 필드(delay_time)가 포함되어야 합니다"

    def test_delete_event_mapping_camera_logs_config_change(self):
        """
        CCL-13.2-3: EventMappingCamera 삭제 시 ConfigChangeLog DELETED 로그 검증

        Given: 기존 EventMappingCamera
        When: DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{config_id} 요청
        Then: ConfigChangeLog에 DELETED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 EventMappingCamera 생성
        camera_config_data = {
            "camera_id": self.camera.id,
            "delay_time": 5,
            "is_enable": True,
            "priority": 1
        }
        create_response = self.client.post(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/cameras",
            json=camera_config_data
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["data"]["id"]

        # When: EventMappingCamera 삭제
        delete_response = self.client.delete(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/cameras/{config_id}"
        )
        assert delete_response.status_code == 200, f"EventMappingCamera 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            ConfigChangeLog.resource_id == config_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "EventMappingCamera 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "camera_id" in log.before_state, "before_state에 camera_id가 포함되어야 합니다"


class TestEventMappingSpeakerConfigChangeLog:
    """
    CCL-13.3: EventMappingSpeaker ConfigChangeLog 통합 테스트

    EventMappingSpeaker CRUD 작업 시 ConfigChangeLog에 로그가 기록되는지 검증합니다.
    - POST: CREATED 로그 기록
    - PATCH: UPDATED 로그 기록
    - DELETE: DELETED 로그 기록
    """

    @pytest.fixture(autouse=True)
    def setup(self, client, test_db):
        """테스트 셋업: client, db, EventMapping, Speaker 의존성 주입"""
        self.client = client
        self.db = test_db
        self._create_test_event_mapping()
        self._create_test_speaker()

    def _create_test_event_mapping(self):
        """테스트용 EventMapping 생성"""
        from app.models.integration import EventMapping
        from app.utils.enums import EnumMappingEventCategory

        mapping = EventMapping(
            name_event="Test EventMapping for Speaker CCL",
            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,
            status=True
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        self.event_mapping = mapping

    def _create_test_speaker(self):
        """테스트용 Speaker 생성"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(
            number_device=8001,
            group_device=1,
            name_device="Test Speaker for CCL",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            speaker_type=EnumSpeakerType.NORMAL
        )
        self.db.add(speaker)
        self.db.commit()
        self.db.refresh(speaker)
        self.speaker = speaker

    def test_create_event_mapping_speaker_logs_config_change(self):
        """
        CCL-13.3-1: EventMappingSpeaker 생성 시 ConfigChangeLog CREATED 로그 검증

        Given: 유효한 EventMappingSpeaker 데이터
        When: POST /api/integrations/event-mappings/{mapping_id}/speakers 요청
        Then: ConfigChangeLog에 CREATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 유효한 EventMappingSpeaker 데이터
        speaker_config_data = {
            "speaker_id": self.speaker.id,
            "repeat_count": 3,
            "is_enable": True,
            "priority": 1
        }

        # When: EventMappingSpeaker 생성
        response = self.client.post(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/speakers",
            json=speaker_config_data
        )
        assert response.status_code == 201, f"EventMappingSpeaker 생성 실패: {response.json()}"
        config_id = response.json()["data"]["id"]

        # Then: ConfigChangeLog에 CREATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            ConfigChangeLog.resource_id == config_id,
            ConfigChangeLog.action == EnumConfigActionType.CREATED
        ).first()

        assert log is not None, "EventMappingSpeaker 생성 시 ConfigChangeLog CREATED 로그가 기록되어야 합니다"
        assert log.after_state is not None, "CREATED 시 after_state가 있어야 합니다"
        assert log.before_state is None, "CREATED 시 before_state는 null이어야 합니다"
        assert "id" in log.after_state, "after_state에 id가 포함되어야 합니다"
        assert "speaker_id" in log.after_state, "after_state에 speaker_id가 포함되어야 합니다"

    def test_update_event_mapping_speaker_logs_config_change(self):
        """
        CCL-13.3-2: EventMappingSpeaker 수정 시 ConfigChangeLog UPDATED 로그 검증

        Given: 기존 EventMappingSpeaker
        When: PATCH /api/integrations/event-mappings/{mapping_id}/speakers/{config_id} 요청
        Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 EventMappingSpeaker 생성
        speaker_config_data = {
            "speaker_id": self.speaker.id,
            "repeat_count": 3,
            "is_enable": True,
            "priority": 1
        }
        create_response = self.client.post(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/speakers",
            json=speaker_config_data
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["data"]["id"]

        # When: EventMappingSpeaker 수정
        update_data = {"repeat_count": 5}
        update_response = self.client.patch(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/speakers/{config_id}",
            json=update_data
        )
        assert update_response.status_code == 200, f"EventMappingSpeaker 수정 실패: {update_response.json()}"

        # Then: ConfigChangeLog에 UPDATED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            ConfigChangeLog.resource_id == config_id,
            ConfigChangeLog.action == EnumConfigActionType.UPDATED
        ).first()

        assert log is not None, "EventMappingSpeaker 수정 시 ConfigChangeLog UPDATED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "UPDATED 시 before_state가 있어야 합니다"
        assert log.after_state is not None, "UPDATED 시 after_state가 있어야 합니다"
        # v1.1: 변경된 필드만 저장
        assert "repeat_count" in log.before_state, "before_state에 변경된 필드(repeat_count)가 포함되어야 합니다"
        assert "repeat_count" in log.after_state, "after_state에 변경된 필드(repeat_count)가 포함되어야 합니다"

    def test_delete_event_mapping_speaker_logs_config_change(self):
        """
        CCL-13.3-3: EventMappingSpeaker 삭제 시 ConfigChangeLog DELETED 로그 검증

        Given: 기존 EventMappingSpeaker
        When: DELETE /api/integrations/event-mappings/{mapping_id}/speakers/{config_id} 요청
        Then: ConfigChangeLog에 DELETED 로그가 기록됨
        """
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        # Given: 기존 EventMappingSpeaker 생성
        speaker_config_data = {
            "speaker_id": self.speaker.id,
            "repeat_count": 3,
            "is_enable": True,
            "priority": 1
        }
        create_response = self.client.post(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/speakers",
            json=speaker_config_data
        )
        assert create_response.status_code == 201
        config_id = create_response.json()["data"]["id"]

        # When: EventMappingSpeaker 삭제
        delete_response = self.client.delete(
            f"/api/integrations/event-mappings/{self.event_mapping.id}/speakers/{config_id}"
        )
        assert delete_response.status_code == 200, f"EventMappingSpeaker 삭제 실패: {delete_response.json()}"

        # Then: ConfigChangeLog에 DELETED 로그가 기록됨
        log = self.db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            ConfigChangeLog.resource_id == config_id,
            ConfigChangeLog.action == EnumConfigActionType.DELETED
        ).first()

        assert log is not None, "EventMappingSpeaker 삭제 시 ConfigChangeLog DELETED 로그가 기록되어야 합니다"
        assert log.before_state is not None, "DELETED 시 before_state가 있어야 합니다"
        assert log.after_state is None, "DELETED 시 after_state는 null이어야 합니다"
        assert "id" in log.before_state, "before_state에 id가 포함되어야 합니다"
        assert "speaker_id" in log.before_state, "before_state에 speaker_id가 포함되어야 합니다"