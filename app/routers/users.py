"""
User API endpoints

v6.0 P8 VeryComplex: 라우터 async 전환 완료.
- 시그니처 async def 유지 / 응답 스키마 완전 유지
- Dependency: get_async_db + *_async 인가 / hash_password_async / verify_password_async / log_action_async / add_to_blacklist_async
- Query: select() + await db.execute(...) / with_for_update() 는 select 문 위에 체이닝
- Bulk update: sqlalchemy.update() construct 사용
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging
import os
import io
import uuid

logger = logging.getLogger(__name__)

from app.config import settings
from app.dependencies import get_async_db
from app.models.user import AccountUser, UserGroup, UserSession
from app.models.system_event import SystemEvent
from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity
from app.schemas.user import AccountUserResponse, AccountUserCreate, AccountUserUpdate, AccountUserSelfUpdate, PasswordResetRequest, PasswordChangeRequest
from app.routers.auth import get_current_account_user_async, require_perm_async, bearer_scheme
from app.utils.auth import hash_password_async, verify_password_async, decode_token
from app.services.audit_service import log_action_async, get_changes
from app.services.token_blacklist_service import add_to_blacklist_async
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from datetime import datetime, timedelta

router = APIRouter()


# ── v6.x RBAC 매트릭스 전환 가드 (require_admin → require_perm) ──────────────
# 계정 관리 endpoint 를 role 문자열 검사에서 매트릭스(등급 ∪ grant) 기반으로 전환한다.
# 단, "권한 정의(role/group 변경)·ADMIN 대상 변경" 은 base-ADMIN(role==ADMIN) 전용으로
# 남겨, grant 로 한시 승격된 USER 가 스스로 영구 승격하는 경로를 차단한다
# (스케쥴 만료 시 원래 등급 RBAC 로 깨끗이 복귀함을 보장).
def _assert_can_modify_admin_target(actor: AccountUser, target: AccountUser) -> None:
    """비-ADMIN(매트릭스 권한자)은 ADMIN 역할 대상 계정을 변경할 수 없다.
    ADMIN 계정의 pw 초기화/잠금/삭제/수정을 통한 횡적 권한 탈취를 차단한다."""
    if actor.role != "ADMIN" and target.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN role can modify an ADMIN account",
        )


def _assert_can_define_permissions(
    actor: AccountUser, *, changing_role: bool, changing_group: bool
) -> None:
    """비-ADMIN(매트릭스 권한자)은 role/group_id(권한 정의)를 변경할 수 없다.
    자기 자신을 영구 승격시키는 경로를 차단한다(한시성 복귀 보장)."""
    if actor.role != "ADMIN" and (changing_role or changing_group):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN role can change role or group assignment",
        )


async def _revoke_all_user_sessions(
    db: AsyncSession, user_id: int, reason: str, actor_id: int | None = None
) -> None:
    """FR-05 (Session Authority): 대상 사용자의 모든 활성 세션을 공통 폐기 서비스로 종료.
    access+refresh JTI 를 각 실제 exp 로 블랙리스트 + 세션 마킹. lock/reset-password 공용."""
    from app.services.session_revoke_service import revoke_session_family_async
    sessions = (await db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,  # noqa: E712
        )
    )).scalars().all()
    for s in sessions:
        await revoke_session_family_async(db, s, reason=reason, actor_id=actor_id)


@router.get("", dependencies=[Depends(require_perm_async("users", "view"))])
async def get_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(100, ge=1, le=100, description="페이지당 항목 수"),
    role: Optional[str] = Query(None, description="역할 필터"),
    group_id: Optional[int] = Query(None, description="그룹 ID 필터"),
    department: Optional[str] = Query(None, description="부서 필터"),
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
):
    """
    사용자 목록 조회

    모든 사용자 목록을 조회합니다.

    **Query Parameters**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 100, 최대: 100)
    - **role**: 역할 필터 (ADMIN, USER — v5.3 role 2종 축소)
    - **group_id**: 그룹 ID 필터
    - **department**: 부서 필터

    **Response**: success, data (사용자 목록)
    """
    stmt = select(AccountUser)

    # Apply filters
    if role:
        stmt = stmt.where(AccountUser.role == role)
    if group_id:
        stmt = stmt.where(AccountUser.group_id == group_id)
    if department:
        stmt = stmt.where(AccountUser.department == department)

    offset = (page - 1) * limit
    result = await db.execute(stmt.offset(offset).limit(limit))
    users = result.scalars().all()

    # v6.0-users_role_response_relax L2 (2026-07-06): fault-tolerant 직렬화.
    # 한 행의 스키마 위반이 목록 전체를 500 으로 만들지 않도록 skip + WARN.
    # (사건 이력: v5.3 EnumUserRole 축소 후 DB 옛 값 OPERATOR/MAINTAINER/… 잔재로 목록 500 발생)
    data = []
    for u in users:
        try:
            data.append(AccountUserResponse.model_validate(u))
        except Exception as exc:
            logger.warning(
                "[users.list] response 직렬화 실패 → 목록에서 skip: user_id=%s login_id=%r role=%r reason=%s",
                getattr(u, "id", "?"),
                getattr(u, "login_id", "?"),
                getattr(u, "role", "?"),
                exc,
            )

    return {
        "success": True,
        "data": data,
    }


@router.get("/me")
async def get_my_info(
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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

    await db.commit()
    await db.refresh(current_user)

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
        await log_action_async(
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


def _current_session_id(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    """현재 요청 Bearer 토큰의 sid(== UserSession.id) 추출. 토큰 부재/무효 시 None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return decode_token(credentials.credentials).sid
    except JWTError:
        return None


async def _invalidate_other_sessions_on_password_change(
    db: AsyncSession, user: AccountUser, current_sid: str | None
) -> int:
    """FR-SV-10: 비밀번호 변경 시 본인의 다른 활성 세션을 전부 무효화.

    각 세션의 access+refresh jti 를 블랙리스트 등록(발급된 JWT 가 exp 까지 통과하는 구멍 차단)하고
    is_active=False + logout_reason=PASSWORD_CHANGED 로 마킹한다. 현재 요청 세션(current_sid)은 보존.
    벌크 force_logout 핸들러(user_sessions.py)와 동일 패턴.

    v6.0 P8: AsyncSession 전환 — add_to_blacklist_async 사용.
    """
    stmt = select(UserSession).where(
        UserSession.user_id == user.id,
        UserSession.is_active == True,
    )
    result = await db.execute(stmt)
    active_sessions = result.scalars().all()

    count = 0
    for session in active_sessions:
        if current_sid is not None and str(session.id) == str(current_sid):
            continue  # 현재 기기 세션은 유지
        if session.token:
            try:
                td = decode_token(session.token)
                if td.jti:
                    await add_to_blacklist_async(
                        db=db, jti=td.jti,
                        expires_at=datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
                        reason="PASSWORD_CHANGED", user_id=user.id, token_type="access",
                    )
            except JWTError:
                pass
        if session.refresh_token:
            try:
                td = decode_token(session.refresh_token, expected_type="refresh")
                if td.jti:
                    await add_to_blacklist_async(
                        db=db, jti=td.jti,
                        expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS),
                        reason="PASSWORD_CHANGED", user_id=user.id, token_type="refresh",
                    )
            except JWTError:
                pass
        session.is_active = False
        session.logout_reason = "PASSWORD_CHANGED"
        session.logged_out_at = datetime.now(settings.tz).replace(tzinfo=None)
        count += 1
    return count


@router.put("/me/password")
async def change_my_password(
    password_data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
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

    **보안(FR-SV-10)**: 변경 성공 시 본인의 다른 활성 세션을 전부 무효화한다
    (access+refresh jti 블랙리스트 + 세션 비활성화). 현재 요청 세션만 유지.
    """
    # Verify current password (P4: bcrypt threadpool async)
    if not await verify_password_async(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = await hash_password_async(password_data.new_password)
    # P2-02: 비밀번호 변경 시각 기록(미갱신 필드 활성화 — 만료정책/감사 기반).
    current_user.password_changed_at = datetime.now(settings.tz).replace(tzinfo=None)

    # FR-SV-10: 비번 변경 후 본인 다른 활성 세션 무효화(타 기기 강제 재로그인). 현재 세션은 보존.
    await _invalidate_other_sessions_on_password_change(
        db, current_user, _current_session_id(credentials)
    )
    await db.commit()

    # Audit log: PASSWORD_CHANGED
    await log_action_async(
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
# 실제 이미지 포맷(Pillow magic-byte) → 확장자. content_type(클라 위조 가능) 대신 이 매핑을 신뢰한다.
IMAGE_FORMAT_TO_EXT = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "GIF": "gif"}


def _detect_image_ext(content: bytes) -> Optional[str]:
    """실제 바이트에서 이미지 포맷을 판별해 확장자를 돌려준다(위조 content_type 방어, P2).

    Pillow 로 열어 무결성(verify)까지 확인. 이미지가 아니거나 미지원 포맷이면 None.
    """
    try:
        from PIL import Image
        with Image.open(io.BytesIO(content)) as img:
            fmt = (img.format or "").upper()   # 'JPEG'/'PNG'/'WEBP'/'GIF'
            img.verify()                        # 손상/비이미지 방어
    except Exception:
        return None
    return IMAGE_FORMAT_TO_EXT.get(fmt)


def _delete_photo_file(photo_url: Optional[str]) -> None:
    """photo_url 이 서버 로컬 업로드 파일을 가리키면 해당 파일을 삭제한다(P1 orphan 정리).

    - None / 외부 URL(/api/users/photo/ 아님) / default.png → 무시(삭제 안 함)
    - traversal 방어 후 존재 시 unlink. 실패(파일 없음·권한 등)는 비치명적이라 로그만 남기고 무시.
    """
    if not photo_url:
        return
    if "/api/users/photo/" not in photo_url:   # 서버 서빙 경로가 아니면(외부 URL 등) 건드리지 않음
        return
    from app.utils.default_profile import DEFAULT_PROFILE_FILENAME
    file_name = photo_url.rstrip("/").split("/")[-1]
    if not file_name or file_name == DEFAULT_PROFILE_FILENAME:   # default 는 공유 자원 → 보존
        return
    if "/" in file_name or "\\" in file_name or ".." in file_name:   # traversal 방어
        return
    file_path = os.path.join(settings.PROFILE_STORAGE_PATH, file_name)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        logger.warning("프로필 사진 파일 삭제 실패(무시): %s (%s)", file_path, e)


async def _save_profile_photo(user: AccountUser, file: UploadFile, request: Request, db: AsyncSession):
    """업로드 파일 검증 → data/profiles 저장 → user.photo_url(절대 URL) 갱신. (본인/admin 공통)

    v6.3-profile_photo_crud: content_type 대신 실제 이미지 magic-byte(P2)로 검증하고,
    재업로드 시 옛 파일을 orphan 으로 남기지 않고 제거(P1)한다.
    """
    # 크기 선검사(헤더 제공 시) → 전량 read → 재확인 (헤더 미제공 대비)
    if file.size is not None and file.size > MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {file.size} bytes (max {MAX_PHOTO_BYTES})",
        )
    content = await file.read()
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {len(content)} bytes (max {MAX_PHOTO_BYTES})",
        )
    # P2: content_type(클라 위조 가능) 이 아닌 실제 바이트로 포맷 판별
    ext = _detect_image_ext(content)
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported or invalid image (declared content_type: {file.content_type}). "
                f"Allowed: {', '.join(ALLOWED_PHOTO_MIME)}"
            ),
        )
    os.makedirs(settings.PROFILE_STORAGE_PATH, exist_ok=True)
    old_url = user.photo_url   # 교체 전 값 — 커밋 성공 후 orphan 제거용
    file_name = f"{user.id}_{uuid.uuid4().hex[:8]}.{ext}"   # uuid 파일명 — traversal/충돌 방지
    file_path = os.path.join(settings.PROFILE_STORAGE_PATH, file_name)
    with open(file_path, "wb") as f:
        f.write(content)
    # 절대 URL — photo_url 검증기(http(s) 허용) 통과 + 클라 ImageConverter(C1) 직접 렌더
    user.photo_url = f"{str(request.base_url).rstrip('/')}/api/users/photo/{file_name}"
    await db.commit()
    await db.refresh(user)
    # P1: 신규 저장이 확정된 뒤에만 옛 파일 제거. default/외부/동일 URL 은 helper 가 걸러냄.
    if old_url and old_url != user.photo_url:
        _delete_photo_file(old_url)
    return {"success": True, "message": "Profile photo uploaded", "data": AccountUserResponse.model_validate(user)}


@router.post("/me/photo", summary="본인 프로필 사진 업로드")
async def upload_my_photo(
    request: Request,
    file: UploadFile = File(..., description="이미지 파일 (jpeg/png/webp/gif, ≤5MB)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
):
    """본인 프로필 사진 업로드 → data/profiles/ 저장 + photo_url(DB) 갱신."""
    return await _save_profile_photo(current_user, file, request, db)


@router.delete("/me/photo", summary="본인 프로필 사진 삭제")
async def delete_my_photo(
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
):
    """본인 프로필 사진 삭제 → data/profiles 파일 제거 + photo_url=None (v6.3-profile_photo_crud, P1-D).

    응답 스키마가 photo_url null 을 default 이미지 URL(/api/users/photo/default.png)로 채우므로,
    삭제 후 사용자는 자동으로 default 아바타로 복귀한다. 사진이 없어도 200(idempotent).
    """
    old_url = current_user.photo_url
    current_user.photo_url = None
    await db.commit()
    await db.refresh(current_user)
    # DB 반영 뒤 파일 정리. default/외부/None 은 helper 가 무시.
    _delete_photo_file(old_url)
    return {
        "success": True,
        "message": "Profile photo deleted",
        "data": AccountUserResponse.model_validate(current_user),
    }


@router.get("/photo/{file_name}", summary="프로필 사진 다운로드(파일명 기반)")
async def get_profile_photo(file_name: str):
    """data/profiles/{file_name} 이미지 바이너리 반환. 인증 불필요(파일명 uuid라 비공개성 확보).

    v6.0-default_profile_image (2026-07-07): 파일이 없으면 404 대신 default 이미지를 반환한다.
    - 응답 스키마가 photo_url null → '/api/users/photo/default.png' 로 채우므로 이 경로가 default 서빙.
    - 개인 사진 파일이 (볼륨 이슈 등으로) 사라져도 깨진 이미지 대신 default 노출.
    """
    from app.utils.default_profile import DEFAULT_PROFILE_FILENAME, ensure_default_profile_image

    if "/" in file_name or "\\" in file_name or ".." in file_name:   # 경로 traversal 차단
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name")
    file_path = os.path.join(settings.PROFILE_STORAGE_PATH, file_name)
    if not os.path.exists(file_path):
        # default 로 폴백 (없으면 즉석 생성 시도)
        default_path = os.path.join(settings.PROFILE_STORAGE_PATH, DEFAULT_PROFILE_FILENAME)
        if not os.path.exists(default_path):
            ensure_default_profile_image(settings.PROFILE_STORAGE_PATH)
        if os.path.exists(default_path):
            return FileResponse(path=default_path, media_type="image/png")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found")
    return FileResponse(path=file_path)


# ── 관리자: 대상 계정 프로필 사진 (v6.3-admin_photo_upload) ────────────────────
# 본인 경로(/me/photo)를 타 계정 편집에 재사용하다 토큰 소유자(로그인 관리자) 사진이
# 오염되던 사고(2026-07-13) 대응. 관리자 CRUD 는 반드시 {user_id} 대상을 향한다.
# require_perm(users:edit) + base-ADMIN 상승 가드(비-ADMIN 의 ADMIN 대상 변경 차단).
# ★ 라우트 순서: 위 리터럴 /me/photo · /photo/{file_name} 뒤, /{user_id} 앞에 등록 —
#   2세그먼트 경로라 단일세그먼트 /{user_id} 와 미충돌, /me/photo 가 먼저라 그림자화 없음.
@router.post(
    "/{user_id}/photo",
    dependencies=[Depends(require_perm_async("users", "edit"))],
    summary="관리자: 대상 계정 프로필 사진 업로드",
)
async def upload_user_photo(
    user_id: int,
    request: Request,
    file: UploadFile = File(..., description="이미지 파일 (jpeg/png/webp/gif, ≤5MB)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
):
    """관리자(권한자)가 **대상 계정**의 프로필 사진을 업로드/교체한다.

    저장/검증/orphan 정리는 본인 경로와 동일한 `_save_profile_photo`(magic-byte·5MB·orphan)를
    재사용하되 대상은 `{user_id}`. 감사에는 행위자(관리자)와 대상을 분리 기록해 추적성을 확보한다.
    """
    target = (await db.execute(
        select(AccountUser).where(AccountUser.id == user_id)
    )).scalars().first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # base-ADMIN 상승 가드 — 비-ADMIN 은 ADMIN 대상 사진 변경 불가(횡적 권한 탈취 차단)
    _assert_can_modify_admin_target(current_user, target)
    resp = await _save_profile_photo(target, file, request, db)
    # 감사: 행위자(관리자) ≠ 대상 을 명시 기록 (2026-07-13 오염사고 추적성)
    await log_action_async(
        db=db,
        action_type="USER_PHOTO_CHANGED",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=target.id,
        resource_name=f"{target.name} ({target.login_id})",
        description=f"프로필 사진 변경(관리자): {target.login_id} (by {current_user.login_id})",
    )
    return resp


@router.delete(
    "/{user_id}/photo",
    dependencies=[Depends(require_perm_async("users", "edit"))],
    summary="관리자: 대상 계정 프로필 사진 삭제",
)
async def delete_user_photo(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
):
    """관리자가 대상 계정의 프로필 사진을 삭제한다(default 복귀, idempotent)."""
    target = (await db.execute(
        select(AccountUser).where(AccountUser.id == user_id)
    )).scalars().first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _assert_can_modify_admin_target(current_user, target)
    old_url = target.photo_url
    target.photo_url = None
    await db.commit()
    await db.refresh(target)
    _delete_photo_file(old_url)   # DB 반영 뒤 파일 정리 (default/외부/None 은 helper 가 무시)
    await log_action_async(
        db=db,
        action_type="USER_PHOTO_DELETED",
        resource_type="USER",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=target.id,
        resource_name=f"{target.name} ({target.login_id})",
        description=f"프로필 사진 삭제(관리자): {target.login_id} (by {current_user.login_id})",
    )
    return {
        "success": True,
        "message": "Profile photo deleted",
        "data": AccountUserResponse.model_validate(target),
    }


@router.get("/{user_id}", dependencies=[Depends(require_perm_async("users", "view"))])
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    result = await db.execute(select(AccountUser).where(AccountUser.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "data": AccountUserResponse.model_validate(user)
    }


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm_async("users", "edit"))])
async def create_user(
    user_data: AccountUserCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    - **role**: 역할 (선택, 기본값: USER — v5.3 role 2종 축소)
    - **group_id**: 그룹 ID (선택)

    **Response**: success, data (생성된 사용자 정보)

    **Error**:
    - 400: 중복된 login_id
    """
    # v6.x 권한정의 가드: 비-ADMIN 은 role(≠USER)·group_id 지정 불가 (한시 승격 자가영구화 차단)
    _assert_can_define_permissions(
        current_user,
        changing_role=(user_data.role is not None and user_data.role != "USER"),
        changing_group=(user_data.group_id is not None),
    )

    # Check for duplicate login_id
    existing = (await db.execute(
        select(AccountUser).where(AccountUser.login_id == user_data.login_id)
    )).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="login_id already exists"
        )

    # Validate group_id if provided
    if user_data.group_id:
        group = (await db.execute(
            select(UserGroup).where(UserGroup.id == user_data.group_id)
        )).scalars().first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="group_id does not exist"
            )

    # Create new user (P4: bcrypt threadpool async)
    new_user = AccountUser(
        login_id=user_data.login_id,
        password_hash=await hash_password_async(user_data.password),
        name=user_data.name,
        email=user_data.email,
        department=user_data.department,
        position=user_data.position,
        employee_number=user_data.employee_number,
        photo_url=user_data.photo_url,
        phone=user_data.phone,
        # v6.0-clone_deploy_bugfix (#1): 기본값 VIEWER → USER (v5.3 role 2분화 정책 정합).
        # 세부 권한은 group_id 매트릭스로 부여. VIEWER 는 v5.3에서 폐지된 레거시 값.
        role=user_data.role or "USER",
        group_id=user_data.group_id,
        is_active=True,
        is_locked=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Audit log: USER_CREATED
    await log_action_async(
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


@router.put("/{user_id}", dependencies=[Depends(require_perm_async("users", "edit"))])
async def update_user(
    user_id: int,
    user_data: AccountUserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    # v5.1 FR-SV-06: 마지막 ADMIN 원자 가드 — ADMIN 강등 또는 비활성화 시 잔여 ADMIN >=1 보장.
    user = (await db.execute(
        select(AccountUser).where(AccountUser.id == user_id).with_for_update()
    )).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # v6.x 가드: 비-ADMIN 은 ADMIN 대상 수정 불가 + role/group 변경 불가
    _assert_can_modify_admin_target(current_user, user)
    _provided = user_data.model_fields_set
    _assert_can_define_permissions(
        current_user,
        changing_role=("role" in _provided and user_data.role is not None),
        changing_group=("group_id" in _provided),
    )

    # ADMIN 강등(role 변경) 또는 비활성화 시도 검사 (자기 자신 포함)
    is_admin_demotion = (
        user.role == "ADMIN" and
        ((user_data.role is not None and user_data.role != "ADMIN") or
         (user_data.is_active is not None and user_data.is_active == False))
    )
    if is_admin_demotion:
        active_admins = (await db.execute(
            select(AccountUser).where(
                AccountUser.role == "ADMIN",
                AccountUser.is_active == True
            ).with_for_update()
        )).scalars().all()
        if len(active_admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot demote/deactivate the last ADMIN user (at least one active ADMIN must remain)"
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

    # v5.4 클라 지적 P0-B: 요청 body에 포함된 필드는 값이 null 이어도 반영(해제 지원).
    # `is not None` → `field in model_fields_set` 로 변경 → 명시적 null 처리 활성.
    # 특히 group_id=null: 구성원 그룹 해제 (기존 is_not_none 필터로 no-op였음).
    provided = user_data.model_fields_set
    if "name" in provided:
        user.name = user_data.name
    if "email" in provided:
        user.email = user_data.email
    if "department" in provided:
        user.department = user_data.department
    if "position" in provided:
        user.position = user_data.position
    if "employee_number" in provided:
        user.employee_number = user_data.employee_number
    if "photo_url" in provided:
        user.photo_url = user_data.photo_url
    if "phone" in provided:
        user.phone = user_data.phone
    if "role" in provided and user_data.role is not None:
        # role은 null 허용 안 함 (EnumUserRole 강제 — v5.4 P0-2)
        user.role = user_data.role
    if "group_id" in provided:
        # v5.4 P0-B: null 허용 → 그룹 해제
        user.group_id = user_data.group_id
    if "is_active" in provided and user_data.is_active is not None:
        # is_active는 null 허용 안 함 (Boolean 강제)
        user.is_active = user_data.is_active

    await db.commit()
    await db.refresh(user)

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
    await log_action_async(
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


@router.delete("/{user_id}", dependencies=[Depends(require_perm_async("users", "delete"))])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    # v5.1 FR-SV-06 (PRD_GOP_Server_RBAC_Enforcement): 마지막 ADMIN 원자 가드.
    # FOR UPDATE 행 잠금으로 TOCTOU 차단 — 동시에 두 ADMIN을 삭제해도 마지막 1명은 보존.
    # PostgreSQL: FOR UPDATE + count()는 비호환 → .all() + len() 패턴 사용.
    user = (await db.execute(
        select(AccountUser).where(AccountUser.id == user_id).with_for_update()
    )).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # v6.x 가드: 비-ADMIN 은 ADMIN 대상 삭제 불가
    _assert_can_modify_admin_target(current_user, user)

    # 삭제 대상이 ADMIN이면 잔여 ADMIN 수 확인 (자기 자신 포함된 잠금 상태에서 fetch)
    if user.role == "ADMIN":
        active_admins = (await db.execute(
            select(AccountUser).where(
                AccountUser.role == "ADMIN",
                AccountUser.is_active == True
            ).with_for_update()
        )).scalars().all()
        if len(active_admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete the last ADMIN user (at least one ADMIN must remain)"
            )

    # Capture user info before deletion (snapshot)
    deleted_user_id = user.id
    deleted_user_name = f"{user.name} ({user.login_id})"
    deleted_login_id = user.login_id

    await db.delete(user)
    await db.commit()

    # Audit log: USER_DELETED (after delete, preserve snapshot)
    await log_action_async(
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


@router.post("/{user_id}/lock", dependencies=[Depends(require_perm_async("users", "control"))])
async def lock_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    # ACC-P1-08: 마지막 활성 ADMIN lockout 방지 — 잠금은 계정을 사용 불가로 만드므로
    # 삭제/강등과 동일하게 마지막 ADMIN 보존이 필요. FOR UPDATE 로 TOCTOU 차단.
    user = (await db.execute(
        select(AccountUser).where(AccountUser.id == user_id).with_for_update()
    )).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # v6.x 가드: 비-ADMIN 은 ADMIN 대상 잠금 불가
    _assert_can_modify_admin_target(current_user, user)

    # ACC-P1-08: 대상이 현재 사용 가능한(active·unlocked) ADMIN 이면, 잠금 후 잔여 사용가능 ADMIN >=1 보장.
    if user.role == "ADMIN" and user.is_active and not user.is_locked:
        usable_admins = (await db.execute(
            select(AccountUser).where(
                AccountUser.role == "ADMIN",
                AccountUser.is_active == True,   # noqa: E712
                AccountUser.is_locked == False,  # noqa: E712
            ).with_for_update()
        )).scalars().all()
        if len(usable_admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot lock the last usable ADMIN user (at least one active, unlocked ADMIN must remain)"
            )

    user.is_locked = True
    # P2-02: 잠금 수행자 기록(누가 잠갔는지 감사).
    user.locked_by = current_user.id
    user.locked_at = datetime.now(settings.tz).replace(tzinfo=None)

    # FR-05 (Session Authority): 활성 세션의 token family(access+refresh) 를 공통 서비스로 폐기.
    # 기존엔 is_active=false 만 했음 → refresh 토큰이 살아 있어 unlock 후 부활 가능했음.
    await _revoke_all_user_sessions(db, user_id, reason="ACCOUNT_LOCKED", actor_id=current_user.id)

    # Create system event for user lock (SECURITY_ALERT: USER_* moved to UserLoginLog per PRD_SystemEvent_Sync.md)
    system_event = SystemEvent(
        type_event=EnumSystemEventType.SECURITY_ALERT,
        severity=EnumSystemEventSeverity.WARNING,
        title=f"사용자 계정 잠금: {user.login_id}",
        message=f"사용자 '{user.name}' ({user.login_id})의 계정이 잠금되었습니다.",
        source="user_api"
    )
    db.add(system_event)

    await db.commit()

    # Audit log: USER_LOCKED
    await log_action_async(
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


@router.post("/{user_id}/unlock", dependencies=[Depends(require_perm_async("users", "control"))])
async def unlock_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    user = (await db.execute(
        select(AccountUser).where(AccountUser.id == user_id)
    )).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # v6.x 가드: 비-ADMIN 은 ADMIN 대상 잠금해제 불가
    _assert_can_modify_admin_target(current_user, user)

    user.is_locked = False
    # ㉱ 해제 시 실패 카운트·잠금시각·사유도 리셋 — 안 하면 해제 직후 1회 실패로 즉시 재잠금(재잠금 트랩).
    user.failed_login_count = 0
    user.locked_at = None
    user.lock_reason = None

    # Create system event for user unlock (SECURITY_ALERT: USER_* moved to UserLoginLog per PRD_SystemEvent_Sync.md)
    system_event = SystemEvent(
        type_event=EnumSystemEventType.SECURITY_ALERT,
        severity=EnumSystemEventSeverity.INFO,
        title=f"사용자 계정 잠금 해제: {user.login_id}",
        message=f"사용자 '{user.name}' ({user.login_id})의 계정 잠금이 해제되었습니다.",
        source="user_api"
    )
    db.add(system_event)

    await db.commit()

    # Audit log: USER_UNLOCKED
    await log_action_async(
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


@router.post("/{user_id}/reset-password", dependencies=[Depends(require_perm_async("users", "edit"))])
async def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async)
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
    user = (await db.execute(
        select(AccountUser).where(AccountUser.id == user_id)
    )).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # v6.x 가드: 비-ADMIN 은 ADMIN 대상 비밀번호 초기화 불가 (횡적 탈취 차단)
    _assert_can_modify_admin_target(current_user, user)

    # P4: bcrypt threadpool async
    user.password_hash = await hash_password_async(password_data.new_password)
    # P2-02: 비밀번호 변경 시각 기록.
    user.password_changed_at = datetime.now(settings.tz).replace(tzinfo=None)

    # FR-05 (Session Authority): 관리자 비밀번호 초기화 시 대상의 모든 활성 세션 token family 폐기.
    # 기존엔 세션을 안 건드려 초기화 후에도 이전 토큰이 유효했음(A07).
    await _revoke_all_user_sessions(db, user.id, reason="PASSWORD_RESET", actor_id=current_user.id)
    await db.commit()

    # Audit log: PASSWORD_RESET
    await log_action_async(
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
