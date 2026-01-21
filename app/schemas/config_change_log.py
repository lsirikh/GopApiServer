"""
ConfigChangeLog Pydantic Schemas
Based on PRD_ConfigChangeLog.md v1.1

JSONB 정규화 규칙 (v1.1):
- CREATED: after_state = {id, name} (식별 정보만)
- UPDATED: before_state/after_state = {변경된 필드만}
- DELETED: before_state = {id, name} (식별 정보만)
- STATUS_CHANGED: {status} 필드만
- ASSIGNED: after_state = {target_id, target_name}
- UNASSIGNED: before_state = {target_id, target_name}
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any, Dict, List

from app.utils.enums import EnumConfigResourceType, EnumConfigActionType


# ==============================================================================
# ConfigChangeLog Schemas
# ==============================================================================

class ConfigChangeLogResponse(BaseModel):
    """
    설정 변경 로그 응답 스키마

    PRD Reference: PRD_ConfigChangeLog.md v1.1 Section 4

    Note: before_state/after_state는 v1.1 정규화 규칙에 따라 변경된 필드만 저장

    Example Response (UPDATED - 변경된 필드만):
        {
            "id": 1,
            "resource_type": "CAMERA",
            "resource_id": 201,
            "resource_name": "Camera-201 (정문 CCTV)",
            "action": "UPDATED",
            "before_state": {"name": "정문 CCTV"},
            "after_state": {"name": "정문 CCTV (수정)"},
            "actor_id": 1,
            "actor_name": "admin",
            "actor_ip": "192.168.1.100",
            "description": "Camera 정보 수정",
            "created_at": "2026-01-20T10:30:00"
        }

    Example Response (CREATED - 식별 정보만):
        {
            "before_state": null,
            "after_state": {"id": 201, "name": "정문 CCTV"}
        }

    Example Response (DELETED - 식별 정보만):
        {
            "before_state": {"id": 201, "name": "정문 CCTV"},
            "after_state": null
        }
    """
    id: int = Field(
        ...,
        description="로그 ID",
        json_schema_extra={"example": 1}
    )
    resource_type: EnumConfigResourceType = Field(
        ...,
        description="리소스 유형 (19종: Device 10, Server 2, Event 4, Integration 3)",
        json_schema_extra={"example": "CAMERA"}
    )
    resource_id: int = Field(
        ...,
        description="리소스 ID",
        json_schema_extra={"example": 201}
    )
    resource_name: Optional[str] = Field(
        None,
        description="리소스 식별명",
        json_schema_extra={"example": "Camera-201 (정문 CCTV)"}
    )
    action: EnumConfigActionType = Field(
        ...,
        description="액션 유형 (CREATED, UPDATED, DELETED, STATUS_CHANGED, ASSIGNED, UNASSIGNED)",
        json_schema_extra={"example": "UPDATED"}
    )
    before_state: Optional[Dict[str, Any]] = Field(
        None,
        description="변경 전 상태 (v1.1: 변경된 필드만 저장)",
        json_schema_extra={"example": {"name": "정문 CCTV"}}
    )
    after_state: Optional[Dict[str, Any]] = Field(
        None,
        description="변경 후 상태 (v1.1: 변경된 필드만 저장)",
        json_schema_extra={"example": {"name": "정문 CCTV (수정)"}}
    )
    actor_id: Optional[int] = Field(
        None,
        description="수행자 ID",
        json_schema_extra={"example": 1}
    )
    actor_name: Optional[str] = Field(
        None,
        description="수행자 이름",
        json_schema_extra={"example": "admin"}
    )
    actor_ip: Optional[str] = Field(
        None,
        description="수행자 IP",
        json_schema_extra={"example": "192.168.1.100"}
    )
    description: Optional[str] = Field(
        None,
        description="설명",
        json_schema_extra={"example": "Camera 정보 수정"}
    )
    created_at: datetime = Field(
        ...,
        description="생성 시간",
        json_schema_extra={"example": "2026-01-20T10:30:00"}
    )

    model_config = ConfigDict(from_attributes=True)


class ConfigChangeLogListResponse(BaseModel):
    """
    설정 변경 로그 목록 응답 스키마

    PRD Reference: PRD_ConfigChangeLog.md v1.1 Section 5

    Example Response:
        {
            "logs": [
                {
                    "id": 1,
                    "resource_type": "CAMERA",
                    "resource_id": 201,
                    "action": "CREATED",
                    "before_state": null,
                    "after_state": {"id": 201, "name": "정문 CCTV"}
                },
                {
                    "id": 2,
                    "resource_type": "CAMERA",
                    "resource_id": 201,
                    "action": "UPDATED",
                    "before_state": {"name": "정문 CCTV"},
                    "after_state": {"name": "정문 CCTV (수정)"}
                }
            ],
            "total": 150,
            "page": 1,
            "limit": 50
        }
    """
    logs: List[ConfigChangeLogResponse] = Field(
        ...,
        description="로그 목록",
        json_schema_extra={"example": []}
    )
    total: int = Field(
        ...,
        description="전체 로그 수",
        json_schema_extra={"example": 150}
    )
    page: int = Field(
        ...,
        description="현재 페이지",
        json_schema_extra={"example": 1}
    )
    limit: int = Field(
        ...,
        description="페이지당 항목 수",
        json_schema_extra={"example": 50}
    )
