"""per-grant 만료 실시간 통지 스케줄러 — FR-07 (grant-enforcement-hardening).

grant 의 `valid_until` 시각에 1회성(date) job 을 등록해 만료 **즉시**
`publish_permissions_changed(GRANT_EXPIRED)` 를 발화한다. 스윕(`GRANT_SWEEP_INTERVAL_MINUTES`)은
누락/재기동 방어 **백스톱**으로 유지 → 실시간성(≈0)과 견고성을 동시에 확보.

설계:
- 스케줄러 인스턴스는 `main.py` lifespan 에서 `set_scheduler()` 로 주입(요청 핸들러 grants.py 가 공유).
- **best-effort**: job 등록/취소 실패가 grant 트랜잭션·API 응답을 막지 않는다(발행과 동일 원칙).
- **재기동 복원(NFR-05)**: 부팅 시 `reschedule_future_grants()` 로 미래 만료분 재등록, 과거분 미발화.
- **스케일(RISK-03)**: `GRANT_JOB_HORIZON_HOURS`(0=무제한) 내 만료만 job 등록, 그 밖은 스윕 위임.
- **보안 비의존**: 인가 차단은 요청시점 계산(_active_grants)이 권위. 본 모듈은 통지 즉시성 최적화.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_scheduler = None  # AsyncIOScheduler — main.py lifespan 에서 주입(미주입 시 전부 무동작)


def set_scheduler(scheduler) -> None:
    """main.py lifespan 에서 스케줄러 주입(테스트는 fake 주입 / None 으로 격리)."""
    global _scheduler
    _scheduler = scheduler


def _job_id(grant_id: int) -> str:
    return f"grant_expiry:{grant_id}"


def _now() -> datetime:
    from app.config import settings
    return datetime.now(settings.tz).replace(tzinfo=None)


def _within_horizon(valid_until: datetime, now: datetime) -> bool:
    from app.config import settings
    horizon = settings.GRANT_JOB_HORIZON_HOURS
    if horizon and horizon > 0:
        return valid_until <= now + timedelta(hours=horizon)
    return True  # 0 = 무제한


async def _fire_expiry(user_id: int) -> None:
    """job 콜백 — 만료 시각 도달 시 권한변경 통지(best-effort, 게이트 off 무동작)."""
    try:
        from app.services.nats_revoke_publisher import publish_permissions_changed
        await publish_permissions_changed(user_id=user_id, reason="GRANT_EXPIRED")
    except Exception as e:  # best-effort
        logger.warning("grant expiry fire failed (user=%s): %s", user_id, e)


def schedule_grant_expiry(grant_id: int, user_id: int, valid_until, now=None) -> bool:
    """grant 만료 시각에 1회성 발화 job 등록. 등록 시 True.

    미등록(False) 조건: 스케줄러 미주입 / valid_until None(상시) / 이미 과거 / 지평 밖.
    best-effort — 예외를 삼켜 grant 트랜잭션을 막지 않는다.
    """
    if _scheduler is None or valid_until is None:
        return False
    now = now or _now()
    if valid_until <= now:
        return False  # 이미 만료 — 요청시점 계산/스윕이 담당
    if not _within_horizon(valid_until, now):
        return False  # 스케일 상한 — 스윕 백스톱 위임
    try:
        _scheduler.add_job(
            _fire_expiry, "date", run_date=valid_until,
            args=[user_id], id=_job_id(grant_id), replace_existing=True,
        )
        return True
    except Exception as e:  # best-effort
        logger.warning("schedule grant expiry failed (grant=%s): %s", grant_id, e)
        return False


def cancel_grant_expiry(grant_id: int) -> bool:
    """grant 회수/갱신 시 예약 발화 job 취소(best-effort). 취소 시 True(없으면 False)."""
    if _scheduler is None:
        return False
    try:
        _scheduler.remove_job(_job_id(grant_id))
        return True
    except Exception:
        return False  # 없는 job 등 — 무시


async def reschedule_future_grants() -> int:
    """부팅 복원(NFR-05) — 미래 만료 active grant 를 재등록. 반환=등록 수.

    자체 `AsyncSessionLocal` 세션 사용(스케줄러 컨텍스트). best-effort.
    """
    if _scheduler is None:
        return 0
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.user import UserGroupGrant

        now = _now()
        count = 0
        async with AsyncSessionLocal() as db:
            stmt = select(UserGroupGrant).where(
                UserGroupGrant.revoked_at.is_(None),
                UserGroupGrant.valid_until.isnot(None),
                UserGroupGrant.valid_until > now,
            )
            result = await db.execute(stmt)
            for g in result.scalars().all():
                if schedule_grant_expiry(g.id, g.user_id, g.valid_until, now=now):
                    count += 1
        return count
    except Exception as e:  # best-effort
        logger.warning("reschedule_future_grants failed: %s", e)
        return 0
