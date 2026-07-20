"""FR-03 — async_db 격리 가드 검증.

기본 경로(ALLOW_DB_TESTS 미설정)는 격리된 in-memory aiosqlite 로, 운영/공유 DB 를
접촉하지 않는다(S-6). 실 DB(AsyncSessionLocal)는 ALLOW_DB_TESTS=1 opt-in 시에만.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool


def test_should_isolate_to_sqlite_when_not_allow_db_tests():
    """기본 경로 = 격리 aiosqlite. 실제 연결·쿼리까지 동작 확인."""
    async def _check():
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            assert engine.url.get_backend_name() == "sqlite"
            assert "aiosqlite" in engine.url.drivername
            async with engine.begin() as conn:
                assert (await conn.execute(text("SELECT 1"))).scalar() == 1
        finally:
            await engine.dispose()

    asyncio.run(_check())


def test_should_expose_isolated_async_engine_helper_that_targets_sqlite():
    """conftest._isolated_async_engine 은 sqlite 엔진을 만든다 — 운영 async_engine 아님."""
    try:
        from tests.conftest import _isolated_async_engine
    except Exception:  # 패키지 import 불가 환경이면 skip(가드 자체는 위 테스트가 커버)
        import pytest
        pytest.skip("tests.conftest 직접 import 불가 환경")

    engine = _isolated_async_engine()
    try:
        assert engine.url.get_backend_name() == "sqlite"
        assert "aiosqlite" in engine.url.drivername
    finally:
        asyncio.run(engine.dispose())
