"""
Models package for GOP API
"""
from app.models.device import Controller, Sensor, Camera, Speaker
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.models.event import DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
from app.models.integration import EventMapping, EventMappingCamera
from app.models.server import ServerCategory, Server
from app.models.camera_preset import CameraPreset, ROI, XyPoint

__all__ = [
    # Device models
    "Controller",
    "Sensor",
    "Camera",
    "Speaker",
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
    # Server models
    "ServerCategory",
    "Server",
    # Camera Preset models
    "CameraPreset",
    "ROI",
    "XyPoint",
]
