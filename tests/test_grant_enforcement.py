"""
유효권한 계산(grant 합집합) 테스트 — FR-02
PRD: PRD_Permission_Group_Scheduling.md §3.2
WS-B / TDD Phase 2

핵심: 유효권한 = 등급 매트릭스 ∪ 현재 유효한 grant 그룹 매트릭스.
권위 판정은 요청 시점(valid_from <= now < valid_until) — is_active(sweep 비정규화) 비의존.
"""
from datetime import datetime, timedelta

from app.config import settings


def _now():
    return datetime.now(settings.tz).replace(tzinfo=None)


def _make_role_group_and_user(db, role="VIEWER"):
    """role 명과 동일한 등급 그룹(권한 없음) + 그 role 사용자."""
    from app.models.user import UserGroup, AccountUser
    from app.utils.auth import hash_password

    role_group = UserGroup(name=role, description="등급 그룹", permissions={"modules": {}})
    db.add(role_group)
    user = AccountUser(
        login_id=f"u_{role.lower()}",
        password_hash=hash_password("pw123456"),
        name="사용자",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_grant_group(db, name="임시정비", module="cameras", verb="control"):
    from app.models.user import UserGroup

    group = UserGroup(name=name, permissions={"modules": {module: {verb: True}}})
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def _grant(db, user, group, valid_from, valid_until=None, is_active=True):
    from app.models.user import UserGroupGrant

    g = UserGroupGrant(
        user_id=user.id, group_id=group.id,
        valid_from=valid_from, valid_until=valid_until, is_active=is_active,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


class TestEffectivePermissions:
    """FR-02: _effective_allows"""

    def test_should_deny_when_no_grant_and_role_lacks_permission(self, db_session):
        from app.routers.auth import _effective_allows

        user = _make_role_group_and_user(db_session)
        assert _effective_allows(db_session, user, "cameras", "control") is False

    def test_should_allow_when_active_grant_adds_permission(self, db_session):
        from app.routers.auth import _effective_allows

        user = _make_role_group_and_user(db_session)
        grp = _make_grant_group(db_session)
        _grant(db_session, user, grp, _now() - timedelta(hours=1), _now() + timedelta(hours=10))

        assert _effective_allows(db_session, user, "cameras", "control") is True

    def test_should_deny_when_grant_expired_even_if_is_active_true(self, db_session):
        """NFR-01: sweep 미실행(is_active=True)이라도 valid_until 경과면 차단(요청시점 권위)."""
        from app.routers.auth import _effective_allows

        user = _make_role_group_and_user(db_session)
        grp = _make_grant_group(db_session)
        _grant(db_session, user, grp,
               _now() - timedelta(hours=5), _now() - timedelta(hours=1), is_active=True)

        assert _effective_allows(db_session, user, "cameras", "control") is False

    def test_should_deny_when_grant_pending(self, db_session):
        from app.routers.auth import _effective_allows

        user = _make_role_group_and_user(db_session)
        grp = _make_grant_group(db_session)
        _grant(db_session, user, grp, _now() + timedelta(hours=2), _now() + timedelta(hours=10))

        assert _effective_allows(db_session, user, "cameras", "control") is False

    def test_should_allow_when_valid_until_null_permanent(self, db_session):
        from app.routers.auth import _effective_allows

        user = _make_role_group_and_user(db_session)
        grp = _make_grant_group(db_session, name="유지보수")
        _grant(db_session, user, grp, _now() - timedelta(hours=1), None)

        assert _effective_allows(db_session, user, "cameras", "control") is True

    def test_should_deny_when_grant_revoked(self, db_session):
        from app.routers.auth import _effective_allows
        from app.models.user import UserGroupGrant

        user = _make_role_group_and_user(db_session)
        grp = _make_grant_group(db_session, name="회수대상")
        g = _grant(db_session, user, grp, _now() - timedelta(hours=1), None)
        g.revoked_at = _now()
        db_session.commit()

        assert _effective_allows(db_session, user, "cameras", "control") is False
