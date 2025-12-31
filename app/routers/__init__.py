"""
Router module exports
"""
from app.routers import auth
from app.routers import logs
from app.routers import controllers
from app.routers import sensors
from app.routers import cameras
from app.routers import detections
from app.routers import malfunctions
from app.routers import connections
from app.routers import actions
from app.routers import event_mappings
from app.routers import camera_event_mappings
from app.routers import server_categories
from app.routers import servers
from app.routers import device_groups
from app.routers import camera_presets
from app.routers import rois
from app.routers import xypoints

__all__ = [
    "auth",
    "logs",
    "controllers",
    "sensors",
    "cameras",
    "detections",
    "malfunctions",
    "connections",
    "actions",
    "event_mappings",
    "camera_event_mappings",
    "server_categories",
    "servers",
    "device_groups",
    "camera_presets",
    "rois",
    "xypoints",
]
