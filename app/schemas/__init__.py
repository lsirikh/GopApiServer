"""
Schemas package for GOP API
"""
from app.schemas.device_group import (
    DeviceGroupCreate,
    DeviceGroupUpdate,
    DeviceGroupResponse,
    DeviceGroupDetailResponse,
    DeviceAssignRequest,
    DeviceAssignResponse,
    DeviceRemoveResponse,
    DeviceSummary,
)
from app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogResponse,
)

__all__ = [
    # DeviceGroup schemas
    "DeviceGroupCreate",
    "DeviceGroupUpdate",
    "DeviceGroupResponse",
    "DeviceGroupDetailResponse",
    "DeviceAssignRequest",
    "DeviceAssignResponse",
    "DeviceRemoveResponse",
    "DeviceSummary",
    # AuditLog schemas
    "AuditLogCreate",
    "AuditLogResponse",
]
