"""
grant 파생 상태(status) 테스트 — FR-05
PRD: PRD_Permission_Group_Scheduling.md §3.3 (파생 상태)
WS-B / TDD Phase 4

status = REVOKED > PENDING > EXPIRED > ACTIVE 우선순위로 파생.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace


def _g(valid_from_delta_h, valid_until_delta_h=None, revoked=False):
    """가짜 grant — grant_status 는 ORM 비의존 순수함수여야 함."""
    now = datetime(2026, 6, 30, 12, 0, 0)
    return now, SimpleNamespace(
        valid_from=now + timedelta(hours=valid_from_delta_h),
        valid_until=(now + timedelta(hours=valid_until_delta_h)) if valid_until_delta_h is not None else None,
        revoked_at=(now if revoked else None),
    )


class TestGrantStatus:
    def test_should_return_active_when_within_window(self):
        from app.services.grant_service import grant_status
        now, g = _g(-1, 10)
        assert grant_status(g, now) == "ACTIVE"

    def test_should_return_active_when_valid_until_null(self):
        from app.services.grant_service import grant_status
        now, g = _g(-1, None)
        assert grant_status(g, now) == "ACTIVE"

    def test_should_return_pending_when_before_valid_from(self):
        from app.services.grant_service import grant_status
        now, g = _g(2, 10)
        assert grant_status(g, now) == "PENDING"

    def test_should_return_expired_when_after_valid_until(self):
        from app.services.grant_service import grant_status
        now, g = _g(-5, -1)
        assert grant_status(g, now) == "EXPIRED"

    def test_should_return_revoked_when_revoked_at_set(self):
        from app.services.grant_service import grant_status
        now, g = _g(-1, 10, revoked=True)
        assert grant_status(g, now) == "REVOKED"

    def test_should_prioritize_revoked_over_expired(self):
        from app.services.grant_service import grant_status
        now, g = _g(-5, -1, revoked=True)
        assert grant_status(g, now) == "REVOKED"
