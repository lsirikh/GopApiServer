"""
UserGroup API Tests
Based on plan.md AC-8: UserGroup API
"""
import pytest


class TestUserGroupListApi:
    """AC-8.1: UserGroup List/Get API Tests"""

    def test_get_user_groups_list(self, client, test_db):
        """GET /api/user-groups returns list of user groups"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user for authentication
        user = AccountUser(
            login_id="grouplistuser1",
            password_hash=hash_password("password123"),
            name="Group List User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)

        # Create test user groups
        group1 = UserGroup(
            name="Engineering",
            description="Engineering team",
            is_active=True
        )
        group2 = UserGroup(
            name="Operations",
            description="Operations team",
            is_active=True
        )
        test_db.add(group1)
        test_db.add(group2)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "grouplistuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get user groups list
        response = client.get(
            "/api/user-groups",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2

        # Verify group structure
        group_names = [g["name"] for g in data["data"]]
        assert "Engineering" in group_names
        assert "Operations" in group_names

    def test_get_user_group_by_id(self, client, test_db):
        """GET /api/user-groups/{id} returns user group by ID"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user for authentication
        user = AccountUser(
            login_id="groupgetuser1",
            password_hash=hash_password("password123"),
            name="Group Get User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)

        # Create test user group
        group = UserGroup(
            name="Test Group",
            description="Test group description",
            is_active=True
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupgetuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get user group by ID
        response = client.get(
            f"/api/user-groups/{group.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == group.id
        assert data["data"]["name"] == "Test Group"
        assert data["data"]["description"] == "Test group description"

    def test_get_user_group_not_found(self, client, test_db):
        """GET /api/user-groups/{id} returns 404 for non-existent group"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create test user for authentication
        user = AccountUser(
            login_id="group404user1",
            password_hash=hash_password("password123"),
            name="Group 404 User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "group404user1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get non-existent user group
        response = client.get(
            "/api/user-groups/99999",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"

    def test_get_user_group_includes_user_count(self, client, test_db):
        """GET /api/user-groups/{id} includes user_count field"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user group first
        group = UserGroup(
            name="Count Test Group",
            description="Group for testing user count",
            is_active=True
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create test users belonging to this group
        user1 = AccountUser(
            login_id="countuser1",
            password_hash=hash_password("password123"),
            name="Count User 1",
            role="VIEWER",
            group_id=group.id,
            is_active=True,
            is_locked=False
        )
        user2 = AccountUser(
            login_id="countuser2",
            password_hash=hash_password("password123"),
            name="Count User 2",
            role="VIEWER",
            group_id=group.id,
            is_active=True,
            is_locked=False
        )
        # Admin user for authentication (not in the group)
        admin_user = AccountUser(
            login_id="countadmin1",
            password_hash=hash_password("password123"),
            name="Count Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user1)
        test_db.add(user2)
        test_db.add(admin_user)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "countadmin1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get user group by ID
        response = client.get(
            f"/api/user-groups/{group.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert "user_count" in data["data"], "Response should include user_count field"
        assert data["data"]["user_count"] == 2


class TestUserGroupCreateUpdateDeleteApi:
    """AC-8.2: UserGroup Create/Update/Delete API Tests"""

    def test_create_user_group_success(self, client, test_db):
        """POST /api/user-groups creates a new user group"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create admin user for authentication
        user = AccountUser(
            login_id="groupcreateuser1",
            password_hash=hash_password("password123"),
            name="Group Create User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupcreateuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Create user group
        response = client.post(
            "/api/user-groups",
            json={
                "name": "New Group",
                "description": "A newly created group",
                "is_active": True
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New Group"
        assert data["data"]["description"] == "A newly created group"
        assert data["data"]["is_active"] is True
        assert "id" in data["data"]

    def test_create_user_group_with_permissions(self, client, test_db):
        """POST /api/user-groups stores permissions JSONB"""
        from app.models.user import AccountUser
        from app.utils.auth import hash_password

        # Create admin user for authentication
        user = AccountUser(
            login_id="grouppermuser1",
            password_hash=hash_password("password123"),
            name="Group Perm User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "grouppermuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Create user group with permissions
        # R4(WS-B 2026-06-30): v4.9 Phase 3 강타입 Dict 구조. 구 List[str] modules 는 422.
        permissions = {
            "modules": {"reports": {"view": True, "edit": True}, "servers": {"view": True}},
            "device_groups": [1, 2, 3],
            "time_restriction": {"start": "09:00", "end": "18:00"}
        }
        response = client.post(
            "/api/user-groups",
            json={
                "name": "Permission Group",
                "description": "Group with permissions",
                "permissions": permissions,
                "is_active": True
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["permissions"]["modules"]["reports"]["edit"] is True
        assert data["data"]["permissions"]["device_groups"] == [1, 2, 3]

    def test_update_user_group_success(self, client, test_db):
        """PUT /api/user-groups/{id} updates a user group"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user group
        group = UserGroup(
            name="Original Name",
            description="Original description",
            is_active=True
        )
        test_db.add(group)

        # Create admin user
        user = AccountUser(
            login_id="groupupdateuser1",
            password_hash=hash_password("password123"),
            name="Group Update User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(group)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupupdateuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Update user group
        response = client.put(
            f"/api/user-groups/{group.id}",
            json={
                "name": "Updated Name",
                "description": "Updated description"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["description"] == "Updated description"
        assert data["data"]["id"] == group.id

    def test_delete_user_group_success(self, client, test_db):
        """DELETE /api/user-groups/{id} deletes a user group"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user group
        group = UserGroup(
            name="Delete Test Group",
            description="Group to be deleted",
            is_active=True
        )
        test_db.add(group)

        # Create admin user
        user = AccountUser(
            login_id="groupdeleteuser1",
            password_hash=hash_password("password123"),
            name="Group Delete User",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user)
        test_db.commit()
        group_id = group.id

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupdeleteuser1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Delete user group
        response = client.delete(
            f"/api/user-groups/{group_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

        # Verify group is deleted
        deleted_group = test_db.query(UserGroup).filter(UserGroup.id == group_id).first()
        assert deleted_group is None

    def test_delete_user_group_sets_users_null(self, client, test_db):
        """DELETE /api/user-groups/{id} sets group_id to NULL for users"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user group
        group = UserGroup(
            name="Group With Users",
            description="Group with users to be deleted",
            is_active=True
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create users belonging to this group
        user1 = AccountUser(
            login_id="groupuserA",
            password_hash=hash_password("password123"),
            name="Group User A",
            role="VIEWER",
            group_id=group.id,
            is_active=True,
            is_locked=False
        )
        user2 = AccountUser(
            login_id="groupuserB",
            password_hash=hash_password("password123"),
            name="Group User B",
            role="VIEWER",
            group_id=group.id,
            is_active=True,
            is_locked=False
        )
        # Admin user for authentication
        admin = AccountUser(
            login_id="groupdeleteadmin2",
            password_hash=hash_password("password123"),
            name="Group Delete Admin 2",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user1)
        test_db.add(user2)
        test_db.add(admin)
        test_db.commit()
        group_id = group.id
        user1_id = user1.id
        user2_id = user2.id

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupdeleteadmin2", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Delete user group
        response = client.delete(
            f"/api/user-groups/{group_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify users still exist but group_id is NULL
        test_db.expire_all()  # Refresh from database
        updated_user1 = test_db.query(AccountUser).filter(AccountUser.id == user1_id).first()
        updated_user2 = test_db.query(AccountUser).filter(AccountUser.id == user2_id).first()

        assert updated_user1 is not None
        assert updated_user2 is not None
        assert updated_user1.group_id is None
        assert updated_user2.group_id is None


class TestUserGroupPermissionsApi:
    """PRD-GOP-01 IMPL-06 / v5.0: POST /api/user-groups/{id}/permissions (ADMIN 전용 권한 수정)

    Note: conftest `client` 픽스처가 get_current_account_user 를 ADMIN(mock_admin)으로 강제
    override 하므로 비-ADMIN 403 경로는 단위테스트로 검증 불가(라이브 서버에서 검증). 여기서는
    200(성공)/404(그룹없음)/422(잘못된 권한 구조)만 검증한다.
    """

    def test_update_group_permissions_success(self, client, test_db):
        """POST /api/user-groups/{id}/permissions 가 그룹 권한(모듈×동작)을 갱신한다"""
        from app.models.user import UserGroup

        group = UserGroup(name="Perm Edit Group", description="권한 편집 대상", is_active=True)
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        payload = {
            "modules": {
                "events": {"view": True, "edit": True},
                "cameras": {"view": True, "control": True},
            },
            "device_groups": [1, 2],
        }
        response = client.post(f"/api/user-groups/{group.id}/permissions", json=payload)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        mods = data["data"]["permissions"]["modules"]
        assert mods["events"]["view"] is True
        assert mods["events"]["edit"] is True
        assert mods["cameras"]["control"] is True
        assert data["data"]["permissions"]["device_groups"] == [1, 2]

    def test_update_group_permissions_not_found(self, client, test_db):
        """POST /api/user-groups/{id}/permissions 가 없는 그룹에 404 반환"""
        payload = {"modules": {"events": {"view": True}}}
        response = client.post("/api/user-groups/99999/permissions", json=payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"

    def test_update_group_permissions_invalid_module(self, client, test_db):
        """POST /api/user-groups/{id}/permissions 가 미정의 모듈 키에 422 반환 (strict 스키마)"""
        from app.models.user import UserGroup

        group = UserGroup(name="Perm Invalid Group", is_active=True)
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        payload = {"modules": {"not_a_real_module": {"view": True}}}
        response = client.post(f"/api/user-groups/{group.id}/permissions", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"


class TestUserGroupUsersApi:
    """AC-8.3: UserGroup Users API Tests"""

    def test_get_user_group_users(self, client, test_db):
        """GET /api/user-groups/{id}/users returns users in the group"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user group
        group = UserGroup(
            name="Users Test Group",
            description="Group for testing users endpoint",
            is_active=True
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)

        # Create users belonging to this group
        user1 = AccountUser(
            login_id="groupmemberA",
            password_hash=hash_password("password123"),
            name="Group Member A",
            role="VIEWER",
            group_id=group.id,
            is_active=True,
            is_locked=False
        )
        user2 = AccountUser(
            login_id="groupmemberB",
            password_hash=hash_password("password123"),
            name="Group Member B",
            role="OPERATOR",
            group_id=group.id,
            is_active=True,
            is_locked=False
        )
        # Admin user for authentication (not in the group)
        admin = AccountUser(
            login_id="groupusersadmin1",
            password_hash=hash_password("password123"),
            name="Group Users Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(user1)
        test_db.add(user2)
        test_db.add(admin)
        test_db.commit()

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "groupusersadmin1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get users in the group
        response = client.get(
            f"/api/user-groups/{group.id}/users",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

        # Verify user data
        login_ids = [u["login_id"] for u in data["data"]]
        assert "groupmemberA" in login_ids
        assert "groupmemberB" in login_ids

    def test_get_user_group_users_empty(self, client, test_db):
        """GET /api/user-groups/{id}/users returns empty array when no users in group"""
        from app.models.user import UserGroup, AccountUser
        from app.utils.auth import hash_password

        # Create test user group with no users
        group = UserGroup(
            name="Empty Users Group",
            description="Group with no users",
            is_active=True
        )
        test_db.add(group)

        # Admin user for authentication (not in the group)
        admin = AccountUser(
            login_id="emptygrpadmin1",
            password_hash=hash_password("password123"),
            name="Empty Group Admin",
            role="ADMIN",
            is_active=True,
            is_locked=False
        )
        test_db.add(admin)
        test_db.commit()
        test_db.refresh(group)

        # Login to get token
        login_response = client.post(
            "/api/auth/login",
            json={"login_id": "emptygrpadmin1", "password": "password123"}
        )
        access_token = login_response.json()["data"]["access_token"]

        # Get users in the group (should be empty)
        response = client.get(
            f"/api/user-groups/{group.id}/users",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0
