"""
Device models: Device (Base), Controller, Sensor, Camera, Speaker, Enclosure, Lamp
PRD: PRD_Device_Structure_Refactoring.md - Section 3.1
PRD: PRD_Enclosure_Device.md v1.1 - Enclosure Device
PRD: PRD_Lamp_Device.md v1.1 - Lamp Device (경광등)

Polymorphic Inheritance using Joined Table strategy.
- Device: Base table with common fields + category_device discriminator
- Controller, Sensor, Camera, Speaker, Enclosure, Lamp: Child tables with specific fields
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory, EnumSpeakerType, EnumDoorStatus


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
        - "speaker" -> Speaker
        - "enclosure" -> Enclosure
        - "lamp" -> Lamp
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
    is_enable = Column(Boolean, nullable=False, default=True)  # PRD_Device_IsEnable_Field.md: 장비 활성화 여부
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
    geolocation = Column(JSON, nullable=True, default=None)  # PRD_Controller_Sensor_Geolocation.md

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
    geolocation = Column(JSON, nullable=True, default=None)  # PRD_Controller_Sensor_Geolocation.md

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
    # Relationship to CameraSetting (PRD_Device_Setting.md)
    setting = relationship("CameraSetting", back_populates="camera", cascade="all, delete-orphan", uselist=False)

    def __repr__(self):
        return (
            f"<Camera(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"mode='{self.mode.value}', category='{self.category.value}')>"
        )


class Speaker(Device):
    """
    Speaker model for managing IP Speaker devices.
    Inherits from Device using Joined Table Inheritance.

    PRD: PRD_Speaker_Device.md - Section 4.1, 4.2
    PRD: PRD_Speaker_Geolocation.md v1.0 - geolocation JSONB 추가

    Additional Attributes:
        speaker_type: Speaker type (EnumSpeakerType: NORMAL, ADMIN, MONITOR, DEV)
        server_id: FK to Server (SPEAKER_API type), SET NULL on delete
        description: Description text
        geolocation: JSONB for location info (v2.6)
    """
    __tablename__ = "speakers"

    # Foreign key to devices table (Joined Table Inheritance)
    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # Speaker-specific fields
    speaker_type = Column(
        SQLEnum(EnumSpeakerType),
        nullable=False,
        default=EnumSpeakerType.NORMAL
    )
    server_id = Column(
        Integer,
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    description = Column(String(500), nullable=True)
    # PRD_Speaker_Geolocation.md v1.0: 위치 정보 JSONB
    geolocation = Column(JSON, nullable=True, default=None)

    # Polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.SPEAKER
    }

    # Relationship to Server
    server = relationship("Server", foreign_keys=[server_id])

    # Relationship to EventMappingSpeaker (PRD: PRD_EventMappingSpeaker.md v1.0)
    event_mapping_speakers = relationship("EventMappingSpeaker", back_populates="speaker")

    def __repr__(self):
        return (
            f"<Speaker(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"speaker_type='{self.speaker_type.value}', server_id={self.server_id})>"
        )


class Enclosure(Device):
    """
    함체관리장비 모델 (Enclosure Device)
    Inherits from Device using Joined Table Inheritance.

    PRD: PRD_Enclosure_Device.md v1.1

    상속 필드 (Device):
        - status: EnumDeviceStatus (ACTIVATED/DEACTIVATED/ERROR) - 장비 운영 상태
        - number_device, name_device, type_device, etc.

    고유 필드 (Enclosure):
        - door_status: EnumDoorStatus (CLOSED/OPEN) - 도어 물리적 상태 (센서 감지)
        - geolocation: JSONB - 위치 정보 (location, latitude, longitude, altitude)
        - threshold_config: JSONB - 알람 임계값 설정
        - heater_enabled: Boolean - 히터 활성화 상태
        - fan_enabled: Boolean - 팬 활성화 상태

    Note: 실시간 측정 데이터(temperature, humidity 등)는 enclosure_metrics 테이블로 분리됨
          (PRD_Enclosure_Metrics_Separation.md v1.0)

    운영 로직:
        - status=ACTIVATED + door_status=OPEN → 비정상 개방 알람 발생
        - status=DEACTIVATED + door_status=OPEN → 점검 중이므로 알람 무시
        - status=ERROR → 함체 이상 상태
    """
    __tablename__ = "enclosures"

    # Foreign key to devices table (Joined Table Inheritance)
    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # Enclosure-specific fields
    door_status = Column(
        SQLEnum(EnumDoorStatus),
        nullable=False,
        default=EnumDoorStatus.CLOSED,
        comment="도어 물리적 상태 (CLOSED/OPEN) - 센서 감지"
    )
    # detail_info 제거됨 → enclosure_metrics 테이블로 분리 (PRD_Enclosure_Metrics_Separation.md v1.0)
    geolocation = Column(
        JSON,
        nullable=True,
        default=None,
        comment="위치 정보 (location, latitude, longitude, altitude)"
    )
    threshold_config = Column(
        JSON,
        nullable=True,
        default=None,
        comment="알람 임계값 설정"
    )
    heater_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="히터 활성화 상태"
    )
    fan_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="팬 활성화 상태"
    )

    # Polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.ENCLOSURE
    }

    def __repr__(self):
        return (
            f"<Enclosure(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"door_status='{self.door_status.value}')>"
        )

    # Relationship to EnclosureMetric (1:N, CASCADE DELETE)
    metrics = relationship(
        "EnclosureMetric",
        back_populates="enclosure",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )


class EnclosureMetric(Base):
    """
    함체 환경 모니터링 메트릭 모델 (Time-series)
    PRD: PRD_Enclosure_Metrics_Separation.md v1.0

    실시간 측정값을 별도 테이블로 분리하여 자산 데이터와 분리 저장.
    Enclosure 삭제 시 CASCADE DELETE.

    Attributes:
        id: Primary key
        enclosure_id: FK to Enclosure (CASCADE DELETE)
        temperature: 온도 (°C)
        humidity: 습도 (%)
        current: 전류 (A)
        voltage: 전압 (V)
        vibration: 진동 레벨 (0-100)
        ups_battery_level: UPS 배터리 잔량 (%)
        ups_charging: UPS 충전 중 여부
        detail: 추가 상세 정보 (JSONB)
        created_at: 레코드 생성 시각
    """
    __tablename__ = "enclosure_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    enclosure_id = Column(
        Integer,
        ForeignKey("enclosures.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    temperature = Column(String(10), nullable=True)  # Decimal(5,2) as string for SQLite compatibility
    humidity = Column(String(10), nullable=True)
    current = Column(String(10), nullable=True)
    voltage = Column(String(10), nullable=True)
    vibration = Column(Integer, nullable=True)
    ups_battery_level = Column(Integer, nullable=True)
    ups_charging = Column(Boolean, nullable=True)
    detail = Column(JSON, nullable=True, default=None)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)

    # Relationship to Enclosure
    enclosure = relationship("Enclosure", back_populates="metrics")

    def __repr__(self):
        return (
            f"<EnclosureMetric(id={self.id}, enclosure_id={self.enclosure_id}, "
            f"temperature={self.temperature}, created_at='{self.created_at}')>"
        )


class Lamp(Device):
    """
    경광등 모델 (Lamp Device)
    Inherits from Device using Joined Table Inheritance.

    PRD: PRD_Lamp_Device.md v1.1

    상속 필드 (Device):
        - status: EnumDeviceStatus (ACTIVATED/DEACTIVATED/ERROR) - 장비 운영 상태
        - number_device, name_device, type_device, is_enable, etc.

    고유 필드 (Lamp):
        - ip_address: IP 주소 (IPv4/IPv6)
        - ip_port: 포트 번호 (기본값: 80)
        - user_name: 접속 사용자명
        - user_password: 접속 비밀번호
        - description: 설명 (설치 위치 정보 등)
        - geolocation: JSONB - 위치 정보 (location, latitude, longitude, altitude)
    """
    __tablename__ = "lamps"

    # Foreign key to devices table (Joined Table Inheritance)
    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # Lamp-specific fields
    ip_address = Column(String(45), nullable=False, comment="IP 주소 (IPv4/IPv6)")
    ip_port = Column(Integer, nullable=False, default=80, comment="포트 번호")
    user_name = Column(String(100), nullable=True, comment="접속 사용자명")
    user_password = Column(String(255), nullable=True, comment="접속 비밀번호")
    description = Column(String(500), nullable=True, comment="설명")
    geolocation = Column(
        JSON,
        nullable=True,
        default=None,
        comment="위치 정보 (location, latitude, longitude, altitude)"
    )

    # Polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.LAMP
    }

    # Relationship to EventMappingLamp (PRD: PRD_Lamp_Device.md v1.1)
    event_mapping_lamps = relationship("EventMappingLamp", back_populates="lamp")

    def __repr__(self):
        return (
            f"<Lamp(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"ip_address='{self.ip_address}')>"
        )
