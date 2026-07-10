"""
Account Models Tests
PRD: PRD_Account_Design.md Section 4 (Database Schema)
TDD Phase: AC-2, AC-3, AC-4, AC-5

Tests for:
- UserGroup model (AC-2.1)
- User model (AC-3.1)
- UserSession model (AC-4.1)
- UserLoginLog model (AC-5.1)
"""
import pytest
from sqlalchemy import inspect


class TestUserGroupModel:
    """AC-2.1: UserGroup 모델 테스트"""

    def test_user_group_model_exists(self):
        """UserGroup 모델이 존재해야 한다"""
        from app.models.user import UserGroup

        assert UserGroup is not None
        assert hasattr(UserGroup, "__tablename__")
        assert UserGroup.__tablename__ == "user_groups"

    def test_user_group_has_name_field(self):
        """UserGroup에 name 필드가 존재해야 한다 (VARCHAR 100, NOT NULL, UNIQUE)"""
        from app.models.user import UserGroup

        assert hasattr(UserGroup, "name")
        column = UserGroup.__table__.columns["name"]
        assert column is not None
        # VARCHAR(100) 확인
        assert str(column.type) == "VARCHAR(100)"
        # NOT NULL 확인
        assert column.nullable is False
        # UNIQUE 확인
        assert column.unique is True

    def test_user_group_has_description_field(self):
        """UserGroup에 description 필드가 존재해야 한다 (TEXT, nullable)"""
        from app.models.user import UserGroup

        assert hasattr(UserGroup, "description")
        column = UserGroup.__table__.columns["description"]
        assert column is not None
        # TEXT 타입 확인
        assert "TEXT" in str(column.type).upper()
        # nullable 확인
        assert column.nullable is True

    def test_user_group_has_permissions_jsonb(self):
        """UserGroup에 permissions JSON 필드가 존재해야 한다"""
        from app.models.user import UserGroup

        assert hasattr(UserGroup, "permissions")
        column = UserGroup.__table__.columns["permissions"]
        assert column is not None
        # JSON 타입 확인 (JSON or JSONB for PostgreSQL compatibility)
        assert "JSON" in str(column.type).upper()

    def test_user_group_has_is_active(self):
        """UserGroup에 is_active 필드가 존재해야 한다 (default True)"""
        from app.models.user import UserGroup

        assert hasattr(UserGroup, "is_active")
        column = UserGroup.__table__.columns["is_active"]
        assert column is not None
        # BOOLEAN 타입 확인
        assert "BOOLEAN" in str(column.type).upper()
        # default True 확인
        assert column.default.arg is True

    def test_user_group_has_timestamps(self):
        """UserGroup에 created_at, updated_at 필드가 존재해야 한다"""
        from app.models.user import UserGroup

        assert hasattr(UserGroup, "created_at")
        assert hasattr(UserGroup, "updated_at")

        created_at = UserGroup.__table__.columns["created_at"]
        updated_at = UserGroup.__table__.columns["updated_at"]

        assert created_at is not None
        assert updated_at is not None

        # DateTime 타입 확인
        assert "TIMESTAMP" in str(created_at.type).upper() or "DATETIME" in str(created_at.type).upper()
        assert "TIMESTAMP" in str(updated_at.type).upper() or "DATETIME" in str(updated_at.type).upper()

    def test_user_group_has_audit_fields(self):
        """UserGroup에 created_by, updated_by 필드가 존재해야 한다"""
        from app.models.user import UserGroup

        assert hasattr(UserGroup, "created_by")
        assert hasattr(UserGroup, "updated_by")

        created_by = UserGroup.__table__.columns["created_by"]
        updated_by = UserGroup.__table__.columns["updated_by"]

        assert created_by is not None
        assert updated_by is not None
        # nullable 확인 (User FK이므로 nullable)
        assert created_by.nullable is True
        assert updated_by.nullable is True


class TestUserModel:
    """AC-3.1: User 모델 테스트"""

    def test_user_model_exists(self):
        """User 모델이 존재해야 한다 (Account PRD 기준)"""
        from app.models.user import AccountUser

        assert AccountUser is not None
        assert hasattr(AccountUser, "__tablename__")
        assert AccountUser.__tablename__ == "account_users"

    def test_user_has_login_id(self):
        """User에 login_id 필드가 존재해야 한다 (UNIQUE, NOT NULL)"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "login_id")
        column = AccountUser.__table__.columns["login_id"]
        assert column is not None
        assert column.unique is True
        assert column.nullable is False

    def test_user_has_password_hash(self):
        """User에 password_hash 필드가 존재해야 한다"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "password_hash")
        column = AccountUser.__table__.columns["password_hash"]
        assert column is not None
        assert column.nullable is False

    def test_user_has_personal_info(self):
        """User에 개인정보 필드가 존재해야 한다"""
        from app.models.user import AccountUser

        # 필수 필드
        assert hasattr(AccountUser, "name")
        assert hasattr(AccountUser, "email")

        # 선택 필드
        assert hasattr(AccountUser, "department")
        assert hasattr(AccountUser, "position")
        assert hasattr(AccountUser, "employee_number")
        assert hasattr(AccountUser, "photo_url")
        assert hasattr(AccountUser, "phone")

    def test_user_has_role(self):
        """User에 role 필드가 존재해야 한다 (EnumUserRole, default VIEWER)"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "role")
        column = AccountUser.__table__.columns["role"]
        assert column is not None
        # default 확인
        assert column.default is not None

    def test_user_has_group_id_fk(self):
        """User에 group_id FK가 존재해야 한다 (nullable - SET NULL)"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "group_id")
        column = AccountUser.__table__.columns["group_id"]
        assert column is not None
        assert column.nullable is True  # SET NULL on delete
        # FK 확인
        assert len(column.foreign_keys) > 0

    def test_user_has_status_fields(self):
        """User에 상태 필드가 존재해야 한다"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "is_active")
        assert hasattr(AccountUser, "is_locked")
        assert hasattr(AccountUser, "lock_reason")
        assert hasattr(AccountUser, "locked_at")
        assert hasattr(AccountUser, "locked_by")

    def test_user_has_password_policy_fields(self):
        """User에 비밀번호 정책 필드가 존재해야 한다"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "password_changed_at")
        assert hasattr(AccountUser, "password_expires_at")
        assert hasattr(AccountUser, "failed_login_count")

    def test_user_has_last_login_fields(self):
        """User에 마지막 로그인 필드가 존재해야 한다"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "last_login_at")
        assert hasattr(AccountUser, "last_login_ip")

    def test_user_has_timestamps(self):
        """User에 타임스탬프 및 감사 필드가 존재해야 한다"""
        from app.models.user import AccountUser

        assert hasattr(AccountUser, "created_at")
        assert hasattr(AccountUser, "updated_at")
        assert hasattr(AccountUser, "created_by")
        assert hasattr(AccountUser, "updated_by")


class TestUserSessionModel:
    """AC-4.1: UserSession 모델 테스트"""

    def test_user_session_model_exists(self):
        """UserSession 모델이 존재해야 한다"""
        from app.models.user import UserSession

        assert UserSession is not None
        assert hasattr(UserSession, "__tablename__")
        assert UserSession.__tablename__ == "user_sessions"

    def test_user_session_has_user_fk(self):
        """UserSession에 user_id FK가 존재해야 한다 (CASCADE)"""
        from app.models.user import UserSession

        assert hasattr(UserSession, "user_id")
        column = UserSession.__table__.columns["user_id"]
        assert column is not None
        assert len(column.foreign_keys) > 0
        assert column.nullable is False

    def test_user_session_has_token_fields(self):
        """UserSession에 토큰 필드가 존재해야 한다"""
        from app.models.user import UserSession

        assert hasattr(UserSession, "token")
        assert hasattr(UserSession, "refresh_token")

        token = UserSession.__table__.columns["token"]
        refresh_token = UserSession.__table__.columns["refresh_token"]
        assert token is not None
        assert refresh_token is not None

    def test_user_session_has_connection_info(self):
        """UserSession에 연결 정보 필드가 존재해야 한다 (PRD_UserSession_Improvement v1.2)"""
        from app.models.user import UserSession

        assert hasattr(UserSession, "ip_address")
        assert hasattr(UserSession, "user_agent")

    def test_user_session_has_time_fields(self):
        """UserSession에 시간 필드가 존재해야 한다 (PRD_UserSession_Improvement v1.2: login_at→created_at, last_activity→updated_at)"""
        from app.models.user import UserSession

        assert hasattr(UserSession, "created_at")
        assert hasattr(UserSession, "expires_at")
        assert hasattr(UserSession, "updated_at")
        assert hasattr(UserSession, "logged_out_at")

    def test_user_session_has_status_fields(self):
        """UserSession에 상태 필드가 존재해야 한다"""
        from app.models.user import UserSession

        assert hasattr(UserSession, "is_active")
        assert hasattr(UserSession, "logout_reason")
        assert hasattr(UserSession, "forced_by")


class TestUserLoginLogModel:
    """AC-5.1: UserLoginLog 모델 테스트"""

    def test_user_login_log_model_exists(self):
        """UserLoginLog 모델이 존재해야 한다"""
        from app.models.user import UserLoginLog

        assert UserLoginLog is not None
        assert hasattr(UserLoginLog, "__tablename__")
        assert UserLoginLog.__tablename__ == "user_login_logs"

    def test_user_login_log_has_user_fk(self):
        """UserLoginLog에 user_id FK가 존재해야 한다 (SET NULL)"""
        from app.models.user import UserLoginLog

        assert hasattr(UserLoginLog, "user_id")
        column = UserLoginLog.__table__.columns["user_id"]
        assert column is not None
        assert len(column.foreign_keys) > 0
        assert column.nullable is True  # SET NULL on delete

    def test_user_login_log_has_login_id(self):
        """UserLoginLog에 login_id 필드가 존재해야 한다"""
        from app.models.user import UserLoginLog

        assert hasattr(UserLoginLog, "login_id")
        column = UserLoginLog.__table__.columns["login_id"]
        assert column is not None
        assert column.nullable is False  # user 삭제 후에도 보존

    def test_user_login_log_has_action(self):
        """UserLoginLog에 action 필드가 존재해야 한다"""
        from app.models.user import UserLoginLog

        assert hasattr(UserLoginLog, "action")
        column = UserLoginLog.__table__.columns["action"]
        assert column is not None
        assert column.nullable is False

    def test_user_login_log_has_result(self):
        """UserLoginLog에 result 필드가 존재해야 한다"""
        from app.models.user import UserLoginLog

        assert hasattr(UserLoginLog, "result")
        column = UserLoginLog.__table__.columns["result"]
        assert column is not None
        assert column.nullable is False

    def test_user_login_log_has_failure_reason(self):
        """UserLoginLog에 failure_reason 필드가 존재해야 한다"""
        from app.models.user import UserLoginLog

        assert hasattr(UserLoginLog, "failure_reason")
        column = UserLoginLog.__table__.columns["failure_reason"]
        assert column is not None
        assert column.nullable is True  # 실패 시에만 값이 있음
