"""
UserSession API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.models.user import UserSession, AccountUser, UserLoginLog
from app.schemas.user import UserSessionResponse
from app.routers.auth import get_current_account_user

router = APIRouter(tags=["User Sessions"])


@router.get("")
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
    query = db.query(UserSession)

    # Apply filters
    if is_active is not None:
        query = query.filter(UserSession.is_active == is_active)

    offset = (page - 1) * limit
    sessions = query.order_by(UserSession.login_at.desc()).offset(offset).limit(limit).all()

    return {
        "success": True,
        "data": [UserSessionResponse.model_validate(session) for session in sessions]
    }


@router.delete("/user/{user_id}")
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

    count = 0
    for session in active_sessions:
        session.is_active = False
        session.logout_reason = "FORCED"
        session.forced_by = current_user.id
        session.logged_out_at = datetime.now(settings.tz)

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

    return {
        "success": True,
        "data": {"count": count}
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
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).order_by(UserSession.login_at.desc()).all()

    return {
        "success": True,
        "data": [UserSessionResponse.model_validate(session) for session in sessions]
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

    return {"success": True}


@router.get("/{session_id}")
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
    session = db.query(UserSession).filter(UserSession.id == session_id).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User session not found"
        )

    return {
        "success": True,
        "data": UserSessionResponse.model_validate(session)
    }


@router.delete("/{session_id}")
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

    system_event = SystemEvent(
        type_event=EnumSystemEventType.SESSION_FORCED_LOGOUT,
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

    return {"success": True}
