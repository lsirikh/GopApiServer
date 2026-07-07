"""
Audit Log Pydantic schemas
PRD: PRD_Audit_Log.md v1.0
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.schemas.common import KSTDatetime

from app.utils.enums import (
    EnumAuditActionType, EnumAuditStatus, EnumAuditResourceType, EnumUserRole,
)


# ============================================================
# Request Schemas
# ============================================================

class AuditLogCreate(BaseModel):
    """감사 로그 생성 스키마 (내부 사용)"""
    action_type: str = Field(
        ...,
        description="행위 유형 (EnumAuditActionType)",
        json_schema_extra={"example": "USER_CREATED"}
    )
    action_status: str = Field(
        default="SUCCESS",
        description="행위 결과 (SUCCESS, FAILURE)",
        json_schema_extra={"example": "SUCCESS"}
    )
    resource_type: str = Field(
        ...,
        description="대상 리소스 유형 (EnumAuditResourceType)",
        json_schema_extra={"example": "USER"}
    )
    resource_id: Optional[int] = Field(
        None,
        description="대상 리소스 ID",
        json_schema_extra={"example": 1}
    )
    resource_name: Optional[str] = Field(
        None,
        description="대상 리소스 이름 (스냅샷)",
        json_schema_extra={"example": "홍길동 (operator01)"}
    )
    actor_id: Optional[int] = Field(
        None,
        description="행위자 ID",
        json_schema_extra={"example": 1}
    )
    actor_login_id: str = Field(
        ...,
        description="행위자 로그인 ID (스냅샷)",
        json_schema_extra={"example": "admin"}
    )
    actor_name: Optional[str] = Field(
        None,
        description="행위자 이름 (스냅샷)",
        json_schema_extra={"example": "관리자"}
    )
    actor_role: Optional[str] = Field(
        None,
        description="행위자 역할 (스냅샷)",
        json_schema_extra={"example": "ADMIN"}
    )
    changes: Optional[Dict[str, Any]] = Field(
        None,
        description="변경 내역 {before: {...}, after: {...}}",
        json_schema_extra={"example": {
            "before": {"role": "VIEWER"},
            "after": {"role": "OPERATOR"}
        }}
    )
    description: Optional[str] = Field(
        None,
        description="활동 설명",
        json_schema_extra={"example": "사용자 역할 변경: VIEWER → OPERATOR"}
    )
    ip_address: Optional[str] = Field(
        None,
        description="클라이언트 IP 주소",
        json_schema_extra={"example": "192.168.1.100"}
    )
    user_agent: Optional[str] = Field(
        None,
        description="클라이언트 User-Agent"
    )
    error_message: Optional[str] = Field(
        None,
        description="오류 메시지 (실패 시)"
    )


# ============================================================
# Response Schemas
# ============================================================

class AuditLogResponse(BaseModel):
    """감사 로그 응답 스키마"""
    id: int = Field(..., description="로그 ID", json_schema_extra={"example": 1})

    # 행위 정보
    # NOTE(v51 hardening): action_type/resource_type 는 응답에서 str(tolerant).
    #   audit_logs 는 append-only(DELETE 불가)라 과거 비-enum 값(예: 테스트 'TEST_INS'/'TEST')이
    #   영구 잔존 → strict enum 이면 목록 직렬화가 500. create 측(AuditLogCreate)도 str 이므로 정합.
    action_type: str = Field(..., description="행위 유형 (EnumAuditActionType)", json_schema_extra={"example": "USER_CREATED"})
    # v6.0-response_schema_audit: EnumAuditStatus → str (String 컬럼 지뢰, action_type 은 이미 str)
    action_status: str = Field(..., description="행위 결과 (SUCCESS/FAILURE 등)", json_schema_extra={"example": "SUCCESS"})

    # 대상 리소스 정보
    resource_type: str = Field(..., description="대상 리소스 유형 (EnumAuditResourceType)", json_schema_extra={"example": "USER"})
    resource_id: Optional[int] = Field(None, description="대상 리소스 ID", json_schema_extra={"example": 5})
    resource_name: Optional[str] = Field(None, description="대상 리소스 이름", json_schema_extra={"example": "홍길동 (operator01)"})

    # 행위자 정보
    actor_id: Optional[int] = Field(None, description="행위자 ID", json_schema_extra={"example": 1})
    actor_login_id: str = Field(..., description="행위자 로그인 ID", json_schema_extra={"example": "admin"})
    actor_name: Optional[str] = Field(None, description="행위자 이름", json_schema_extra={"example": "관리자"})
    # v6.0-clone_deploy_bugfix (#2): EnumUserRole → str 완화 (servers.port·users.role 과 동일 패턴).
    # v5.3 role 축소 후에도 audit_logs 는 append-only 라 옛 값(OPERATOR/MAINTAINER/VIEWER) 이 영구 잔존.
    # 감사 로그 응답에서 strict enum 검증하면 옛 행 1개가 목록 전체를 500 으로 만든다 (Postel's Law).
    actor_role: Optional[str] = Field(None, description="행위자 역할 (ADMIN/USER, 옛 감사행은 OPERATOR 등 가능)", json_schema_extra={"example": "ADMIN"})

    # 변경 상세
    changes: Optional[Dict[str, Any]] = Field(None, description="변경 내역")
    description: Optional[str] = Field(None, description="활동 설명")

    # 클라이언트 정보
    ip_address: Optional[str] = Field(None, description="IP 주소", json_schema_extra={"example": "192.168.1.100"})
    user_agent: Optional[str] = Field(None, description="User-Agent")

    # 오류 정보
    error_message: Optional[str] = Field(None, description="오류 메시지")

    # 타임스탬프
    created_at: KSTDatetime = Field(..., description="생성 시간", json_schema_extra={"example": "2026-01-19T10:30:00+09:00"})

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Filter & List Schemas
# ============================================================

class AuditLogFilter(BaseModel):
    """감사 로그 필터 스키마"""
    # 페이지네이션
    page: int = Field(
        default=1,
        ge=1,
        description="페이지 번호",
        json_schema_extra={"example": 1}
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="페이지당 항목 수",
        json_schema_extra={"example": 20}
    )

    # 필터
    action_type: Optional[str] = Field(
        None,
        description="행위 유형 필터 (EnumAuditActionType)",
        json_schema_extra={"example": "USER_CREATED"}
    )
    resource_type: Optional[str] = Field(
        None,
        description="대상 리소스 유형 필터 (EnumAuditResourceType)",
        json_schema_extra={"example": "USER"}
    )
    actor_login_id: Optional[str] = Field(
        None,
        description="행위자 로그인 ID 필터",
        json_schema_extra={"example": "admin"}
    )
    action_status: Optional[str] = Field(
        None,
        description="행위 결과 필터 (SUCCESS, FAILURE)",
        json_schema_extra={"example": "SUCCESS"}
    )

    # 날짜 필터
    start_date: Optional[KSTDatetime] = Field(
        None,
        description="시작 날짜 (이 날짜 이후의 로그만 조회)",
        json_schema_extra={"example": "2026-01-01T00:00:00+09:00"}
    )
    end_date: Optional[KSTDatetime] = Field(
        None,
        description="종료 날짜 (이 날짜 이전의 로그만 조회)",
        json_schema_extra={"example": "2026-01-31T23:59:59+09:00"}
    )


class AuditLogListResponse(BaseModel):
    """감사 로그 목록 응답 스키마"""
    total: int = Field(
        ...,
        description="전체 항목 수",
        json_schema_extra={"example": 100}
    )
    page: int = Field(
        ...,
        description="현재 페이지 번호",
        json_schema_extra={"example": 1}
    )
    limit: int = Field(
        ...,
        description="페이지당 항목 수",
        json_schema_extra={"example": 20}
    )
    items: List[AuditLogResponse] = Field(
        ...,
        description="감사 로그 목록"
    )
