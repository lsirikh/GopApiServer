"""
UserGroupGrant API — 권한그룹 시간기반 부여 관리 (ADMIN 전용)
PRD: PRD_Permission_Group_Scheduling.md FR-03

경로(main.py 에서 prefix="/api" 로 마운트 — users.py 무접촉):
- POST   /api/users/{user_id}/grants   부여
- GET    /api/users/{user_id}/grants   목록(+status)
- DELETE /api/grants/{grant_id}        회수(soft, revoked_at)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.config import settings
from app.dependencies import get_db
from app.models.user import AccountUser, UserGroup, UserGroupGrant
from app.schemas.grant import GrantCreate, GrantResponse
from app.routers.auth import get_current_account_user, require_admin
from app.services.audit_service import log_action
from app.services.grant_service import grant_status

router = APIRouter(tags=["User Group Grants"])


def _now() -> datetime:
    return datetime.now(settings.tz).replace(tzinfo=None)


def _to_naive_kst(dt: Optional[datetime]) -> Optional[datetime]:
    """tz-aware 입력을 KST 기준 naive 로 정규화(타 테이블 저장 컨벤션 일치)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(settings.tz)
    return dt.replace(tzinfo=None)


def _serialize(grant: UserGroupGrant, now: Optional[datetime] = None) -> GrantResponse:
    now = now or _now()
    return GrantResponse(
        id=grant.id,
        user_id=grant.user_id,
        group_id=grant.group_id,
        group_name=grant.group.name if grant.group else None,
        valid_from=grant.valid_from,
        valid_until=grant.valid_until,
        is_active=grant.is_active,
        status=grant_status(grant, now),
        granted_by=grant.granted_by,
        revoked_at=grant.revoked_at,
        created_at=grant.created_at,
    )


@router.post("/users/{user_id}/grants", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
async def create_grant(
    user_id: int,
    payload: GrantCreate,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """사용자에게 권한그룹을 기간을 정해 부여한다 (ADMIN 전용).

    - **valid_until** 생략/NULL = 상시(무기한).
    - 검증: 사용자/그룹 존재, `valid_from < valid_until`, 과거 `valid_until` 거부.
    """
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    group = db.query(UserGroup).filter(UserGroup.id == payload.group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User group not found")

    now = _now()
    valid_from = _to_naive_kst(payload.valid_from)
    valid_until = _to_naive_kst(payload.valid_until)

    if valid_until is not None:
        if valid_until <= valid_from:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="valid_until must be after valid_from",
            )
        if valid_until <= now:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="valid_until must be in the future",
            )

    grant = UserGroupGrant(
        user_id=user_id,
        group_id=payload.group_id,
        valid_from=valid_from,
        valid_until=valid_until,
        is_active=True,
        granted_by=current_user.id,
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)

    await log_action(
        db=db,
        action_type="GRANT_CREATED",
        resource_type="USER_GROUP",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=grant.id,
        resource_name=group.name,
        description=f"권한그룹 부여: user={user_id} group={group.name} until={valid_until}",
    )

    return {"success": True, "data": _serialize(grant, now)}


@router.get("/users/{user_id}/grants", dependencies=[Depends(require_admin)])
async def list_grants(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """사용자의 부여 목록(+파생 status) 조회 (ADMIN 전용)."""
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    now = _now()
    grants = db.query(UserGroupGrant).filter(UserGroupGrant.user_id == user_id).all()
    return {"success": True, "data": [_serialize(g, now) for g in grants]}


@router.delete("/grants/{grant_id}", dependencies=[Depends(require_admin)])
async def revoke_grant(
    grant_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """부여 회수 — soft(revoked_at 기록, 물리삭제 아님). ADMIN 전용."""
    grant = db.query(UserGroupGrant).filter(UserGroupGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    if grant.revoked_at is None:
        grant.revoked_at = _now()
        grant.is_active = False
        db.commit()

        await log_action(
            db=db,
            action_type="GRANT_REVOKED",
            resource_type="USER_GROUP",
            actor_login_id=current_user.login_id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            resource_id=grant.id,
            resource_name=grant.group.name if grant.group else None,
            description=f"권한그룹 부여 회수: grant={grant_id} user={grant.user_id}",
        )

    return {"success": True, "message": f"Grant {grant_id} revoked", "data": None}
