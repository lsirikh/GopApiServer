# PRD: Device Inheritance Structure Refactoring

## 문서 정보

| 항목 | 내용 |
|------|------|
| **문서 버전** | v1.3 |
| **작성일** | 2025-12-31 |
| **상위 PRD** | PRD_Device_Structure_Refactoring.md |
| **목적** | Device 상속 구조 및 ORM 구현 상세 명세 |

---

## 1. 개요

### 1.1 배경

기존 시스템에서는 Controller, Sensor, Camera가 완전히 독립된 테이블과 모델로 관리되었습니다. 이로 인해:

- **코드 중복**: 공통 필드(number_device, name_device, status 등)가 각 모델에 반복 정의
- **유지보수 어려움**: 공통 로직 변경 시 3개 모델 모두 수정 필요
- **확장성 제한**: 새로운 디바이스 타입 추가 시 전체 구조 재설계 필요
- **통합 조회 불가**: 모든 디바이스를 통합 조회하려면 UNION 쿼리 필요

### 1.2 목표

**Joined Table Inheritance** 패턴을 적용하여:

1. **Base Device 클래스** 정의: 모든 디바이스의 공통 속성 통합
2. **상속 기반 구조**: Controller, Sensor, Camera가 Base Device를 상속
3. **Polymorphic Query 지원**: 단일 쿼리로 모든 디바이스 타입 조회 가능
4. **확장성 확보**: 새 디바이스 타입 추가 시 상속만으로 구현

---

## 2. 상속 구조 설계

### 2.1 클래스 계층 구조

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Device (Base)                               │
│  ───────────────────────────────────────────────────────────────    │
│  id, category_device, number_device, group_device,                  │
│  name_device, type_device, version, status,                         │
│  created_at, updated_at                                             │
│                                                                      │
│  Discriminator: category_device                                      │
│  Polymorphic Identity: "device"                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐
│   Controller    │   │     Sensor      │   │        Camera           │
│  ─────────────  │   │  ─────────────  │   │  ─────────────────────  │
│  ip_address     │   │  controller_id  │   │  ip_address, ip_port    │
│  ip_port        │   │                 │   │  user_name, user_pwd    │
│                 │   │                 │   │  rtsp_uri, rtsp_port    │
│  Identity:      │   │  Identity:      │   │  mode, category         │
│  "controller"   │   │  "sensor"       │   │  is_record              │
│                 │   │                 │   │  hardware_spec (JSON)   │
│                 │   │                 │   │  geolocation (JSON)     │
│                 │   │                 │   │                         │
│                 │   │                 │   │  Identity: "camera"     │
└─────────────────┘   └─────────────────┘   └─────────────────────────┘
```

### 2.2 Discriminator 컬럼

**category_device** 컬럼이 각 디바이스 타입을 구분하는 식별자 역할을 수행합니다.

| 값 | 디바이스 타입 | 설명 |
|----|--------------|------|
| `device` | Device | 기본 타입 (직접 사용 안함) |
| `controller` | Controller | 센서 제어 장치 |
| `sensor` | Sensor | 감지 장치 |
| `camera` | Camera | 영상 감시 장치 |

---

## 3. 데이터베이스 테이블 구조

### 3.1 테이블 관계도

```
┌─────────────────────────────────────────────────────────────────────┐
│                          devices (Base Table)                        │
├─────────────────────────────────────────────────────────────────────┤
│  PK  id              INTEGER       AUTO_INCREMENT                    │
│      category_device VARCHAR(50)   NOT NULL, INDEX (Discriminator)  │
│      number_device   INTEGER       NOT NULL, INDEX                  │
│      group_device    INTEGER       NOT NULL, INDEX (Deprecated)     │
│      name_device     VARCHAR(200)  NOT NULL                         │
│      type_device     ENUM          NOT NULL                         │
│      version         VARCHAR(50)   NOT NULL                         │
│      status          ENUM          NOT NULL, DEFAULT 'ACTIVATED'    │
│      created_at      DATETIME      NOT NULL                         │
│      updated_at      DATETIME      NOT NULL                         │
└─────────────────────────────────────────────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐
│   controllers   │   │     sensors     │   │        cameras          │
├─────────────────┤   ├─────────────────┤   ├─────────────────────────┤
│ PK/FK id        │   │ PK/FK id        │   │ PK/FK id                │
│     ip_address  │   │ FK controller_id│   │     ip_address          │
│     ip_port     │   │                 │   │     ip_port             │
│                 │   │                 │   │     user_name           │
│                 │   │                 │   │     user_password       │
│                 │   │                 │   │     rtsp_uri            │
│                 │   │                 │   │     rtsp_port           │
│                 │   │                 │   │     mode                │
│                 │   │                 │   │     category            │
│                 │   │                 │   │     is_record           │
│                 │   │                 │   │     hardware_spec (JSON)│
│                 │   │                 │   │     geolocation (JSON)  │
└─────────────────┘   └─────────────────┘   └─────────────────────────┘
```

### 3.2 devices 테이블 (Base Table)

모든 디바이스의 공통 속성을 저장하는 기본 테이블입니다.

```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_device VARCHAR(50) NOT NULL,      -- Polymorphic Discriminator
    number_device INTEGER NOT NULL,              -- 디바이스 번호 (타입별 중복 가능)
    group_device INTEGER NOT NULL,              -- 레거시 그룹 (deprecated)
    name_device VARCHAR(200) NOT NULL,          -- 디바이스 이름
    type_device VARCHAR(50) NOT NULL,           -- 디바이스 타입 ENUM
    version VARCHAR(50) NULL,                   -- 펌웨어/소프트웨어 버전 (nullable)
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVATED',  -- 상태 ENUM
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX ix_devices_category_device ON devices(category_device);
CREATE INDEX ix_devices_number_device ON devices(number_device);
CREATE INDEX ix_devices_group_device ON devices(group_device);
```

### 3.3 controllers 테이블 (Child Table)

Controller 전용 속성을 저장합니다.

```sql
CREATE TABLE controllers (
    id INTEGER PRIMARY KEY,
    ip_address VARCHAR(50) NOT NULL,    -- 컨트롤러 IP 주소
    ip_port INTEGER NOT NULL,            -- 통신 포트

    FOREIGN KEY (id) REFERENCES devices(id) ON DELETE CASCADE
);
```

### 3.4 sensors 테이블 (Child Table)

Sensor 전용 속성을 저장합니다.

```sql
CREATE TABLE sensors (
    id INTEGER PRIMARY KEY,
    controller_id INTEGER NOT NULL,      -- 소속 컨트롤러 FK

    FOREIGN KEY (id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (controller_id) REFERENCES controllers(id)
);

CREATE INDEX ix_sensors_controller_id ON sensors(controller_id);
```

### 3.5 cameras 테이블 (Child Table)

Camera 전용 속성 및 확장 필드(JSON)를 저장합니다.

```sql
CREATE TABLE cameras (
    id INTEGER PRIMARY KEY,
    ip_address VARCHAR(50) NOT NULL,
    ip_port INTEGER NOT NULL,
    user_name VARCHAR(100) NULL,         -- 카메라 인증 사용자명 (nullable)
    user_password VARCHAR(200) NULL,     -- 카메라 인증 비밀번호 (nullable)
    rtsp_uri VARCHAR(500) NULL,          -- RTSP 스트림 URI (nullable)
    rtsp_port INTEGER NOT NULL DEFAULT 554,
    mode VARCHAR(50) NOT NULL DEFAULT 'NONE',
    category VARCHAR(50) NOT NULL DEFAULT 'NONE',
    is_record BOOLEAN NOT NULL DEFAULT FALSE,
    hardware_spec JSON,                  -- 확장 필드: 하드웨어 스펙
    geolocation JSON,                    -- 확장 필드: 좌표 정보

    FOREIGN KEY (id) REFERENCES devices(id) ON DELETE CASCADE
);
```

---

## 4. SQLAlchemy ORM 구현

### 4.1 Device Base Model

```python
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.enums import EnumDeviceType, EnumDeviceStatus
from app.core.config import settings
from datetime import datetime

class Device(Base):
    """
    Device Base Model - Polymorphic Parent

    모든 디바이스 타입(Controller, Sensor, Camera)의 부모 클래스입니다.
    Joined Table Inheritance 패턴을 사용하여 공통 필드를 통합 관리합니다.

    Discriminator: category_device
    - "controller": Controller 클래스
    - "sensor": Sensor 클래스
    - "camera": Camera 클래스
    """
    __tablename__ = "devices"

    # ===== Primary Key =====
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ===== Polymorphic Discriminator =====
    category_device = Column(
        String(50),
        nullable=False,
        index=True,
        doc="디바이스 분류 (controller/sensor/camera)"
    )

    # ===== Common Fields =====
    number_device = Column(
        Integer,
        nullable=False,
        index=True,
        doc="디바이스 번호 (타입별 중복 가능)"
    )

    group_device = Column(
        Integer,
        nullable=False,
        index=True,
        doc="레거시 그룹 번호 (deprecated, group_ids 사용 권장)"
    )

    name_device = Column(
        String(200),
        nullable=False,
        doc="디바이스 이름"
    )

    type_device = Column(
        SQLEnum(EnumDeviceType),
        nullable=False,
        doc="디바이스 타입 (Controller/Fence/Pir/IpCamera 등)"
    )

    version = Column(
        String(50),
        nullable=True,
        doc="펌웨어/소프트웨어 버전 (nullable)"
    )

    status = Column(
        SQLEnum(EnumDeviceStatus),
        nullable=False,
        default=EnumDeviceStatus.ACTIVATED,
        doc="디바이스 상태 (ACTIVATED/DEACTIVATED/MAINTENANCE)"
    )

    # ===== Timestamps =====
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        onupdate=lambda: datetime.now(settings.tz),
        nullable=False
    )

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_on": category_device,  # Discriminator 컬럼 지정
        "polymorphic_identity": "device"     # Base 클래스 identity
    }
```

### 4.2 Controller Model (상속 클래스)

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Controller(Device):
    """
    Controller Model - Inherits from Device

    센서를 관리하는 상위 제어 장치입니다.
    Device의 모든 필드를 상속받고, 추가로 IP 통신 정보를 가집니다.

    Polymorphic Identity: "controller"
    """
    __tablename__ = "controllers"

    # ===== Primary Key (FK to devices) =====
    id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True,
        doc="디바이스 ID (devices.id 참조)"
    )

    # ===== Controller-Specific Fields =====
    ip_address = Column(
        String(50),
        nullable=False,
        doc="컨트롤러 IP 주소"
    )

    ip_port = Column(
        Integer,
        nullable=False,
        doc="통신 포트 번호"
    )

    # ===== Relationships =====
    sensors = relationship(
        "Sensor",
        back_populates="controller",
        cascade="all, delete-orphan",
        doc="소속 센서 목록"
    )

    device_group_mappings = relationship(
        "DeviceGroupMapping",
        primaryjoin="and_(Controller.id == foreign(DeviceGroupMapping.device_id), "
                   "DeviceGroupMapping.category_device == 'controller')",
        viewonly=True,
        doc="디바이스 그룹 매핑 (N:N)"
    )

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "controller"  # Discriminator 값
    }
```

### 4.3 Sensor Model (상속 클래스)

```python
class Sensor(Device):
    """
    Sensor Model - Inherits from Device

    Controller에 종속된 감지 장치입니다.
    Device의 모든 필드를 상속받고, 소속 컨트롤러 정보를 가집니다.

    Polymorphic Identity: "sensor"
    """
    __tablename__ = "sensors"

    # ===== Primary Key (FK to devices) =====
    id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True
    )

    # ===== Sensor-Specific Fields =====
    controller_id = Column(
        Integer,
        ForeignKey("controllers.id"),
        nullable=False,
        index=True,
        doc="소속 컨트롤러 ID"
    )

    # ===== Relationships =====
    controller = relationship(
        "Controller",
        back_populates="sensors",
        doc="소속 컨트롤러"
    )

    device_group_mappings = relationship(
        "DeviceGroupMapping",
        primaryjoin="and_(Sensor.id == foreign(DeviceGroupMapping.device_id), "
                   "DeviceGroupMapping.category_device == 'sensor')",
        viewonly=True
    )

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "sensor"
    }
```

### 4.4 Camera Model (상속 클래스 + 확장 필드)

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy import Enum as SQLEnum
from app.models.enums import EnumCameraMode, EnumCameraType

class Camera(Device):
    """
    Camera Model - Inherits from Device with Extended Fields

    영상 감시 장치입니다.
    Device의 모든 필드를 상속받고, 추가로:
    - IP/RTSP 통신 정보
    - 카메라 모드/카테고리
    - 확장 필드 (hardware_spec, geolocation - JSON)

    Polymorphic Identity: "camera"

    Extended Fields (JSON Composite Types):
    - hardware_spec: 하드웨어 스펙 정보
    - geolocation: 좌표/위치 정보
    """
    __tablename__ = "cameras"

    # ===== Primary Key (FK to devices) =====
    id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True
    )

    # ===== Network Fields =====
    ip_address = Column(String(50), nullable=False, doc="카메라 IP 주소")
    ip_port = Column(Integer, nullable=False, doc="HTTP 포트")

    # ===== Authentication Fields (nullable) =====
    user_name = Column(String(100), nullable=True, doc="접속 사용자명 (nullable)")
    user_password = Column(String(200), nullable=True, doc="접속 비밀번호 (nullable)")

    # ===== RTSP Fields =====
    rtsp_uri = Column(String(500), nullable=True, doc="RTSP 스트림 URI (nullable)")
    rtsp_port = Column(Integer, nullable=False, default=554, doc="RTSP 포트")

    # ===== Camera Configuration =====
    mode = Column(
        SQLEnum(EnumCameraMode),
        nullable=False,
        default=EnumCameraMode.NONE,
        doc="카메라 모드 (NONE/ONVIF/RTSP)"
    )

    category = Column(
        SQLEnum(EnumCameraType),
        nullable=False,
        default=EnumCameraType.NONE,
        doc="카메라 카테고리 (NONE/PTZ/FIXED/THERMAL)"
    )

    # ===== Extended Fields (Phase 3) =====
    is_record = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="녹화 활성화 여부"
    )

    hardware_spec = Column(
        JSON,
        nullable=True,
        default=None,
        doc="하드웨어 스펙 정보 (JSON Composite Type)"
    )

    geolocation = Column(
        JSON,
        nullable=True,
        default=None,
        doc="좌표/위치 정보 (JSON Composite Type)"
    )

    # ===== Relationships =====
    device_group_mappings = relationship(
        "DeviceGroupMapping",
        primaryjoin="and_(Camera.id == foreign(DeviceGroupMapping.device_id), "
                   "DeviceGroupMapping.category_device == 'camera')",
        viewonly=True
    )

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "camera"
    }
```

---

## 5. Camera 확장 필드 (JSON Composite Types)

### 5.1 HardwareSpec 구조

카메라 하드웨어의 상세 스펙 정보를 저장합니다.

```python
# Pydantic Schema
class HardwareSpec(BaseModel):
    """
    카메라 하드웨어 스펙 정보 (Composite Type)
    JSON 컬럼에 저장되는 중첩 객체
    """
    name: Optional[str] = Field(
        None,
        max_length=200,
        description="하드웨어 이름"
    )
    location: Optional[str] = Field(
        None,
        max_length=500,
        description="설치 위치"
    )
    manufacturer: Optional[str] = Field(
        None,
        max_length=200,
        description="제조사"
    )
    model: Optional[str] = Field(
        None,
        max_length=200,
        description="모델명"
    )
    hardware: Optional[str] = Field(
        None,
        max_length=200,
        description="하드웨어 정보"
    )
    firmware: Optional[str] = Field(
        None,
        max_length=100,
        description="펌웨어 버전"
    )
    device_id: Optional[str] = Field(
        None,
        max_length=200,
        description="장치 ID"
    )
    mac_address: Optional[str] = Field(
        None,
        max_length=17,
        description="MAC 주소 (XX:XX:XX:XX:XX:XX)"
    )
    onvif_version: Optional[str] = Field(
        None,
        max_length=50,
        description="ONVIF 버전"
    )

    model_config = ConfigDict(from_attributes=True)
```

**JSON 저장 예시:**
```json
{
    "name": "GOP 1구역 PTZ 카메라",
    "location": "GOP 1구역 전방 초소 상단",
    "manufacturer": "Hanwha Vision",
    "model": "XNP-6320RH",
    "hardware": "PTZ 32x Optical Zoom",
    "firmware": "2.41.01",
    "device_id": "HWV-XNP-001",
    "mac_address": "00:09:18:AB:CD:EF",
    "onvif_version": "2.4.2"
}
```

### 5.2 Geolocation 구조

카메라 설치 위치의 좌표 정보를 저장합니다.

```python
# Pydantic Schema
class Geolocation(BaseModel):
    """
    좌표 정보 (Composite Type)
    JSON 컬럼에 저장되는 중첩 객체
    """
    location: Optional[str] = Field(
        None,
        max_length=500,
        description="설치 위치 (예: GOP 1구역 전방 초소)"
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="위도"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="경도"
    )
    altitude: Optional[float] = Field(
        None,
        description="고도 (미터)"
    )

    model_config = ConfigDict(from_attributes=True)
```

**JSON 저장 예시:**
```json
{
    "location": "GOP 1구역 전방 초소",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 245.5
}
```

---

## 6. N:N 관계 (DeviceGroup Mapping)

### 6.1 Junction Table 구조

디바이스와 그룹 간의 다대다(N:N) 관계를 지원합니다.

```
┌─────────────────┐         ┌─────────────────────────┐         ┌─────────────────┐
│    devices      │         │  device_group_mappings  │         │  device_groups  │
├─────────────────┤         ├─────────────────────────┤         ├─────────────────┤
│ PK id           │◄────────│ FK device_id            │         │ PK id           │
│    category_    │         │    category_device      │         │    name         │
│    device       │         │ FK group_id             │────────►│    description  │
│    ...          │         │    created_at           │         │    created_at   │
└─────────────────┘         └─────────────────────────┘         │    updated_at   │
                                                                 └─────────────────┘
```

### 6.2 DeviceGroupMapping Model

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class DeviceGroupMapping(Base):
    """
    Device-Group N:N 관계 Junction Table

    하나의 디바이스는 여러 그룹에 속할 수 있고,
    하나의 그룹은 여러 디바이스를 포함할 수 있습니다.

    Unique Constraint: (device_id, category_device, group_id)
    """
    __tablename__ = "device_group_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ===== Device Reference (Polymorphic) =====
    device_id = Column(
        Integer,
        nullable=False,
        index=True,
        doc="디바이스 ID (devices.id 참조)"
    )

    category_device = Column(
        String(50),
        nullable=False,
        index=True,
        doc="디바이스 분류 (controller/sensor/camera)"
    )

    # ===== Group Reference =====
    group_id = Column(
        Integer,
        ForeignKey("device_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="그룹 ID"
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False
    )

    # ===== Relationships =====
    group = relationship("DeviceGroup", back_populates="device_mappings")

    # ===== Unique Constraint =====
    __table_args__ = (
        UniqueConstraint(
            'device_id',
            'category_device',
            'group_id',
            name='uq_device_category_group'
        ),
    )
```

### 6.3 사용 예시

**디바이스 생성 시 그룹 할당:**
```python
# POST /devices/controllers
{
    "number_device": 1,
    "group_device": 1,
    "name_device": "Main Controller",
    "type_device": "Controller",
    "version": "1.0.0",
    "status": "ACTIVATED",
    "ip_address": "192.168.1.100",
    "ip_port": 8080,
    "group_ids": [1, 2, 3]  # N:N 관계로 여러 그룹에 할당
}
```

---

## 7. Polymorphic Query 패턴

### 7.1 기본 조회 (특정 타입)

```python
# Controller만 조회
controllers = db.query(Controller).all()

# Sensor만 조회
sensors = db.query(Sensor).filter(Sensor.controller_id == 1).all()

# Camera만 조회
cameras = db.query(Camera).filter(Camera.status == "ACTIVATED").all()
```

### 7.2 통합 조회 (모든 디바이스)

```python
# 모든 디바이스 조회 (polymorphic query)
all_devices = db.query(Device).all()

# 각 디바이스는 실제 타입으로 반환됨
for device in all_devices:
    print(f"Type: {type(device).__name__}, Name: {device.name_device}")

    if isinstance(device, Camera):
        print(f"  Camera Mode: {device.mode}")
    elif isinstance(device, Controller):
        print(f"  IP: {device.ip_address}")
```

### 7.3 조건부 조회

```python
# status로 필터링 (모든 디바이스 타입)
active_devices = db.query(Device).filter(
    Device.status == EnumDeviceStatus.ACTIVATED
).all()

# category_device로 특정 타입 필터링
only_cameras = db.query(Device).filter(
    Device.category_device == "camera"
).all()
```

---

## 8. ENUM 타입 정의

### 8.1 EnumDeviceCategory (Polymorphic Discriminator)

**category_device** 컬럼을 ENUM으로 관리하여 타입 안전성을 확보합니다.

```python
from enum import Enum

class EnumDeviceCategory(str, Enum):
    """
    디바이스 카테고리 열거형 (Polymorphic Discriminator)

    Joined Table Inheritance의 discriminator 값으로 사용됩니다.
    새로운 디바이스 타입 추가 시 이 ENUM에 값을 추가해야 합니다.
    """
    CONTROLLER = "controller"
    SENSOR = "sensor"
    CAMERA = "camera"
```

**ENUM 사용의 장점:**

| 장점 | 설명 |
|------|------|
| **타입 안전성** | 잘못된 값 입력 방지 (`"cotroller"` 같은 오타 차단) |
| **IDE 자동완성** | 개발 시 유효한 값 제안 |
| **일관성** | 다른 필드들(`type_device`, `status`)과 동일한 패턴 |
| **API 문서화** | Swagger/OpenAPI에서 허용 값이 명확히 표시 |
| **리팩토링 안전** | 값 변경 시 컴파일/린트 타임에 오류 감지 |

**ORM 적용:**

```python
from sqlalchemy import Enum as SQLEnum

class Device(Base):
    __tablename__ = "devices"

    # ENUM 타입으로 Discriminator 정의
    category_device = Column(
        SQLEnum(EnumDeviceCategory),
        nullable=False,
        index=True,
        doc="디바이스 분류 (controller/sensor/camera)"
    )

    __mapper_args__ = {
        "polymorphic_on": category_device,
        "polymorphic_identity": EnumDeviceCategory.CONTROLLER  # 또는 문자열 "controller"
    }
```

**DeviceGroupMapping 적용:**

```python
class DeviceGroupMapping(Base):
    __tablename__ = "device_group_mappings"

    # ENUM 타입으로 category_device 정의
    category_device = Column(
        SQLEnum(EnumDeviceCategory),
        nullable=False,
        index=True,
        doc="디바이스 분류"
    )
```

**라우터에서 사용:**

```python
# Before (문자열 하드코딩 - 오타 위험)
mapping = DeviceGroupMapping(
    device_id=device_id,
    category_device="controller",  # 오타 가능
    group_id=group_id
)

# After (ENUM 사용 - 타입 안전)
from app.utils.enums import EnumDeviceCategory

mapping = DeviceGroupMapping(
    device_id=device_id,
    category_device=EnumDeviceCategory.CONTROLLER,  # IDE 자동완성
    group_id=group_id
)
```

---

### 8.2 기타 ENUM 타입 참조

아래 ENUM 타입들은 기존 `GOP_Restful_Api_연동설계.md` 문서를 기반으로 정의되어 있습니다.
전체 정의는 `app/utils/enums.py` 파일을 참조하세요.

| ENUM 클래스 | 설명 | 주요 값 |
|-------------|------|---------|
| `EnumDeviceType` | 디바이스 타입 | Controller, Fence, PIR, IpCamera 등 18종 |
| `EnumDeviceStatus` | 디바이스 상태 | ACTIVATED, ERROR, DEACTIVATED |
| `EnumCameraMode` | 카메라 연결 모드 | NONE, ONVIF, EMSTONE_API, INNODEP_API, ETC |
| `EnumCameraType` | 카메라 카테고리 | NONE, FIXED, PTZ |

> **참조 문서**: `docs/GOP_Restful_Api_연동설계.md`
> **구현 파일**: `app/utils/enums.py`

---

## 9. API Schema 설계

### 9.1 Create Schema 예시 (Camera)

```python
class CameraCreate(BaseModel):
    """카메라 생성 스키마"""

    # ===== Device Base Fields =====
    number_device: int = Field(..., description="장치 번호")
    group_device: int = Field(..., description="장치 그룹 번호 (레거시)")
    name_device: str = Field(..., max_length=200, description="장치 이름")
    type_device: str = Field(..., description="장치 타입 (IpCamera)")
    version: str = Field(..., max_length=50, description="버전")
    status: str = Field(..., description="상태 (ACTIVATED|DEACTIVATED|MAINTENANCE)")

    # ===== Camera-Specific Fields =====
    ip_address: str = Field(..., description="카메라 IP 주소")
    ip_port: int = Field(..., ge=1, le=65535, description="HTTP 포트")
    user_name: str = Field(..., description="접속 사용자명")
    user_password: str = Field(..., description="접속 비밀번호")
    rtsp_uri: str = Field(..., description="RTSP 스트림 URI")
    rtsp_port: int = Field(554, ge=1, le=65535, description="RTSP 포트")
    mode: str = Field(..., description="카메라 모드 (NONE|ONVIF|RTSP)")
    category: str = Field(..., description="카메라 카테고리 (NONE|PTZ|FIXED|THERMAL)")

    # ===== Extended Fields =====
    is_record: bool = Field(False, description="녹화 활성화 여부")
    hardware_spec: Optional[HardwareSpec] = Field(None, description="하드웨어 스펙")
    geolocation: Optional[Geolocation] = Field(None, description="좌표 정보")

    # ===== N:N Relationship =====
    group_ids: Optional[List[int]] = Field(None, description="소속 그룹 ID 배열")
```

### 9.2 Response Schema 예시 (Camera)

```python
class CameraResponse(BaseModel):
    """카메라 응답 스키마"""

    # ===== All Fields + Timestamps =====
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: str
    status: str
    ip_address: str
    ip_port: int
    user_name: str
    user_password: str
    rtsp_uri: str
    rtsp_port: int
    mode: str
    category: str
    is_record: bool
    hardware_spec: Optional[HardwareSpec]
    geolocation: Optional[Geolocation]
    created_at: datetime
    updated_at: datetime

    # ===== N:N Relationship =====
    device_groups: List[DeviceGroupResponse] = []

    model_config = ConfigDict(from_attributes=True)
```

---

## 10. 마이그레이션 전략

### 10.1 단계별 마이그레이션

```
Phase 1: 기존 테이블 백업
    └── controllers_backup, sensors_backup, cameras_backup 생성

Phase 2: 새 테이블 구조 생성
    └── devices (base), controllers, sensors, cameras 생성

Phase 3: 데이터 마이그레이션
    └── 기존 데이터를 새 구조로 이전
    └── devices 테이블에 공통 필드 삽입
    └── 각 child 테이블에 전용 필드 삽입

Phase 4: 관계 테이블 생성
    └── device_groups, device_group_mappings 생성
    └── group_device → device_group_mappings 마이그레이션

Phase 5: 검증 및 정리
    └── 데이터 무결성 검증
    └── 백업 테이블 삭제 (선택)
```

### 10.2 데이터 마이그레이션 SQL

```sql
-- Phase 3: Controller 마이그레이션
INSERT INTO devices (category_device, number_device, group_device, name_device,
                     type_device, version, status, created_at, updated_at)
SELECT 'controller', number_device, group_device, name_device,
       type_device, version, status, created_at, updated_at
FROM controllers_backup;

INSERT INTO controllers (id, ip_address, ip_port)
SELECT d.id, cb.ip_address, cb.ip_port
FROM devices d
JOIN controllers_backup cb ON d.number_device = cb.number_device
WHERE d.category_device = 'controller';
```

---

## 11. 테스트 전략 (TDD)

### 11.1 Unit Tests

```python
# tests/test_device_inheritance.py

def test_controller_inherits_from_device():
    """Controller가 Device를 상속하는지 확인"""
    assert issubclass(Controller, Device)
    assert Controller.__mapper_args__["polymorphic_identity"] == "controller"

def test_sensor_inherits_from_device():
    """Sensor가 Device를 상속하는지 확인"""
    assert issubclass(Sensor, Device)
    assert Sensor.__mapper_args__["polymorphic_identity"] == "sensor"

def test_camera_inherits_from_device():
    """Camera가 Device를 상속하는지 확인"""
    assert issubclass(Camera, Device)
    assert Camera.__mapper_args__["polymorphic_identity"] == "camera"

def test_camera_has_extended_fields():
    """Camera가 확장 필드를 가지는지 확인"""
    camera_columns = [c.name for c in Camera.__table__.columns]
    assert "is_record" in camera_columns
    assert "hardware_spec" in camera_columns
    assert "geolocation" in camera_columns
```

### 11.2 Integration Tests

```python
def test_polymorphic_query(db_session):
    """Polymorphic query가 정상 동작하는지 확인"""
    # Create devices
    controller = Controller(number_device=1, name_device="Ctrl1", ...)
    sensor = Sensor(number_device=2, name_device="Sensor1", ...)
    camera = Camera(number_device=3, name_device="Cam1", ...)

    db_session.add_all([controller, sensor, camera])
    db_session.commit()

    # Query all devices
    all_devices = db_session.query(Device).all()

    assert len(all_devices) == 3
    assert isinstance(all_devices[0], Controller)
    assert isinstance(all_devices[1], Sensor)
    assert isinstance(all_devices[2], Camera)
```

---

## 12. 성능 고려사항

### 12.1 인덱스 전략

| 컬럼 | 인덱스 타입 | 용도 |
|------|------------|------|
| devices.id | PRIMARY KEY | 기본 조회 |
| devices.category_device | INDEX | Polymorphic 필터링 |
| devices.number_device | INDEX | 디바이스 번호 조회 |
| devices.group_device | INDEX | 레거시 그룹 필터링 |
| sensors.controller_id | INDEX | 컨트롤러별 센서 조회 |
| device_group_mappings.device_id | INDEX | 디바이스별 그룹 조회 |
| device_group_mappings.group_id | INDEX | 그룹별 디바이스 조회 |

### 12.2 JOIN 최적화

```python
# Eager loading으로 N+1 문제 방지
controllers = db.query(Controller).options(
    joinedload(Controller.sensors),
    joinedload(Controller.device_group_mappings)
).all()
```

---

## 13. 참조 문서

| 문서 | 설명 |
|------|------|
| PRD_Device_Structure_Refactoring.md | 상위 PRD (전체 구조) |
| Device_Refactoring_Final_Report.md | 구현 완료 리포트 |
| SQLAlchemy Joined Table Inheritance | [공식 문서](https://docs.sqlalchemy.org/en/20/orm/inheritance.html#joined-table-inheritance) |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2025-12-31 | 초기 버전 작성 |
| v1.1 | 2025-12-31 | Section 8.1 EnumDeviceCategory 추가 (Polymorphic Discriminator ENUM 관리) |
| v1.2 | 2025-12-31 | Nullable 필드 수정: version, user_name, user_password, rtsp_uri |
| v1.3 | 2025-12-31 | Section 8.2~8.5 삭제, GOP_Restful_Api_연동설계.md 참조로 대체 |
