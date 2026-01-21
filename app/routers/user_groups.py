"""
UserGroup API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.models.user import UserGroup, AccountUser
from app.schemas.user import UserGroupResponse, UserGroupCreate, UserGroupUpdate, AccountUserResponse
from app.routers.auth import get_current_account_user
from app.services.audit_service import log_action, get_changes

router = APIRouter(tags=["User Groups"])


@router.get("")
async def get_user_groups(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(100, ge=1, le=100, description="페이지당 항목 수"),
    is_active: Optional[bool] = Query(None, description="활성화 상태 필터"),
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
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
    query = db.query(UserGroup)

    # Apply filters
    if is_active is not None:
        query = query.filter(UserGroup.is_active == is_active)

    offset = (page - 1) * limit
    groups = query.offset(offset).limit(limit).all()

    return {
        "success": True,
        "data": [UserGroupResponse.model_validate(group) for group in groups]
    }


@router.get("/{group_id}")
async def get_user_group_by_id(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
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
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Count users in this group
    user_count = db.query(AccountUser).filter(AccountUser.group_id == group_id).count()

    # Create response with user_count
    group_data = UserGroupResponse.model_validate(group)
    response_dict = group_data.model_dump()
    response_dict["user_count"] = user_count

    return {
        "success": True,
        "data": response_dict
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user_group(
    group_data: UserGroupCreate,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
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
    new_group = UserGroup(
        name=group_data.name,
        description=group_data.description,
        permissions=group_data.permissions,
        is_active=group_data.is_active if group_data.is_active is not None else True
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

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


@router.put("/{group_id}")
async def update_user_group(
    group_id: int,
    group_data: UserGroupUpdate,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 그룹 수정

    사용자 그룹 정보를 수정합니다.

    **Path Parameters**:
    - **group_id**: 그룹 ID

    **Request Body**:
    - **name**: 그룹 이름 (선택)
    - **description**: 설명 (선택)
    - **permissions**: 권한 설정 (선택)
    - **is_active**: 활성화 상태 (선택)

    **Response**: success, data (수정된 그룹 정보)

    **Error**:
    - 404: 그룹을 찾을 수 없음
    """
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # 변경 전 상태 저장
    before_state = {
        "name": group.name,
        "description": group.description,
        "permissions": group.permissions,
        "is_active": group.is_active
    }

    # Update fields if provided
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description
    if group_data.permissions is not None:
        group.permissions = group_data.permissions
    if group_data.is_active is not None:
        group.is_active = group_data.is_active

    db.commit()
    db.refresh(group)

    # 변경 후 상태 저장
    after_state = {
        "name": group.name,
        "description": group.description,
        "permissions": group.permissions,
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


@router.delete("/{group_id}")
async def delete_user_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
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
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # 삭제 전 스냅샷 저장
    group_name = group.name
    group_description = group.description

    # Set group_id to NULL for all users in this group
    db.query(AccountUser).filter(AccountUser.group_id == group_id).update({"group_id": None})

    db.delete(group)
    db.commit()

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

    return {"success": True}


@router.get("/{group_id}/users")
async def get_user_group_users(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
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
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    users = db.query(AccountUser).filter(AccountUser.group_id == group_id).all()

    return {
        "success": True,
        "data": [AccountUserResponse.model_validate(user) for user in users]
    }
