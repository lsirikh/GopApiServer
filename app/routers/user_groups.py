"""
UserGroup API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.dependencies import get_async_db
from app.models.user import UserGroup, AccountUser
from app.schemas.user import UserGroupResponse, UserGroupCreate, UserGroupUpdate, AccountUserResponse
from app.routers.auth import get_current_account_user_async, require_admin_async, require_perm_async
from app.services.audit_service import log_action, get_changes
from app.schemas.user import PermissionsSchema

router = APIRouter(tags=["User Groups"])


@router.get("", dependencies=[Depends(require_perm_async("user_groups", "view"))])
async def get_user_groups(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(100, ge=1, le=100, description="페이지당 항목 수"),
    is_active: Optional[bool] = Query(None, description="활성화 상태 필터"),
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    사용자 그룹 목록 조회

    모든 사용자 그룹 목록을 조회합니다.

    **Query Parameters**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 100, 최대: 100)
    - **is_active**: 활성화 상태 필터

    **Response**: success, data (사용자 그룹 목록)
    """
    stmt = select(UserGroup)

    # Apply filters
    if is_active is not None:
        stmt = stmt.where(UserGroup.is_active == is_active)

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)
    groups = (await db.execute(stmt)).scalars().all()

    return {
        "success": True,
        "data": [UserGroupResponse.model_validate(group) for group in groups]
    }


@router.get("/{group_id}", dependencies=[Depends(require_perm_async("user_groups", "view"))])
async def get_user_group_by_id(
    group_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    사용자 그룹 상세 조회

    ID로 사용자 그룹 정보를 조회합니다.

    **Path Parameters**:
    - **group_id**: 그룹 ID

    **Response**: success, data (사용자 그룹 정보)

    **Error**:
    - 404: 그룹을 찾을 수 없음
    """
    group = (await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )).scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Count users in this group
    user_count = (await db.execute(
        select(func.count()).select_from(AccountUser).where(AccountUser.group_id == group_id)
    )).scalar()

    # Create response with user_count
    group_data = UserGroupResponse.model_validate(group)
    response_dict = group_data.model_dump()
    response_dict["user_count"] = user_count

    return {
        "success": True,
        "data": response_dict
    }


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_async)])
async def create_user_group(
    group_data: UserGroupCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    사용자 그룹 생성

    새 사용자 그룹을 생성합니다.

    **Request Body**:
    - **name**: 그룹 이름 (필수)
    - **description**: 설명 (선택)
    - **permissions**: 권한 설정 (선택, JSONB)
    - **is_active**: 활성화 상태 (선택, 기본값: True)

    **Response**: success, data (생성된 그룹 정보)
    """
    # Check if name already exists
    existing = (await db.execute(
        select(UserGroup).where(UserGroup.name == group_data.name)
    )).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User group with name '{group_data.name}' already exists"
        )

    # PRD v4.9 Phase 3 (A-2.1): PermissionsSchema → JSON dict 직렬화 (JSONB 컬럼 호환)
    perms_dict = group_data.permissions.model_dump(mode="json", exclude_none=True) if group_data.permissions else None

    new_group = UserGroup(
        name=group_data.name,
        description=group_data.description,
        permissions=perms_dict,
        is_active=group_data.is_active if group_data.is_active is not None else True
    )
    db.add(new_group)

    try:
        await db.commit()
        await db.refresh(new_group)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User group with name '{group_data.name}' already exists"
        )

    # 감사 로그 기록: GROUP_CREATED
    await log_action(
        db=db,
        action_type="GROUP_CREATED",
        resource_type="USER_GROUP",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=new_group.id,
        resource_name=new_group.name,
        description=f"신규 사용자 그룹 생성: {new_group.name}"
    )

    return {
        "success": True,
        "data": UserGroupResponse.model_validate(new_group)
    }


@router.put("/{group_id}", dependencies=[Depends(require_admin_async)])
async def update_user_group(
    group_id: int,
    group_data: UserGroupUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    사용자 그룹 수정

    사용자 그룹 정보를 수정합니다.

    **Path Parameters**:
    - **group_id**: 그룹 ID

    **Request Body**:
    - **name**: 그룹 이름 (선택)
    - **description**: 설명 (선택)
    - **is_active**: 활성화 상태 (선택)

    **Note (PRD v4.8 Phase 12-7a — P0)**:
    - `permissions` 필드는 일반 수정 API에서 차단됨 (권한 상승 공격 방지).
    - 권한 변경은 향후 전용 admin 엔드포인트(POST /user-groups/{id}/permissions)로만 허용 예정 (v5.0).
    - `extra="forbid"`로 인해 `permissions` 또는 기타 알 수 없는 필드 전송 시 422 반환.

    **Response**: success, data (수정된 그룹 정보)

    **Error**:
    - 404: 그룹을 찾을 수 없음
    - 422: `permissions` 또는 알 수 없는 필드 전송 시
    """
    group = (await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )).scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # 변경 전 상태 저장 (permissions은 일반 수정 경로에서 변경 불가 — PRD v4.8 Phase 12-7a)
    before_state = {
        "name": group.name,
        "description": group.description,
        "is_active": group.is_active
    }

    # Check if name already exists (when updating name)
    if group_data.name is not None and group_data.name != group.name:
        existing = (await db.execute(
            select(UserGroup).where(
                UserGroup.name == group_data.name,
                UserGroup.id != group_id
            )
        )).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User group with name '{group_data.name}' already exists"
            )

    # Update fields if provided (permissions은 스키마에서 제거됨 — 권한 변경 차단)
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description
    if group_data.is_active is not None:
        group.is_active = group_data.is_active

    try:
        await db.commit()
        await db.refresh(group)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User group with name '{group_data.name}' already exists"
        )

    # 변경 후 상태 저장
    after_state = {
        "name": group.name,
        "description": group.description,
        "is_active": group.is_active
    }

    # 변경 내역 계산
    changes = get_changes(before_state, after_state)

    # 감사 로그 기록: GROUP_UPDATED
    await log_action(
        db=db,
        action_type="GROUP_UPDATED",
        resource_type="USER_GROUP",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=group.id,
        resource_name=group.name,
        changes=changes,
        description=f"사용자 그룹 수정: {group.name}"
    )

    return {
        "success": True,
        "data": UserGroupResponse.model_validate(group)
    }


@router.post("/{group_id}/permissions", dependencies=[Depends(require_admin_async)])
async def update_user_group_permissions(
    group_id: int,
    permissions: PermissionsSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    사용자 그룹 권한 수정 (ADMIN 전용) — PRD v5.0

    일반 수정(PUT)은 `permissions`를 차단(권한 상승 공격 방지, PRD v4.8 Phase 12-7a)하므로,
    그룹 권한(모듈 × 동작) 변경은 이 ADMIN 전용 전용 엔드포인트로만 수행한다.

    **Path Parameters**:
    - **group_id**: 그룹 ID

    **Request Body** (`PermissionsSchema`, strict):
    - **modules**: `{모듈: {view, edit, delete, control}}` — 모듈 키는 EnumPermissionModule
      (devices/events/reports/cameras/users/user_groups/audit_logs/servers).
      미정의 모듈 키 또는 미정의 verb → 422 자동 거부. `view/edit/delete/control` 는 StrictBool.
    - **device_groups**: 접근 가능한 디바이스 그룹 ID 목록 (선택)

    **Response**: success, data (갱신된 그룹 — permissions 반영)

    **Error**:
    - 403: ADMIN 이 아님 (require_admin)
    - 404: 그룹을 찾을 수 없음
    - 422: 잘못된 권한 구조 (미정의 모듈/verb, truthy 문자열 등)
    """
    group = (await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )).scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # 변경 전/후 스냅샷 (감사 추적)
    before_perms = group.permissions

    # PermissionsSchema → JSON dict 직렬화 (JSONB 컬럼 호환). 전체 교체(부분 병합 아님).
    group.permissions = permissions.model_dump(mode="json", exclude_none=True)
    await db.commit()
    await db.refresh(group)

    changes = get_changes(
        {"permissions": before_perms},
        {"permissions": group.permissions}
    )

    # 감사 로그 기록: PERMISSION_CHANGED (append-only)
    await log_action(
        db=db,
        action_type="PERMISSION_CHANGED",
        resource_type="USER_GROUP",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=group.id,
        resource_name=group.name,
        changes=changes,
        description=f"그룹 권한 변경: {group.name}"
    )

    return {
        "success": True,
        "data": UserGroupResponse.model_validate(group)
    }


@router.delete("/{group_id}", dependencies=[Depends(require_admin_async)])
async def delete_user_group(
    group_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    사용자 그룹 삭제

    사용자 그룹을 삭제합니다. 소속 사용자들의 group_id는 NULL로 설정됩니다.

    **Path Parameters**:
    - **group_id**: 그룹 ID

    **Response**: success: true

    **Error**:
    - 404: 그룹을 찾을 수 없음
    """
    group = (await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )).scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # 삭제 전 스냅샷 저장
    group_name = group.name
    group_description = group.description

    # Set group_id to NULL for all users in this group
    await db.execute(
        update(AccountUser).where(AccountUser.group_id == group_id).values(group_id=None)
    )

    await db.delete(group)
    await db.commit()

    # 감사 로그 기록: GROUP_DELETED
    await log_action(
        db=db,
        action_type="GROUP_DELETED",
        resource_type="USER_GROUP",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=group_id,
        resource_name=group_name,
        description=f"사용자 그룹 삭제: {group_name}"
    )

    return {
        "success": True,
        "message": f"User group {group_id} deleted successfully",
        "data": None
    }


@router.get("/{group_id}/users", dependencies=[Depends(require_perm_async("user_groups", "view"))])
async def get_user_group_users(
    group_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    그룹 소속 사용자 목록 조회

    특정 그룹에 소속된 사용자 목록을 조회합니다.

    **Path Parameters**:
    - **group_id**: 그룹 ID

    **Response**: success, data (사용자 목록)

    **Error**:
    - 404: 그룹을 찾을 수 없음
    """
    group = (await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )).scalars().first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    users = (await db.execute(
        select(AccountUser).where(AccountUser.group_id == group_id)
    )).scalars().all()

    return {
        "success": True,
        "data": [AccountUserResponse.model_validate(user) for user in users]
    }
