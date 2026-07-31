"""
server_metrics collected_at 타임존 정규화 테스트 (v6.3 server_metrics_tz_fix).

버그: tz-aware(KST +09:00) collected_at 을 naive 컬럼(TIMESTAMP WITHOUT TIME ZONE)에 넣으면
asyncpg 가 "can't subtract offset-naive and offset-aware datetimes" 로 거부(500)
→ CPU/RAM/디스크 메트릭 저장 통째 실패. `_to_naive_kst` 로 naive-KST 정규화.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import select

from app.models.server import Server, ServerCategory, ServerMetrics
from app.schemas.server import ServerMetricsCreate
from app.utils.enums import EnumServerType, EnumServerStatus
from app.routers.server_metrics import _to_naive_kst, create_server_metrics

KST = timezone(timedelta(hours=9))


# ---- _to_naive_kst 순수 로직 (핵심 가드) ----

def test_to_naive_kst_strips_aware_kst():
    out = _to_naive_kst(datetime(2026, 7, 31, 10, 0, 0, tzinfo=KST))
    assert out.tzinfo is None
    assert (out.year, out.month, out.day, out.hour, out.minute) == (2026, 7, 31, 10, 0)


def test_to_naive_kst_converts_utc_to_kst():
    out = _to_naive_kst(datetime(2026, 7, 31, 1, 0, 0, tzinfo=timezone.utc))  # 01:00 UTC = 10:00 KST
    assert out.tzinfo is None
    assert out.hour == 10


def test_to_naive_kst_passthrough_naive_and_none():
    naive = datetime(2026, 7, 31, 10, 0, 0)
    assert _to_naive_kst(naive) == naive and _to_naive_kst(naive).tzinfo is None
    assert _to_naive_kst(None) is None


# ---- 엔드포인트 통합 (격리 async_db) ----

pytestmark = pytest.mark.asyncio


async def _mk_server(db) -> Server:
    cat = ServerCategory(name="VMS Cat", type_server=EnumServerType.VMS)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    srv = Server(name="SRV", category_id=cat.id, status=EnumServerStatus.NORMAL, ip_address="1.1.1.1", port=8080)
    db.add(srv)
    await db.commit()
    await db.refresh(srv)
    return srv


async def test_create_metrics_accepts_aware_collected_at(async_db):
    """aware collected_at 을 보내도 저장 성공 + DB엔 naive-KST 로 저장."""
    srv = await _mk_server(async_db)
    payload = ServerMetricsCreate(cpu_usage=50.0, collected_at=datetime(2026, 7, 31, 10, 0, 0, tzinfo=KST))
    resp = await create_server_metrics(server_id=srv.id, metrics_data=payload, current_user=None, db=async_db)
    assert resp.success is True

    row = (await async_db.execute(select(ServerMetrics).where(ServerMetrics.server_id == srv.id))).scalars().first()
    assert row is not None and row.collected_at is not None
    assert row.collected_at.tzinfo is None      # 핵심: naive 로 저장
    assert row.collected_at.hour == 10
