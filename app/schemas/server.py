"""
Server schemas: ServerCategory, Server
Based on PRD_Server_Monitoring.md
"""
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.utils.enums import EnumServerType, EnumServerStatus


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
    type_server: str  # EnumServerType value as string
    description: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Server Schemas
# ============================================================

class ServerCreate(BaseModel):
    """Schema for creating a new Server"""
    category_id: int
    name: str
    status: EnumServerStatus = EnumServerStatus.NORMAL
    ip_address: str
    port: int
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    threshold_config: Optional[Dict[str, Any]] = None

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v


class ServerUpdate(BaseModel):
    """Schema for updating a Server (all fields optional for PATCH)"""
    category_id: Optional[int] = None
    name: Optional[str] = None
    status: Optional[EnumServerStatus] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    threshold_config: Optional[Dict[str, Any]] = None


class ServerResponse(BaseModel):
    """Schema for Server response"""
    id: int
    category_id: int
    name: str
    status: str  # EnumServerStatus value as string
    ip_address: str
    port: int
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    threshold_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Summary/Dashboard Schemas
# ============================================================

class ServerNestedResponse(BaseModel):
    """
    Server Nested Response - for use in other resources (e.g., Speaker)
    PRD: PRD_Speaker_Device.md Section 5.3
    Excludes created_at, updated_at per nested response rule
    """
    id: int
    category_id: int
    name: str
    status: str  # EnumServerStatus value as string
    ip_address: str
    port: int
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    threshold_config: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ServerCategoryWithServers(BaseModel):
    """Schema for ServerCategory with nested servers list"""
    id: int
    name: str
    type_server: str
    description: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    servers: List[ServerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ServerCategorySummary(BaseModel):
    """Schema for dashboard summary - category with status counts"""
    id: int
    name: str
    type_server: str
    total: int = 0
    normal: int = 0
    warning: int = 0
    error: int = 0
    servers: List[ServerResponse] = []

    model_config = ConfigDict(from_attributes=True)


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
    collected_at: Optional[datetime] = None


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
    collected_at: Optional[datetime] = None
    created_at: datetime
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
