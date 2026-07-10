"""require_perm_optional (휴면 RBAC 집행) 단위 테스트 — v5.x FR-SV-04.

휴면 설계 검증:
- AUTH_MODE=public → 무집행(역할/토큰 무관 통과) = 현 라우터 동작 보존.
- AUTH_MODE=token → 매트릭스 집행(ADMIN bypass / 무권한 403 / 무토큰 401).
"""
import asyncio

import pytest
from fastapi import HTTPException

from app.config import settings
from app.models.user import AccountUser, UserGroup
from app.routers.auth import require_perm_optional
from app.utils.auth import hash_password


def _seed(test_db):
    """cameras:edit 보유 OPERATOR 그룹 + 역할별 사용자 시드."""
    op_group = UserGroup(
        name="OPERATOR",
        description="op",
        permissions={"modules": {"cameras": {"view": True, "edit": True, "delete": False, "control": False}}},
        is_active=True,
    )
    viewer_group = UserGroup(
        name="VIEWER",
        description="viewer",
        permissions={"modules": {"cameras": {"view": True, "edit": False, "delete": False, "control": False}}},
        is_active=True,
    )
    test_db.add_all([op_group, viewer_group])
    test_db.flush()

    # ADR_Permission_Model_v5.2 (R10①, WS-B): 권한원천 name==role 폐기 → 배정 group_id 명시.
    # 본 시드는 op/viewer 사용자를 동명 그룹에 배정해 기존 의도(operator=cameras:edit) 유지.
    def _user(login_id, role, group_id=None):
        u = AccountUser(login_id=login_id, password_hash=hash_password("pw12345678"),
                        name=login_id, role=role, group_id=group_id)
        test_db.add(u)
        test_db.flush()
        return u

    admin = _user("rpo_admin", "ADMIN")
    operator = _user("rpo_op", "OPERATOR", group_id=op_group.id)
    viewer = _user("rpo_viewer", "VIEWER", group_id=viewer_group.id)
    test_db.commit()
    return admin, operator, viewer


def test_should_passthrough_when_public_mode_regardless_of_role(test_db, monkeypatch):
    """public 모드: 무권한 VIEWER 도 통과(무집행) — 현 동작 보존."""
    _admin, _op, viewer = _seed(test_db)
    monkeypatch.setattr(settings, "AUTH_MODE", "public")
    checker = require_perm_optional("cameras", "edit")
    result = asyncio.run(checker(db=test_db, current_user=viewer))
    assert result is viewer  # 403 없이 통과


def test_should_allow_admin_when_token_mode(test_db, monkeypatch):
    """token 모드: ADMIN 은 매트릭스 무관 bypass."""
    admin, _op, _viewer = _seed(test_db)
    monkeypatch.setattr(settings, "AUTH_MODE", "token")
    checker = require_perm_optional("cameras", "edit")
    assert asyncio.run(checker(db=test_db, current_user=admin)) is admin


def test_should_allow_role_with_permission_when_token_mode(test_db, monkeypatch):
    """token 모드: cameras:edit 보유 OPERATOR 통과."""
    _admin, operator, _viewer = _seed(test_db)
    monkeypatch.setattr(settings, "AUTH_MODE", "token")
    checker = require_perm_optional("cameras", "edit")
    assert asyncio.run(checker(db=test_db, current_user=operator)) is operator


def test_should_forbid_role_without_permission_when_token_mode(test_db, monkeypatch):
    """token 모드: cameras:edit 없는 VIEWER → 403."""
    _admin, _op, viewer = _seed(test_db)
    monkeypatch.setattr(settings, "AUTH_MODE", "token")
    checker = require_perm_optional("cameras", "edit")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(checker(db=test_db, current_user=viewer))
    assert exc.value.status_code == 403


def test_should_require_token_when_token_mode_and_no_user(test_db, monkeypatch):
    """token 모드 + current_user None(무토큰) → 401."""
    monkeypatch.setattr(settings, "AUTH_MODE", "token")
    checker = require_perm_optional("cameras", "edit")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(checker(db=test_db, current_user=None))
    assert exc.value.status_code == 401
