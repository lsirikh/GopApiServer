"""FR-08 — grant sweep 주기 설정화 (GRANT_SWEEP_INTERVAL_MINUTES).

기본 10분, env 로 override 가능, main.py 스케줄러가 하드코딩(minutes=10)이 아니라
설정값을 배선하는지 검증한다. (보안 비의존 — 표시/통지 백스톱 최신성만 좌우.)
"""
from __future__ import annotations

import inspect


def test_should_default_grant_sweep_interval_to_10():
    from app.config import Settings
    assert Settings().GRANT_SWEEP_INTERVAL_MINUTES == 10


def test_should_override_grant_sweep_interval_from_env(monkeypatch):
    monkeypatch.setenv("GRANT_SWEEP_INTERVAL_MINUTES", "5")
    from app.config import Settings
    assert Settings().GRANT_SWEEP_INTERVAL_MINUTES == 5


def test_should_wire_configured_interval_into_grant_sweep_job():
    import app.main as main_mod
    src = inspect.getsource(main_mod)
    # 하드코딩 minutes=10 이 아니라 설정값을 사용해야
    assert "run_grant_sweep" in src
    assert "minutes=settings.GRANT_SWEEP_INTERVAL_MINUTES" in src
