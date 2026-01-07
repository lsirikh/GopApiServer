"""
Device models: Device (Base), Controller, Sensor, Camera
PRD: PRD_Device_Structure_Refactoring.md - Section 3.1

Polymorphic Inheritance using Joined Table strategy.
- Device: Base table with common fields + category_device discriminator
- Controller, Sensor, Camera: Child tables with specific fields
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory


class Device(Base):
    """
    Device Base model - Polymorphic parent for all device types.

    Uses Joined Table Inheritance (STI alternative).
    All common fields are stored here, device-specific fields in child tables.

    Attributes:
        id: Primary key
        category_device: Discriminator column ('controller', 'sensor', 'camera')
        number_device: Device number identifier (can be duplicated across device types)
        group_device: Legacy group identifier (deprecated, for backward compatibility)
        name_device: Device name
        type_device: Device type enum (EnumDeviceType)
        version: Device version
        status: Device status (EnumDeviceStatus)
        created_at: Creation timestamp
        updated_at: Last update timestamp

    Discriminator Values:
        - "controller" -> Controller
        - "sensor" -> Sensor
        - "camera" -> Camera
    """
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_device = Column(SQLEnum(EnumDeviceCategory), nullable=False, index=True)  # PRD v1.3: ENUM Discriminator

    # Common fields (moved from child tables)
    number_device = Column(Integer, nullable=False, index=True)  # Not unique - can be duplicated across device types
    group_device = Column(Integer, nullable=False, index=True)  # Deprecated but kept for compatibility
    name_device = Column(String(200), nullable=False)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    version = Column(String(50), nullable=True)  # PRD v1.2: nullable
    status = Column(SQLEnum(EnumDeviceStatus), nullable=False, default=EnumDeviceStatus.ACTIVATED)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    # Polymorphic configuration
    __mapper_args__ = {
        "polymorphic_on": category_device,
        # Base class - no specific identity (not directly instantiated)
    }

    # Relationship to DeviceGroupMapping (N:N via Junction Table)
    group_mappings = relationship(
        "DeviceGroupMapping",
        primaryjoin="Device.id == foreign(DeviceGroupMapping.device_id)",
        viewonly=True,
        lazy="dynamic"
    )

    def __repr__(self):
        return (
            f"<Device(id={self.id}, category_device='{self.category_device}', "
            f"number_device={self.number_device}, name_device='{self.name_device}')>"
        )


class Controller(Device):
    """
    Controller model for managing control devices.
    Inherits from Device using Joined Table Inheritance.

    Additional Attributes:
        ip_address: IP address of the device
        ip_port: Port number
        sensors: Relationship to Sensor models
    """
    __tablename__ = "controllers"

    # Foreign key to devices table
    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # Controller-specific fields
    ip_address = Column(String(50), nullable=False)
    ip_port = Column(Integer, nullable=False)

    # Polymorphic identity - use ENUM value
    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.CONTROLLER
    }

    # Relationship to sensors - explicitly specify foreign_keys to avoid ambiguity
    # with the inheritance FK (sensors.id -> devices.id)
    sensors = relationship(
        "Sensor",
        back_populates="controller",
        cascade="all, delete-orphan",
        foreign_keys="[Sensor.controller_id]"
    )

    def __repr__(self):
        return (
            f"<Controller(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}')>"
        )


class Sensor(Device):
    """
    Sensor model for managing sensor devices.
    Inherits from Device using Joined Table Inheritance.

    Additional Attributes:
        controller_id: Foreign key to Controller
        controller: Relationship to Controller model
    """
    __tablename__ = "sensors"

    # Foreign key to devices table
    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # Sensor-specific fields
    controller_id = Column(Integer, ForeignKey("controllers.id"), nullable=False, index=True)

    # Polymorphic identity - use ENUM value
    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.SENSOR
    }

    # Relationship to controller
    controller = relationship("Controller", back_populates="sensors", foreign_keys=[controller_id])

    def __repr__(self):
        return (
            f"<Sensor(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"controller_id={self.controller_id})>"
        )


class Camera(Device):
    """
    Camera model for managing IP camera devices.
    Inherits from Device using Joined Table Inheritance.

    Additional Attributes:
        ip_address: IP address of the camera
        ip_port: Port number
        user_name: Username for camera authentication
        user_password: Password for camera authentication
        urls: URL information (JSONB) - replaces rtsp_uri/rtsp_port (PRD_Camera_Urls_JsonB.md)
        mode: Camera operation mode (EnumCameraMode)
        category: Camera category/type (EnumCameraType)
        is_record: Recording enabled (default False)
        hardware_spec: Hardware specification (JSON)
        geolocation: GPS coordinates (JSON)
    """
    __tablename__ = "cameras"

    # Foreign key to devices table
    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # Camera-specific fields
    ip_address = Column(String(50), nullable=False)
    ip_port = Column(Integer, nullable=False)
    user_name = Column(String(100), nullable=True)  # PRD v1.2: nullable
    user_password = Column(String(200), nullable=True)  # PRD v1.2: nullable
    urls = Column(JSON, nullable=True)  # PRD_Camera_Urls_JsonB.md: replaces rtsp_uri/rtsp_port
    mode = Column(SQLEnum(EnumCameraMode), nullable=False, default=EnumCameraMode.NONE)
    category = Column(SQLEnum(EnumCameraType), nullable=False, default=EnumCameraType.NONE)

    # Phase 3: Camera 확장 필드 (PRD Section 3.2)
    is_record = Column(Boolean, nullable=False, default=False)
    hardware_spec = Column(JSON, nullable=True, default=None)
    geolocation = Column(JSON, nullable=True, default=None)

    # Polymorphic identity - use ENUM value
    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.CAMERA
    }

    # Relationship to CameraPreset
    presets = relationship("CameraPreset", back_populates="camera", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return (
            f"<Camera(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"mode='{self.mode.value}', category='{self.category.value}')>"
        )
