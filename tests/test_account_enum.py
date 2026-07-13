"""
Account Enum Tests
PRD: PRD_Account_Design.md Section 3.2, 5.2, 6.2
TDD Phase: AC-1

Tests for:
- EnumUserRole (5 values)
- EnumLogoutReason (6 values)
- EnumLoginAction (3 values)
- EnumLoginResult (2 values)
- EnumLoginFailureReason (7 values)
- EnumSystemEventType extensions (7 new values)
"""
import pytest
from enum import Enum


class TestEnumUserRole:
    """AC-1.1: EnumUserRole 테스트"""

    def test_enum_user_role_exists(self):
        """EnumUserRole Enum이 존재해야 한다"""
        from app.utils.enums import EnumUserRole

        assert EnumUserRole is not None
        assert issubclass(EnumUserRole, Enum)

    def test_enum_user_role_values(self):
        """EnumUserRole은 5개의 값을 가져야 한다 (ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST)"""
        from app.utils.enums import EnumUserRole

        expected_values = {"ADMIN", "MAINTAINER", "OPERATOR", "VIEWER", "GUEST"}
        actual_values = {e.value for e in EnumUserRole}

        assert actual_values == expected_values
        assert len(EnumUserRole) == 5

    def test_enum_user_role_str_inheritance(self):
        """EnumUserRole은 str과 Enum을 상속해야 한다 (SQLAlchemy/Pydantic 호환)"""
        from app.utils.enums import EnumUserRole

        assert issubclass(EnumUserRole, str)
        assert issubclass(EnumUserRole, Enum)
        # str 상속 확인 - 직접 문자열처럼 사용 가능
        assert EnumUserRole.ADMIN == "ADMIN"
        assert EnumUserRole.VIEWER == "VIEWER"


class TestEnumLogoutReason:
    """AC-1.2: EnumLogoutReason 테스트"""

    def test_enum_logout_reason_exists(self):
        """EnumLogoutReason Enum이 존재해야 한다"""
        from app.utils.enums import EnumLogoutReason

        assert EnumLogoutReason is not None
        assert issubclass(EnumLogoutReason, Enum)

    def test_enum_logout_reason_values(self):
        """EnumLogoutReason은 6개의 값을 가져야 한다"""
        from app.utils.enums import EnumLogoutReason

        expected_values = {
            "MANUAL", "EXPIRED", "FORCED", "LOCKED", "PASSWORD_CHANGED", "DUPLICATE"
        }
        actual_values = {e.value for e in EnumLogoutReason}

        assert actual_values == expected_values
        assert len(EnumLogoutReason) == 6


class TestEnumLoginActionAndResult:
    """AC-1.3: EnumLoginAction, EnumLoginResult 테스트"""

    def test_enum_login_action_exists(self):
        """EnumLoginAction Enum이 존재해야 한다"""
        from app.utils.enums import EnumLoginAction

        assert EnumLoginAction is not None
        assert issubclass(EnumLoginAction, Enum)

    def test_enum_login_action_values(self):
        """EnumLoginAction은 3개의 값을 가져야 한다 (LOGIN, LOGOUT, REFRESH)"""
        from app.utils.enums import EnumLoginAction

        expected_values = {"LOGIN", "LOGOUT", "REFRESH"}
        actual_values = {e.value for e in EnumLoginAction}

        assert actual_values == expected_values
        assert len(EnumLoginAction) == 3

    def test_enum_login_result_exists(self):
        """EnumLoginResult Enum이 존재해야 한다"""
        from app.utils.enums import EnumLoginResult

        assert EnumLoginResult is not None
        assert issubclass(EnumLoginResult, Enum)

    def test_enum_login_result_values(self):
        """EnumLoginResult는 2개의 값을 가져야 한다 (SUCCESS, FAILURE)"""
        from app.utils.enums import EnumLoginResult

        expected_values = {"SUCCESS", "FAILURE"}
        actual_values = {e.value for e in EnumLoginResult}

        assert actual_values == expected_values
        assert len(EnumLoginResult) == 2


class TestEnumLoginFailureReason:
    """AC-1.4: EnumLoginFailureReason 테스트"""

    def test_enum_login_failure_reason_exists(self):
        """EnumLoginFailureReason Enum이 존재해야 한다"""
        from app.utils.enums import EnumLoginFailureReason

        assert EnumLoginFailureReason is not None
        assert issubclass(EnumLoginFailureReason, Enum)

    def test_enum_login_failure_reason_values(self):
        """EnumLoginFailureReason은 7개의 값을 가져야 한다"""
        from app.utils.enums import EnumLoginFailureReason

        expected_values = {
            "INVALID_CREDENTIALS",  # 아이디/비밀번호 불일치
            "ACCOUNT_LOCKED",       # 계정 잠금
            "ACCOUNT_INACTIVE",     # 비활성화 계정
            "PASSWORD_EXPIRED",     # 비밀번호 만료
            "IP_BLOCKED",           # IP 차단
            "TIME_RESTRICTED",      # 접속 시간 제한
            "MAX_SESSIONS",         # 최대 세션 수 초과
        }
        actual_values = {e.value for e in EnumLoginFailureReason}

        assert actual_values == expected_values
        assert len(EnumLoginFailureReason) == 7


class TestEnumSystemEventTypeExtension:
    """AC-1.5: EnumSystemEventType 확장 테스트 - USER_* 타입은 EnumAuditLogActionType으로 이동 (PRD_SystemEvent_Sync.md v1.2)"""

    def test_user_types_removed_from_system_event_type(self):
        """USER_* 타입이 EnumSystemEventType에서 제거됨 (PRD_SystemEvent_Sync.md v1.2)"""
        from app.utils.enums import EnumSystemEventType
        # These types have been moved to EnumAuditLogActionType per PRD_SystemEvent_Sync.md
        removed_types = [
            "USER_LOGIN", "USER_LOGOUT", "USER_LOGIN_FAILED",
            "USER_LOCKED", "USER_UNLOCKED", "USER_CREATED",
            "USER_UPDATED", "USER_DELETED", "SESSION_FORCED_LOGOUT"
        ]
        for type_name in removed_types:
            assert not hasattr(EnumSystemEventType, type_name), f"{type_name} should be removed from EnumSystemEventType"

    def test_user_types_exist_in_audit_action_type(self):
        """USER_* 타입이 EnumAuditActionType에 존재해야 한다"""
        from app.utils.enums import EnumAuditActionType
        # These types should exist in EnumAuditActionType
        user_types = ["USER_CREATED", "USER_UPDATED", "USER_DELETED", "USER_LOCKED", "USER_UNLOCKED"]
        for type_name in user_types:
            assert hasattr(EnumAuditActionType, type_name), f"{type_name} should exist in EnumAuditActionType"

    def test_session_types_exist_in_audit_action_type(self):
        """SESSION_FORCED_LOGOUT 타입이 EnumAuditActionType에 존재해야 한다"""
        from app.utils.enums import EnumAuditActionType
        assert hasattr(EnumAuditActionType, "SESSION_FORCED_LOGOUT"), "SESSION_FORCED_LOGOUT should exist in EnumAuditActionType"

    def test_security_alert_exists_in_system_event_type(self):
        """SECURITY_ALERT 타입이 EnumSystemEventType에 존재해야 한다 (새로 추가)"""
        from app.utils.enums import EnumSystemEventType
        assert hasattr(EnumSystemEventType, "SECURITY_ALERT"), "SECURITY_ALERT should exist in EnumSystemEventType"
        assert EnumSystemEventType.SECURITY_ALERT.value == "SECURITY_ALERT"
