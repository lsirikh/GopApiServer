"""
System Event Pydantic Schemas
Based on PRD_System_Event.md Section 3
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any, Dict

from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity


# ==============================================================================
# System Event Schemas
# ==============================================================================

class SystemEventCreate(BaseModel):
    """
    System Event 생성 스키마

    PRD Reference: PRD_System_Event.md Section 3

    Attributes:
        server_id: 서버 ID (선택 - 전역 이벤트는 NULL)
        server_description: 서버 설명 (서버 삭제 후에도 기록 유지)
        type_event: 이벤트 유형 (EnumSystemEventType)
        severity: 심각도 (EnumSystemEventSeverity)
        title: 이벤트 제목 (필수)
        message: 이벤트 메시지 (선택)
        detail: 추가 상세 정보 (JSONB, 선택)
    """
    server_id: Optional[int] = Field(None, description="서버 ID (선택 - 전역 이벤트는 NULL)")
    server_description: Optional[str] = Field(None, max_length=200, description="서버 설명")
    type_event: EnumSystemEventType = Field(..., description="이벤트 유형")
    severity: EnumSystemEventSeverity = Field(
        default=EnumSystemEventSeverity.INFO,
        description="심각도"
    )
    title: str = Field(..., max_length=200, description="이벤트 제목")
    message: Optional[str] = Field(None, max_length=1000, description="이벤트 메시지")
    detail: Optional[Dict[str, Any]] = Field(None, description="추가 상세 정보 (JSONB)")


class SystemEventUpdate(BaseModel):
    """
    System Event 수정 스키마

    PRD Reference: PRD_System_Event.md Section 3

    모든 필드가 Optional - 부분 업데이트 지원
    """
    severity: Optional[EnumSystemEventSeverity] = Field(None, description="심각도")
    title: Optional[str] = Field(None, max_length=200, description="이벤트 제목")
    message: Optional[str] = Field(None, max_length=1000, description="이벤트 메시지")
    detail: Optional[Dict[str, Any]] = Field(None, description="추가 상세 정보 (JSONB)")


class SystemEventResponse(BaseModel):
    """
    System Event 응답 스키마

    PRD Reference: PRD_System_Event.md Section 3
    """
    id: int = Field(..., description="이벤트 ID")
    server_id: Optional[int] = Field(None, description="서버 ID")
    server_description: Optional[str] = Field(None, description="서버 설명")
    type_event: EnumSystemEventType = Field(..., description="이벤트 유형")
    severity: EnumSystemEventSeverity = Field(..., description="심각도")
    title: str = Field(..., description="이벤트 제목")
    message: Optional[str] = Field(None, description="이벤트 메시지")
    detail: Optional[Dict[str, Any]] = Field(None, description="추가 상세 정보")
    is_acknowledged: bool = Field(..., description="확인 여부")
    acknowledged_by: Optional[str] = Field(None, description="확인자")
    acknowledged_at: Optional[datetime] = Field(None, description="확인 시간")
    created_at: datetime = Field(..., description="생성 시간")

    model_config = ConfigDict(from_attributes=True)


class SystemEventAcknowledge(BaseModel):
    """
    System Event 확인(Acknowledge) 스키마

    PRD Reference: PRD_System_Event.md Section 3

    Attributes:
        acknowledged_by: 확인자 이름/ID
    """
    acknowledged_by: str = Field(..., max_length=100, description="확인자")


class SystemEventSummary(BaseModel):
    """
    System Event 요약 통계 스키마

    PRD Reference: PRD_System_Event.md Section 3

    Attributes:
        total_count: 전체 이벤트 수
        unacknowledged_count: 미확인 이벤트 수
        by_severity: 심각도별 이벤트 수
        by_type: 유형별 이벤트 수
        recent_critical: 최근 CRITICAL 이벤트 목록
    """
    total_count: int = Field(..., description="전체 이벤트 수")
    unacknowledged_count: int = Field(..., description="미확인 이벤트 수")
    by_severity: Dict[str, int] = Field(..., description="심각도별 이벤트 수")
    by_type: Dict[str, int] = Field(..., description="유형별 이벤트 수")
    recent_critical: list = Field(default_factory=list, description="최근 CRITICAL 이벤트 목록")
