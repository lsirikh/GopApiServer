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
from app.services.nats_revoke_publisher import publish_permissions_changed

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
    # v5.4 (REQ_Server_Grants_ListAll): user_login_id / user_name 비정규화 포함
    # relationship 'user' 는 UserGroupGrant.user_id → AccountUser (models/user.py:125)
    return GrantResponse(
        id=grant.id,
        user_id=grant.user_id,
        user_login_id=grant.user.login_id if grant.user else None,
        user_name=grant.user.name if grant.user else None,
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

    # FR-06: 권한 변경 통지(best-effort, 게이트 NATS_REVOKE_ENABLED off 시 무동작). 클라 재평가 트리거.
    await publish_permissions_changed(user_id=user_id, reason="GRANT_CREATED")

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


@router.get("/grants", dependencies=[Depends(require_admin)])
async def list_all_grants(
    page: int = 1,
    size: int = 20,
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    status: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """전체 grant 목록 조회 (ADMIN 전용) — v5.4 REQ_Server_Grants_ListAll.

    클라 관리자 대시보드 성격: 계정별 순회 대신 단일 호출로 전체 부여 현황 표시.

    **쿼리 파라미터** (모두 선택):
    - **page**: 페이지 번호 (기본 1)
    - **size**: 페이지 크기 (기본 20, 최대 100)
    - **user_id**: 계정 필터
    - **group_id**: 그룹 필터
    - **status**: 파생 상태 필터 (ACTIVE/PENDING/EXPIRED/REVOKED)
    - **active_only**: `is_active=true` 만 (sweep 비정규화 기준)

    **응답**: `{success, data: [GrantResponse...], total}` — 기존 리스트 엔벨로프 일관.

    **Error**: 403 (require_admin) — 나머지 정상 (필터 결과 0건은 빈 배열).
    """
    if page < 1:
        raise HTTPException(status_code=422, detail="page must be >= 1")
    if size < 1 or size > 100:
        raise HTTPException(status_code=422, detail="size must be between 1 and 100")

    query = db.query(UserGroupGrant)
    if user_id is not None:
        query = query.filter(UserGroupGrant.user_id == user_id)
    if group_id is not None:
        query = query.filter(UserGroupGrant.group_id == group_id)
    if active_only:
        query = query.filter(UserGroupGrant.is_active == True)

    now = _now()

    # status 필터는 파생값이므로 DB 조회 후 필터 (총 grant 수 소규모 예상)
    if status is not None:
        valid_statuses = {"ACTIVE", "PENDING", "EXPIRED", "REVOKED"}
        if status not in valid_statuses:
            raise HTTPException(status_code=422, detail=f"status must be one of {sorted(valid_statuses)}")
        all_grants = query.order_by(UserGroupGrant.created_at.desc()).all()
        filtered = [g for g in all_grants if grant_status(g, now) == status]
        total = len(filtered)
        offset = (page - 1) * size
        page_items = filtered[offset:offset + size]
        return {
            "success": True,
            "data": [_serialize(g, now) for g in page_items],
            "total": total,
        }

    # status 필터 없음 — DB 레벨 페이지네이션
    total = query.count()
    offset = (page - 1) * size
    grants = query.order_by(UserGroupGrant.created_at.desc()).offset(offset).limit(size).all()
    return {
        "success": True,
        "data": [_serialize(g, now) for g in grants],
        "total": total,
    }


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

        # FR-06: 권한 변경 통지(best-effort, 게이트 off 시 무동작)
        await publish_permissions_changed(user_id=grant.user_id, reason="GRANT_REVOKED")

    return {"success": True, "message": f"Grant {grant_id} revoked", "data": None}
