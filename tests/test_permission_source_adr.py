"""
권한 원천 = 배정 그룹(group_id) + grant — ADR_Permission_Model_v5.2 (R10①②)
WS-B / 차장님 결정 2026-06-30 "리스크 최소안"

핵심: `name==role` 자동해석 폐기. role 은 ADMIN 특권 라벨일 뿐, 기능권한은 배정 그룹+grant 에서만.
"""
from datetime import datetime, timedelta

from app.config import settings


def _now():
    return datetime.now(settings.tz).replace(tzinfo=None)


def _user(db, role="VIEWER", group_id=None, login_id="adr_u"):
    from app.models.user import AccountUser
    from app.utils.auth import hash_password
    u = AccountUser(login_id=login_id, password_hash=hash_password("pw123456"),
                    name="u", role=role, group_id=group_id)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _group(db, name, perms):
    from app.models.user import UserGroup
    g = UserGroup(name=name, permissions=perms)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


class TestPermissionSourceAdr:
    def test_should_ignore_role_named_group_when_no_group_id(self, db_session):
        """ADR: role 과 동명인 그룹이 있어도 배정(group_id) 안 했으면 권한 0."""
        from app.routers.auth import _effective_allows
        # name==role("VIEWER") 그룹이 cameras:edit 를 가져도…
        _group(db_session, "VIEWER", {"modules": {"cameras": {"edit": True}}})
        user = _user(db_session, role="VIEWER", group_id=None)
        # …배정 안 했으니 권한 없음 (name==role 폐기)
        assert _effective_allows(db_session, user, "cameras", "edit") is False

    def test_should_use_assigned_group_when_group_id_set(self, db_session):
        """ADR: 권한은 배정된 그룹(group_id)에서 나온다."""
        from app.routers.auth import _effective_allows
        g = _group(db_session, "정비반", {"modules": {"events": {"view": True}}})
        user = _user(db_session, role="VIEWER", group_id=g.id, login_id="adr_assigned")
        assert _effective_allows(db_session, user, "events", "view") is True

    def test_should_have_no_permission_when_unassigned_non_admin(self, db_session):
        """ADR: 비-ADMIN 부트스트랩(그룹 미배정) = 권한 0 (명시·안전)."""
        from app.routers.auth import _effective_allows
        user = _user(db_session, role="OPERATOR", group_id=None, login_id="adr_boot")
        assert _effective_allows(db_session, user, "events", "edit") is False

    def test_should_union_assigned_group_and_grant(self, db_session):
        """ADR: 배정 그룹 ∪ 유효 grant."""
        from app.routers.auth import _effective_allows
        from app.models.user import UserGroupGrant
        base = _group(db_session, "기본반", {"modules": {"events": {"view": True}}})
        extra = _group(db_session, "임시카메라", {"modules": {"cameras": {"control": True}}})
        user = _user(db_session, role="VIEWER", group_id=base.id, login_id="adr_union")
        db_session.add(UserGroupGrant(user_id=user.id, group_id=extra.id,
                                      valid_from=_now() - timedelta(hours=1),
                                      valid_until=_now() + timedelta(hours=10)))
        db_session.commit()
        assert _effective_allows(db_session, user, "events", "view") is True     # 배정 그룹
        assert _effective_allows(db_session, user, "cameras", "control") is True  # grant
