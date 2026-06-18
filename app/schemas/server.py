"""
Server schemas: ServerCategory, Server
Based on PRD_Server_Monitoring.md
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from app.schemas.common import KSTDatetime
from typing import Optional, List, Dict, Any

from app.utils.enums import EnumServerType, EnumServerStatus


# ============================================================
# Common Examples for Swagger Documentation
# ============================================================

THRESHOLD_CONFIG_EXAMPLE = {
    "cpu": {"warning": 80, "critical": 95},
    "ram": {"warning": 75, "critical": 90},
    "disk": {"warning": 80, "critical": 95},
    "network": {"warning": 70, "critical": 85}
}


# ============================================================
# ServerCategory Schemas
# ============================================================

class ServerCategoryCreate(BaseModel):
    """Schema for creating a new ServerCategory"""
    name: str
    type_server: EnumServerType
    description: Optional[str] = None
    sort_order: int = 0

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v


class ServerCategoryUpdate(BaseModel):
    """Schema for updating a ServerCategory (all fields optional for PATCH)"""
    name: Optional[str] = None
    type_server: Optional[EnumServerType] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class ServerCategoryResponse(BaseModel):
    """Schema for ServerCategory response"""
    id: int
    name: str
    type_server: EnumServerType
    description: Optional[str] = None
    sort_order: int
    created_at: KSTDatetime
    updated_at: KSTDatetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Server Schemas
# ============================================================

class ServerCreate(BaseModel):
    """Schema for creating a new Server"""
    category_id: int = Field(..., description="소속 카테고리 ID")
    name: str = Field(..., description="서버 이름")
    status: EnumServerStatus = Field(EnumServerStatus.NORMAL, description="서버 상태")
    ip_address: str = Field(..., description="서버 IP 주소")
    port: int = Field(..., description="서버 포트")
    hostname: Optional[str] = Field(None, description="호스트명")
    user_name: Optional[str] = Field(None, description="접속 사용자명")
    user_password: Optional[str] = Field(None, description="접속 비밀번호")
    threshold_config: Optional[Dict[str, Any]] = Field(
        None,
        description="임계치 설정 JSONB (v2.9 신규). cpu/ram/disk/network 각각 warning, critical 값 설정"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_id": 1,
                "name": "VMS-Server-01",
                "status": "NORMAL",
                "ip_address": "192.168.1.100",
                "port": 8080,
                "hostname": "vms-server-01",
                "user_name": "admin",
                "user_password": "password123",
                "threshold_config": THRESHOLD_CONFIG_EXAMPLE
            }
        }
    )

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v


class ServerUpdate(BaseModel):
    """Schema for updating a Server (all fields optional for PATCH)"""
    category_id: Optional[int] = Field(None, description="소속 카테고리 ID")
    name: Optional[str] = Field(None, description="서버 이름")
    status: Optional[EnumServerStatus] = Field(None, description="서버 상태")
    ip_address: Optional[str] = Field(None, description="서버 IP 주소")
    port: Optional[int] = Field(None, description="서버 포트")
    hostname: Optional[str] = Field(None, description="호스트명")
    user_name: Optional[str] = Field(None, description="접속 사용자명")
    user_password: Optional[str] = Field(None, description="접속 비밀번호")
    threshold_config: Optional[Dict[str, Any]] = Field(
        None,
        description="임계치 설정 JSONB (v2.9 신규). cpu/ram/disk/network 각각 warning, critical 값 설정"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "WARNING",
                "threshold_config": THRESHOLD_CONFIG_EXAMPLE
            }
        }
    )


class ServerResponse(BaseModel):
    """Schema for Server response (v4.4 Phase 5: user_password 응답 노출 복원, 정책은 v4.5에서 결정)"""
    id: int = Field(..., description="서버 ID")
    category_id: int = Field(..., description="소속 카테고리 ID")
    name: str = Field(..., description="서버 이름")
    status: EnumServerStatus = Field(..., description="서버 상태 (NORMAL/WARNING/ERROR)")
    ip_address: str = Field(..., description="서버 IP 주소")
    port: int = Field(..., description="서버 포트")
    hostname: Optional[str] = Field(None, description="호스트명")
    user_name: Optional[str] = Field(None, description="접속 사용자명")
    user_password: Optional[str] = Field(None, description="접속 비밀번호")
    threshold_config: Optional[Dict[str, Any]] = Field(
        None,
        description="임계치 설정 JSONB (v2.9 신규). cpu/ram/disk/network 각각 warning, critical 값 설정"
    )
    created_at: KSTDatetime = Field(..., description="생성 일시")
    updated_at: KSTDatetime = Field(..., description="수정 일시")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "category_id": 1,
                "name": "VMS-Server-01",
                "status": "NORMAL",
                "ip_address": "192.168.1.100",
                "port": 8080,
                "hostname": "vms-server-01",
                "user_name": "admin",
                "user_password": "password123",
                "threshold_config": THRESHOLD_CONFIG_EXAMPLE,
                "created_at": "2026-01-26T10:00:00.000000",
                "updated_at": "2026-01-26T10:00:00.000000"
            }
        }
    )


# ============================================================
# Summary/Dashboard Schemas
# ============================================================

class ServerNestedResponse(BaseModel):
    """
    Server Nested Response - for use in other resources (e.g., Speaker)
    PRD: PRD_Speaker_Device.md Section 5.3
    Excludes created_at, updated_at per nested response rule
    v4.4 Phase 5: user_password 응답 노출 복원 (정책은 v4.5에서 결정)
    """
    id: int = Field(..., description="서버 ID")
    category_id: int = Field(..., description="소속 카테고리 ID")
    name: str = Field(..., description="서버 이름")
    status: EnumServerStatus = Field(..., description="서버 상태 (NORMAL/WARNING/ERROR)")
    ip_address: str = Field(..., description="서버 IP 주소")
    port: int = Field(..., description="서버 포트")
    hostname: Optional[str] = Field(None, description="호스트명")
    user_name: Optional[str] = Field(None, description="접속 사용자명")
    user_password: Optional[str] = Field(None, description="접속 비밀번호")
    threshold_config: Optional[Dict[str, Any]] = Field(
        None,
        description="임계치 설정 JSONB (v2.9 신규). cpu/ram/disk/network 각각 warning, critical 값 설정"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "category_id": 1,
                "name": "Broadcast-Server-01",
                "status": "NORMAL",
                "ip_address": "192.168.1.50",
                "port": 9000,
                "hostname": "bcast-srv-01",
                "user_name": "admin",
                "user_password": "password123",
                "threshold_config": THRESHOLD_CONFIG_EXAMPLE
            }
        }
    )


class ServerCategoryWithServers(BaseModel):
    """Schema for ServerCategory with nested servers list"""
    id: int
    name: str
    type_server: EnumServerType
    description: Optional[str] = None
    sort_order: int
    created_at: KSTDatetime
    updated_at: KSTDatetime
    servers: List[ServerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ServerCategorySummary(BaseModel):
    """Schema for dashboard summary - category with status counts"""
    id: int = Field(..., description="카테고리 ID")
    name: str = Field(..., description="카테고리 이름")
    type_server: EnumServerType = Field(..., description="서버 타입")
    total: int = Field(0, description="전체 서버 수")
    normal: int = Field(0, description="정상 서버 수")
    warning: int = Field(0, description="경고 서버 수")
    error: int = Field(0, description="오류 서버 수")
    servers: List[ServerResponse] = Field(default_factory=list, description="서버 목록")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "VMS 서버",
                "type_server": "VMS",
                "total": 3,
                "normal": 2,
                "warning": 1,
                "error": 0,
                "servers": [
                    {
                        "id": 1,
                        "category_id": 1,
                        "name": "VMS-Server-01",
                        "status": "NORMAL",
                        "ip_address": "192.168.1.100",
                        "port": 8080,
                        "hostname": "vms-server-01",
                        "user_name": "admin",
                        "user_password": "password123",
                        "threshold_config": THRESHOLD_CONFIG_EXAMPLE,
                        "created_at": "2026-01-26T10:00:00.000000",
                        "updated_at": "2026-01-26T10:00:00.000000"
                    }
                ]
            }
        }
    )


# ============================================================
# ServerMetrics Schemas
# ============================================================

class ServerMetricsCreate(BaseModel):
    """
    Schema for creating server metrics
    PRD Reference: PRD_System_Event.md Section 2.4
    """
    cpu_usage: Optional[float] = None
    ram_usage: Optional[float] = None
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    disk_usage: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    network_in_mbps: Optional[float] = None
    network_out_mbps: Optional[float] = None
    process_count: Optional[int] = None
    detail: Optional[Dict[str, Any]] = None
    collected_at: Optional[KSTDatetime] = None


class ServerMetricsResponse(BaseModel):
    """
    Schema for server metrics response
    PRD Reference: PRD_System_Event.md Section 2.4
    """
    id: int
    server_id: int
    cpu_usage: Optional[float] = None
    ram_usage: Optional[float] = None
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    disk_usage: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    network_in_mbps: Optional[float] = None
    network_out_mbps: Optional[float] = None
    process_count: Optional[int] = None
    detail: Optional[Dict[str, Any]] = None
    collected_at: Optional[KSTDatetime] = None
    created_at: KSTDatetime
    threshold_exceeded: Optional[Dict[str, Any]] = None  # 임계치 초과 정보

    model_config = ConfigDict(from_attributes=True)


class ServerMetricsLatestResponse(BaseModel):
    """
    Schema for latest server metrics response
    PRD Reference: PRD_System_Event.md Section 2.4
    """
    server_id: int
    server_name: str
    latest_metrics: Optional[ServerMetricsResponse] = None

    model_config = ConfigDict(from_attributes=True)
