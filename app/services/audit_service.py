"""
Audit Service for logging user activities
PRD: PRD_Audit_Log.md v1.0
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


# Sensitive fields to remove from changes
SENSITIVE_FIELDS = {"password", "hashed_password", "token", "secret"}


def get_changes(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    두 dict를 비교하여 변경된 필드만 추출합니다.

    Args:
        before: 변경 전 상태 dict
        after: 변경 후 상태 dict

    Returns:
        {"before": {변경된 필드들}, "after": {변경된 필드들}}
    """
    before_changes = {}
    after_changes = {}

    # 모든 키를 합집합으로 가져옴
    all_keys = set(before.keys()) | set(after.keys())

    for key in all_keys:
        before_val = before.get(key)
        after_val = after.get(key)

        if before_val != after_val:
            if key in before:
                before_changes[key] = before_val
            if key in after:
                after_changes[key] = after_val

    return {"before": before_changes, "after": after_changes}


def sanitize_changes(changes: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    변경 내역에서 민감한 정보를 제거합니다.

    Args:
        changes: {"before": {...}, "after": {...}} 형태의 변경 내역

    Returns:
        민감정보가 제거된 변경 내역
    """
    result = {"before": {}, "after": {}}

    for key in ["before", "after"]:
        if key in changes and changes[key]:
            result[key] = {
                k: v for k, v in changes[key].items()
                if k not in SENSITIVE_FIELDS
            }

    return result


async def log_action(
    db: Session,
    action_type: str,
    resource_type: str,
    actor_login_id: str,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    actor_role: Optional[str] = None,
    resource_id: Optional[int] = None,
    resource_name: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    action_status: str = "SUCCESS",
    error_message: Optional[str] = None
) -> AuditLog:
    """
    감사 로그를 생성합니다.

    Args:
        db: 데이터베이스 세션
        action_type: 행위 유형 (EnumAuditActionType)
        resource_type: 대상 리소스 유형 (EnumAuditResourceType)
        actor_login_id: 행위자 로그인 ID
        actor_id: 행위자 ID (FK)
        actor_name: 행위자 이름
        actor_role: 행위자 역할
        resource_id: 대상 리소스 ID
        resource_name: 대상 리소스 이름
        changes: 변경 내역 {before: {...}, after: {...}}
        description: 활동 설명
        ip_address: 클라이언트 IP 주소
        user_agent: 클라이언트 User-Agent
        action_status: 행위 결과 (SUCCESS, FAILURE)
        error_message: 오류 메시지 (실패 시)

    Returns:
        생성된 AuditLog 객체
    """
    # 민감 정보 제거
    sanitized_changes = sanitize_changes(changes) if changes else None

    audit_log = AuditLog(
        action_type=action_type,
        action_status=action_status,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        actor_id=actor_id,
        actor_login_id=actor_login_id,
        actor_name=actor_name,
        actor_role=actor_role,
        changes=sanitized_changes,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        error_message=error_message
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log
