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
]
