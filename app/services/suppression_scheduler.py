"""억제 창 경계 전이 통지 스케줄러 — event-suppression-sync-message FR-05.

**왜 필요한가**: 억제 창의 시간 전이는 DB 쓰기 없이 일어난다.
- `pending → active`(창 시작): **어떤 컬럼도 바뀌지 않는다** → CRUD 트리거로 원리적 포착 불가.
- `active → expired`(창 종료): sweep 의 `is_active=false` 쓰기가 실재해 트리거가 잡지만 **최대 5분 지연**.

**해법**: `window_start`/`window_end` 에 1회성(date) job 을 걸고, 콜백은 **NATS 를 직접 붙이지 않고**
`notified_status` 컬럼만 UPDATE 한다. 그 UPDATE 를 기존 트리거(`trg_notify_suppression_sync`)가 잡아
`SYNC_EVENT_SUPPRESSION` 을 발행한다.

설계 원칙:
- **발행자 단일화**: 봉투(id/from/created) 생성 지점을 `db_monitor` 한 곳으로 유지. api-server 가
  NATS 를 직접 붙이면 동일 subject 에 발행자가 2개가 되어 순서·규약이 드리프트한다.
- **멱등**: 계산 상태 == `notified_status` 면 UPDATE 0행 → 트리거 미발화 → 발행 0건.
  잡 재실행·멀티인스턴스·백스톱 중복 전부 자연 흡수.
- **이중 통지 차단**: 창 종료 잡은 `is_active=false` 도 **같은 UPDATE 로** 처리한다. 이렇게 해야
  5분 뒤 sweep 이 같은 행을 다시 잡아 다른 트랜잭션에서 재발행하는 일이 없다.
- **best-effort**: job 등록/취소/발화 실패가 억제 API 트랜잭션을 막지 않는다.
- **재기동 복원**: 부팅 시 `reschedule_future_windows()` 로 미래 경계분 재등록.
- **억제 판정 비의존**: 억제 게이트는 요청시점 계산(`window_start <= now < window_end`)이 권위.
  본 모듈은 **통지 즉시성**만 담당한다(지연되어도 억제 자체는 정확).
"""
from __future__ import annotations

import logging
from datetime import datetime

from app.utils.datetime import utc_now

logger = logging.getLogger(__name__)

_scheduler = None  # AsyncIOScheduler — main.py lifespan 에서 주입(미주입 시 전부 무동작)


def set_scheduler(scheduler) -> None:
    """main.py lifespan 에서 스케줄러 주입(테스트는 fake 주입 / None 으로 격리)."""
    global _scheduler
    _scheduler = scheduler


def _job_id(schedule_id: int, boundary: str) -> str:
    return f"suppression_{boundary}:{schedule_id}"


def _naive_utc(dt: datetime | None) -> datetime | None:
    """저장값(naive-UTC 규약) 비교용 정규화. aware → UTC 로 변환 후 tz strip."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        from datetime import timezone
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def _fire_boundary(schedule_id: int, boundary: str) -> None:
    """job 콜백 — 창 경계 도달 시 `notified_status` 를 현재 파생상태로 UPDATE.

    NATS 직접 발행하지 않는다. UPDATE → 트리거 → pg_notify → db_monitor → NATS.
    현재 상태가 이미 기록된 상태와 같으면 아무것도 쓰지 않아 발행도 일어나지 않는다(멱등).
    """
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.event_suppression import EventSuppressionSchedule
        from app.services.event_suppression_service import suppression_status

        async with AsyncSessionLocal() as db:
            s = (await db.execute(
                select(EventSuppressionSchedule).where(EventSuppressionSchedule.id == schedule_id)
            )).scalars().first()
            if s is None:
                return  # 하드삭제됨 — 통지 불필요
            st = suppression_status(s)
            if s.notified_status == st:
                return  # 멱등: 이미 통지한 상태 → UPDATE 0행 → 발행 0건
            s.notified_status = st
            # 창 종료 잡은 is_active 도 **같은 UPDATE** 로 내려 sweep 재발화(이중 통지)를 차단한다.
            if boundary == "end" and s.is_active:
                s.is_active = False
            await db.commit()
            logger.info(
                "suppression boundary fired: schedule_id=%s boundary=%s status=%s",
                schedule_id, boundary, st,
            )
    except Exception as e:  # best-effort
        logger.warning(
            "suppression boundary fire failed (schedule_id=%s boundary=%s): %s",
            schedule_id, boundary, e,
        )


def _add(schedule_id: int, boundary: str, when: datetime | None, now: datetime) -> bool:
    if _scheduler is None or when is None:
        return False
    w = _naive_utc(when)
    if w is None or w <= now:
        return False  # 과거 경계 — 발화하지 않음(백스톱 sweep 이 재조정)
    try:
        from datetime import timezone
        from app.config import settings
        # ★ 반드시 **aware UTC** 로 넘긴다. 스케줄러는 AsyncIOScheduler(timezone=settings.tz=KST) 로
        #   생성되므로 naive datetime 을 주면 KST 로 해석해 실제 발화가 9시간 밀린다(창 시작 미발화).
        run_at = w.replace(tzinfo=timezone.utc)
        _scheduler.add_job(
            _fire_boundary, "date", run_date=run_at, args=[schedule_id, boundary],
            id=_job_id(schedule_id, boundary), replace_existing=True,
            misfire_grace_time=getattr(settings, "SUPPRESSION_SWEEP_INTERVAL_MINUTES", 5) * 60,
        )
        return True
    except Exception as e:  # best-effort
        logger.warning("suppression job add failed (id=%s %s): %s", schedule_id, boundary, e)
        return False


def schedule_window_boundaries(schedule, now: datetime | None = None) -> int:
    """스케줄의 `window_start`/`window_end` 에 date job 2건 등록. 반환 = 등록된 잡 수.

    취소(`revoked_at`) 된 스케줄은 등록하지 않고 기존 잡을 제거한다.
    """
    if _scheduler is None:
        return 0
    n = now or utc_now()
    n = _naive_utc(n)
    if getattr(schedule, "revoked_at", None) is not None:
        unschedule_window_boundaries(schedule.id)
        return 0
    cnt = 0
    if _add(schedule.id, "start", schedule.window_start, n):
        cnt += 1
    if _add(schedule.id, "end", schedule.window_end, n):
        cnt += 1
    return cnt


def unschedule_window_boundaries(schedule_id: int) -> int:
    """스케줄의 경계 잡 제거(취소/삭제 시). 반환 = 제거된 잡 수."""
    if _scheduler is None:
        return 0
    removed = 0
    for boundary in ("start", "end"):
        try:
            _scheduler.remove_job(_job_id(schedule_id, boundary))
            removed += 1
        except Exception:
            pass  # 없는 job — 무시
    return removed


async def reschedule_future_windows() -> int:
    """부팅 복원 — 미래 경계를 가진 미취소 스케줄의 잡을 재등록. 반환 = 등록 수.

    자체 `AsyncSessionLocal` 세션 사용(스케줄러 컨텍스트). best-effort.
    """
    if _scheduler is None:
        return 0
    try:
        from sqlalchemy import select, or_
        from app.database import AsyncSessionLocal
        from app.models.event_suppression import EventSuppressionSchedule

        now = _naive_utc(utc_now())
        count = 0
        async with AsyncSessionLocal() as db:
            stmt = select(EventSuppressionSchedule).where(
                EventSuppressionSchedule.revoked_at.is_(None),
                or_(
                    EventSuppressionSchedule.window_start > now,
                    EventSuppressionSchedule.window_end > now,
                ),
            )
            for s in (await db.execute(stmt)).scalars().all():
                count += schedule_window_boundaries(s, now=now)
        return count
    except Exception as e:  # best-effort
        logger.warning("reschedule_future_windows failed: %s", e)
        return 0
