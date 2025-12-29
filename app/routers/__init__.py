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
from app.routers import server_categories
from app.routers import servers

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
    "server_categories",
    "servers",
]
