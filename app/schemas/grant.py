"""
UserGroupGrant Pydantic schemas — FR-03/FR-05
PRD: PRD_Permission_Group_Scheduling.md §3.4
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.schemas.common import KSTDatetime


class GrantCreate(BaseModel):
    """그룹 부여 요청 (ADMIN 전용)."""
    model_config = ConfigDict(extra="forbid")

    group_id: int = Field(..., description="부여할 권한그룹 ID", json_schema_extra={"example": 3})
    valid_from: datetime = Field(
        ..., description="유효 시작 일시(KST)",
        json_schema_extra={"example": "2026-06-30T13:00:00+09:00"}
    )
    valid_until: Optional[datetime] = Field(
        None, description="유효 종료 일시(KST). 생략/NULL = 상시(무기한)",
        json_schema_extra={"example": "2026-07-01T14:00:00+09:00"}
    )


class GrantResponse(BaseModel):
    """부여 응답 — 파생 status 포함."""
    id: int
    user_id: int
    group_id: int
    group_name: Optional[str] = Field(None, description="부여 그룹명")
    valid_from: KSTDatetime
    valid_until: Optional[KSTDatetime] = None
    is_active: bool = Field(..., description="sweep 비정규화 플래그(표시용). 인가 권위는 status")
    status: str = Field(..., description="파생 상태: ACTIVE/PENDING/EXPIRED/REVOKED")
    granted_by: Optional[int] = None
    revoked_at: Optional[KSTDatetime] = None
    created_at: KSTDatetime

    model_config = {"from_attributes": True}
