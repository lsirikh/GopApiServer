"""
System Event Pydantic Schemas
Based on PRD_System_Event.md Section 3
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.schemas.common import KSTDatetime
from typing import Optional, Any, Dict

from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity


# ==============================================================================
# System Event Schemas
# ==============================================================================

class SystemEventCreate(BaseModel):
    """
    System Event 생성 스키마

    PRD Reference: PRD_System_Event.md Section 3
    PRD Reference: PRD_SystemEvent_Sync.md v1.2 (15종 동기화)

    Attributes:
        server_id: 서버 ID (선택 - 전역 이벤트는 NULL)
        server_description: 서버 설명 (서버 삭제 후에도 기록 유지)
        type_event: 이벤트 유형 (EnumSystemEventType 15종)
        severity: 심각도 (EnumSystemEventSeverity)
        title: 이벤트 제목 (필수)
        message: 이벤트 메시지 (선택)
        detail: 추가 상세 정보 (JSONB, 선택)
        source: 이벤트 발생 소스 (PRD 3.2)

    Example Request:
        {
            "server_id": 1,
            "server_description": "메인 서버",
            "type_event": "SERVER_CONNECTED",
            "severity": "INFO",
            "title": "서버 연결 완료",
            "message": "메인 서버와의 연결이 성공적으로 완료되었습니다.",
            "detail": {"ip": "192.168.1.100", "port": 8080},
            "source": "system-monitor"
        }
    """
    server_id: Optional[int] = Field(
        None,
        description="서버 ID (선택 - 전역 이벤트는 NULL)",
        json_schema_extra={"example": 1}
    )
    server_description: Optional[str] = Field(
        None,
        max_length=200,
        description="서버 설명",
        json_schema_extra={"example": "메인 서버"}
    )
    type_event: EnumSystemEventType = Field(
        ...,
        description="이벤트 유형 (15종: RESOURCE_THRESHOLD, SERVER_CONNECTED, SERVER_DISCONNECTED, SERVER_ERROR, SERVICE_STARTED, SERVICE_STOPPED, SERVICE_ERROR, CONNECTION_LOST, CONNECTION_RESTORED, SECURITY_ALERT, DEVICE_CONNECTED, BACKUP_STARTED, BACKUP_COMPLETED, BACKUP_FAILED, SYSTEM_UPDATE)",
        json_schema_extra={"example": "SERVER_CONNECTED"}
    )
    severity: EnumSystemEventSeverity = Field(
        default=EnumSystemEventSeverity.INFO,
        description="심각도 (INFO, WARNING, ERROR, CRITICAL)",
        json_schema_extra={"example": "INFO"}
    )
    title: str = Field(
        ...,
        max_length=200,
        description="이벤트 제목",
        json_schema_extra={"example": "서버 연결 완료"}
    )
    message: Optional[str] = Field(
        None,
        max_length=1000,
        description="이벤트 메시지",
        json_schema_extra={"example": "메인 서버와의 연결이 성공적으로 완료되었습니다."}
    )
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="추가 상세 정보 (JSONB)",
        json_schema_extra={"example": {"ip": "192.168.1.100", "port": 8080}}
    )
    source: Optional[str] = Field(
        None,
        max_length=100,
        description="이벤트 발생 소스 (PRD 3.2)",
        json_schema_extra={"example": "system-monitor"}
    )


class SystemEventUpdate(BaseModel):
    """
    System Event 수정 스키마 (PATCH)

    PRD Reference: PRD_System_Event.md Section 3

    모든 필드가 Optional - 부분 업데이트 지원

    Example Request:
        {
            "severity": "WARNING",
            "message": "추가 정보 업데이트됨"
        }
    """
    severity: Optional[EnumSystemEventSeverity] = Field(
        None,
        description="심각도 (INFO, WARNING, ERROR, CRITICAL)",
        json_schema_extra={"example": "WARNING"}
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="이벤트 제목",
        json_schema_extra={"example": "업데이트된 제목"}
    )
    message: Optional[str] = Field(
        None,
        max_length=1000,
        description="이벤트 메시지",
        json_schema_extra={"example": "업데이트된 메시지 내용"}
    )
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="추가 상세 정보 (JSONB)",
        json_schema_extra={"example": {"updated_field": "new_value"}}
    )
    source: Optional[str] = Field(
        None,
        max_length=100,
        description="이벤트 발생 소스 (PRD 3.2)",
        json_schema_extra={"example": "system-monitor"}
    )


class SystemEventResponse(BaseModel):
    """
    System Event 응답 스키마

    PRD Reference: PRD_System_Event.md Section 3
    PRD Reference: PRD_SystemEvent_Sync.md v1.2 (15종 동기화)

    Example Response:
        {
            "id": 1,
            "server_id": 1,
            "server_description": "메인 서버",
            "type_event": "SERVER_CONNECTED",
            "severity": "INFO",
            "title": "서버 연결 완료",
            "message": "메인 서버와의 연결이 성공적으로 완료되었습니다.",
            "detail": {"ip": "192.168.1.100", "port": 8080},
            "source": "system-monitor",
            "is_acknowledged": false,
            "acknowledged_by": null,
            "acknowledged_at": null,
            "created_at": "2026-01-20T10:00:00",
            "updated_at": null
        }
    """
    id: int = Field(
        ...,
        description="이벤트 ID",
        json_schema_extra={"example": 1}
    )
    server_id: Optional[int] = Field(
        None,
        description="서버 ID",
        json_schema_extra={"example": 1}
    )
    server_description: Optional[str] = Field(
        None,
        description="서버 설명",
        json_schema_extra={"example": "메인 서버"}
    )
    type_event: EnumSystemEventType = Field(
        ...,
        description="이벤트 유형 (15종)",
        json_schema_extra={"example": "SERVER_CONNECTED"}
    )
    severity: EnumSystemEventSeverity = Field(
        ...,
        description="심각도 (INFO, WARNING, ERROR, CRITICAL)",
        json_schema_extra={"example": "INFO"}
    )
    title: str = Field(
        ...,
        description="이벤트 제목",
        json_schema_extra={"example": "서버 연결 완료"}
    )
    message: Optional[str] = Field(
        None,
        description="이벤트 메시지",
        json_schema_extra={"example": "메인 서버와의 연결이 성공적으로 완료되었습니다."}
    )
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="추가 상세 정보 (JSONB)",
        json_schema_extra={"example": {"ip": "192.168.1.100", "port": 8080}}
    )
    source: Optional[str] = Field(
        None,
        description="이벤트 발생 소스 (PRD 3.2)",
        json_schema_extra={"example": "system-monitor"}
    )
    is_acknowledged: bool = Field(
        ...,
        description="확인 여부",
        json_schema_extra={"example": False}
    )
    acknowledged_by: Optional[str] = Field(
        None,
        description="확인자",
        json_schema_extra={"example": "admin"}
    )
    acknowledged_at: Optional[KSTDatetime] = Field(
        None,
        description="확인 시간",
        json_schema_extra={"example": "2026-01-20T10:30:00"}
    )
    created_at: KSTDatetime = Field(
        ...,
        description="생성 시간",
        json_schema_extra={"example": "2026-01-20T10:00:00"}
    )
    updated_at: Optional[KSTDatetime] = Field(
        None,
        description="수정 시간 (PRD 3.2)",
        json_schema_extra={"example": "2026-01-20T10:15:00"}
    )

    model_config = ConfigDict(from_attributes=True)


class SystemEventAcknowledge(BaseModel):
    """
    System Event 확인(Acknowledge) 스키마

    PRD Reference: PRD_System_Event.md Section 3

    Attributes:
        acknowledged_by: 확인자 이름/ID

    Example Request:
        {
            "acknowledged_by": "admin"
        }
    """
    acknowledged_by: str = Field(
        ...,
        max_length=100,
        description="확인자",
        json_schema_extra={"example": "admin"}
    )


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

    Example Response:
        {
            "total_count": 150,
            "unacknowledged_count": 25,
            "by_severity": {"INFO": 100, "WARNING": 30, "ERROR": 15, "CRITICAL": 5},
            "by_type": {"SERVER_CONNECTED": 50, "SERVICE_STARTED": 40, "BACKUP_COMPLETED": 30},
            "recent_critical": [...]
        }
    """
    total_count: int = Field(
        ...,
        description="전체 이벤트 수",
        json_schema_extra={"example": 150}
    )
    unacknowledged_count: int = Field(
        ...,
        description="미확인 이벤트 수",
        json_schema_extra={"example": 25}
    )
    by_severity: Dict[str, int] = Field(
        ...,
        description="심각도별 이벤트 수",
        json_schema_extra={"example": {"INFO": 100, "WARNING": 30, "ERROR": 15, "CRITICAL": 5}}
    )
    by_type: Dict[str, int] = Field(
        ...,
        description="유형별 이벤트 수 (15종)",
        json_schema_extra={"example": {"SERVER_CONNECTED": 50, "SERVICE_STARTED": 40, "BACKUP_COMPLETED": 30}}
    )
    recent_critical: list = Field(
        default_factory=list,
        description="최근 CRITICAL 이벤트 목록",
        json_schema_extra={"example": []}
    )
