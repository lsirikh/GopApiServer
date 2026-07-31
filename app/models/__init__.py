"""
Models package for GOP API
"""
from app.models.device import Controller, Sensor, Camera, Speaker, Enclosure, EnclosureMetric
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.models.event import DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
from app.models.integration import EventMapping, EventMappingCamera, EventMappingSpeaker
from app.models.server import ServerCategory, Server, ServerMetrics
from app.models.system_event import SystemEvent
from app.models.camera_preset import CameraPreset, ROI, XyPoint
from app.models.file_group import FileGroup
from app.models.audit_log import AuditLog
from app.models.device_setting import ProxySetting, CameraSetting
from app.models.thumbnail import Thumbnail
from app.models.tracking import TrackPoint
from app.models.event_suppression import (
    EventSuppressionSchedule, EventSuppressionTargetDevice, EventSuppressionTargetGroup,
)

__all__ = [
    # Device models
    "Controller",
    "Sensor",
    "Camera",
    "Speaker",
    "Enclosure",
    "EnclosureMetric",
    # DeviceGroup models
    "DeviceGroup",
    "DeviceGroupMapping",
    # Event models
    "DetectionEvent",
    "MalfunctionEvent",
    "ConnectionEvent",
    "ActionEvent",
    # Integration models
    "EventMapping",
    "EventMappingCamera",
    "EventMappingSpeaker",
    # Server models
    "ServerCategory",
    "Server",
    "ServerMetrics",
    # System Event models
    "SystemEvent",
    # Camera Preset models
    "CameraPreset",
    "ROI",
    "XyPoint",
    # FileGroup models
    "FileGroup",
    # Audit Log models
    "AuditLog",
    # Device Setting models
    "ProxySetting",
    "CameraSetting",
    # Thumbnail models
    "Thumbnail",
    # Tracking models
    "TrackPoint",
    # Event Suppression Schedule models
    "EventSuppressionSchedule",
    "EventSuppressionTargetDevice",
    "EventSuppressionTargetGroup",
]
