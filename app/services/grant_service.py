"""
권한그룹 부여(grant) 도메인 서비스 — FR-04/FR-05
PRD: PRD_Permission_Group_Scheduling.md

- grant_status: 파생 상태(ACTIVE/PENDING/EXPIRED/REVOKED) 계산 (순수함수, ORM 비의존)
- is_valid_now: 요청 시점 유효성 (인가 권위 — auth._active_grant_groups 와 동일 기준)
- expire_due_grants: 만료 grant 의 is_active 플래그를 false 로 내리는 sweep (표시/통지용)
"""
from __future__ import annotations

from datetime import datetime
from app.utils.datetime import utc_now

# 파생 상태 리터럴
STATUS_ACTIVE = "ACTIVE"
STATUS_PENDING = "PENDING"
STATUS_EXPIRED = "EXPIRED"
STATUS_REVOKED = "REVOKED"


def grant_status(grant, now: datetime) -> str:
    """grant 의 파생 상태. 우선순위: REVOKED > PENDING > EXPIRED > ACTIVE.

    - REVOKED: revoked_at 설정됨(soft 회수)
    - PENDING: now < valid_from (아직 시작 전)
    - EXPIRED: valid_until 있고 valid_until <= now
    - ACTIVE: 그 외(유효 윈도우 내, valid_until NULL=상시 포함)
    """
    if getattr(grant, "revoked_at", None) is not None:
        return STATUS_REVOKED
    if grant.valid_from > now:
        return STATUS_PENDING
    if grant.valid_until is not None and grant.valid_until <= now:
        return STATUS_EXPIRED
    return STATUS_ACTIVE


def is_valid_now(grant, now: datetime) -> bool:
    """요청 시점 유효 여부(인가 권위). is_active(sweep 비정규화) 비의존."""
    return grant_status(grant, now) == STATUS_ACTIVE


def find_due_grants(db, now: datetime):
    """만료됐는데 아직 is_active=True 인 grant 목록(sweep 대상)."""
    from app.models.user import UserGroupGrant

    return db.query(UserGroupGrant).filter(
        UserGroupGrant.is_active == True,  # noqa: E712
        UserGroupGrant.valid_until.isnot(None),
        UserGroupGrant.valid_until <= now,
    ).all()


def expire_due_grants(db, now: datetime) -> int:
    """만료된 grant 의 is_active 플래그를 false 로 내린다(sweep, 표시/통지용).

    ★ 보안 비의존 — 인가 차단은 요청 시점 계산(is_valid_now/auth._effective_allows)이 담당.
    본 sweep 은 목록/UI 표시·통지·정리 목적. 반환값 = 갱신된 행 수.
    """
    due = find_due_grants(db, now)
    for g in due:
        g.is_active = False
    if due:
        db.commit()
    return len(due)


async def run_grant_sweep() -> int:
    """스케줄러 진입점(FR-04) — 만료 grant is_active=false + GRANT_EXPIRED 감사.

    자체 DB 세션을 열고 닫는다(스케줄러 컨텍스트, AsyncSessionLocal 기반).
    보안 비의존(요청시점 계산이 권위).
    예외는 호출 측(스케줄러 래퍼)에서 잡아 기동/주기를 막지 않는다.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.database import AsyncSessionLocal
    from app.config import settings
    from app.models.user import UserGroupGrant
    from app.services.audit_service import log_action_async

    async with AsyncSessionLocal() as db:
        now = utc_now()
        stmt = (
            select(UserGroupGrant)
            .options(selectinload(UserGroupGrant.group))
            .where(
                UserGroupGrant.is_active == True,  # noqa: E712
                UserGroupGrant.valid_until.isnot(None),
                UserGroupGrant.valid_until <= now,
            )
        )
        result = await db.execute(stmt)
        due = result.scalars().all()
        if not due:
            return 0
        snapshot = [(g.id, g.user_id, (g.group.name if g.group else None)) for g in due]
        for g in due:
            g.is_active = False
        await db.commit()
        for gid, uid, gname in snapshot:
            await log_action_async(
                db=db,
                action_type="GRANT_EXPIRED",
                resource_type="USER_GROUP",
                actor_login_id="SYSTEM",
                resource_id=gid,
                resource_name=gname,
                description=f"부여 만료(sweep): grant={gid} user={uid}",
            )
        # FR-06: 영향 사용자별 권한변경 통지(best-effort, 게이트 off 시 무동작) — 사용자 단위 dedup
        from app.services.nats_revoke_publisher import publish_permissions_changed
        for uid in {u for _, u, _ in snapshot}:
            await publish_permissions_changed(user_id=uid, reason="GRANT_EXPIRED")
        return len(due)
