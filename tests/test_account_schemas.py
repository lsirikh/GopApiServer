"""
Account Schemas Tests
PRD: PRD_Account_Design.md Section 4 (Schemas)
TDD Phase: AC-2.3, AC-3.3, AC-4.2, AC-5.2

Tests for:
- UserGroup schemas (AC-2.3)
- User schemas (AC-3.3)
- UserSession schemas (AC-4.2)
- UserLoginLog schemas (AC-5.2)
"""
import pytest
from pydantic import ValidationError
from typing import get_type_hints


class TestUserGroupSchemas:
    """AC-2.3: UserGroup 스키마 테스트"""

    def test_user_group_create_schema(self):
        """UserGroupCreate 스키마 구조 검증"""
        from app.schemas.user import UserGroupCreate

        # 필수 필드 확인
        hints = get_type_hints(UserGroupCreate)
        assert "name" in hints

        # 인스턴스 생성 테스트
        data = {
            "name": "Test Group",
            "description": "Test Description",
            "permissions": {"modules": ["dashboard"]},
            "is_active": True
        }
        schema = UserGroupCreate(**data)
        assert schema.name == "Test Group"
        assert schema.description == "Test Description"
        assert schema.permissions == {"modules": ["dashboard"]}
        assert schema.is_active is True

    def test_user_group_update_schema(self):
        """UserGroupUpdate 스키마 구조 검증 (모든 필드 Optional)"""
        from app.schemas.user import UserGroupUpdate

        # Optional 필드 확인 - 빈 객체 생성 가능해야 함
        schema = UserGroupUpdate()
        assert schema.name is None
        assert schema.description is None
        assert schema.permissions is None
        assert schema.is_active is None

        # 일부 필드만 업데이트
        schema = UserGroupUpdate(name="Updated Name")
        assert schema.name == "Updated Name"
        assert schema.description is None

    def test_user_group_response_schema(self):
        """UserGroupResponse 스키마 구조 검증"""
        from app.schemas.user import UserGroupResponse
        from datetime import datetime

        hints = get_type_hints(UserGroupResponse)
        assert "id" in hints
        assert "name" in hints
        assert "description" in hints
        assert "permissions" in hints
        assert "is_active" in hints
        assert "created_at" in hints
        assert "updated_at" in hints

        # 인스턴스 생성 테스트
        now = datetime.now()
        data = {
            "id": 1,
            "name": "Test Group",
            "description": "Test Description",
            "permissions": {"modules": ["dashboard"]},
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        schema = UserGroupResponse(**data)
        assert schema.id == 1
        assert schema.name == "Test Group"

    def test_user_group_permissions_structure(self):
        """permissions JSONB 구조 검증 (modules, device_groups, time_restriction)"""
        from app.schemas.user import PermissionsSchema

        # 전체 구조 테스트
        data = {
            "modules": ["dashboard", "events", "devices"],
            "device_groups": [1, 2, 3],
            "time_restriction": {
                "enabled": True,
                "start_time": "09:00",
                "end_time": "18:00",
                "days": ["mon", "tue", "wed", "thu", "fri"]
            }
        }
        schema = PermissionsSchema(**data)
        assert schema.modules == ["dashboard", "events", "devices"]
        assert schema.device_groups == [1, 2, 3]
        assert schema.time_restriction is not None
        assert schema.time_restriction["enabled"] is True

        # 최소 구조 테스트 (모든 필드 Optional)
        schema_minimal = PermissionsSchema()
        assert schema_minimal.modules is None
        assert schema_minimal.device_groups is None
        assert schema_minimal.time_restriction is None


class TestAccountUserSchemas:
    """AC-3.3: User 스키마 테스트"""

    def test_user_create_schema(self):
        """AccountUserCreate 스키마 구조 검증 (password 포함)"""
        from app.schemas.user import AccountUserCreate

        hints = get_type_hints(AccountUserCreate)
        assert "login_id" in hints
        assert "password" in hints
        assert "name" in hints

        # 인스턴스 생성 테스트
        data = {
            "login_id": "testuser",
            "password": "securepassword123",
            "name": "Test User",
            "email": "test@example.com",
            "role": "VIEWER"
        }
        schema = AccountUserCreate(**data)
        assert schema.login_id == "testuser"
        assert schema.password == "securepassword123"
        assert schema.name == "Test User"

    def test_user_update_schema(self):
        """AccountUserUpdate 스키마 구조 검증 (모든 필드 Optional)"""
        from app.schemas.user import AccountUserUpdate

        # Optional 필드 확인 - 빈 객체 생성 가능해야 함
        schema = AccountUserUpdate()
        assert schema.name is None
        assert schema.email is None
        assert schema.role is None

        # 일부 필드만 업데이트
        schema = AccountUserUpdate(name="Updated Name", email="new@example.com")
        assert schema.name == "Updated Name"
        assert schema.email == "new@example.com"

    def test_user_response_schema(self):
        """AccountUserResponse 스키마 구조 검증 (password_hash 제외)"""
        from app.schemas.user import AccountUserResponse
        from datetime import datetime

        hints = get_type_hints(AccountUserResponse)
        assert "id" in hints
        assert "login_id" in hints
        assert "name" in hints
        assert "role" in hints
        # password_hash는 제외되어야 함
        assert "password_hash" not in hints
        assert "password" not in hints

        # 인스턴스 생성 테스트
        now = datetime.now()
        data = {
            "id": 1,
            "login_id": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "department": "IT",
            "position": "Developer",
            "employee_number": "EMP001",
            "photo_url": None,
            "phone": "010-1234-5678",
            "role": "VIEWER",
            "group_id": 1,
            "is_active": True,
            "is_locked": False,
            "lock_reason": None,
            "locked_at": None,
            "last_login_at": None,
            "last_login_ip": None,
            "created_at": now,
            "updated_at": now
        }
        schema = AccountUserResponse(**data)
        assert schema.id == 1
        assert schema.login_id == "testuser"

    def test_user_nested_response_schema(self):
        """AccountUserNestedResponse 스키마 구조 검증 (세션/그룹용 - 최소 필드)"""
        from app.schemas.user import AccountUserNestedResponse

        hints = get_type_hints(AccountUserNestedResponse)
        assert "id" in hints
        assert "login_id" in hints
        assert "name" in hints
        assert "role" in hints

        # 인스턴스 생성 테스트
        data = {
            "id": 1,
            "login_id": "testuser",
            "name": "Test User",
            "role": "VIEWER"
        }
        schema = AccountUserNestedResponse(**data)
        assert schema.id == 1
        assert schema.name == "Test User"


class TestUserSessionSchemas:
    """AC-4.3: UserSession 스키마 테스트"""

    def test_user_session_response_schema(self):
        """UserSessionResponse 스키마 구조 검증"""
        from app.schemas.user import UserSessionResponse
        from datetime import datetime

        # PRD_UserSession_Improvement v1.2: device_type/location/login_at/last_activity 제거,
        # created_at/updated_at으로 통합
        hints = get_type_hints(UserSessionResponse)
        assert "id" in hints
        assert "user_id" in hints
        assert "ip_address" in hints
        assert "created_at" in hints
        assert "updated_at" in hints
        assert "expires_at" in hints
        assert "is_active" in hints

        # 인스턴스 생성 테스트
        now = datetime.now()
        data = {
            "id": 1,
            "user_id": 1,
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "created_at": now,
            "updated_at": now,
            "expires_at": now,
            "is_active": True,
            "logout_reason": None,
            "logged_out_at": None
        }
        schema = UserSessionResponse(**data)
        assert schema.id == 1
        assert schema.is_active is True

    def test_user_session_list_response(self):
        """UserSessionListResponse 스키마 구조 검증"""
        from app.schemas.user import UserSessionListResponse, UserSessionResponse
        from datetime import datetime

        hints = get_type_hints(UserSessionListResponse)
        assert "sessions" in hints
        assert "total" in hints

        # 인스턴스 생성 테스트 (PRD_UserSession_Improvement v1.2)
        now = datetime.now()
        session_data = {
            "id": 1,
            "user_id": 1,
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "created_at": now,
            "updated_at": now,
            "expires_at": now,
            "is_active": True,
            "logout_reason": None,
            "logged_out_at": None
        }
        schema = UserSessionListResponse(
            sessions=[UserSessionResponse(**session_data)],
            total=1
        )
        assert len(schema.sessions) == 1
        assert schema.total == 1


class TestUserLoginLogSchemas:
    """AC-5.3: UserLoginLog 스키마 테스트"""

    def test_user_login_log_response_schema(self):
        """UserLoginLogResponse 스키마 구조 검증"""
        from app.schemas.user import UserLoginLogResponse
        from datetime import datetime

        hints = get_type_hints(UserLoginLogResponse)
        assert "id" in hints
        assert "user_id" in hints
        assert "login_id" in hints
        assert "action" in hints
        assert "result" in hints
        assert "failure_reason" in hints
        assert "ip_address" in hints
        assert "created_at" in hints

        # 인스턴스 생성 테스트
        now = datetime.now()
        data = {
            "id": 1,
            "user_id": 1,
            "login_id": "testuser",
            "action": "LOGIN",
            "result": "SUCCESS",
            "failure_reason": None,
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "created_at": now
        }
        schema = UserLoginLogResponse(**data)
        assert schema.id == 1
        assert schema.action == "LOGIN"
        assert schema.result == "SUCCESS"
