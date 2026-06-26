"""
User API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid

from app.config import settings
from app.dependencies import get_db
from app.models.user import AccountUser, UserGroup, UserSession
from app.models.system_event import SystemEvent
from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity
from app.schemas.user import AccountUserResponse, AccountUserCreate, AccountUserUpdate, AccountUserSelfUpdate, PasswordResetRequest, PasswordChangeRequest
from app.routers.auth import get_current_account_user, require_admin
from app.utils.auth import hash_password, verify_password
from app.services.audit_service import log_action, get_changes

router = APIRouter(tags=["Users"])


@router.get("", dependencies=[Depends(require_admin)])
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
    user_data: AccountUserSelfUpdate,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    내 정보 수정 (PRD v4.8 Phase 12-7c)

    현재 로그인한 사용자의 본인 정보만 수정합니다.
    권한 필드(role/group_id/is_active)는 본 경로로 변경 불가 — 전용 admin 경로 /users/{user_id} 사용.

    **Request Body** (권한 필드 전송 시 422):
    - **name**: 이름 (선택)
    - **email**: 이메일 (선택)
    - **department**: 부서 (선택)
    - **position**: 직책 (선택)
    - **photo_url**: 프로필 사진 URL (선택)
    - **phone**: 전화번호 (선택)

    **Error**:
    - 422: role/group_id/is_active 등 권한 필드 전송 시
    """
    # Capture before state for audit log
    before_state = {
        "name": current_user.name,
        "email": current_user.email,
        "department": current_user.department,
        "position": current_user.position,
        "phone": current_user.phone
    }

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

    # Capture after state for audit log
    after_state = {
        "name": current_user.name,
        "email": current_user.email,
        "department": current_user.department,
        "position": current_user.position,
        "phone": current_user.phone
    }

    # Audit log: USER_UPDATED (self)
    changes = get_changes(before_state, after_state)
    if changes["before"] or changes["after"]:
        await log_action(
            db=db,
            action_type="USER_UPDATED",
            resource_type="USER",
            actor_login_id=current_user.login_id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            resource_id=current_user.id,
            resource_name=f"{current_user.name} ({current_user.login_id})",
            changes=changes,
            description=f"내 정보 수정: {current_user.login_id}"
        )

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

    # Audit log: PASSWORD_CHANGED
    await log_action(
        db=db,
        action_type="PASSWORD_CHANGED",
        resource_type="PASSWORD",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=current_user.id,
        resource_name=f"{current_user.name} ({current_user.login_id})",
        description=f"비밀번호 변경: {current_user.login_id}"
    )

    return {"success": True}


# ──────────────── Profile Photo (프로필 사진 업로드/서빙) ────────────────
# 파일은 settings.PROFILE_STORAGE_PATH(=data/profiles, 호스트 ./data 바인드 마운트 → 영속)에 저장.
# photo_url(DB)에는 절대 API URL 저장 → 클라가 그대로 표시(GET /api/users/photo/{name}).
ALLOWED_PHOTO_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5MB


async def _save_profile_photo(user: AccountUser, file: UploadFile, request: Request, db: Session):
    """업로드 파일 검증 → data/profiles 저장 → user.photo_url(절대 URL) 갱신. (본인/admin 공통)"""
    ext = ALLOWED_PHOTO_MIME.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_PHOTO_MIME)}",
        )
    content = await file.read()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {len(content)} bytes (max {MAX_PHOTO_BYTES})",
        )
    os.makedirs(settings.PROFILE_STORAGE_PATH, exist_ok=True)
    file_name = f"{user.id}_{uuid.uuid4().hex[:8]}.{ext}"   # uuid 파일명 — traversal/충돌 방지
    file_path = os.path.join(settings.PROFILE_STORAGE_PATH, file_name)
    with open(file_path, "wb") as f:
        f.write(content)
    # 절대 URL — photo_url 검증기(http(s) 허용) 통과 + 클라 ImageConverter(C1) 직접 렌더
    user.photo_url = f"{str(request.base_url).rstrip('/')}/api/users/photo/{file_name}"
    db.commit()
    db.refresh(user)
    return {"success": True, "message": "Profile photo uploaded", "data": AccountUserResponse.model_validate(user)}


@router.post("/me/photo", summary="본인 프로필 사진 업로드")
async def upload_my_photo(
    request: Request,
    file: UploadFile = File(..., description="이미지 파일 (jpeg/png/webp/gif, ≤5MB)"),
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """본인 프로필 사진 업로드 → data/profiles/ 저장 + photo_url(DB) 갱신."""
    return await _save_profile_photo(current_user, file, request, db)


@router.get("/photo/{file_name}", summary="프로필 사진 다운로드(파일명 기반)")
async def get_profile_photo(file_name: str):
    """data/profiles/{file_name} 이미지 바이너리 반환. 인증 불필요(파일명 uuid라 비공개성 확보)."""
    if "/" in file_name or "\\" in file_name or ".." in file_name:   # 경로 traversal 차단
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name")
    file_path = os.path.join(settings.PROFILE_STORAGE_PATH, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found")
    return FileResponse(path=file_path)


@router.get("/{user_id}", dependencies=[Depends(require_admin)])
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


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
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

    # Audit log: USER_CREATED
    await log_action(
        db=db,
        action_type="USER_CREATED",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=new_user.id,
        resource_name=f"{new_user.name} ({new_user.login_id})",
        description=f"신규 사용자 생성: {new_user.login_id}"
    )

    return {
        "success": True,
        "data": AccountUserResponse.model_validate(new_user)
    }


@router.put("/{user_id}", dependencies=[Depends(require_admin)])
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

    # Capture before state for audit log
    before_state = {
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "position": user.position,
        "employee_number": user.employee_number,
        "photo_url": user.photo_url,
        "phone": user.phone,
        "role": user.role,
        "group_id": user.group_id,
        "is_active": user.is_active
    }

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

    # Capture after state for audit log
    after_state = {
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "position": user.position,
        "employee_number": user.employee_number,
        "photo_url": user.photo_url,
        "phone": user.phone,
        "role": user.role,
        "group_id": user.group_id,
        "is_active": user.is_active
    }

    # Audit log: USER_UPDATED
    changes = get_changes(before_state, after_state)
    await log_action(
        db=db,
        action_type="USER_UPDATED",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=user.id,
        resource_name=f"{user.name} ({user.login_id})",
        changes=changes,
        description=f"사용자 정보 수정: {user.login_id}"
    )

    return {
        "success": True,
        "data": AccountUserResponse.model_validate(user)
    }


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
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

    # Capture user info before deletion (snapshot)
    deleted_user_id = user.id
    deleted_user_name = f"{user.name} ({user.login_id})"
    deleted_login_id = user.login_id

    db.delete(user)
    db.commit()

    # Audit log: USER_DELETED (after delete, preserve snapshot)
    await log_action(
        db=db,
        action_type="USER_DELETED",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=deleted_user_id,
        resource_name=deleted_user_name,
        description=f"사용자 삭제: {deleted_login_id}"
    )

    return {
        "success": True,
        "message": f"User {deleted_user_id} deleted successfully",
        "data": None
    }


@router.post("/{user_id}/lock", dependencies=[Depends(require_admin)])
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

    # Create system event for user lock (SECURITY_ALERT: USER_* moved to UserLoginLog per PRD_SystemEvent_Sync.md)
    system_event = SystemEvent(
        type_event=EnumSystemEventType.SECURITY_ALERT,
        severity=EnumSystemEventSeverity.WARNING,
        title=f"사용자 계정 잠금: {user.login_id}",
        message=f"사용자 '{user.name}' ({user.login_id})의 계정이 잠금되었습니다.",
        source="user_api"
    )
    db.add(system_event)

    db.commit()

    # Audit log: USER_LOCKED
    await log_action(
        db=db,
        action_type="USER_LOCKED",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=user.id,
        resource_name=f"{user.name} ({user.login_id})",
        description=f"사용자 계정 잠금: {user.login_id}"
    )

    return {"success": True}


@router.post("/{user_id}/unlock", dependencies=[Depends(require_admin)])
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

    # Create system event for user unlock (SECURITY_ALERT: USER_* moved to UserLoginLog per PRD_SystemEvent_Sync.md)
    system_event = SystemEvent(
        type_event=EnumSystemEventType.SECURITY_ALERT,
        severity=EnumSystemEventSeverity.INFO,
        title=f"사용자 계정 잠금 해제: {user.login_id}",
        message=f"사용자 '{user.name}' ({user.login_id})의 계정 잠금이 해제되었습니다.",
        source="user_api"
    )
    db.add(system_event)

    db.commit()

    # Audit log: USER_UNLOCKED
    await log_action(
        db=db,
        action_type="USER_UNLOCKED",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=user.id,
        resource_name=f"{user.name} ({user.login_id})",
        description=f"사용자 계정 잠금 해제: {user.login_id}"
    )

    return {"success": True}


@router.post("/{user_id}/reset-password", dependencies=[Depends(require_admin)])
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

    # Audit log: PASSWORD_RESET
    await log_action(
        db=db,
        action_type="PASSWORD_RESET",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=user.id,
        resource_name=f"{user.name} ({user.login_id})",
        description=f"비밀번호 초기화: {user.login_id}"
    )

    return {"success": True}
