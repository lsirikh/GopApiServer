"""
User API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.dependencies import get_db
from app.models.user import AccountUser, UserGroup, UserSession
from app.models.system_event import SystemEvent
from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity
from app.schemas.user import AccountUserResponse, AccountUserCreate, AccountUserUpdate, PasswordResetRequest, PasswordChangeRequest
from app.routers.auth import get_current_account_user
from app.utils.auth import hash_password, verify_password

router = APIRouter(tags=["Users"])


@router.get("")
async def get_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(100, ge=1, le=100, description="페이지당 항목 수"),
    role: Optional[str] = Query(None, description="역할 필터"),
    group_id: Optional[int] = Query(None, description="그룹 ID 필터"),
    department: Optional[str] = Query(None, description="부서 필터"),
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 목록 조회

    모든 사용자 목록을 조회합니다.

    **Query Parameters**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 100, 최대: 100)
    - **role**: 역할 필터 (ADMIN, OPERATOR, VIEWER)
    - **group_id**: 그룹 ID 필터
    - **department**: 부서 필터

    **Response**: success, data (사용자 목록)
    """
    query = db.query(AccountUser)

    # Apply filters
    if role:
        query = query.filter(AccountUser.role == role)
    if group_id:
        query = query.filter(AccountUser.group_id == group_id)
    if department:
        query = query.filter(AccountUser.department == department)

    offset = (page - 1) * limit
    users = query.offset(offset).limit(limit).all()

    return {
        "success": True,
        "data": [AccountUserResponse.model_validate(user) for user in users]
    }


@router.get("/me")
async def get_my_info(
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    내 정보 조회

    현재 로그인한 사용자의 정보를 조회합니다.

    **Response**: success, data (사용자 정보)
    """
    return {
        "success": True,
        "data": AccountUserResponse.model_validate(current_user)
    }


@router.put("/me")
async def update_my_info(
    user_data: AccountUserUpdate,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    내 정보 수정

    현재 로그인한 사용자의 정보를 수정합니다.

    **Request Body**:
    - **name**: 이름 (선택)
    - **email**: 이메일 (선택)
    - **department**: 부서 (선택)
    - **position**: 직책 (선택)
    - **phone**: 전화번호 (선택)

    **Response**: success, data (수정된 사용자 정보)
    """
    # Update fields if provided
    if user_data.name is not None:
        current_user.name = user_data.name
    if user_data.email is not None:
        current_user.email = user_data.email
    if user_data.department is not None:
        current_user.department = user_data.department
    if user_data.position is not None:
        current_user.position = user_data.position
    if user_data.phone is not None:
        current_user.phone = user_data.phone

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "data": AccountUserResponse.model_validate(current_user)
    }


@router.put("/me/password")
async def change_my_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    내 비밀번호 변경

    현재 로그인한 사용자의 비밀번호를 변경합니다.

    **Request Body**:
    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호

    **Response**: success: true

    **Error**:
    - 400: 현재 비밀번호가 일치하지 않음
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"success": True}


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 상세 조회

    ID로 사용자 정보를 조회합니다.

    **Path Parameters**:
    - **user_id**: 사용자 ID

    **Response**: success, data (사용자 정보)

    **Error**:
    - 404: 사용자를 찾을 수 없음
    """
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "data": AccountUserResponse.model_validate(user)
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AccountUserCreate,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 생성

    새 사용자를 생성합니다.

    **Request Body**:
    - **login_id**: 로그인 ID (필수)
    - **password**: 비밀번호 (필수)
    - **name**: 이름 (필수)
    - **email**: 이메일 (선택)
    - **department**: 부서 (선택)
    - **role**: 역할 (선택, 기본값: VIEWER)
    - **group_id**: 그룹 ID (선택)

    **Response**: success, data (생성된 사용자 정보)

    **Error**:
    - 400: 중복된 login_id
    """
    # Check for duplicate login_id
    existing = db.query(AccountUser).filter(AccountUser.login_id == user_data.login_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="login_id already exists"
        )

    # Validate group_id if provided
    if user_data.group_id:
        group = db.query(UserGroup).filter(UserGroup.id == user_data.group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="group_id does not exist"
            )

    # Create new user
    new_user = AccountUser(
        login_id=user_data.login_id,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        email=user_data.email,
        department=user_data.department,
        position=user_data.position,
        employee_number=user_data.employee_number,
        photo_url=user_data.photo_url,
        phone=user_data.phone,
        role=user_data.role or "VIEWER",
        group_id=user_data.group_id,
        is_active=True,
        is_locked=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "data": AccountUserResponse.model_validate(new_user)
    }


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_data: AccountUserUpdate,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 수정

    사용자 정보를 수정합니다.

    **Path Parameters**:
    - **user_id**: 사용자 ID

    **Request Body**:
    - **name**: 이름 (선택)
    - **email**: 이메일 (선택)
    - **department**: 부서 (선택)
    - **role**: 역할 (선택)
    - **group_id**: 그룹 ID (선택)
    - **is_active**: 활성화 상태 (선택)

    **Response**: success, data (수정된 사용자 정보)

    **Error**:
    - 404: 사용자를 찾을 수 없음
    """
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields if provided
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.department is not None:
        user.department = user_data.department
    if user_data.position is not None:
        user.position = user_data.position
    if user_data.employee_number is not None:
        user.employee_number = user_data.employee_number
    if user_data.photo_url is not None:
        user.photo_url = user_data.photo_url
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.group_id is not None:
        user.group_id = user_data.group_id
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "data": AccountUserResponse.model_validate(user)
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 삭제

    사용자를 삭제합니다.

    **Path Parameters**:
    - **user_id**: 사용자 ID

    **Response**: success: true

    **Error**:
    - 404: 사용자를 찾을 수 없음
    """
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {"success": True}


@router.post("/{user_id}/lock")
async def lock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 잠금

    사용자 계정을 잠급니다.

    **Path Parameters**:
    - **user_id**: 사용자 ID

    **Response**: success: true

    **Error**:
    - 404: 사용자를 찾을 수 없음
    """
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_locked = True

    # Terminate all active sessions for the user
    db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).update({"is_active": False})

    # Create system event for user lock
    system_event = SystemEvent(
        type_event=EnumSystemEventType.USER_LOCKED,
        severity=EnumSystemEventSeverity.WARNING,
        title=f"사용자 계정 잠금: {user.login_id}",
        message=f"사용자 '{user.name}' ({user.login_id})의 계정이 잠금되었습니다.",
        source="user_api"
    )
    db.add(system_event)

    db.commit()

    return {"success": True}


@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 잠금 해제

    사용자 계정 잠금을 해제합니다.

    **Path Parameters**:
    - **user_id**: 사용자 ID

    **Response**: success: true

    **Error**:
    - 404: 사용자를 찾을 수 없음
    """
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_locked = False

    # Create system event for user unlock
    system_event = SystemEvent(
        type_event=EnumSystemEventType.USER_UNLOCKED,
        severity=EnumSystemEventSeverity.INFO,
        title=f"사용자 계정 잠금 해제: {user.login_id}",
        message=f"사용자 '{user.name}' ({user.login_id})의 계정 잠금이 해제되었습니다.",
        source="user_api"
    )
    db.add(system_event)

    db.commit()

    return {"success": True}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 비밀번호 초기화 (관리자용)

    관리자가 사용자의 비밀번호를 초기화합니다.

    **Path Parameters**:
    - **user_id**: 사용자 ID

    **Request Body**:
    - **new_password**: 새 비밀번호

    **Response**: success: true

    **Error**:
    - 404: 사용자를 찾을 수 없음
    """
    user = db.query(AccountUser).filter(AccountUser.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"success": True}
