"""관리자 프로필 사진 업로드 단위 테스트 (v6.3-admin_photo_upload, 2026-07-21).

POST/DELETE /api/users/{user_id}/photo 가 의존하는 **보안 가드(base-ADMIN 상승 차단)** 와
**라우트 등록**을 순수 로직으로 격리 검증한다. async 라우터 + Postgres HTTP 왕복(대상 사진
갱신·404·orphan 정리·감사 actor≠target)은 test_profile_photo_crud.py 와 동일하게
라이브 E2E 로 확인한다(conftest client 는 sync 의존성만 override).

사고 배경: 본인 경로(/me/photo)를 타 계정 편집에 재사용 → 토큰 소유자(관리자) 사진 오염
(2026-07-13). 신규 {user_id} 경로 + 이 가드로 재발 차단.
"""
import pytest
from fastapi import HTTPException

from app.models.user import AccountUser
from app.routers.users import _assert_can_modify_admin_target, router


def _user(role: str) -> AccountUser:
    return AccountUser(login_id=f"u_{role.lower()}", name=role, role=role)


# ── 보안 가드: base-ADMIN 상승 차단 (사진 엔드포인트가 재사용) ────────────────
class TestAdminTargetGuardForPhoto:
    def test_should_allow_when_admin_targets_admin(self):
        _assert_can_modify_admin_target(_user("ADMIN"), _user("ADMIN"))  # no raise

    def test_should_allow_when_admin_targets_user(self):
        _assert_can_modify_admin_target(_user("ADMIN"), _user("USER"))

    def test_should_allow_when_non_admin_targets_user(self):
        # users:edit 보유 USER 가 일반 USER 사진 변경 = 허용
        _assert_can_modify_admin_target(_user("USER"), _user("USER"))

    def test_should_raise_403_when_non_admin_targets_admin(self):
        with pytest.raises(HTTPException) as ei:
            _assert_can_modify_admin_target(_user("USER"), _user("ADMIN"))
        assert ei.value.status_code == 403


# ── 라우트 등록: /{user_id}/photo POST·DELETE 존재 (그림자화 없음) ────────────
class TestAdminPhotoRoutesRegistered:
    def _methods_by_path(self):
        mapping: dict[str, set[str]] = {}
        for r in router.routes:
            methods = getattr(r, "methods", None)
            if methods:
                mapping.setdefault(r.path, set()).update(methods)
        return mapping

    def test_should_register_admin_photo_upload_route(self):
        assert "POST" in self._methods_by_path().get("/{user_id}/photo", set())

    def test_should_register_admin_photo_delete_route(self):
        assert "DELETE" in self._methods_by_path().get("/{user_id}/photo", set())

    def test_should_keep_self_photo_route_intact(self):
        # 회귀: 본인 경로 /me/photo 가 신규 라우트에 의해 그림자화되지 않아야 한다.
        methods = self._methods_by_path().get("/me/photo", set())
        assert "POST" in methods and "DELETE" in methods
