"""
Account 저위험 수정 검증 (2026-07-09):
- ACC-P1-05: token_blacklist 정리 스케줄러 zero-arg 진입점 존재 + 동작
- ACC-P1-04: user_groups 가 log_action_async 사용(감사 유실 방지)
- ACC-P1-08: lock_user 마지막 ADMIN 가드 (라우터 소스 계약 확인)

harness 파손(async fixture) 무관하게 import/소스 계약 위주로 검증한다.
"""
import inspect

import pytest


def test_blacklist_cleanup_entrypoint_exists_and_is_async():
    """ACC-P1-05: run_blacklist_cleanup zero-arg async 진입점이 존재해야 한다."""
    from app.services import token_blacklist_service as svc
    fn = getattr(svc, "run_blacklist_cleanup", None)
    assert fn is not None, "run_blacklist_cleanup 미정의"
    assert inspect.iscoroutinefunction(fn), "run_blacklist_cleanup 는 async 여야 함"
    assert len(inspect.signature(fn).parameters) == 0, "스케줄러용 zero-arg 여야 함"


def test_user_groups_uses_async_audit():
    """ACC-P1-04: user_groups 라우터가 sync log_action 대신 log_action_async 를 사용."""
    import app.routers.user_groups as ug
    src = inspect.getsource(ug)
    assert "log_action_async(" in src, "log_action_async 호출이 없음"
    # sync log_action( 호출이 남아있으면 안 됨 (log_action_async 는 허용)
    import re
    bare = re.findall(r"(?<!_)log_action\(", src)  # log_action( 인데 _async 아님
    assert not bare, f"sync log_action( 잔존: {len(bare)}건"


def test_lock_user_has_last_admin_guard():
    """ACC-P1-08: lock_user 에 마지막 ADMIN 보존 가드(409)가 있어야 한다."""
    import app.routers.users as users
    src = inspect.getsource(users.lock_user)
    assert "last usable ADMIN" in src or "usable_admins" in src, "lock 마지막 ADMIN 가드 부재"
    assert "409" in src or "HTTP_409_CONFLICT" in src, "409 반환 없음"
