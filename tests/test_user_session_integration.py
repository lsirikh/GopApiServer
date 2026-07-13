"""
Integration Tests for UserSession Improvement
PRD: PRD_UserSession_Improvement.md v1.2
TDD: Red -> Green -> Refactor
US-6: E2E Integration Tests
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.models.user import AccountUser, UserSession
from app.config import settings


# ============================================
# US-6.1: End-to-End Tests
# ============================================

class TestUserSessionE2EFlow:
    """US-6.1: 전체 기능 통합 테스트"""

    def test_login_then_list_sessions_has_join_fields(self, client: TestClient, test_db):
        """
        US-6.1: 로그인 → 세션 목록 조회 → login_id, role, created_at, updated_at 확인

        E2E Flow:
        1. 사용자 생성
        2. 로그인 API 호출
        3. 세션 목록 API 조회
        4. 응답에 login_id, role, created_at, updated_at 필드 존재 확인
        """
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # 1. Create test user
        user = AccountUser(
            login_id="e2e_test_user",
            password_hash=pwd_context.hash("test1234"),
            name="E2E Test User",
            role="OPERATOR",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # 2. Login via API
        login_response = client.post("/api/auth/login", json={
            "login_id": "e2e_test_user",
            "password": "test1234"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        access_token = login_response.json()["data"]["access_token"]

        # 3. Get session list via API
        headers = {"Authorization": f"Bearer {access_token}"}
        list_response = client.get("/api/user-sessions", headers=headers)
        assert list_response.status_code == 200, f"Session list failed: {list_response.json()}"

        # 4. Verify response has JOIN fields
        data = list_response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

        session_data = data["data"][0]
        # Verify JOIN fields (login_id, role)
        assert "login_id" in session_data, "Response should have login_id field"
        assert "role" in session_data, "Response should have role field"
        assert session_data["login_id"] == "e2e_test_user", "login_id should match user"
        assert session_data["role"] == "OPERATOR", "role should match user"

        # Verify timestamp fields (created_at, updated_at)
        assert "created_at" in session_data, "Response should have created_at field"
        assert "updated_at" in session_data, "Response should have updated_at field"
        assert session_data["created_at"] is not None, "created_at should not be null"

    def test_login_then_get_session_has_client_info(self, client: TestClient, test_db):
        """
        US-6.1: 로그인 → 세션 상세 조회 → ip_address, user_agent 확인

        E2E Flow:
        1. 사용자 생성
        2. User-Agent 헤더와 함께 로그인 API 호출
        3. 세션 상세 API 조회
        4. 응답에 ip_address, user_agent 필드 존재 확인
        """
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # 1. Create test user
        user = AccountUser(
            login_id="e2e_client_info_user",
            password_hash=pwd_context.hash("test1234"),
            name="E2E Client Info User",
            role="VIEWER",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # 2. Login with User-Agent header
        login_headers = {"User-Agent": "Mozilla/5.0 (E2E Test)"}
        login_response = client.post(
            "/api/auth/login",
            json={
                "login_id": "e2e_client_info_user",
                "password": "test1234"
            },
            headers=login_headers
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        access_token = login_response.json()["data"]["access_token"]

        # 3. Get session list to find the session ID
        headers = {"Authorization": f"Bearer {access_token}"}
        list_response = client.get("/api/user-sessions", headers=headers)
        assert list_response.status_code == 200
        sessions = list_response.json()["data"]
        session_id = sessions[0]["id"]

        # 4. Get session detail via API
        detail_response = client.get(f"/api/user-sessions/{session_id}", headers=headers)
        assert detail_response.status_code == 200, f"Session detail failed: {detail_response.json()}"

        session_data = detail_response.json()["data"]

        # Verify client info fields
        assert "ip_address" in session_data, "Response should have ip_address field"
        assert "user_agent" in session_data, "Response should have user_agent field"
        # Note: ip_address may be None in test environment (testclient)
        assert session_data["user_agent"] == "Mozilla/5.0 (E2E Test)", \
            f"user_agent should match login header, got: {session_data['user_agent']}"

    def test_force_logout_sets_session_inactive(self, client: TestClient, test_db):
        """
        US-6.1: 강제 로그아웃 → 세션 is_active=false 확인

        E2E Flow:
        1. ADMIN 사용자 생성
        2. 일반 사용자 생성 및 로그인
        3. ADMIN으로 로그인
        4. ADMIN이 일반 사용자 세션 강제 로그아웃
        5. 세션 is_active=false 확인
        """
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # 1. Create admin user
        admin_user = AccountUser(
            login_id="e2e_admin_user",
            password_hash=pwd_context.hash("admin1234"),
            name="E2E Admin User",
            role="ADMIN",
            is_active=True
        )
        test_db.add(admin_user)

        # 2. Create regular user
        regular_user = AccountUser(
            login_id="e2e_regular_user",
            password_hash=pwd_context.hash("user1234"),
            name="E2E Regular User",
            role="VIEWER",
            is_active=True
        )
        test_db.add(regular_user)
        test_db.commit()
        test_db.refresh(admin_user)
        test_db.refresh(regular_user)

        # 3. Login regular user first to create a session
        regular_login = client.post("/api/auth/login", json={
            "login_id": "e2e_regular_user",
            "password": "user1234"
        })
        assert regular_login.status_code == 200
        regular_token = regular_login.json()["data"]["access_token"]

        # Get the regular user's session ID
        regular_headers = {"Authorization": f"Bearer {regular_token}"}
        regular_sessions = client.get("/api/user-sessions", headers=regular_headers)
        regular_session_id = regular_sessions.json()["data"][0]["id"]

        # 4. Login admin
        admin_login = client.post("/api/auth/login", json={
            "login_id": "e2e_admin_user",
            "password": "admin1234"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["data"]["access_token"]

        # 5. Force logout the regular user's session
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        force_logout_response = client.delete(
            f"/api/user-sessions/{regular_session_id}",
            headers=admin_headers
        )
        assert force_logout_response.status_code == 200, \
            f"Force logout failed: {force_logout_response.json()}"
        assert force_logout_response.json()["success"] is True

        # 6. Verify session is now inactive
        session_detail = client.get(
            f"/api/user-sessions/{regular_session_id}",
            headers=admin_headers
        )
        assert session_detail.status_code == 200

        session_data = session_detail.json()["data"]
        assert session_data["is_active"] is False, "Session should be inactive after force logout"
        assert session_data["logout_reason"] == "FORCED", "Logout reason should be FORCED"
        assert session_data["logged_out_at"] is not None, "logged_out_at should be set"
