"""
api_logs TTL sweep — 30일 초과 로그 삭제 스케줄러
v5.4 후속: 문서 A-7 #6 대응 (`GOPDB_통합_원인분석_및_조치_20260702.md`).

배경: 문서 시점 api_logs 크기 10,606,885행 / 3.2GB (무제한 성장). 파티셔닝은 별도.
간단 TTL로 무한 성장 방지 — 일 1회(정오 근처) 실행, 30일 초과 row DELETE.

파티셔닝/롤오버는 v6.0 async 전환과 함께 도입 예정.
"""
from __future__ import annotations

from datetime import datetime, timedelta

DEFAULT_RETENTION_DAYS = 30


async def run_api_logs_sweep(retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
    """스케줄러 진입점 — 30일(기본) 초과 api_logs row 삭제.

    Returns: 삭제된 row 수.
    """
    from sqlalchemy import text
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        # 컬럼명은 `timestamp` (PostgreSQL 예약어라 quote 필수)
        result = db.execute(
            text('DELETE FROM api_logs WHERE "timestamp" < :cutoff'),
            {"cutoff": cutoff},
        )
        deleted = result.rowcount or 0
        db.commit()
        return deleted
    except Exception as e:
        print(f"[api_logs_sweep] error: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return 0
    finally:
        db.close()
