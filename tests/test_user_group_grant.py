"""
UserGroupGrant Model Tests (FR-01)
PRD: PRD_Permission_Group_Scheduling.md §3.3
WS-B / TDD Phase 1

권한그룹 시간기반 부여(grant) 모델 — 다대다 부여 + 기간(valid_from/until) + soft 회수.
"""
import pytest
from datetime import datetime, timedelta

from app.config import settings


def _make_user(db, login_id="grantee01"):
    from app.models.user import AccountUser
    from app.utils.auth import hash_password

    user = AccountUser(
        login_id=login_id,
        password_hash=hash_password("pw123456"),
        name="피부여자",
        role="VIEWER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_group(db, name="임시정비"):
    from app.models.user import UserGroup

    group = UserGroup(name=name, description="외부 수리기사 한시 그룹", permissions={"modules": {}})
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


class TestUserGroupGrantModel:
    """FR-01: user_group_grants 모델"""

    def test_should_define_grant_model_when_imported(self):
        from app.models.user import UserGroupGrant

        assert UserGroupGrant.__tablename__ == "user_group_grants"

    def test_should_create_grant_when_valid_window(self, db_session):
        from app.models.user import UserGroupGrant

        user = _make_user(db_session)
        group = _make_group(db_session)
        now = datetime.now(settings.tz).replace(tzinfo=None)

        grant = UserGroupGrant(
            user_id=user.id,
            group_id=group.id,
            valid_from=now,
            valid_until=now + timedelta(hours=25),
            granted_by=user.id,
        )
        db_session.add(grant)
        db_session.commit()
        db_session.refresh(grant)

        assert grant.id is not None
        assert grant.user_id == user.id
        assert grant.group_id == group.id
        assert grant.valid_until > grant.valid_from
        assert grant.created_at is not None

    def test_should_default_is_active_true_when_not_specified(self, db_session):
        from app.models.user import UserGroupGrant

        user = _make_user(db_session, "grantee02")
        group = _make_group(db_session, "유지보수")
        now = datetime.now(settings.tz).replace(tzinfo=None)

        grant = UserGroupGrant(user_id=user.id, group_id=group.id, valid_from=now)
        db_session.add(grant)
        db_session.commit()
        db_session.refresh(grant)

        assert grant.is_active is True
        # 상시(permanent) = valid_until NULL 허용
        assert grant.valid_until is None
        assert grant.revoked_at is None

    def test_should_cascade_delete_grant_when_user_removed(self, db_session):
        from app.models.user import AccountUser, UserGroupGrant

        user = _make_user(db_session, "grantee03")
        group = _make_group(db_session, "관제")
        now = datetime.now(settings.tz).replace(tzinfo=None)
        grant = UserGroupGrant(user_id=user.id, group_id=group.id, valid_from=now)
        db_session.add(grant)
        db_session.commit()
        grant_id = grant.id

        db_session.delete(db_session.get(AccountUser, user.id))
        db_session.commit()

        assert db_session.get(UserGroupGrant, grant_id) is None
