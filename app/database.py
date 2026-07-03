"""
Database connection setup using SQLAlchemy (sync + async dual-stack).

v6.0 Foundation (P0):
- 기존 sync engine/SessionLocal은 **완전 유지** (라우터 점진 마이그레이션 위해 병존).
- 신규 async_engine/AsyncSessionLocal 추가 — asyncpg 드라이버 기반.
- URL 파생: `postgresql://…` → `postgresql+asyncpg://…` 자동 변환.
- pool 설정은 동일 (10 + 20 overflow, 30s timeout, pre_ping, 1800s recycle).

이후 phase에서 라우터별로 `Depends(get_db)` → `Depends(get_async_db)` 교체.
Dual-stack 유지 기간 = 전체 41 라우터 전환 완료 시점(v6.0 P9)까지.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


# ─── sync engine (기존 유지) ────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,        # 기본 커넥션 수 (기존 SQLite 기본값 5에서 확장)
    max_overflow=20,     # 최대 초과 커넥션 수 (총 30커넥션)
    pool_timeout=30,     # 커넥션 대기 타임아웃 (초)
    pool_pre_ping=True,  # 커넥션 유효성 사전 확인 (stale connection 방지)
    pool_recycle=1800,   # 30분마다 커넥션 재생성 (idle 커넥션 정리)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─── async engine (v6.0 신규) ───────────────────────────────────
# URL 파생: `postgresql://user:pw@host/db` → `postgresql+asyncpg://user:pw@host/db`
# SQLite는 `sqlite+aiosqlite://` 필요하나 프로덕션은 postgres이므로 postgres 우선.
def _to_async_url(sync_url: str) -> str:
    """sync DB URL을 async 드라이버 URL로 변환."""
    if sync_url.startswith("postgresql+asyncpg://"):
        return sync_url
    if sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if sync_url.startswith("postgres://"):
        return sync_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if sync_url.startswith("sqlite:///"):
        # 개발용 SQLite 폴백 — aiosqlite 필요(별도 설치 시)
        return sync_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return sync_url


async_engine = create_async_engine(
    _to_async_url(settings.DATABASE_URL),
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800,
    # asyncpg는 statement cache를 자체 관리하나 pgbouncer 등 프록시 뒤에서는 비활성 권장.
    # 우리 배포는 직접 연결이므로 기본값 유지.
)
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # commit 후 객체 접근 시 자동 refresh 방지 → async 컨텍스트에서 MissingGreenlet 회피
)


# ─── Model Base (기존 유지) ─────────────────────────────────────
Base = declarative_base()
