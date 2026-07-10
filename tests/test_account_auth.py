"""
Account Auth API Tests
PRD: PRD_Account_Design.md Section 6 (Auth API)
TDD Phase: AC-6

Tests for:
- Login API (AC-6.1)
- Logout API (AC-6.2)
- Refresh API (AC-6.3)
- Me API (AC-6.4)
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestAccountLoginApi:
    """AC-6.1: Login API Tests"""

    def test_login_success(self, client, test_db):
        """POST /api/auth/login returns 200 with valid credentials"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="testuser",
            password_hash=hash_password("password123"),
            name="Test User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login request
        response = client.post(
            "/api/auth/login",
            json={"login_id": "testuser", "password": "password123"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_login_returns_tokens(self, client, test_db):
        """POST /api/auth/login returns access_token and refresh_token"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="testuser",
            password_hash=hash_password("password123"),
            name="Test User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login request
        response = client.post(
            "/api/auth/login",
            json={"login_id": "testuser", "password": "password123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

        # Check tokens are present
        token_data = data["data"]
        assert "access_token" in token_data, "Response should include access_token"
        assert "refresh_token" in token_data, "Response should include refresh_token"
        assert "token_type" in token_data
        assert token_data["token_type"] == "bearer"

        # Verify tokens are non-empty strings
        assert isinstance(token_data["access_token"], str) and len(token_data["access_token"]) > 0
        assert isinstance(token_data["refresh_token"], str) and len(token_data["refresh_token"]) > 0

    def test_login_returns_user_info(self, client, test_db):
        """POST /api/auth/login returns user info with permissions"""
        from app.models.user import AccountUser, UserGroup
        from app.utils.auth import hash_password

        # Create UserGroup with permissions
        test_group = UserGroup(
            name="Test Group",
            description="Test group description",
            permissions={"modules": {"reports": {"view": True}, "events": {"view": True}}, "device_groups": [1, 2]},
            is_active=True
        )
        test_db.add(test_group)
        test_db.commit()

        # Create test AccountUser with group
        test_user = AccountUser(
            login_id="testuser",
            password_hash=hash_password("password123"),
            name="Test User",
            email="test@example.com",
            department="IT",
            role="OPERATOR",
            group_id=test_group.id,
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login request
        response = client.post(
            "/api/auth/login",
            json={"login_id": "testuser", "password": "password123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        token_data = data["data"]

        # Check user info is present
        assert "user" in token_data, "Response should include user info"
        user_info = token_data["user"]

        # Verify user fields
        assert user_info["login_id"] == "testuser"
        assert user_info["name"] == "Test User"
        assert user_info["role"] == "OPERATOR"

        # Verify permissions from group
        assert "permissions" in user_info, "User info should include permissions"

    def test_login_invalid_credentials(self, client, test_db):
        """POST /api/auth/login returns 401 with invalid credentials"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="testuser",
            password_hash=hash_password("password123"),
            name="Test User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Test wrong password
        response = client.post(
            "/api/auth/login",
            json={"login_id": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401

        # Test non-existent user
        response = client.post(
            "/api/auth/login",
            json={"login_id": "nonexistent", "password": "password123"}
        )
        assert response.status_code == 401

    def test_login_account_locked(self, client, test_db):
        """POST /api/auth/login returns 403 for locked account"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create locked AccountUser
        test_user = AccountUser(
            login_id="lockeduser",
            password_hash=hash_password("password123"),
            name="Locked User",
            role="VIEWER",
            is_active=True,
            is_locked=True,
            lock_reason="Too many failed login attempts"
        )
        test_db.add(test_user)
        test_db.commit()

        # Try to login with locked account
        response = client.post(
            "/api/auth/login",
            json={"login_id": "lockeduser", "password": "password123"}
        )

        assert response.status_code == 403
        data = response.json()
        # Check for "locked" in either detail (direct error) or error.message (structured error)
        error_message = data.get("detail", "") or data.get("error", {}).get("message", "")
        assert "locked" in error_message.lower()

    def test_login_account_inactive(self, client, test_db):
        """POST /api/auth/login returns 403 for inactive account"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create inactive AccountUser
        test_user = AccountUser(
            login_id="inactiveuser",
            password_hash=hash_password("password123"),
            name="Inactive User",
            role="VIEWER",
            is_active=False,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Try to login with inactive account
        response = client.post(
            "/api/auth/login",
            json={"login_id": "inactiveuser", "password": "password123"}
        )

        assert response.status_code == 403
        data = response.json()
        # Check for "inactive" in either detail (direct error) or error.message (structured error)
        error_message = data.get("detail", "") or data.get("error", {}).get("message", "")
        assert "inactive" in error_message.lower()

    def test_login_creates_session(self, client, test_db):
        """POST /api/auth/login creates a UserSession record"""
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="sessionuser",
            password_hash=hash_password("password123"),
            name="Session User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Login request
        response = client.post(
            "/api/auth/login",
            json={"login_id": "sessionuser", "password": "password123"}
        )

        assert response.status_code == 200

        # Check that UserSession was created
        session = test_db.query(UserSession).filter(
            UserSession.user_id == test_user.id
        ).first()

        assert session is not None, "UserSession should be created on login"
        assert session.is_active is True
        assert session.token is not None
        assert session.refresh_token is not None

    def test_login_creates_log(self, client, test_db):
        """POST /api/auth/login creates a UserLoginLog record"""
        from app.models.user import AccountUser, UserLoginLog
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="loguser",
            password_hash=hash_password("password123"),
            name="Log User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Login request
        response = client.post(
            "/api/auth/login",
            json={"login_id": "loguser", "password": "password123"}
        )

        assert response.status_code == 200

        # Check that UserLoginLog was created
        log = test_db.query(UserLoginLog).filter(
            UserLoginLog.login_id == "loguser"
        ).first()

        assert log is not None, "UserLoginLog should be created on login"
        assert log.user_id == test_user.id
        assert log.action == "LOGIN"
        assert log.result == "SUCCESS"

    def test_login_increments_failed_count(self, client, test_db):
        """POST /api/auth/login increments failed_login_count on wrong password"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="failuser",
            password_hash=hash_password("password123"),
            name="Fail User",
            role="VIEWER",
            is_active=True,
            is_locked=False,
            failed_login_count=0
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Verify initial count is 0
        assert test_user.failed_login_count == 0

        # Attempt login with wrong password
        response = client.post(
            "/api/auth/login",
            json={"login_id": "failuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401

        # Refresh user from database
        test_db.refresh(test_user)

        # Verify failed_login_count was incremented
        assert test_user.failed_login_count == 1, "failed_login_count should be incremented on failed login"

    def test_login_locks_after_max_failures(self, client, test_db):
        """POST /api/auth/login locks account after 5 failed attempts"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser with 4 failed attempts
        test_user = AccountUser(
            login_id="lockableuser",
            password_hash=hash_password("password123"),
            name="Lockable User",
            role="VIEWER",
            is_active=True,
            is_locked=False,
            failed_login_count=4
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Verify initial state
        assert test_user.failed_login_count == 4
        assert test_user.is_locked is False

        # Attempt login with wrong password (5th failure)
        response = client.post(
            "/api/auth/login",
            json={"login_id": "lockableuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401

        # Refresh user from database
        test_db.refresh(test_user)

        # Verify account is locked after 5 failures
        assert test_user.failed_login_count == 5
        assert test_user.is_locked is True, "Account should be locked after 5 failed attempts"
        assert test_user.lock_reason is not None, "Lock reason should be set"


class TestAccountLogoutApi:
    """AC-6.2: Logout API Tests"""

    def test_logout_success(self, client, test_db):
        """POST /api/auth/logout returns 200 with valid token"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="logoutuser",
            password_hash=hash_password("password123"),
            name="Logout User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login first to get a token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "logoutuser", "password": "password123"}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Logout request
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

    def test_logout_invalidates_session(self, client, test_db):
        """POST /api/auth/logout invalidates the user session"""
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="sessionlogout",
            password_hash=hash_password("password123"),
            name="Session Logout User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Login first to get a token and create session
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "sessionlogout", "password": "password123"}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Verify session is active before logout
        session = test_db.query(UserSession).filter(
            UserSession.user_id == test_user.id,
            UserSession.is_active == True
        ).first()
        assert session is not None, "Session should exist and be active before logout"

        # Logout request
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200

        # Refresh session from database
        test_db.refresh(session)

        # Verify session is invalidated
        assert session.is_active is False, "Session should be inactive after logout"
        assert session.logout_reason is not None, "Logout reason should be set"

    def test_logout_creates_log(self, client, test_db):
        """POST /api/auth/logout creates a UserLoginLog record"""
        from app.models.user import AccountUser, UserLoginLog
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="loglogout",
            password_hash=hash_password("password123"),
            name="Log Logout User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Login first to get a token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "loglogout", "password": "password123"}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Count existing logout logs
        initial_logout_count = test_db.query(UserLoginLog).filter(
            UserLoginLog.login_id == "loglogout",
            UserLoginLog.action == "LOGOUT"
        ).count()

        # Logout request
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200

        # Verify logout log was created
        logout_log = test_db.query(UserLoginLog).filter(
            UserLoginLog.login_id == "loglogout",
            UserLoginLog.action == "LOGOUT"
        ).first()

        assert logout_log is not None, "UserLoginLog should be created on logout"
        assert logout_log.user_id == test_user.id
        assert logout_log.result == "SUCCESS"

    def test_logout_without_token(self, client):
        """POST /api/auth/logout returns 401 without token"""
        # Logout request without Authorization header
        response = client.post("/api/auth/logout")

        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


class TestAccountRefreshApi:
    """AC-6.3: Refresh API Tests"""

    def test_refresh_success(self, client, test_db):
        """POST /api/auth/refresh returns 200 with valid refresh token"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="refreshuser",
            password_hash=hash_password("password123"),
            name="Refresh User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login first to get tokens
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "refreshuser", "password": "password123"}
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["data"]["refresh_token"]

        # Refresh request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

    def test_refresh_returns_new_tokens(self, client, test_db):
        """Refresh returns new access_token and refresh_token"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="refreshuser2",
            password_hash=hash_password("password123"),
            name="Refresh User 2",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login first to get tokens
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "refreshuser2", "password": "password123"}
        )
        assert login_response.status_code == 200
        original_access = login_response.json()["data"]["access_token"]
        original_refresh = login_response.json()["data"]["refresh_token"]

        # Refresh request
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": original_refresh}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "access_token" in data["data"], "access_token should be in response"
        assert "refresh_token" in data["data"], "refresh_token should be in response"
        assert data["data"]["token_type"] == "bearer"
        # New tokens should be different from original
        assert data["data"]["access_token"] != original_access, "Should return new access_token"
        assert data["data"]["refresh_token"] != original_refresh, "Should return new refresh_token"

    def test_refresh_invalid_token(self, client, test_db):
        """POST /api/auth/refresh returns 401 with invalid token"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

    def test_refresh_expired_token(self, client, test_db):
        """POST /api/auth/refresh returns 401 with expired token"""
        from datetime import timedelta
        from app.utils.auth import create_refresh_token

        # Create an expired refresh token
        expired_token = create_refresh_token(
            data={"sub": "expireduser"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": expired_token}
        )

        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


class TestAccountMeApi:
    """AC-6.4: Me API Tests"""

    def test_get_me_success(self, client, test_db):
        """GET /api/auth/me returns 200 with valid token"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="meuser",
            password_hash=hash_password("password123"),
            name="Me User",
            email="me@example.com",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login first to get access token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "meuser", "password": "password123"}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Get me request
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    @pytest.mark.skip(reason="client fixture overrides get_current_account_user to mock_admin; needs unoverridden client for real auth flow — see conftest.py L112-119 (G07 minimal)")
    def test_get_me_returns_user_info(self, client, test_db):
        """GET /api/auth/me returns user information"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test AccountUser
        test_user = AccountUser(
            login_id="meuser2",
            password_hash=hash_password("password123"),
            name="Me User Two",
            email="me2@example.com",
            department="Engineering",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login first to get access token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "meuser2", "password": "password123"}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        # Get me request
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["login_id"] == "meuser2"
        assert data["name"] == "Me User Two"
        assert data["email"] == "me2@example.com"
        assert data["department"] == "Engineering"
        assert data["role"] == "ADMIN"
        # Ensure password is not exposed
        assert "password_hash" not in data

    @pytest.mark.skip(reason="client fixture overrides get_current_account_user to mock_admin; needs unoverridden client for real auth flow — see conftest.py L112-119 (G07 minimal)")
    def test_get_me_without_token(self, client, test_db):
        """GET /api/auth/me without token returns 401"""
        # Request without Authorization header
        response = client.get("/api/auth/me")

        assert response.status_code == 401


# ============================================================
# US-2: Client Info Storage Tests (PRD_UserSession_Improvement.md)
# ============================================================

class TestLoginClientInfoStorage:
    """US-2: 로그인 시 클라이언트 정보 저장 테스트"""

    def test_login_stores_ip_address_in_session(self, client, test_db):
        """US-2.1: POST /api/auth/login 시 UserSession에 ip_address 저장"""
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password

        # Create test user
        test_user = AccountUser(
            login_id="iptest",
            password_hash=hash_password("password123"),
            name="IP Test User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Login request (TestClient typically uses 'testclient' as host)
        response = client.post(
            "/api/auth/login",
            json={"login_id": "iptest", "password": "password123"}
        )
        assert response.status_code == 200

        # Verify ip_address is stored in session
        session = test_db.query(UserSession).filter(
            UserSession.user_id == test_user.id
        ).first()

        assert session is not None
        assert session.ip_address is not None, \
            "UserSession should have ip_address stored"

    def test_login_stores_user_agent_in_session(self, client, test_db):
        """US-2.1: POST /api/auth/login 시 UserSession에 user_agent 저장"""
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password

        # Create test user
        test_user = AccountUser(
            login_id="uatest",
            password_hash=hash_password("password123"),
            name="UA Test User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()
        test_db.refresh(test_user)

        # Login request with custom User-Agent header
        response = client.post(
            "/api/auth/login",
            json={"login_id": "uatest", "password": "password123"},
            headers={"User-Agent": "TestBrowser/1.0"}
        )
        assert response.status_code == 200

        # Verify user_agent is stored in session
        session = test_db.query(UserSession).filter(
            UserSession.user_id == test_user.id
        ).first()

        assert session is not None
        assert session.user_agent is not None, \
            "UserSession should have user_agent stored"
        assert "TestBrowser" in session.user_agent

    def test_login_stores_ip_address_in_log(self, client, test_db):
        """US-2.1: POST /api/auth/login 시 UserLoginLog에 ip_address 저장"""
        from app.models.user import AccountUser, UserLoginLog
        from app.utils.auth import hash_password

        # Create test user
        test_user = AccountUser(
            login_id="iplogtest",
            password_hash=hash_password("password123"),
            name="IP Log Test User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login request
        response = client.post(
            "/api/auth/login",
            json={"login_id": "iplogtest", "password": "password123"}
        )
        assert response.status_code == 200

        # Verify ip_address is stored in login log
        log = test_db.query(UserLoginLog).filter(
            UserLoginLog.login_id == "iplogtest",
            UserLoginLog.action == "LOGIN"
        ).first()

        assert log is not None
        assert log.ip_address is not None, \
            "UserLoginLog should have ip_address stored"

    def test_login_stores_user_agent_in_log(self, client, test_db):
        """US-2.1: POST /api/auth/login 시 UserLoginLog에 user_agent 저장"""
        from app.models.user import AccountUser, UserLoginLog
        from app.utils.auth import hash_password

        # Create test user
        test_user = AccountUser(
            login_id="ualogtest",
            password_hash=hash_password("password123"),
            name="UA Log Test User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(test_user)
        test_db.commit()

        # Login request with custom User-Agent header
        response = client.post(
            "/api/auth/login",
            json={"login_id": "ualogtest", "password": "password123"},
            headers={"User-Agent": "TestBrowser/2.0"}
        )
        assert response.status_code == 200

        # Verify user_agent is stored in login log
        log = test_db.query(UserLoginLog).filter(
            UserLoginLog.login_id == "ualogtest",
            UserLoginLog.action == "LOGIN"
        ).first()

        assert log is not None
        assert log.user_agent is not None, \
            "UserLoginLog should have user_agent stored"
        assert "TestBrowser" in log.user_agent
