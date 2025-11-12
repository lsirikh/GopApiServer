"""
Device models: Controller, Sensor, Camera
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class EnumDeviceType(str, enum.Enum):
    """Device type enumeration"""
    NONE = "NONE"
    Controller = "Controller"
    Multi = "Multi"
    Fence = "Fence"
    Underground = "Underground"
    Contact = "Contact"
    PIR = "PIR"
    IoController = "IoController"
    Laser = "Laser"
    Cable = "Cable"
    IpCamera = "IpCamera"
    SmartSensor = "SmartSensor"
    SmartSensor2 = "SmartSensor2"
    SmartCompound = "SmartCompound"
    IpSpeaker = "IpSpeaker"
    Radar = "Radar"
    OpticalCable = "OpticalCable"
    Fence_Group = "Fence_Group"


class EnumDeviceStatus(str, enum.Enum):
    """Device status enumeration"""
    ACTIVATED = "ACTIVATED"
    ERROR = "ERROR"
    DEACTIVATED = "DEACTIVATED"


class EnumCameraMode(str, enum.Enum):
    """Camera mode enumeration"""
    NONE = "NONE"
    ONVIF = "ONVIF"
    EMSTONE_API = "EMSTONE_API"
    INNODEP_API = "INNODEP_API"
    ETC = "ETC"


class EnumCameraType(str, enum.Enum):
    """Camera type enumeration"""
    NONE = "NONE"
    FIXED = "FIXED"
    PTZ = "PTZ"
    FISHEYES = "FISHEYES"
    THERMAL = "THERMAL"


class Controller(Base):
    """
    Controller model for managing control devices

    Attributes:
        id: Primary key
        number_device: Device number identifier
        group_device: Device group identifier
        name_device: Device name
        type_device: Device type (EnumDeviceType)
        version: Device version
        status: Device status (EnumDeviceStatus)
        ip_address: IP address of the device
        ip_port: Port number
        created_at: Creation timestamp
        updated_at: Last update timestamp
        sensors: Relationship to Sensor models
    """
    __tablename__ = "controllers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number_device = Column(Integer, nullable=False, index=True)
    group_device = Column(Integer, nullable=False, index=True)
    name_device = Column(String(200), nullable=False)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(SQLEnum(EnumDeviceStatus), nullable=False, default=EnumDeviceStatus.ACTIVATED)
    ip_address = Column(String(50), nullable=False)
    ip_port = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to sensors
    sensors = relationship("Sensor", back_populates="controller", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Controller(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}')>"
        )


class Sensor(Base):
    """
    Sensor model for managing sensor devices

    Attributes:
        id: Primary key
        number_device: Device number identifier
        group_device: Device group identifier
        name_device: Device name
        type_device: Device type (EnumDeviceType)
        version: Device version
        status: Device status (EnumDeviceStatus)
        controller_id: Foreign key to Controller
        created_at: Creation timestamp
        updated_at: Last update timestamp
        controller: Relationship to Controller model
    """
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number_device = Column(Integer, nullable=False, index=True)
    group_device = Column(Integer, nullable=False, index=True)
    name_device = Column(String(200), nullable=False)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(SQLEnum(EnumDeviceStatus), nullable=False, default=EnumDeviceStatus.ACTIVATED)
    controller_id = Column(Integer, ForeignKey("controllers.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to controller
    controller = relationship("Controller", back_populates="sensors")

    def __repr__(self):
        return (
            f"<Sensor(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"controller_id={self.controller_id})>"
        )


class Camera(Base):
    """
    Camera model for managing IP camera devices

    Attributes:
        id: Primary key
        number_device: Device number identifier
        group_device: Device group identifier
        name_device: Device name
        type_device: Device type (EnumDeviceType)
        version: Device version
        status: Device status (EnumDeviceStatus)
        ip_address: IP address of the camera
        ip_port: Port number
        user_name: Username for camera authentication
        user_password: Password for camera authentication
        rtsp_uri: RTSP stream URI
        rtsp_port: RTSP port number
        mode: Camera operation mode (EnumCameraMode)
        category: Camera category/type (EnumCameraType)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number_device = Column(Integer, nullable=False, index=True)
    group_device = Column(Integer, nullable=False, index=True)
    name_device = Column(String(200), nullable=False)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(SQLEnum(EnumDeviceStatus), nullable=False, default=EnumDeviceStatus.ACTIVATED)
    ip_address = Column(String(50), nullable=False)
    ip_port = Column(Integer, nullable=False)
    user_name = Column(String(100), nullable=False)
    user_password = Column(String(200), nullable=False)
    rtsp_uri = Column(String(500), nullable=False)
    rtsp_port = Column(Integer, nullable=False)
    mode = Column(SQLEnum(EnumCameraMode), nullable=False, default=EnumCameraMode.NONE)
    category = Column(SQLEnum(EnumCameraType), nullable=False, default=EnumCameraType.NONE)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<Camera(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"mode='{self.mode.value}', category='{self.category.value}')>"
        )
