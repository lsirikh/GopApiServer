"""
유효권한 페이로드 / /me/permissions / 로그인 병합 — FR-06, FR-07
PRD: PRD_Permission_Group_Scheduling.md §3.5
WS-B / TDD Phase 6-7
"""
from datetime import datetime, timedelta

from app.config import settings


def _now():
    return datetime.now(settings.tz).replace(tzinfo=None)


def _setup(db, role_perms, grant_perms, valid_until_delta_h=10, login_id="payload_u", role="VIEWER"):
    from app.models.user import AccountUser, UserGroup, UserGroupGrant
    from app.utils.auth import hash_password

    # ADR_Permission_Model_v5.2: 권한은 배정 그룹(group_id)에서. role 명 매칭 폐기 → group_id 명시 배정.
    role_group = UserGroup(name=f"assigned_{login_id}", permissions=role_perms)
    grant_group = UserGroup(name=f"grant_{login_id}", permissions=grant_perms)
    db.add_all([role_group, grant_group])
    db.commit()
    db.refresh(role_group)
    db.refresh(grant_group)
    user = AccountUser(login_id=login_id, password_hash=hash_password("pw123456"),
                       name="u", role=role, is_active=True, group_id=role_group.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    grant = UserGroupGrant(
        user_id=user.id, group_id=grant_group.id,
        valid_from=_now() - timedelta(hours=1),
        valid_until=_now() + timedelta(hours=valid_until_delta_h),
    )
    db.add(grant)
    db.commit()
    return user


class TestEffectivePermissionsPayload:
    def test_should_union_modules_from_role_and_grant(self, db_session):
        from app.routers.auth import effective_permissions_payload

        user = _setup(
            db_session,
            role_perms={"modules": {"events": {"view": True}}},
            grant_perms={"modules": {"cameras": {"control": True}}},
        )
        payload = effective_permissions_payload(db_session, user, _now())

        assert payload["modules"]["events"]["view"] is True   # 등급
        assert payload["modules"]["cameras"]["control"] is True  # grant 합집합
        assert payload["valid_until"] is not None

    def test_should_union_device_groups(self, db_session):
        from app.routers.auth import effective_permissions_payload

        user = _setup(
            db_session,
            role_perms={"modules": {}, "device_groups": [1, 2]},
            grant_perms={"modules": {}, "device_groups": [2, 3]},
            login_id="dg_u",
        )
        payload = effective_permissions_payload(db_session, user, _now())
        assert sorted(payload["device_groups"]) == [1, 2, 3]

    def test_should_have_null_valid_until_when_no_grant(self, db_session):
        from app.routers.auth import effective_permissions_payload
        from app.models.user import AccountUser, UserGroup
        from app.utils.auth import hash_password

        rg = UserGroup(name="정비반2", permissions={"modules": {"events": {"view": True}}})
        db_session.add(rg)
        db_session.commit()
        db_session.refresh(rg)
        u = AccountUser(login_id="nogrant", password_hash=hash_password("pw123456"),
                        name="u", role="OPERATOR", is_active=True, group_id=rg.id)
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)

        payload = effective_permissions_payload(db_session, u, _now())
        assert payload["valid_until"] is None
        assert payload["modules"]["events"]["view"] is True


class TestMePermissionsApi:
    def test_should_return_permissions_shape_with_server_time(self, client):
        resp = client.get("/api/auth/me/permissions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "modules" in data
        assert "device_groups" in data
        assert "valid_until" in data
        assert data["server_time"] is not None


class TestLoginGrantMerge:
    def test_should_merge_grant_permissions_on_login(self, client, test_db):
        _setup(
            test_db,
            role_perms={"modules": {"events": {"view": True}}},
            grant_perms={"modules": {"cameras": {"control": True}}},
            login_id="login_merge",
        )
        resp = client.post("/api/auth/login",
                           json={"login_id": "login_merge", "password": "pw123456"})
        assert resp.status_code == 200, resp.text
        perms = resp.json()["data"]["user"]["permissions"]
        assert perms["modules"]["cameras"]["control"] is True
        assert perms["modules"]["events"]["view"] is True
        assert perms["valid_until"] is not None
