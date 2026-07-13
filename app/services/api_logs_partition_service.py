"""
DB-02 — api_logs 월별 파티션 사전 생성 서비스.

v60 파티셔닝(월별 RANGE, `PARTITION BY RANGE ("timestamp")`)은 당월+3개월만 생성했고
자동 확장 장치가 없어, 마지막 파티션 경계(예: 2026-11-01) 이후 INSERT 가 실패한다
(대상 파티션 없음 + default 파티션 부재).

이 서비스는 **당월 + 향후 N개월** 파티션을 멱등 생성(`CREATE TABLE IF NOT EXISTS ...
PARTITION OF`, PostgreSQL 11+)하여 경계 초과 INSERT 실패를 예방한다.
- startup 1회 + 스케줄러(일 1회 cron)로 재보장 → 장기 무재시작 인스턴스도 안전.
- 파티션명은 v60 규약(`api_logs_YYYY_MM`)과 동일 → 기존 파티션은 IF NOT EXISTS 로 skip.
"""
from __future__ import annotations

from datetime import date

MONTHS_AHEAD_DEFAULT = 6


def _month_partition_ddl(year: int, month: int) -> tuple[str, str]:
    """(partition_name, ddl) — 해당 월 [1일, 다음달 1일) 반열림 RANGE 파티션 DDL."""
    name = f"api_logs_{year:04d}_{month:02d}"
    frm = f"{year:04d}-{month:02d}-01"
    to = f"{year + 1:04d}-01-01" if month == 12 else f"{year:04d}-{month + 1:02d}-01"
    ddl = (
        f"CREATE TABLE IF NOT EXISTS {name} PARTITION OF api_logs "
        f"FOR VALUES FROM ('{frm}') TO ('{to}')"
    )
    return name, ddl


async def ensure_api_log_partitions(months_ahead: int = MONTHS_AHEAD_DEFAULT) -> list[str]:
    """당월 + 향후 `months_ahead` 개월 api_logs 파티션을 멱등 생성한다.

    반환: 보장(생성 또는 이미 존재)된 파티션명 리스트.
    파티션명/경계는 코드가 생성한 상수(사용자 입력 아님)라 SQL injection 무관.
    """
    from sqlalchemy import text
    from app.database import AsyncSessionLocal

    today = date.today()
    base = today.year * 12 + (today.month - 1)  # 0-기준 월 인덱스
    ensured: list[str] = []
    async with AsyncSessionLocal() as db:
        for offset in range(months_ahead + 1):
            year, month0 = divmod(base + offset, 12)
            name, ddl = _month_partition_ddl(year, month0 + 1)
            await db.execute(text(ddl))
            ensured.append(name)
        await db.commit()
    return ensured
