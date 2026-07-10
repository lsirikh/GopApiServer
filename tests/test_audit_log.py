"""
Audit Log TDD Tests
PRD: PRD_Audit_Log.md v1.0

TDD Cycle: Red -> Green -> Refactor
"""
import pytest
from enum import Enum


# ============================================================
# Phase AL-1: Enum Tests
# ============================================================

class TestAuditEnum:
    """AL-1: Audit Log Enum 테스트"""

    # AL-1.1: EnumAuditActionType Tests
    def test_enum_audit_action_type_exists(self):
        """EnumAuditActionType Enum이 존재하는지 확인"""
        from app.utils.enums import EnumAuditActionType
        assert issubclass(EnumAuditActionType, Enum)

    def test_enum_audit_action_type_user_crud_values(self):
        """USER_CREATED, USER_UPDATED, USER_DELETED 값 존재 확인"""
        from app.utils.enums import EnumAuditActionType
        assert EnumAuditActionType.USER_CREATED.value == "USER_CREATED"
        assert EnumAuditActionType.USER_UPDATED.value == "USER_UPDATED"
        assert EnumAuditActionType.USER_DELETED.value == "USER_DELETED"

    def test_enum_audit_action_type_user_lock_values(self):
        """USER_LOCKED, USER_UNLOCKED 값 존재 확인"""
        from app.utils.enums import EnumAuditActionType
        assert EnumAuditActionType.USER_LOCKED.value == "USER_LOCKED"
        assert EnumAuditActionType.USER_UNLOCKED.value == "USER_UNLOCKED"

    def test_enum_audit_action_type_user_activation_values(self):
        """USER_ACTIVATED, USER_DEACTIVATED 값 존재 확인"""
        from app.utils.enums import EnumAuditActionType
        assert EnumAuditActionType.USER_ACTIVATED.value == "USER_ACTIVATED"
        assert EnumAuditActionType.USER_DEACTIVATED.value == "USER_DEACTIVATED"

    def test_enum_audit_action_type_password_values(self):
        """PASSWORD_CHANGED, PASSWORD_RESET 값 존재 확인"""
        from app.utils.enums import EnumAuditActionType
        assert EnumAuditActionType.PASSWORD_CHANGED.value == "PASSWORD_CHANGED"
        assert EnumAuditActionType.PASSWORD_RESET.value == "PASSWORD_RESET"

    def test_enum_audit_action_type_role_group_values(self):
        """ROLE_CHANGED, GROUP_ASSIGNED 값 존재 확인"""
        from app.utils.enums import EnumAuditActionType
        assert EnumAuditActionType.ROLE_CHANGED.value == "ROLE_CHANGED"
        assert EnumAuditActionType.GROUP_ASSIGNED.value == "GROUP_ASSIGNED"

    def test_enum_audit_action_type_group_crud_values(self):
        """GROUP_CREATED, GROUP_UPDATED, GROUP_DELETED, PERMISSION_CHANGED 값 존재 확인"""
        from app.utils.enums import EnumAuditActionType
        assert EnumAuditActionType.GROUP_CREATED.value == "GROUP_CREATED"
        assert EnumAuditActionType.GROUP_UPDATED.value == "GROUP_UPDATED"
        assert EnumAuditActionType.GROUP_DELETED.value == "GROUP_DELETED"
        assert EnumAuditActionType.PERMISSION_CHANGED.value == "PERMISSION_CHANGED"

    def test_enum_audit_action_type_session_values(self):
        """SESSION_CREATED, SESSION_TERMINATED, SESSION_FORCED_LOGOUT 값 존재 확인"""
        from app.utils.enums import EnumAuditActionType
        assert EnumAuditActionType.SESSION_CREATED.value == "SESSION_CREATED"
        assert EnumAuditActionType.SESSION_TERMINATED.value == "SESSION_TERMINATED"
        assert EnumAuditActionType.SESSION_FORCED_LOGOUT.value == "SESSION_FORCED_LOGOUT"

    def test_enum_audit_action_type_has_18_values(self):
        """EnumAuditActionType이 18개의 값을 가지는지 확인"""
        from app.utils.enums import EnumAuditActionType
        assert len(EnumAuditActionType) == 18

    # AL-1.2: EnumAuditResourceType Tests
    def test_enum_audit_resource_type_exists(self):
        """EnumAuditResourceType Enum이 존재하는지 확인"""
        from app.utils.enums import EnumAuditResourceType
        assert issubclass(EnumAuditResourceType, Enum)

    def test_enum_audit_resource_type_values(self):
        """USER, USER_GROUP, USER_SESSION, PASSWORD 값 존재 확인"""
        from app.utils.enums import EnumAuditResourceType
        assert EnumAuditResourceType.USER.value == "USER"
        assert EnumAuditResourceType.USER_GROUP.value == "USER_GROUP"
        assert EnumAuditResourceType.USER_SESSION.value == "USER_SESSION"
        assert EnumAuditResourceType.PASSWORD.value == "PASSWORD"

    def test_enum_audit_resource_type_has_4_values(self):
        """EnumAuditResourceType이 4개의 값을 가지는지 확인"""
        from app.utils.enums import EnumAuditResourceType
        assert len(EnumAuditResourceType) == 4

    # AL-1.3: EnumAuditStatus Tests
    def test_enum_audit_status_exists(self):
        """EnumAuditStatus Enum이 존재하는지 확인"""
        from app.utils.enums import EnumAuditStatus
        assert issubclass(EnumAuditStatus, Enum)

    def test_enum_audit_status_values(self):
        """SUCCESS, FAILURE 값 존재 확인"""
        from app.utils.enums import EnumAuditStatus
        assert EnumAuditStatus.SUCCESS.value == "SUCCESS"
        assert EnumAuditStatus.FAILURE.value == "FAILURE"

    def test_enum_audit_status_has_2_values(self):
        """EnumAuditStatus가 2개의 값을 가지는지 확인"""
        from app.utils.enums import EnumAuditStatus
        assert len(EnumAuditStatus) == 2


# ============================================================
# Phase AL-2: AuditLog Model Tests
# ============================================================

class TestAuditLogModel:
    """AL-2: AuditLog SQLAlchemy Model 테스트"""

    def test_audit_log_model_exists(self):
        """AuditLog 모델 클래스가 존재하는지 확인"""
        from app.models.audit_log import AuditLog
        assert AuditLog is not None
        assert AuditLog.__tablename__ == "audit_logs"

    def test_audit_log_has_action_type_field(self):
        """action_type 필드 존재 확인 (String, nullable=False)"""
        from app.models.audit_log import AuditLog
        column = AuditLog.__table__.columns.get("action_type")
        assert column is not None
        assert column.nullable is False

    def test_audit_log_has_action_status_field(self):
        """action_status 필드 존재 확인 (String, default='SUCCESS')"""
        from app.models.audit_log import AuditLog
        column = AuditLog.__table__.columns.get("action_status")
        assert column is not None
        assert column.default is not None

    def test_audit_log_has_resource_fields(self):
        """resource_type, resource_id, resource_name 필드 존재 확인"""
        from app.models.audit_log import AuditLog
        columns = AuditLog.__table__.columns
        assert columns.get("resource_type") is not None
        assert columns.get("resource_id") is not None
        assert columns.get("resource_name") is not None

    def test_audit_log_has_actor_fields(self):
        """actor_id (FK), actor_login_id, actor_name, actor_role 필드 존재 확인"""
        from app.models.audit_log import AuditLog
        columns = AuditLog.__table__.columns
        assert columns.get("actor_id") is not None
        assert columns.get("actor_login_id") is not None
        assert columns.get("actor_name") is not None
        assert columns.get("actor_role") is not None

    def test_audit_log_has_changes_and_description(self):
        """changes (JSONB), description 필드 존재 확인"""
        from app.models.audit_log import AuditLog
        columns = AuditLog.__table__.columns
        assert columns.get("changes") is not None
        assert columns.get("description") is not None

    def test_audit_log_has_client_info_fields(self):
        """ip_address, user_agent 필드 존재 확인"""
        from app.models.audit_log import AuditLog
        columns = AuditLog.__table__.columns
        assert columns.get("ip_address") is not None
        assert columns.get("user_agent") is not None

    def test_audit_log_has_error_message_field(self):
        """error_message 필드 존재 확인"""
        from app.models.audit_log import AuditLog
        column = AuditLog.__table__.columns.get("error_message")
        assert column is not None

    def test_audit_log_has_created_at_field(self):
        """created_at 필드 존재 확인"""
        from app.models.audit_log import AuditLog
        column = AuditLog.__table__.columns.get("created_at")
        assert column is not None
        assert column.nullable is False

    def test_audit_log_can_be_imported_from_models(self):
        """models/__init__.py에서 AuditLog를 import할 수 있는지 확인"""
        from app.models import AuditLog
        assert AuditLog is not None


# ============================================================
# Phase AL-3: AuditLog Schema Tests
# ============================================================

class TestAuditLogSchema:
    """AL-3: AuditLog Pydantic Schema 테스트"""

    # AL-3.1: AuditLogCreate 테스트
    def test_audit_log_create_schema_exists(self):
        """AuditLogCreate 스키마 클래스 존재 확인"""
        from app.schemas.audit_log import AuditLogCreate
        assert AuditLogCreate is not None

    def test_audit_log_create_required_fields(self):
        """action_type, resource_type, actor_login_id 필수 필드 확인"""
        from app.schemas.audit_log import AuditLogCreate
        from pydantic import ValidationError

        # 필수 필드 없이 생성 시도 - 실패해야 함
        try:
            AuditLogCreate()
            assert False, "Should raise ValidationError"
        except ValidationError:
            pass

        # 필수 필드만 제공 - 성공해야 함
        log = AuditLogCreate(
            action_type="USER_CREATED",
            resource_type="USER",
            actor_login_id="admin"
        )
        assert log.action_type == "USER_CREATED"
        assert log.resource_type == "USER"
        assert log.actor_login_id == "admin"

    def test_audit_log_create_optional_fields(self):
        """Optional 필드들 확인 (resource_id, resource_name, changes, description 등)"""
        from app.schemas.audit_log import AuditLogCreate

        log = AuditLogCreate(
            action_type="USER_UPDATED",
            resource_type="USER",
            actor_login_id="admin",
            resource_id=1,
            resource_name="홍길동 (operator01)",
            changes={"before": {"role": "VIEWER"}, "after": {"role": "OPERATOR"}},
            description="역할 변경"
        )
        assert log.resource_id == 1
        assert log.resource_name == "홍길동 (operator01)"
        assert log.changes["before"]["role"] == "VIEWER"

    # AL-3.2: AuditLogResponse 테스트
    def test_audit_log_response_schema_exists(self):
        """AuditLogResponse 스키마 클래스 존재 확인"""
        from app.schemas.audit_log import AuditLogResponse
        assert AuditLogResponse is not None

    def test_audit_log_response_has_id_and_action_fields(self):
        """id, action_type, action_status 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogResponse
        fields = AuditLogResponse.model_fields
        assert "id" in fields
        assert "action_type" in fields
        assert "action_status" in fields

    def test_audit_log_response_has_resource_fields(self):
        """resource_type, resource_id, resource_name 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogResponse
        fields = AuditLogResponse.model_fields
        assert "resource_type" in fields
        assert "resource_id" in fields
        assert "resource_name" in fields

    def test_audit_log_response_has_actor_fields(self):
        """actor_id, actor_login_id, actor_name, actor_role 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogResponse
        fields = AuditLogResponse.model_fields
        assert "actor_id" in fields
        assert "actor_login_id" in fields
        assert "actor_name" in fields
        assert "actor_role" in fields

    def test_audit_log_response_has_detail_fields(self):
        """changes, description, ip_address, user_agent 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogResponse
        fields = AuditLogResponse.model_fields
        assert "changes" in fields
        assert "description" in fields
        assert "ip_address" in fields
        assert "user_agent" in fields

    def test_audit_log_response_has_created_at(self):
        """created_at 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogResponse
        fields = AuditLogResponse.model_fields
        assert "created_at" in fields

    def test_audit_log_response_has_examples(self):
        """json_schema_extra examples 설정 확인"""
        from app.schemas.audit_log import AuditLogResponse
        schema = AuditLogResponse.model_json_schema()
        properties = schema.get("properties", {})
        # action_type에 example이 있어야 함
        assert properties.get("action_type", {}).get("example") is not None

    def test_audit_log_can_be_imported_from_schemas(self):
        """schemas/__init__.py에서 import 가능한지 확인"""
        from app.schemas import AuditLogCreate, AuditLogResponse
        assert AuditLogCreate is not None
        assert AuditLogResponse is not None


# ============================================================
# Phase AL-4: Audit Service Tests
# ============================================================

class TestAuditService:
    """AL-4: AuditService 테스트"""

    # AL-4.1: 기본 함수 테스트
    def test_log_action_function_exists(self):
        """log_action() 함수가 존재하는지 확인"""
        from app.services.audit_service import log_action
        assert callable(log_action)

    def test_get_changes_function_exists(self):
        """get_changes() 함수가 존재하는지 확인"""
        from app.services.audit_service import get_changes
        assert callable(get_changes)

    def test_sanitize_changes_function_exists(self):
        """sanitize_changes() 함수가 존재하는지 확인"""
        from app.services.audit_service import sanitize_changes
        assert callable(sanitize_changes)

    def test_get_changes_returns_before_after_dict(self):
        """get_changes()가 before/after dict를 반환하는지 확인"""
        from app.services.audit_service import get_changes

        before = {"role": "VIEWER", "name": "홍길동"}
        after = {"role": "OPERATOR", "name": "홍길동"}

        result = get_changes(before, after)

        assert "before" in result
        assert "after" in result
        # 변경된 필드만 포함되어야 함
        assert result["before"] == {"role": "VIEWER"}
        assert result["after"] == {"role": "OPERATOR"}

    def test_get_changes_empty_when_no_changes(self):
        """get_changes()가 변경 없을 때 빈 dict 반환"""
        from app.services.audit_service import get_changes

        before = {"role": "VIEWER", "name": "홍길동"}
        after = {"role": "VIEWER", "name": "홍길동"}

        result = get_changes(before, after)

        assert result["before"] == {}
        assert result["after"] == {}

    def test_sanitize_changes_removes_password_field(self):
        """sanitize_changes()가 password 필드를 제거하는지 확인"""
        from app.services.audit_service import sanitize_changes

        changes = {
            "before": {"password": "old_hash", "role": "VIEWER"},
            "after": {"password": "new_hash", "role": "OPERATOR"}
        }

        result = sanitize_changes(changes)

        assert "password" not in result["before"]
        assert "password" not in result["after"]
        assert result["before"]["role"] == "VIEWER"
        assert result["after"]["role"] == "OPERATOR"

    def test_sanitize_changes_removes_hashed_password_field(self):
        """sanitize_changes()가 hashed_password 필드를 제거하는지 확인"""
        from app.services.audit_service import sanitize_changes

        changes = {
            "before": {"hashed_password": "old_hash", "name": "홍길동"},
            "after": {"hashed_password": "new_hash", "name": "김철수"}
        }

        result = sanitize_changes(changes)

        assert "hashed_password" not in result["before"]
        assert "hashed_password" not in result["after"]
        assert result["before"]["name"] == "홍길동"
        assert result["after"]["name"] == "김철수"

    def test_sanitize_changes_removes_password_hash_field(self):
        """sanitize_changes()가 password_hash 필드를 제거하는지 확인 (PRD 5.2)"""
        from app.services.audit_service import sanitize_changes

        changes = {
            "before": {"password_hash": "old_hash", "role": "VIEWER"},
            "after": {"password_hash": "new_hash", "role": "OPERATOR"}
        }

        result = sanitize_changes(changes)

        assert "password_hash" not in result["before"]
        assert "password_hash" not in result["after"]
        assert result["before"]["role"] == "VIEWER"
        assert result["after"]["role"] == "OPERATOR"

    def test_sanitize_changes_removes_refresh_token_field(self):
        """sanitize_changes()가 refresh_token 필드를 제거하는지 확인 (PRD 5.2)"""
        from app.services.audit_service import sanitize_changes

        changes = {
            "before": {"refresh_token": "old_token", "is_active": True},
            "after": {"refresh_token": "new_token", "is_active": False}
        }

        result = sanitize_changes(changes)

        assert "refresh_token" not in result["before"]
        assert "refresh_token" not in result["after"]
        assert result["before"]["is_active"] is True
        assert result["after"]["is_active"] is False

    def test_sanitize_changes_removes_user_password_field(self):
        """sanitize_changes()가 user_password 필드를 제거하는지 확인 (PRD 5.2)"""
        from app.services.audit_service import sanitize_changes

        changes = {
            "before": {"user_password": "old_pw", "ip_address": "192.168.1.1"},
            "after": {"user_password": "new_pw", "ip_address": "192.168.1.2"}
        }

        result = sanitize_changes(changes)

        assert "user_password" not in result["before"]
        assert "user_password" not in result["after"]
        assert result["before"]["ip_address"] == "192.168.1.1"
        assert result["after"]["ip_address"] == "192.168.1.2"


# ============================================================
# Phase AL-5: AuditLog Router Tests
# ============================================================

class TestAuditLogApi:
    """AL-5: AuditLog API 라우터 테스트"""

    # AL-5.1: GET /api/audit-logs 테스트
    def test_get_audit_logs_endpoint_exists(self):
        """GET /api/audit-logs 엔드포인트 존재 확인"""
        from app.routers.audit_logs import router
        routes = [route.path for route in router.routes]
        # 라우터에서 "" 경로가 있으면 main.py에서 prefix와 결합됨
        assert "" in routes

    def test_get_audit_logs_function_exists(self):
        """get_audit_logs 함수가 존재하는지 확인"""
        from app.routers.audit_logs import get_audit_logs
        assert callable(get_audit_logs)

    def test_get_audit_log_detail_endpoint_exists(self):
        """GET /api/audit-logs/{id} 엔드포인트 존재 확인"""
        from app.routers.audit_logs import router
        routes = [route.path for route in router.routes]
        # 라우터에서 /{audit_log_id} 경로가 있으면 main.py에서 prefix와 결합됨
        assert "/{audit_log_id}" in routes

    def test_get_audit_log_detail_function_exists(self):
        """get_audit_log_detail 함수가 존재하는지 확인"""
        from app.routers.audit_logs import get_audit_log_detail
        assert callable(get_audit_log_detail)

    # AL-5.2: AuditLogFilter 스키마 테스트
    def test_audit_log_filter_schema_exists(self):
        """AuditLogFilter 스키마 클래스 존재 확인"""
        from app.schemas.audit_log import AuditLogFilter
        assert AuditLogFilter is not None

    def test_audit_log_filter_has_pagination_fields(self):
        """page, limit 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogFilter
        fields = AuditLogFilter.model_fields
        assert "page" in fields
        assert "limit" in fields

    def test_audit_log_filter_has_filter_fields(self):
        """action_type, resource_type, actor_login_id 필터 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogFilter
        fields = AuditLogFilter.model_fields
        assert "action_type" in fields
        assert "resource_type" in fields
        assert "actor_login_id" in fields

    def test_audit_log_filter_has_date_filter_fields(self):
        """start_date, end_date 필터 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogFilter
        fields = AuditLogFilter.model_fields
        assert "start_date" in fields
        assert "end_date" in fields

    def test_audit_log_list_response_schema_exists(self):
        """AuditLogListResponse 스키마 클래스 존재 확인"""
        from app.schemas.audit_log import AuditLogListResponse
        assert AuditLogListResponse is not None

    def test_audit_log_list_response_has_pagination_fields(self):
        """total, page, limit, items 필드 존재 확인"""
        from app.schemas.audit_log import AuditLogListResponse
        fields = AuditLogListResponse.model_fields
        assert "total" in fields
        assert "page" in fields
        assert "limit" in fields
        assert "items" in fields


# ============================================================
# Phase AL-6: Integration Tests (기존 라우터에 감사 로그 호출 추가)
# ============================================================

class TestAuditIntegration:
    """AL-6: 기존 라우터에 감사 로그 연동 테스트"""

    # AL-6.1: users.py 감사 로그 연동
    def test_user_created_audit_log(self, client, test_db):
        """POST /api/users 시 USER_CREATED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog

        # 사용자 생성
        response = client.post("/api/users", json={
            "login_id": "testuser01",
            "password": "test1234",
            "name": "테스트유저"
        })
        assert response.status_code == 201

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_CREATED"
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER"
        assert audit_log.action_status == "SUCCESS"
        assert "testuser01" in audit_log.resource_name

    def test_user_updated_audit_log(self, client, test_db):
        """PUT /api/users/{id} 시 USER_UPDATED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # 테스트 사용자 생성
        user = AccountUser(
            login_id="updateuser01",
            password_hash=hash_password("test1234"),
            name="수정전이름",
            role="VIEWER"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # 사용자 수정
        response = client.put(f"/api/users/{user.id}", json={
            "name": "수정후이름"
        })
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_UPDATED",
            AuditLog.resource_id == user.id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER"
        assert audit_log.action_status == "SUCCESS"
        # before/after 변경 내역 확인
        assert audit_log.changes is not None
        assert "before" in audit_log.changes
        assert "after" in audit_log.changes

    def test_user_deleted_audit_log(self, client, test_db):
        """DELETE /api/users/{id} 시 USER_DELETED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # 테스트 사용자 생성
        user = AccountUser(
            login_id="deleteuser01",
            password_hash=hash_password("test1234"),
            name="삭제할유저",
            role="VIEWER"
        )
        test_db.add(user)
        test_db.commit()
        user_id = user.id
        user_name = f"{user.name} ({user.login_id})"

        # 사용자 삭제
        response = client.delete(f"/api/users/{user_id}")
        assert response.status_code == 200

        # 감사 로그 확인 (삭제된 사용자 정보가 스냅샷으로 저장되어야 함)
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_DELETED",
            AuditLog.resource_id == user_id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER"
        assert audit_log.action_status == "SUCCESS"
        # 삭제된 사용자 정보가 resource_name에 스냅샷으로 저장되어야 함
        assert audit_log.resource_name is not None

    def test_user_locked_audit_log(self, client, test_db):
        """POST /api/users/{id}/lock 시 USER_LOCKED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # 테스트 사용자 생성
        user = AccountUser(
            login_id="lockuser01",
            password_hash=hash_password("test1234"),
            name="잠금할유저",
            role="VIEWER",
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # 사용자 잠금
        response = client.post(f"/api/users/{user.id}/lock")
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_LOCKED",
            AuditLog.resource_id == user.id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER"
        assert audit_log.action_status == "SUCCESS"

    def test_user_unlocked_audit_log(self, client, test_db):
        """POST /api/users/{id}/unlock 시 USER_UNLOCKED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # 테스트 사용자 생성 (이미 잠긴 상태)
        user = AccountUser(
            login_id="unlockuser01",
            password_hash=hash_password("test1234"),
            name="잠금해제할유저",
            role="VIEWER",
            is_locked=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # 사용자 잠금 해제
        response = client.post(f"/api/users/{user.id}/unlock")
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_UNLOCKED",
            AuditLog.resource_id == user.id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER"
        assert audit_log.action_status == "SUCCESS"

    def test_password_reset_audit_log(self, client, test_db):
        """POST /api/users/{id}/reset-password 시 PASSWORD_RESET 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # 테스트 사용자 생성
        user = AccountUser(
            login_id="resetpwuser01",
            password_hash=hash_password("oldpassword"),
            name="비밀번호초기화유저",
            role="VIEWER"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # 비밀번호 초기화
        response = client.post(f"/api/users/{user.id}/reset-password", json={
            "new_password": "newpassword123"
        })
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "PASSWORD_RESET",
            AuditLog.resource_id == user.id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER"
        assert audit_log.action_status == "SUCCESS"
        # 비밀번호는 changes에 포함되지 않아야 함
        if audit_log.changes:
            assert "password" not in audit_log.changes.get("before", {})
            assert "password" not in audit_log.changes.get("after", {})

    # AL-6.2: user_groups.py 감사 로그 연동
    def test_group_created_audit_log(self, client, test_db):
        """POST /api/user-groups 시 GROUP_CREATED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog

        # 그룹 생성
        response = client.post("/api/user-groups", json={
            "name": "테스트그룹",
            "description": "테스트용 그룹입니다"
        })
        assert response.status_code == 201

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "GROUP_CREATED"
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER_GROUP"
        assert audit_log.action_status == "SUCCESS"
        assert "테스트그룹" in audit_log.resource_name

    def test_group_updated_audit_log(self, client, test_db):
        """PUT /api/user-groups/{id} 시 GROUP_UPDATED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import UserGroup

        # 테스트 그룹 생성
        group = UserGroup(
            name="수정전그룹",
            description="수정 전 설명"
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # 그룹 수정
        response = client.put(f"/api/user-groups/{group.id}", json={
            "name": "수정후그룹",
            "description": "수정 후 설명"
        })
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "GROUP_UPDATED",
            AuditLog.resource_id == group.id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER_GROUP"
        assert audit_log.action_status == "SUCCESS"
        # before/after 변경 내역 확인
        assert audit_log.changes is not None
        assert "before" in audit_log.changes
        assert "after" in audit_log.changes

    def test_group_deleted_audit_log(self, client, test_db):
        """DELETE /api/user-groups/{id} 시 GROUP_DELETED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import UserGroup

        # 테스트 그룹 생성
        group = UserGroup(
            name="삭제할그룹",
            description="삭제 테스트용"
        )
        test_db.add(group)
        test_db.commit()
        group_id = group.id
        group_name = group.name

        # 그룹 삭제
        response = client.delete(f"/api/user-groups/{group_id}")
        assert response.status_code == 200

        # 감사 로그 확인 (삭제된 그룹 정보가 스냅샷으로 저장되어야 함)
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "GROUP_DELETED",
            AuditLog.resource_id == group_id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER_GROUP"
        assert audit_log.action_status == "SUCCESS"
        # 삭제된 그룹 정보가 resource_name에 스냅샷으로 저장되어야 함
        assert audit_log.resource_name is not None
        assert group_name in audit_log.resource_name

    # AL-6.3: user_sessions.py 감사 로그 연동
    def test_session_forced_logout_audit_log(self, client, test_db):
        """DELETE /api/user-sessions/{id} 시 SESSION_FORCED_LOGOUT 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password
        from datetime import datetime
        from app.config import settings

        # 테스트 사용자 생성
        target_user = AccountUser(
            login_id="sessionuser01",
            password_hash=hash_password("test1234"),
            name="세션테스트유저",
            role="VIEWER"
        )
        test_db.add(target_user)
        test_db.commit()
        test_db.refresh(target_user)

        # 테스트 세션 생성
        from datetime import timedelta
        session = UserSession(
            user_id=target_user.id,
            token="test_session_token_123",
            ip_address="192.168.1.100",
            user_agent="Test User Agent",
            is_active=True,
            expires_at=datetime.now(settings.tz) + timedelta(hours=1)
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)

        session_id = session.id

        # 세션 강제 로그아웃
        response = client.delete(f"/api/user-sessions/{session_id}")
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "SESSION_FORCED_LOGOUT",
            AuditLog.resource_id == session_id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER_SESSION"
        assert audit_log.action_status == "SUCCESS"
        assert audit_log.resource_name is not None

    # AL-6.4: users.py (me/password) 비밀번호 변경 감사 로그 연동
    def test_password_changed_audit_log(self, client, test_db):
        """PUT /api/users/me/password 시 PASSWORD_CHANGED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog

        # 현재 로그인한 사용자(test_admin)의 비밀번호 변경
        response = client.put("/api/users/me/password", json={
            "current_password": "test1234",
            "new_password": "newpassword123"
        })
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "PASSWORD_CHANGED"
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "PASSWORD"
        assert audit_log.action_status == "SUCCESS"
        # 비밀번호는 changes에 포함되지 않아야 함
        if audit_log.changes:
            assert "password" not in audit_log.changes.get("before", {})
            assert "password" not in audit_log.changes.get("after", {})

    # AL-6.5: PUT /me (내 정보 수정) 감사 로그 연동
    def test_update_my_info_creates_audit_log(self, client, test_db):
        """PUT /api/users/me 시 USER_UPDATED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog

        # 현재 로그인한 사용자(test_admin)의 정보 수정
        response = client.put("/api/users/me", json={
            "name": "수정된관리자이름"
        })
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_UPDATED"
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER"
        assert audit_log.action_status == "SUCCESS"
        # before/after 변경 내역 확인
        assert audit_log.changes is not None
        assert "before" in audit_log.changes
        assert "after" in audit_log.changes
        assert audit_log.changes["before"]["name"] == "Test Admin"
        assert audit_log.changes["after"]["name"] == "수정된관리자이름"

    def test_update_my_info_audit_captures_changed_fields_only(self, client, test_db):
        """PUT /api/users/me 시 변경된 필드만 감사 로그에 기록되는지 확인"""
        from app.models.audit_log import AuditLog

        # 이름과 이메일만 수정 (department, position, phone은 변경 안 함)
        response = client.put("/api/users/me", json={
            "name": "변경이름",
            "email": "changed@test.com"
        })
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_UPDATED"
        ).first()

        assert audit_log is not None
        assert audit_log.changes is not None
        # 변경된 필드만 기록
        assert "name" in audit_log.changes["after"]
        assert "email" in audit_log.changes["after"]
        # 변경되지 않은 필드는 기록되지 않아야 함
        assert "department" not in audit_log.changes.get("after", {})
        assert "position" not in audit_log.changes.get("after", {})
        assert "phone" not in audit_log.changes.get("after", {})

    def test_update_my_info_no_change_no_audit(self, client, test_db):
        """PUT /api/users/me 시 변경 사항이 없으면 감사 로그가 생성되지 않아야 함"""
        from app.models.audit_log import AuditLog

        # 현재 이름과 동일한 값으로 수정 시도 (test_admin의 이름은 "Test Admin")
        response = client.put("/api/users/me", json={
            "name": "Test Admin"
        })
        assert response.status_code == 200

        # 감사 로그 미생성 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "USER_UPDATED"
        ).first()

        assert audit_log is None

    # AL-6.6: user_sessions.py — 전체 세션 강제 로그아웃 감사 로그 연동
    def test_force_logout_all_sessions_creates_audit_log(self, client, test_db):
        """DELETE /api/user-sessions/user/{user_id} 시 SESSION_FORCED_LOGOUT 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password
        from datetime import datetime, timedelta
        from app.config import settings

        # 테스트 대상 사용자 생성
        target_user = AccountUser(
            login_id="bulklogout01",
            password_hash=hash_password("test1234"),
            name="전체로그아웃대상",
            role="VIEWER"
        )
        test_db.add(target_user)
        test_db.commit()
        test_db.refresh(target_user)

        # 활성 세션 2개 생성
        for i in range(2):
            session = UserSession(
                user_id=target_user.id,
                token=f"bulk_token_{i}",
                ip_address="192.168.1.100",
                user_agent="Test Agent",
                is_active=True,
                expires_at=datetime.now(settings.tz) + timedelta(hours=1)
            )
            test_db.add(session)
        test_db.commit()

        # 전체 세션 강제 로그아웃
        response = client.delete(f"/api/user-sessions/user/{target_user.id}")
        assert response.status_code == 200

        # 감사 로그 확인
        audit_logs = test_db.query(AuditLog).filter(
            AuditLog.action_type == "SESSION_FORCED_LOGOUT",
        ).all()

        assert len(audit_logs) >= 1
        audit_log = audit_logs[0]
        assert audit_log.resource_type == "USER_SESSION"
        assert audit_log.action_status == "SUCCESS"

    # AL-6.7: user_sessions.py — 내 세션 종료 감사 로그 연동
    def test_delete_my_session_creates_audit_log(self, client, test_db):
        """DELETE /api/user-sessions/me/{session_id} 시 SESSION_TERMINATED 감사 로그가 생성되는지 확인"""
        from app.models.audit_log import AuditLog
        from app.models.user import AccountUser, UserSession
        from datetime import datetime, timedelta
        from app.config import settings

        # 현재 로그인한 사용자(test_admin)의 세션 조회
        admin = test_db.query(AccountUser).filter(
            AccountUser.login_id == "test_admin"
        ).first()

        # 세션 생성
        session = UserSession(
            user_id=admin.id,
            token="my_session_token_for_delete",
            ip_address="192.168.1.200",
            user_agent="Test Agent",
            is_active=True,
            expires_at=datetime.now(settings.tz) + timedelta(hours=1)
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)

        session_id = session.id

        # 내 세션 종료
        response = client.delete(f"/api/user-sessions/me/{session_id}")
        assert response.status_code == 200

        # 감사 로그 확인
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.action_type == "SESSION_TERMINATED",
            AuditLog.resource_id == session_id
        ).first()

        assert audit_log is not None
        assert audit_log.resource_type == "USER_SESSION"
        assert audit_log.action_status == "SUCCESS"