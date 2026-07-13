"""
DB Engine Configuration Tests

PostgreSQL 마이그레이션 검증:
- check_same_thread (SQLite 전용) 제거 확인
- Pool 파라미터 (pool_size, max_overflow, pool_pre_ping, pool_recycle) 설정 확인
- psycopg2 드라이버 import 확인

PRD: docs/PRD_PostgreSQL_Migration.md v1.0
TDD: Red → Green → Refactor
"""
import pytest


class TestPsycopg2Available:
    """Phase 1.2: psycopg2-binary 의존성 확인"""

    def test_psycopg2_importable(self):
        """psycopg2 드라이버가 설치되어 있어야 한다"""
        import psycopg2  # noqa: F401


class TestEnginePoolConfig:
    """Phase 2.2~2.3: DB 엔진 Pool 설정 확인"""

    def test_engine_has_no_explicit_sqlite_connect_args(self):
        """database.py에서 check_same_thread를 명시적으로 전달하지 않아야 한다.
        SQLite URL 환경에서는 dialect가 자동으로 추가하므로 PostgreSQL URL일 때만 완전 검증 가능.
        코드 수준 검증은 app/database.py를 직접 확인."""
        from app.database import engine
        import app.database as db_module
        import inspect
        src = inspect.getsource(db_module)
        assert "check_same_thread" not in src, (
            "app/database.py에 check_same_thread가 남아있습니다. SQLite 전용 인자이므로 제거해야 합니다."
        )

    def test_engine_pool_size(self):
        """pool_size가 10 이상이어야 한다 (기본값 5에서 확장)"""
        from app.database import engine
        assert engine.pool.size() >= 10, (
            f"pool_size가 {engine.pool.size()}입니다. QueuePool 고갈 방지를 위해 10 이상이어야 합니다."
        )

    def test_engine_max_overflow(self):
        """max_overflow가 20 이상이어야 한다"""
        from app.database import engine
        assert engine.pool._max_overflow >= 20, (
            f"max_overflow가 {engine.pool._max_overflow}입니다. 20 이상이어야 합니다."
        )

    def test_engine_pool_pre_ping_enabled(self):
        """pool_pre_ping이 True여야 한다 (stale connection 방지)"""
        from app.database import engine
        assert engine.pool._pre_ping is True, (
            "pool_pre_ping=True가 설정되어야 합니다. 장시간 idle 커넥션 사용 시 오류를 방지합니다."
        )

    def test_engine_pool_recycle_set(self):
        """pool_recycle이 1800초(30분) 이하여야 한다"""
        from app.database import engine
        assert 0 < engine.pool._recycle <= 1800, (
            f"pool_recycle이 {engine.pool._recycle}입니다. 1800초(30분) 이하로 설정해야 합니다."
        )
