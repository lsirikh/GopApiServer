"""
부여 만료 sweep 테스트 — FR-04
PRD: PRD_Permission_Group_Scheduling.md §3 (sweep)
WS-B / TDD Phase 5

sweep 은 표시/통지용(is_active 비정규화). 보안은 요청시점 계산(FR-02)이 권위.
"""
from datetime import datetime, timedelta

from app.config import settings


def _now():
    return datetime.now(settings.tz).replace(tzinfo=None)


def _make_user_group_grant(db, valid_until_delta_h, login_id):
    from app.models.user import AccountUser, UserGroup, UserGroupGrant
    from app.utils.auth import hash_password

    u = AccountUser(login_id=login_id, password_hash=hash_password("pw123456"), name="u", role="VIEWER")
    g = UserGroup(name=f"grp_{login_id}", permissions={"modules": {}})
    db.add_all([u, g])
    db.commit()
    db.refresh(u)
    db.refresh(g)
    grant = UserGroupGrant(
        user_id=u.id, group_id=g.id,
        valid_from=_now() - timedelta(hours=5),
        valid_until=_now() + timedelta(hours=valid_until_delta_h),
        is_active=True,
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)
    return grant


class TestGrantSweep:
    def test_should_deactivate_grant_when_expired_on_sweep(self, db_session):
        from app.services.grant_service import expire_due_grants
        from app.models.user import UserGroupGrant

        expired = _make_user_group_grant(db_session, -1, "sweep_exp")   # 만료
        active = _make_user_group_grant(db_session, +10, "sweep_act")   # 유효

        count = expire_due_grants(db_session, _now())

        assert count == 1
        assert db_session.get(UserGroupGrant, expired.id).is_active is False
        assert db_session.get(UserGroupGrant, active.id).is_active is True

    def test_should_not_touch_permanent_grant_on_sweep(self, db_session):
        from app.models.user import AccountUser, UserGroup, UserGroupGrant
        from app.utils.auth import hash_password
        from app.services.grant_service import expire_due_grants

        u = AccountUser(login_id="sweep_perm", password_hash=hash_password("pw123456"), name="u", role="VIEWER")
        g = UserGroup(name="grp_perm", permissions={"modules": {}})
        db_session.add_all([u, g])
        db_session.commit()
        grant = UserGroupGrant(user_id=u.id, group_id=g.id,
                               valid_from=_now() - timedelta(hours=5), valid_until=None, is_active=True)
        db_session.add(grant)
        db_session.commit()

        count = expire_due_grants(db_session, _now())

        assert count == 0
        assert db_session.get(UserGroupGrant, grant.id).is_active is True
