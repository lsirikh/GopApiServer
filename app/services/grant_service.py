"""
권한그룹 부여(grant) 도메인 서비스 — FR-04/FR-05
PRD: PRD_Permission_Group_Scheduling.md

- grant_status: 파생 상태(ACTIVE/PENDING/EXPIRED/REVOKED) 계산 (순수함수, ORM 비의존)
- is_valid_now: 요청 시점 유효성 (인가 권위 — auth._active_grant_groups 와 동일 기준)
- expire_due_grants: 만료 grant 의 is_active 플래그를 false 로 내리는 sweep (표시/통지용)
"""
from __future__ import annotations

from datetime import datetime

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


def expire_due_grants(db, now: datetime) -> int:
    """만료된 grant 의 is_active 플래그를 false 로 내린다(sweep, 표시/통지용).

    ★ 보안 비의존 — 인가 차단은 요청 시점 계산(is_valid_now/auth._effective_allows)이 담당.
    본 sweep 은 목록/UI 표시·통지·정리 목적. 반환값 = 갱신된 행 수.
    """
    from app.models.user import UserGroupGrant

    due = db.query(UserGroupGrant).filter(
        UserGroupGrant.is_active == True,  # noqa: E712
        UserGroupGrant.valid_until.isnot(None),
        UserGroupGrant.valid_until <= now,
    ).all()
    for g in due:
        g.is_active = False
    if due:
        db.commit()
    return len(due)
