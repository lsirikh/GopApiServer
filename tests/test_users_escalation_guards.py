"""
계정 관리 RBAC 매트릭스 전환(v6.x) — 권한상승 가드 단위 테스트.

require_admin → require_perm 전환 시, "권한 정의(role/group)·ADMIN 대상 변경" 은
base-ADMIN(role==ADMIN) 전용으로 남겨 grant 로 한시 승격된 USER 의 영구 승격 경로를
차단한다. 가드는 순수함수라 DB/async harness 없이 검증한다(사전존재 통합 harness 파손 무관).
"""
import pytest
from fastapi import HTTPException

from app.models.user import AccountUser
from app.routers.users import (
    _assert_can_modify_admin_target,
    _assert_can_define_permissions,
)


def _user(role: str) -> AccountUser:
    """세션 없이 role 속성만 갖는 최소 AccountUser (가드는 role 만 참조)."""
    return AccountUser(login_id="x", role=role)


class TestModifyAdminTargetGuard:
    def test_should_allow_when_actor_is_admin_and_target_is_admin(self):
        # base-ADMIN 은 ADMIN 대상도 변경 가능 (무회귀)
        _assert_can_modify_admin_target(_user("ADMIN"), _user("ADMIN"))

    def test_should_allow_when_non_admin_actor_targets_non_admin(self):
        # 매트릭스 USER 는 비-ADMIN 대상 변경 가능 (한시 admin 정상 동작)
        _assert_can_modify_admin_target(_user("USER"), _user("USER"))

    def test_should_deny_when_non_admin_actor_targets_admin(self):
        # 매트릭스 USER 는 ADMIN 대상 변경 불가 (횡적 탈취 차단)
        with pytest.raises(HTTPException) as exc:
            _assert_can_modify_admin_target(_user("USER"), _user("ADMIN"))
        assert exc.value.status_code == 403


class TestDefinePermissionsGuard:
    def test_should_allow_when_admin_changes_role_or_group(self):
        # base-ADMIN 은 role/group 정의 변경 가능 (무회귀)
        _assert_can_define_permissions(_user("ADMIN"), changing_role=True, changing_group=True)

    def test_should_allow_when_non_admin_changes_neither(self):
        # 매트릭스 USER 도 role/group 을 안 건드리면 프로필 수정 등 가능
        _assert_can_define_permissions(_user("USER"), changing_role=False, changing_group=False)

    def test_should_deny_when_non_admin_changes_role(self):
        # 매트릭스 USER 의 role 변경(자기 승격 포함) 차단 — 영구 승격 방지
        with pytest.raises(HTTPException) as exc:
            _assert_can_define_permissions(_user("USER"), changing_role=True, changing_group=False)
        assert exc.value.status_code == 403

    def test_should_deny_when_non_admin_changes_group(self):
        # 매트릭스 USER 의 group_id 변경(전권 그룹 고정) 차단 — 영구 승격 방지
        with pytest.raises(HTTPException) as exc:
            _assert_can_define_permissions(_user("USER"), changing_role=False, changing_group=True)
        assert exc.value.status_code == 403
