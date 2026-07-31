"""
EventSuppressionSchedule Pydantic schemas.

PRD: event-suppression-schedule-prd.md v1.1 (기반) + event-suppression-multi-target-prd.md v1.0 (복수 대상)

- Create: 억제 스케줄 생성(extra='forbid', 창 순서·대상 배열 검증).
- Update: 부분 수정(PATCH).
- Response: 파생 status + 대상 배열(target_device_ids/target_group_ids).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import KSTDatetime
from app.utils.datetime import to_utc
from app.utils.enums import (
    EnumSuppressionTargetType,
    EnumSuppressionSide,
    EnumSuppressionEventScope,
)


class EventSuppressionScheduleCreate(BaseModel):
    """억제 스케줄 생성 요청 — 대상 복수(모드 내)."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200, description="작업명/사유",
                      json_schema_extra={"example": "GOP 3구역 펜스 보수"})
    description: Optional[str] = Field(None, max_length=500, description="상세 설명")
    target_type: EnumSuppressionTargetType = Field(..., description="대상 모드(배타): device/group/all")
    target_device_ids: list[int] = Field(
        default_factory=list, description="target_type=device 시 최소 1개(그 외 무시)",
        json_schema_extra={"example": [11, 12, 13]},
    )
    target_group_ids: list[int] = Field(
        default_factory=list, description="target_type=group 시 최소 1개(그 외 무시)",
        json_schema_extra={"example": [5, 6]},
    )
    target_side: EnumSuppressionSide = Field(
        EnumSuppressionSide.BOTH, description="감지/감시 필터(group·all 적용). 기본 both",
    )
    event_scope: EnumSuppressionEventScope = Field(
        ..., description="억제할 이벤트 유형: connection/detection/malfunction/all",
    )
    window_start: datetime = Field(..., description="억제 시작(KST 권장, +09:00)",
                                   json_schema_extra={"example": "2026-08-01T09:00:00+09:00"})
    window_end: datetime = Field(..., description="억제 종료(필수, 자동 만료)",
                                 json_schema_extra={"example": "2026-08-01T18:00:00+09:00"})
    recurrence_rule: Optional[str] = Field(None, max_length=255, description="Phase 2 RRULE. 현재 미사용(단발)")

    @model_validator(mode="after")
    def _validate(self):
        # 창 순서: end > start (UTC 정규화 후 비교)
        s, e = to_utc(self.window_start), to_utc(self.window_end)
        if s is not None and e is not None and e <= s:
            raise ValueError("window_end must be after window_start")
        # 모드별 대상 배열 최소 1개 (중복 제거)
        if self.target_type == EnumSuppressionTargetType.DEVICE:
            self.target_device_ids = list(dict.fromkeys(self.target_device_ids))
            if len(self.target_device_ids) < 1:
                raise ValueError("target_device_ids requires at least 1 id when target_type=device")
        elif self.target_type == EnumSuppressionTargetType.GROUP:
            self.target_group_ids = list(dict.fromkeys(self.target_group_ids))
            if len(self.target_group_ids) < 1:
                raise ValueError("target_group_ids requires at least 1 id when target_type=group")
        return self


class EventSuppressionScheduleUpdate(BaseModel):
    """억제 스케줄 부분 수정(PATCH). 전 필드 선택."""
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    target_type: Optional[EnumSuppressionTargetType] = None
    target_device_ids: Optional[list[int]] = None
    target_group_ids: Optional[list[int]] = None
    target_side: Optional[EnumSuppressionSide] = None
    event_scope: Optional[EnumSuppressionEventScope] = None
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    recurrence_rule: Optional[str] = Field(None, max_length=255)


class EventSuppressionScheduleResponse(BaseModel):
    """억제 스케줄 응답 — 파생 status + 대상 배열."""
    id: int
    name: str
    description: Optional[str] = None
    target_type: EnumSuppressionTargetType
    target_device_ids: list[int] = Field(default_factory=list)
    target_group_ids: list[int] = Field(default_factory=list)
    target_side: EnumSuppressionSide
    event_scope: EnumSuppressionEventScope
    window_start: KSTDatetime
    window_end: KSTDatetime
    recurrence_rule: Optional[str] = None
    is_active: bool = Field(..., description="sweep 비정규화 플래그(표시용). 억제 권위는 status")
    status: str = Field(..., description="파생 상태: pending/active/expired/cancelled")
    revoked_at: Optional[KSTDatetime] = None
    created_by: Optional[int] = None
    created_at: KSTDatetime
    updated_at: KSTDatetime

    model_config = {"from_attributes": True}
