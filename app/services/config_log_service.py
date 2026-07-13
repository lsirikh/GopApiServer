"""
Config Change Log Service for tracking configuration changes
PRD: PRD_ConfigChangeLog.md v1.1

v6.0 P6 후속: sync/async dual-stack (log_config_change_async 신설).
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config_change_log import ConfigChangeLog
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType


def get_changed_fields(before: Dict[str, Any], after: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    두 dict를 비교하여 변경된 필드만 추출합니다. (v1.1)

    PRD Reference: PRD_ConfigChangeLog.md v1.1 Section 3.3, 6.1

    Args:
        before: 변경 전 상태 dict
        after: 변경 후 상태 dict

    Returns:
        (변경된 before 필드, 변경된 after 필드) 튜플
    """
    before_changes = {}
    after_changes = {}

    all_keys = set(before.keys()) | set(after.keys())

    for key in all_keys:
        before_val = before.get(key)
        after_val = after.get(key)

        if before_val != after_val:
            if key in before:
                before_changes[key] = before_val
            if key in after:
                after_changes[key] = after_val

    return before_changes, after_changes


def get_identifier(model: Any) -> Dict[str, Any]:
    """
    모델의 식별 정보(id, name)만 추출합니다. (v1.1)

    PRD Reference: PRD_ConfigChangeLog.md v1.1 Section 3.3, 6.1

    Args:
        model: SQLAlchemy 모델 인스턴스

    Returns:
        {"id": ..., "name": ...} 형태의 dict (name이 없으면 id만 반환)
    """
    result = {"id": model.id}

    # name 필드 탐색 (name, name_device, title 순서)
    for attr in ["name", "name_device", "title"]:
        if hasattr(model, attr):
            value = getattr(model, attr)
            if value is not None:
                result["name"] = value
                break

    return result


def model_to_dict(model: Any) -> Dict[str, Any]:
    """
    SQLAlchemy 모델을 dict로 변환합니다.
    datetime은 ISO 문자열로, Enum은 문자열로 변환합니다.
    상속된 모델의 경우 모든 컬럼(부모 포함)을 포함합니다.

    Args:
        model: SQLAlchemy 모델 인스턴스

    Returns:
        모델의 컬럼 값을 담은 dict
    """
    from sqlalchemy import inspect
    from sqlalchemy.exc import NoInspectionAvailable
    result = {}

    try:
        # SQLAlchemy 모델: 상속된 모델도 포함하여 모든 컬럼 가져오기
        mapper = inspect(model.__class__)
        for column in mapper.columns:
            value = getattr(model, column.key, None)

            # datetime 처리
            if isinstance(value, datetime):
                result[column.key] = value.isoformat()
            # Enum 처리
            elif isinstance(value, Enum):
                result[column.key] = value.value
            else:
                result[column.key] = value
    except NoInspectionAvailable:
        # Mock 객체 또는 비-SQLAlchemy 모델: __table__ 사용
        for column in model.__table__.columns:
            value = getattr(model, column.name, None)

            # datetime 처리
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            # Enum 처리
            elif isinstance(value, Enum):
                result[column.name] = value.value
            else:
                result[column.name] = value

    return result


def log_config_change(
    db: Session,
    resource_type: EnumConfigResourceType,
    resource_id: int,
    action: EnumConfigActionType,
    resource_name: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    actor_ip: Optional[str] = None,
    description: Optional[str] = None
) -> ConfigChangeLog:
    """
    설정 변경 로그를 생성합니다.

    Args:
        db: 데이터베이스 세션
        resource_type: 리소스 유형 (EnumConfigResourceType)
        resource_id: 리소스 ID
        action: 변경 액션 (EnumConfigActionType)
        resource_name: 리소스 이름 (표시용)
        before_state: 변경 전 상태 dict
        after_state: 변경 후 상태 dict
        actor_id: 수행자 ID (FK)
        actor_name: 수행자 이름
        actor_ip: 수행자 IP 주소
        description: 변경 설명

    Returns:
        생성된 ConfigChangeLog 객체
    """
    log = ConfigChangeLog(
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        action=action,
        before_state=before_state,
        after_state=after_state,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_ip=actor_ip,
        description=description
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


async def log_config_change_async(
    db: AsyncSession,
    resource_type: EnumConfigResourceType,
    resource_id: int,
    action: EnumConfigActionType,
    resource_name: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    actor_ip: Optional[str] = None,
    description: Optional[str] = None
) -> ConfigChangeLog:
    """log_config_change의 async 병존 버전 (v6.0 P6 후속).

    라우터가 AsyncSession 사용 시 호출. 로직/필드는 sync와 100% 동일.
    """
    log = ConfigChangeLog(
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        action=action,
        before_state=before_state,
        after_state=after_state,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_ip=actor_ip,
        description=description
    )

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return log
