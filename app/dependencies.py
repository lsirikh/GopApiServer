"""
Dependency functions for FastAPI.

v6.0 Foundation (P0):
- 기존 `get_db()` (sync Session yield) 완전 유지.
- 신규 `get_async_db()` — AsyncSession 반환. 라우터에서 `Depends(get_async_db)` 로 사용.
- Dual-stack: 라우터별 점진 마이그레이션.
"""
from __future__ import annotations

from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import AsyncSessionLocal, SessionLocal


# ─── sync (기존 유지) ───────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Sync SQLAlchemy Session dependency (기존 코드 호환).

    v6.0 Dual-stack 기간: 라우터별 async 전환 미완료 시까지 유지.
    전 라우터 전환 완료 후(v6.0 P9) 폐지 예정.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── async (v6.0 신규) ──────────────────────────────────────────
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async SQLAlchemy Session dependency.

    사용 예:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    - autocommit=False, autoflush=False, expire_on_commit=False
    - close()는 async 컨텍스트 매니저가 처리 → yield 후 자동 정리
    """
    async with AsyncSessionLocal() as db:
        yield db
