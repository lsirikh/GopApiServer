"""
Tests for Account User API endpoints (AC-7)
Following TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient


class TestUserListApi:
    """AC-7.1: User List/Get API Tests"""

    def test_get_users_list(self, client, test_db):
        """GET /api/users returns 200 with list of users"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test users
        user1 = AccountUser(
            login_id="listuser1",
            password_hash=hash_password("password123"),
            name="List User One",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        user2 = AccountUser(
            login_id="listuser2",
            password_hash=hash_password("password123"),
            name="List User Two",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([user1, user2])
        test_db.commit()

        # Login to get token (need admin user for this endpoint)
        admin_user = AccountUser(
            login_id="adminuser",
            password_hash=hash_password("adminpass"),
            name="Admin User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin_user)
        test_db.commit()

        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "adminuser", "password": "adminpass"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get users list
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2  # At least our test users

    def test_get_users_with_pagination(self, client, test_db):
        """GET /api/users supports page and limit parameters"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create multiple test users
        for i in range(15):
            user = AccountUser(
                login_id=f"pageuser{i}",
                password_hash=hash_password("password123"),
                name=f"Page User {i}",
                role="VIEWER",
                is_active=True,
                is_locked=False
            )
            test_db.add(user)
        test_db.commit()

        # Login to get token
        admin_user = AccountUser(
            login_id="paginationadmin",
            password_hash=hash_password("adminpass"),
            name="Pagination Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin_user)
        test_db.commit()

        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "paginationadmin", "password": "adminpass"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Test with limit
        response = client.get(
            "/api/users?limit=5",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5

        # Test with page and limit
        response2 = client.get(
            "/api/users?page=2&limit=5",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["data"]) == 5
        # Page 2 should have different users than page 1
        page1_ids = [u["id"] for u in data["data"]]
        page2_ids = [u["id"] for u in data2["data"]]
        assert set(page1_ids).isdisjoint(set(page2_ids))

    def test_get_users_filter_by_role(self, client, test_db):
        """GET /api/users supports role filter"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create users with different roles
        admin = AccountUser(
            login_id="roleadmin1",
            password_hash=hash_password("password123"),
            name="Role Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        viewer = AccountUser(
            login_id="roleviewer1",
            password_hash=hash_password("password123"),
            name="Role Viewer",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        operator = AccountUser(
            login_id="roleoperator1",
            password_hash=hash_password("password123"),
            name="Role Operator",
            role="OPERATOR",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([admin, viewer, operator])
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "roleadmin1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Filter by role=ADMIN
        response = client.get(
            "/api/users?role=ADMIN",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # All returned users should have role=ADMIN
        for user in data["data"]:
            assert user["role"] == "ADMIN"

    def test_get_users_filter_by_group(self, client, test_db):
        """GET /api/users supports group_id filter"""
        from app.models.user import AccountUser, UserGroup
        from app.utils.auth import hash_password

        # Create user groups
        group1 = UserGroup(name="Group One", is_active=True)
        group2 = UserGroup(name="Group Two", is_active=True)
        test_db.add_all([group1, group2])
        test_db.commit()
        test_db.refresh(group1)
        test_db.refresh(group2)

        # Create users in different groups
        user1 = AccountUser(
            login_id="groupuser1",
            password_hash=hash_password("password123"),
            name="Group User 1",
            role="VIEWER",
            group_id=group1.id,
            is_active=True,
            is_locked=False
        )
        user2 = AccountUser(
            login_id="groupuser2",
            password_hash=hash_password("password123"),
            name="Group User 2",
            role="VIEWER",
            group_id=group2.id,
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="groupadmin",
            password_hash=hash_password("password123"),
            name="Group Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([user1, user2, admin])
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Filter by group_id
        response = client.get(
            f"/api/users?group_id={group1.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # All returned users should belong to group1
        for user in data["data"]:
            assert user["group_id"] == group1.id

    def test_get_users_filter_by_department(self, client, test_db):
        """GET /api/users supports department filter"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create users in different departments
        user1 = AccountUser(
            login_id="deptuser1",
            password_hash=hash_password("password123"),
            name="Dept User 1",
            department="Engineering",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        user2 = AccountUser(
            login_id="deptuser2",
            password_hash=hash_password("password123"),
            name="Dept User 2",
            department="Marketing",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="deptadmin",
            password_hash=hash_password("password123"),
            name="Dept Admin",
            department="Engineering",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([user1, user2, admin])
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "deptadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Filter by department
        response = client.get(
            "/api/users?department=Engineering",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2  # At least user1 and admin
        # All returned users should have department=Engineering
        for user in data["data"]:
            assert user["department"] == "Engineering"

    def test_get_user_by_id(self, client, test_db):
        """GET /api/users/{id} returns 200 with user details"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test user
        target_user = AccountUser(
            login_id="targetuser1",
            password_hash=hash_password("password123"),
            name="Target User",
            email="target@example.com",
            department="IT",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="getbyidadmin",
            password_hash=hash_password("password123"),
            name="Get By ID Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "getbyidadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get user by ID
        response = client.get(
            f"/api/users/{target_user.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["data"]["id"] == target_user.id
        assert data["data"]["login_id"] == "targetuser1"
        assert data["data"]["name"] == "Target User"
        assert data["data"]["email"] == "target@example.com"

    def test_get_user_not_found(self, client, test_db):
        """GET /api/users/{id} returns 404 for non-existent user"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create admin user for authentication
        admin = AccountUser(
            login_id="notfoundadmin",
            password_hash=hash_password("password123"),
            name="Not Found Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "notfoundadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get non-existent user
        response = client.get(
            "/api/users/99999",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 404


class TestUserCreateApi:
    """AC-7.2: User Create API Tests"""

    def test_create_user_success(self, client, test_db):
        """POST /api/users creates a new user and returns 201"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create admin user for authentication
        admin = AccountUser(
            login_id="createadmin",
            password_hash=hash_password("password123"),
            name="Create Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "createadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Create new user
        response = client.post(
            "/api/users",
            json={
                "login_id": "newuser1",
                "password": "newpassword123",
                "name": "New User One",
                "email": "newuser1@example.com",
                "department": "Engineering",
                "role": "VIEWER"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["login_id"] == "newuser1"
        assert data["data"]["name"] == "New User One"
        assert "password_hash" not in data["data"]

    def test_create_user_hashes_password(self, client, test_db):
        """POST /api/users stores password as bcrypt hash"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password, verify_password

        # Create admin user for authentication
        admin = AccountUser(
            login_id="hashadmin",
            password_hash=hash_password("password123"),
            name="Hash Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "hashadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Create new user
        plain_password = "securepassword123"
        response = client.post(
            "/api/users",
            json={
                "login_id": "hashuser1",
                "password": plain_password,
                "name": "Hash User"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 201

        # Verify password is hashed in database
        created_user = test_db.query(AccountUser).filter(
            AccountUser.login_id == "hashuser1"
        ).first()
        assert created_user is not None
        # Password should be hashed, not plain text
        assert created_user.password_hash != plain_password
        # Should be able to verify the password
        assert verify_password(plain_password, created_user.password_hash) is True

    def test_create_user_duplicate_login_id(self, client, test_db):
        """POST /api/users returns 400 for duplicate login_id"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create existing user
        existing_user = AccountUser(
            login_id="duplicateuser",
            password_hash=hash_password("password123"),
            name="Existing User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="dupadmin",
            password_hash=hash_password("password123"),
            name="Dup Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([existing_user, admin])
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "dupadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Try to create user with same login_id
        response = client.post(
            "/api/users",
            json={
                "login_id": "duplicateuser",  # Same as existing
                "password": "newpassword123",
                "name": "New User"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 400

    def test_create_user_invalid_group(self, client, test_db):
        """POST /api/users returns 400 for non-existent group_id"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create admin user for authentication
        admin = AccountUser(
            login_id="groupadmin2",
            password_hash=hash_password("password123"),
            name="Group Admin 2",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupadmin2", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Try to create user with non-existent group_id
        response = client.post(
            "/api/users",
            json={
                "login_id": "invalidgroupuser",
                "password": "password123",
                "name": "Invalid Group User",
                "group_id": 99999  # Non-existent group
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 400


class TestUserUpdateDeleteApi:
    """AC-7.3: User Update/Delete API Tests"""

    def test_update_user_success(self, client, test_db):
        """PUT /api/users/{id} updates user and returns 200"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create user to update
        target_user = AccountUser(
            login_id="updateuser1",
            password_hash=hash_password("password123"),
            name="Original Name",
            email="original@example.com",
            department="Original Dept",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="updateadmin",
            password_hash=hash_password("password123"),
            name="Update Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "updateadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Update user
        response = client.put(
            f"/api/users/{target_user.id}",
            json={
                "name": "Updated Name",
                "email": "updated@example.com",
                "department": "Updated Dept"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["email"] == "updated@example.com"
        assert data["data"]["department"] == "Updated Dept"

    def test_update_user_not_found(self, client, test_db):
        """PUT /api/users/{id} returns 404 for non-existent user"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create admin user for authentication
        admin = AccountUser(
            login_id="updatenotfound",
            password_hash=hash_password("password123"),
            name="Update Not Found Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "updatenotfound", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Update non-existent user
        response = client.put(
            "/api/users/99999",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 404

    def test_delete_user_success(self, client, test_db):
        """DELETE /api/users/{id} deletes user and returns 200"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create user to delete
        target_user = AccountUser(
            login_id="deleteuser1",
            password_hash=hash_password("password123"),
            name="Delete User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="deleteadmin",
            password_hash=hash_password("password123"),
            name="Delete Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "deleteadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Delete user
        response = client.delete(
            f"/api/users/{target_user.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify user is deleted
        deleted_user = test_db.query(AccountUser).filter(
            AccountUser.id == target_user.id
        ).first()
        assert deleted_user is None

    def test_delete_user_not_found(self, client, test_db):
        """DELETE /api/users/{id} returns 404 for non-existent user"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create admin user for authentication
        admin = AccountUser(
            login_id="deletenotfound",
            password_hash=hash_password("password123"),
            name="Delete Not Found Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "deletenotfound", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Delete non-existent user
        response = client.delete(
            "/api/users/99999",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 404


class TestUserLockUnlockApi:
    """AC-7.4: User Lock/Unlock API Tests"""

    def test_lock_user_success(self, client, test_db):
        """POST /api/users/{id}/lock locks user and returns 200"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create user to lock
        target_user = AccountUser(
            login_id="lockuser1",
            password_hash=hash_password("password123"),
            name="Lock User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="lockadmin",
            password_hash=hash_password("password123"),
            name="Lock Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "lockadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Lock user
        response = client.post(
            f"/api/users/{target_user.id}/lock",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

        # Verify user is locked in database
        test_db.refresh(target_user)
        assert target_user.is_locked is True

    def test_lock_user_terminates_sessions(self, client, test_db):
        """POST /api/users/{id}/lock terminates user's active sessions"""
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import hash_password
        from datetime import datetime, timedelta

        # Create user to lock with active session
        target_user = AccountUser(
            login_id="lockuser2",
            password_hash=hash_password("password123"),
            name="Lock User 2",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="lockadmin2",
            password_hash=hash_password("password123"),
            name="Lock Admin 2",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Create active session for target user
        active_session = UserSession(
            user_id=target_user.id,
            token="test_access_token_123",
            refresh_token="test_refresh_token_123",
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=True
        )
        test_db.add(active_session)
        test_db.commit()

        # Verify session is active
        session_before = test_db.query(UserSession).filter(
            UserSession.user_id == target_user.id,
            UserSession.is_active == True
        ).first()
        assert session_before is not None

        # Login admin to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "lockadmin2", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Lock user
        response = client.post(
            f"/api/users/{target_user.id}/lock",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200

        # Verify all sessions are terminated
        active_sessions = test_db.query(UserSession).filter(
            UserSession.user_id == target_user.id,
            UserSession.is_active == True
        ).all()
        assert len(active_sessions) == 0

    def test_unlock_user_success(self, client, test_db):
        """POST /api/users/{id}/unlock unlocks user and returns 200"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create locked user to unlock
        target_user = AccountUser(
            login_id="unlockuser1",
            password_hash=hash_password("password123"),
            name="Unlock User",
            role="VIEWER",
            is_active=True,
            is_locked=True  # User is locked
        )
        admin = AccountUser(
            login_id="unlockadmin",
            password_hash=hash_password("password123"),
            name="Unlock Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "unlockadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Unlock user
        response = client.post(
            f"/api/users/{target_user.id}/unlock",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

        # Verify user is unlocked in database
        test_db.refresh(target_user)
        assert target_user.is_locked is False

    def test_lock_unlock_creates_system_event(self, client, test_db):
        """POST /api/users/{id}/lock and unlock create SystemEvent"""
        from app.models.user import AccountUser
        from app.models.system_event import SystemEvent
        from app.utils.auth import hash_password
        from app.utils.enums import EnumSystemEventType

        # Create user to lock/unlock
        target_user = AccountUser(
            login_id="eventuser1",
            password_hash=hash_password("password123"),
            name="Event User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="eventadmin",
            password_hash=hash_password("password123"),
            name="Event Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "eventadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Lock user
        client.post(
            f"/api/users/{target_user.id}/lock",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        # Verify SECURITY_ALERT system event was created for lock (USER_LOCKED moved to UserLoginLog per PRD_SystemEvent_Sync.md)
        lock_event = test_db.query(SystemEvent).filter(
            SystemEvent.type_event == EnumSystemEventType.SECURITY_ALERT.value,
            SystemEvent.title.contains("잠금")
        ).order_by(SystemEvent.id.desc()).first()
        assert lock_event is not None, "SECURITY_ALERT system event should be created for user lock"

        # Unlock user
        client.post(
            f"/api/users/{target_user.id}/unlock",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        # Verify SECURITY_ALERT system event was created for unlock (USER_UNLOCKED moved to UserLoginLog per PRD_SystemEvent_Sync.md)
        unlock_event = test_db.query(SystemEvent).filter(
            SystemEvent.type_event == EnumSystemEventType.SECURITY_ALERT.value,
            SystemEvent.title.contains("잠금 해제")
        ).order_by(SystemEvent.id.desc()).first()
        assert unlock_event is not None, "SECURITY_ALERT system event should be created for user unlock"


class TestUserPasswordApi:
    """AC-7.5: User Password API Tests"""

    def test_reset_password_success(self, client, test_db):
        """POST /api/users/{id}/reset-password resets password and returns 200"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password, verify_password

        # Create user to reset password
        target_user = AccountUser(
            login_id="resetuser1",
            password_hash=hash_password("oldpassword123"),
            name="Reset User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        admin = AccountUser(
            login_id="resetadmin",
            password_hash=hash_password("password123"),
            name="Reset Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add_all([target_user, admin])
        test_db.commit()
        test_db.refresh(target_user)

        # Store old password hash
        old_password_hash = target_user.password_hash

        # Login admin to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "resetadmin", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Reset password
        response = client.post(
            f"/api/users/{target_user.id}/reset-password",
            json={"new_password": "newpassword456"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

        # Verify password was changed in database
        test_db.refresh(target_user)
        assert target_user.password_hash != old_password_hash
        assert verify_password("newpassword456", target_user.password_hash) is True

    @pytest.mark.skip(reason="client fixture overrides get_current_account_user to mock_admin; needs unoverridden client for real auth flow — see conftest.py L112-119 (G07 minimal)")
    def test_change_my_password_success(self, client, test_db):
        """PUT /api/users/me/password changes current user's password"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password, verify_password

        # Create user
        user = AccountUser(
            login_id="changeuser1",
            password_hash=hash_password("oldpassword123"),
            name="Change User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # Store old password hash
        old_password_hash = user.password_hash

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "changeuser1", "password": "oldpassword123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Change password
        response = client.put(
            "/api/users/me/password",
            json={"current_password": "oldpassword123", "new_password": "newpassword456"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

        # Verify password was changed in database
        test_db.refresh(user)
        assert user.password_hash != old_password_hash
        assert verify_password("newpassword456", user.password_hash) is True

    def test_change_password_wrong_current(self, client, test_db):
        """PUT /api/users/me/password returns 400 with wrong current password"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create user
        user = AccountUser(
            login_id="wrongpwuser1",
            password_hash=hash_password("correctpassword123"),
            name="Wrong Password User",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "wrongpwuser1", "password": "correctpassword123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Try to change password with wrong current password
        response = client.put(
            "/api/users/me/password",
            json={"current_password": "wrongpassword123", "new_password": "newpassword456"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is False
        assert "incorrect" in data["error"]["message"].lower()

    def test_should_blacklist_other_sessions_when_password_changed(self, client, test_db):
        """FR-SV-10: PUT /api/users/me/password 성공 시 본인 다른 활성 세션의
        access+refresh jti 가 블랙리스트되고 세션이 비활성화된다(타 기기 강제 재로그인)."""
        from datetime import datetime, timedelta
        from app.models.user import AccountUser, UserSession
        from app.utils.auth import create_access_token, create_refresh_token, decode_token
        from app.services.token_blacklist_service import is_blacklisted

        # client 픽스처가 get_current_account_user 를 test_admin(mock_admin)으로 override → 그 사용자 대상.
        admin = test_db.query(AccountUser).filter(AccountUser.login_id == "test_admin").first()
        assert admin is not None

        # 본인 활성 세션 2개(실 토큰=jti 포함) 생성
        created = []
        for i in range(2):
            at = create_access_token(data={"sub": admin.login_id, "sid": str(9000 + i)})
            rt = create_refresh_token(data={"sub": admin.login_id, "sid": str(9000 + i)})
            session = UserSession(
                user_id=admin.id,
                token=at,
                refresh_token=rt,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_active=True,
            )
            test_db.add(session)
            test_db.flush()
            created.append(
                (session, decode_token(at).jti, decode_token(rt, expected_type="refresh").jti)
            )
        test_db.commit()

        # 비번 변경 — current_password 는 mock_admin 의 비번(test1234). Authorization 헤더 없음
        # → 현재 세션 sid 식별 불가 → 모든 활성 세션 무효화.
        response = client.put(
            "/api/users/me/password",
            json={"current_password": "test1234", "new_password": "NewSecurePass456"},
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # 모든 세션 비활성화 + access/refresh jti 블랙리스트
        for session, access_jti, refresh_jti in created:
            test_db.refresh(session)
            assert session.is_active is False
            assert is_blacklisted(test_db, access_jti) is True
            assert is_blacklisted(test_db, refresh_jti) is True


class TestUserMeApi:
    """AC-7.6: User Me API Tests"""

    @pytest.mark.skip(reason="client fixture overrides get_current_account_user to mock_admin; needs unoverridden client for real auth flow — see conftest.py L112-119 (G07 minimal)")
    def test_get_me_success(self, client, test_db):
        """GET /api/users/me returns current user info"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create user
        user = AccountUser(
            login_id="meuser1",
            password_hash=hash_password("password123"),
            name="Me User",
            email="me@example.com",
            department="Engineering",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "meuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get my info
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["login_id"] == "meuser1"
        assert data["data"]["name"] == "Me User"
        assert data["data"]["email"] == "me@example.com"
        assert data["data"]["department"] == "Engineering"

    @pytest.mark.skip(reason="client fixture overrides get_current_account_user to mock_admin; needs unoverridden client for real auth flow — see conftest.py L112-119 (G07 minimal)")
    def test_update_me_success(self, client, test_db):
        """PUT /api/users/me updates current user info"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create user
        user = AccountUser(
            login_id="meupdateuser1",
            password_hash=hash_password("password123"),
            name="Original Name",
            email="original@example.com",
            department="Original Dept",
            role="VIEWER",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "meupdateuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Update my info
        response = client.put(
            "/api/users/me",
            json={"name": "Updated Name", "email": "updated@example.com"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["email"] == "updated@example.com"
        # Original fields should be preserved
        assert data["data"]["login_id"] == "meupdateuser1"
        assert data["data"]["department"] == "Original Dept"
