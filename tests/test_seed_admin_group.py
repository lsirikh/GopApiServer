"""
시드: admin 사용자 ADMIN 그룹 배정 — R10③ (ADR_Permission_Model_v5.2)
WS-B / 2026-06-30

name==role 폐기 후 권한 원천 = group_id → admin 도 ADMIN 그룹에 배정돼야 로그인 payload 정합.
"""
from app.utils.auth import hash_password


def test_should_assign_admin_to_admin_group_when_seeded(db_session):
    from app.models.user import AccountUser, UserGroup
    from app.utils.init_db import ensure_role_permission_groups

    # admin 사용자(group_id 없음) 선존재 상태
    admin = AccountUser(login_id="admin", password_hash=hash_password("admin123"),
                        name="관리자", role="ADMIN", is_active=True)
    db_session.add(admin)
    db_session.commit()

    ensure_role_permission_groups(db_session)

    admin_group = db_session.query(UserGroup).filter(UserGroup.name == "ADMIN").first()
    db_session.refresh(admin)
    assert admin_group is not None
    assert admin.group_id == admin_group.id


def test_should_be_idempotent_when_admin_already_assigned(db_session):
    from app.models.user import AccountUser, UserGroup
    from app.utils.init_db import ensure_role_permission_groups

    other = UserGroup(name="기존배정", permissions={"modules": {}})
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    admin = AccountUser(login_id="admin", password_hash=hash_password("admin123"),
                        name="관리자", role="ADMIN", is_active=True, group_id=other.id)
    db_session.add(admin)
    db_session.commit()

    ensure_role_permission_groups(db_session)

    db_session.refresh(admin)
    # 이미 배정돼 있으면 덮어쓰지 않음(멱등)
    assert admin.group_id == other.id
