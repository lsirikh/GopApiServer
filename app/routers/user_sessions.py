"""
UserSession API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from app.dependencies import get_db
from app.models.user import UserSession, AccountUser, UserLoginLog
from app.schemas.user import UserSessionResponse
from app.routers.auth import get_current_account_user, require_admin
from app.services.audit_service import log_action

router = APIRouter(tags=["User Sessions"])


def _session_to_response(session: UserSession) -> dict:
    """
    Convert UserSession to response dict with login_id and role from related user.
    US-3: PRD_UserSession_Improvement.md - JOIN 필드 추가
    """
    response = {
        "id": session.id,
        "user_id": session.user_id,
        "login_id": session.user.login_id if session.user else None,
        "role": session.user.role if session.user else None,
        "ip_address": session.ip_address,
        "user_agent": session.user_agent,
        "expires_at": session.expires_at,
        "is_active": session.is_active,
        "logout_reason": session.logout_reason,
        "logged_out_at": session.logged_out_at,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
    return response


@router.get("", dependencies=[Depends(require_admin)])
async def get_user_sessions(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(100, ge=1, le=100, description="페이지당 항목 수"),
    is_active: Optional[bool] = Query(None, description="활성화 상태 필터"),
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 세션 목록 조회

    모든 사용자 세션 목록을 조회합니다.

    **Query Parameters**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 100, 최대: 100)
    - **is_active**: 활성화 상태 필터

    **Response**: success, data (세션 목록)
    """
    # Use joinedload for eager loading of user relationship (US-3: JOIN)
    query = db.query(UserSession).options(joinedload(UserSession.user))

    # Apply filters
    if is_active is not None:
        query = query.filter(UserSession.is_active == is_active)

    offset = (page - 1) * limit
    sessions = query.order_by(UserSession.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "success": True,
        "data": [_session_to_response(session) for session in sessions]
    }


@router.delete("/user/{user_id}", dependencies=[Depends(require_admin)])
async def force_logout_all_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    특정 사용자의 모든 세션 강제 로그아웃

    특정 사용자의 모든 활성 세션을 강제 로그아웃합니다.

    **Path Parameters**:
    - **user_id**: 사용자 ID

    **Response**: success, data (종료된 세션 수)

    **Error**:
    - 404: 사용자를 찾을 수 없음
    """
    from datetime import datetime
    from app.config import settings

    # Verify user exists
    target_user = db.query(AccountUser).filter(AccountUser.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get all active sessions for the user
    active_sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).all()

    # v5.1 FR-SV-01: 벌크 force_logout 시 각 세션의 access+refresh jti 블랙리스트 등록
    # — is_active=False 만으로는 발급된 JWT가 exp(24h)까지 통과해 강제 로그아웃 실효 없음.
    # 단건(/{session_id}) 핸들러와 동일 패턴(commit 980abbc).
    from jose import JWTError
    from app.utils.auth import decode_token as _decode
    from app.services.token_blacklist_service import add_to_blacklist
    from datetime import timedelta as _td

    count = 0
    for session in active_sessions:
        session.is_active = False
        session.logout_reason = "FORCED"
        session.forced_by = current_user.id
        session.logged_out_at = datetime.now(settings.tz).replace(tzinfo=None)

        # access jti 블랙리스트 — v5.2 hotfix: expires_in(부재) → expires_at(시그니처 일치)
        # 단건 핸들러(L362) 패턴과 동일하게 settings TTL 사용.
        if session.token:
            try:
                td = _decode(session.token)
                if td.jti:
                    add_to_blacklist(
                        db=db,
                        jti=td.jti,
                        expires_at=datetime.utcnow() + _td(hours=settings.JWT_EXPIRATION_HOURS),
                        reason="FORCE_LOGOUT_BULK",
                        user_id=user_id,
                        token_type="access",
                    )
            except JWTError:
                pass
        # refresh jti 블랙리스트 — refresh는 expected_type 명시
        if session.refresh_token:
            try:
                td = _decode(session.refresh_token, expected_type="refresh")
                if td.jti:
                    add_to_blacklist(
                        db=db,
                        jti=td.jti,
                        expires_at=datetime.utcnow() + _td(days=settings.JWT_REFRESH_EXPIRATION_DAYS),
                        reason="FORCE_LOGOUT_BULK",
                        user_id=user_id,
                        token_type="refresh",
                    )
            except JWTError:
                pass

        # Create a login log entry for each force logout
        log_entry = UserLoginLog(
            user_id=user_id,
            login_id=target_user.login_id,
            action="FORCE_LOGOUT",
            result="SUCCESS",
            ip_address=session.ip_address
        )
        db.add(log_entry)
        count += 1

    db.commit()

    # 감사 로그 기록: SESSION_FORCED_LOGOUT (전체 세션)
    if count > 0:
        await log_action(
            db=db,
            action_type="SESSION_FORCED_LOGOUT",
            resource_type="USER_SESSION",
            actor_login_id=current_user.login_id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            resource_id=user_id,
            resource_name=f"{target_user.name} ({target_user.login_id}) - {count}개 세션",
            description=f"전체 세션 강제 로그아웃: {target_user.login_id} ({count}개)"
        )

    return {
        "success": True,
        "message": f"User {user_id} sessions force-logged-out ({count} terminated)",
        "data": None
    }


@router.get("/me")
async def get_my_sessions(
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    내 세션 목록 조회

    현재 로그인한 사용자의 모든 세션 목록을 조회합니다.

    **Response**: success, data (세션 목록)
    """
    # Use joinedload for eager loading of user relationship (US-3: JOIN)
    sessions = db.query(UserSession).options(joinedload(UserSession.user)).filter(
        UserSession.user_id == current_user.id
    ).order_by(UserSession.created_at.desc()).all()

    return {
        "success": True,
        "data": [_session_to_response(session) for session in sessions]
    }


@router.delete("/me/{session_id}")
async def delete_my_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    내 다른 세션 종료

    현재 로그인한 사용자의 다른 세션을 종료합니다.

    **Path Parameters**:
    - **session_id**: 세션 ID

    **Response**: success: true

    **Error**:
    - 404: 세션을 찾을 수 없거나 내 세션이 아님
    """
    from datetime import datetime
    from app.config import settings

    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or not your session"
        )

    session.is_active = False
    session.logout_reason = "SELF_LOGOUT"
    session.logged_out_at = datetime.now(settings.tz)

    db.commit()

    # 감사 로그 기록: SESSION_TERMINATED (자기 세션 종료)
    await log_action(
        db=db,
        action_type="SESSION_TERMINATED",
        resource_type="USER_SESSION",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=session_id,
        resource_name=f"Session {session_id} ({current_user.login_id})",
        description=f"내 세션 종료: {current_user.login_id}"
    )

    return {
        "success": True,
        "message": f"My session {session_id} terminated successfully",
        "data": None
    }


@router.get("/{session_id}", dependencies=[Depends(require_admin)])
async def get_user_session_by_id(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 세션 상세 조회

    ID로 사용자 세션 정보를 조회합니다.

    **Path Parameters**:
    - **session_id**: 세션 ID

    **Response**: success, data (세션 정보)

    **Error**:
    - 404: 세션을 찾을 수 없음
    """
    # Use joinedload for eager loading of user relationship (US-3: JOIN)
    session = db.query(UserSession).options(joinedload(UserSession.user)).filter(
        UserSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User session not found"
        )

    return {
        "success": True,
        "data": _session_to_response(session)
    }


@router.delete("/{session_id}", dependencies=[Depends(require_admin)])
async def force_logout_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user)
):
    """
    사용자 세션 강제 로그아웃

    특정 세션을 강제 로그아웃합니다.

    **Path Parameters**:
    - **session_id**: 세션 ID

    **Response**: success: true

    **Error**:
    - 404: 세션을 찾을 수 없음
    """
    from datetime import datetime
    from app.config import settings

    session = db.query(UserSession).filter(UserSession.id == session_id).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User session not found"
        )

    # Get the user who owns this session (for logging)
    session_user = db.query(AccountUser).filter(AccountUser.id == session.user_id).first()

    # Force logout the session
    session.is_active = False
    session.logout_reason = "FORCED"
    session.forced_by = current_user.id
    session.logged_out_at = datetime.now(settings.tz)

    # ★ 토큰 즉시 무효화 — is_active=False 만으로는 이미 발급된 JWT가 exp(24h)까지 통과하여
    #    강제 로그아웃이 실효 없음. access + refresh jti 를 블랙리스트에 등록해야:
    #    (1) 그 토큰으로의 모든 요청 → 401 "Token has been revoked"
    #    (2) refresh 도 거부(refresh 가 is_blacklisted 검사) → 클라가 재발급 못 받고 SessionExpired → 로그아웃.
    from jose import JWTError
    from app.utils.auth import decode_token as _decode
    from app.services.token_blacklist_service import add_to_blacklist
    from datetime import timedelta as _td
    if session.token:
        try:
            _at = _decode(session.token)
            if _at.jti:
                add_to_blacklist(db=db, jti=_at.jti,
                                 expires_at=datetime.utcnow() + _td(hours=settings.JWT_EXPIRATION_HOURS),
                                 reason="FORCED", user_id=session.user_id, token_type="access")
        except JWTError:
            pass
    if session.refresh_token:
        try:
            _rt = _decode(session.refresh_token, expected_type="refresh")
            if _rt.jti:
                add_to_blacklist(db=db, jti=_rt.jti,
                                 expires_at=datetime.utcnow() + _td(days=settings.JWT_REFRESH_EXPIRATION_DAYS),
                                 reason="FORCED", user_id=session.user_id, token_type="refresh")
        except JWTError:
            pass

    # Create a login log entry for the force logout
    log_entry = UserLoginLog(
        user_id=session.user_id,
        login_id=session_user.login_id if session_user else "unknown",
        action="FORCE_LOGOUT",
        result="SUCCESS",
        ip_address=session.ip_address
    )
    db.add(log_entry)

    # Create a system event for the force logout
    from app.models.system_event import SystemEvent
    from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity

    # SECURITY_ALERT: SESSION_FORCED_LOGOUT moved to UserLoginLog per PRD_SystemEvent_Sync.md
    system_event = SystemEvent(
        type_event=EnumSystemEventType.SECURITY_ALERT,
        severity=EnumSystemEventSeverity.WARNING,
        title=f"Session forced logout: {session_user.login_id if session_user else 'unknown'}",
        message=f"Session {session_id} was forcefully terminated by {current_user.login_id}",
        detail={
            "session_id": session_id,
            "user_id": session.user_id,
            "forced_by_id": current_user.id,
            "forced_by_login_id": current_user.login_id,
            "ip_address": session.ip_address
        },
        source="user_sessions_api"
    )
    db.add(system_event)

    db.commit()

    # 감사 로그 기록: SESSION_FORCED_LOGOUT
    await log_action(
        db=db,
        action_type="SESSION_FORCED_LOGOUT",
        resource_type="USER_SESSION",
        actor_login_id=current_user.login_id,
        actor_id=current_user.id,
        actor_name=current_user.name,
        actor_role=current_user.role,
        resource_id=session_id,
        resource_name=f"Session {session_id} ({session_user.login_id if session_user else 'unknown'})",
        description=f"세션 강제 로그아웃: {session_user.login_id if session_user else 'unknown'}"
    )

    return {
        "success": True,
        "message": f"Session {session_id} force-logged-out successfully",
        "data": None
    }
