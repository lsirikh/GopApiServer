# PRD: Lamp Device 및 EventMappingLamp 추가

**문서 버전**: v1.1
**작성일**: 2026-01-26
**상태**: Draft

---

## 1. 개요

### 1.1 목적

GOP 시스템에 경광등(Lamp) 장비를 새로운 Device 타입으로 추가하고, 이벤트 발생 시 경광등 연동을 위한 EventMappingLamp 기능을 구현한다.

### 1.2 배경

- 현재 Device 계층: Controller, Sensor, Camera, Speaker, Enclosure
- 이벤트 연동: EventMappingCamera (카메라 프리셋), EventMappingSpeaker (방송)
- **신규 요구사항**: 이벤트 발생 시 경광등 점등/부저 연동 기능 필요

### 1.3 범위

1. **Lamp Device**: Device Joined Table Inheritance 확장
2. **EventMappingLamp**: EventMapping에 연동된 경광등 설정
3. **Enum 추가**: EnumDeviceType 확장, Lamp 관련 Enum 신규
4. **문서 업데이트**: GOP_스키마_전체.md, GOP_Restful_Api_연동설계.md

---

## 2. Enum 정의

### 2.1 EnumDeviceType 확장

기존 EnumDeviceType에 `Lamp`, `Enclosure` 항목을 추가한다.

**파일**: `app/utils/enums.py`

```python
class EnumDeviceType(str, Enum):
    """Device type enumeration"""
    # 기존 항목
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

    # 신규 추가 (v3.4)
    Lamp = "Lamp"              # 경광등
    Enclosure = "Enclosure"    # 함체
```

### 2.2 EnumDeviceCategory 확장

**파일**: `app/utils/enums.py`

```python
class EnumDeviceCategory(str, Enum):
    """Device category for polymorphic inheritance"""
    CONTROLLER = "controller"
    SENSOR = "sensor"
    CAMERA = "camera"
    SPEAKER = "speaker"
    ENCLOSURE = "enclosure"
    LAMP = "lamp"  # 신규 추가
```

### 2.3 EnumLampColor (신규)

**파일**: `app/utils/enums.py`

```python
class EnumLampColor(str, Enum):
    """Lamp color enumeration"""
    RED = "Red"
    ORANGE = "Orange"
    GREEN = "Green"
    BLUE = "Blue"
    WHITE = "White"
```

| 값 | 설명 |
|----|------|
| Red | 빨간색 (위험/침입) |
| Orange | 주황색 (경고) |
| Green | 녹색 (정상/안전) |
| Blue | 파란색 (정보) |
| White | 흰색 (일반) |

### 2.4 EnumBuzzerSound (신규)

**파일**: `app/utils/enums.py`

```python
class EnumBuzzerSound(str, Enum):
    """Buzzer sound pattern enumeration"""
    FIRE_AWANG = "Fire A-WANG"
    EMERGENCY = "Emergency"
    AMBULANCE = "Ambulance"
    PI_PI_PI = "PI-PI-PI"        # 기본값
    PI_CONTINUE = "PI_continue"
```

| 값 | 설명 |
|----|------|
| Fire A-WANG | 화재 경보음 |
| Emergency | 비상 경보음 |
| Ambulance | 구급차 사이렌 |
| PI-PI-PI | 단속음 (**기본값**) |
| PI_continue | 연속음 |

### 2.5 EnumLightMode (신규)

**파일**: `app/utils/enums.py`

```python
class EnumLightMode(str, Enum):
    """Lamp light mode enumeration"""
    STEADY = "steady"      # 불이 계속 켜진 상태 유지
    BLINKING = "blinking"  # 점멸
```

| 값 | 설명 |
|----|------|
| steady | 불이 계속 켜진 상태 유지 (**기본값**) |
| blinking | 점멸 (깜빡임) |

---

## 3. 데이터 모델

### 3.1 Lamp 테이블

Device Joined Table Inheritance를 확장하여 Lamp 테이블을 추가한다.

#### 3.1.1 테이블 구조

```sql
CREATE TABLE lamps (
    -- PK/FK: Device 상속
    id INTEGER PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,

    -- 네트워크 정보
    ip_address VARCHAR(45) NOT NULL,
    ip_port INTEGER NOT NULL DEFAULT 80,
    user_name VARCHAR(100),
    user_password VARCHAR(255),

    -- 추가 정보
    description TEXT,
    geolocation JSONB
);

-- 인덱스
CREATE INDEX idx_lamps_ip_address ON lamps(ip_address);
```

#### 3.1.2 필드 정의

| 필드명 | 타입 | 필수 | 기본값 | 설명 |
|--------|------|------|--------|------|
| id | INTEGER | Y | - | PK/FK → devices.id (CASCADE) |
| ip_address | VARCHAR(45) | Y | - | IP 주소 (IPv4/IPv6) |
| ip_port | INTEGER | Y | 80 | 포트 번호 |
| user_name | VARCHAR(100) | N | NULL | 접속 사용자명 |
| user_password | VARCHAR(255) | N | NULL | 접속 비밀번호 |
| description | TEXT | N | NULL | 설명 (설치 위치 정보 등) |
| geolocation | JSONB | N | NULL | 좌표/위치 정보 |

#### 3.1.3 geolocation JSON 구조

```json
{
  "location": "GOP 1구역 전방 초소",
  "latitude": 38.1234,
  "longitude": 127.5678,
  "altitude": 245.5
}
```

#### 3.1.4 상속 필드 (Device 공통)

| 필드명 | 타입 | 필수 | 기본값 | 설명 |
|--------|------|------|--------|------|
| number_device | INTEGER | Y | - | 장비 번호 |
| group_device | INTEGER | N | 0 | 그룹 번호 (레거시) |
| name_device | VARCHAR(200) | Y | - | 장비명 |
| type_device | EnumDeviceType | N | Lamp | 장비 유형 |
| version | VARCHAR(50) | N | NULL | 펌웨어 버전 |
| status | EnumDeviceStatus | N | ACTIVATED | 운영 상태 |
| is_enable | BOOLEAN | N | TRUE | 활성화 여부 |
| category_device | EnumDeviceCategory | N | lamp | 카테고리 (polymorphic) |
| created_at | TIMESTAMP | Y | NOW() | 생성 일시 |
| updated_at | TIMESTAMP | Y | NOW() | 수정 일시 |

### 3.2 EventMappingLamp 테이블

EventMapping에 연동된 경광등 설정을 저장하는 테이블.

#### 3.2.1 테이블 구조

```sql
CREATE TABLE event_mapping_lamps (
    id SERIAL PRIMARY KEY,

    -- FK 관계
    event_mapping_id INTEGER NOT NULL REFERENCES event_mappings(id) ON DELETE CASCADE,
    lamp_id INTEGER REFERENCES lamps(id) ON DELETE SET NULL,

    -- 경광등 설정
    color VARCHAR(20) NOT NULL DEFAULT 'Red',
    buzzer_time INTEGER NOT NULL DEFAULT 5,
    buzzer_sound VARCHAR(50) NOT NULL DEFAULT 'PI-PI-PI',
    light_mode VARCHAR(20) NOT NULL DEFAULT 'steady',

    -- 공통
    is_enable BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 1,

    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_event_mapping_lamps_event_mapping_id ON event_mapping_lamps(event_mapping_id);
CREATE INDEX idx_event_mapping_lamps_lamp_id ON event_mapping_lamps(lamp_id);

-- 유니크 제약 (동일 EventMapping에 동일 Lamp는 1번만 매핑 가능)
CREATE UNIQUE INDEX idx_event_mapping_lamps_unique ON event_mapping_lamps(event_mapping_id, lamp_id);
```

#### 3.2.2 필드 정의

| 필드명 | 타입 | 필수 | 기본값 | 설명 |
|--------|------|------|--------|------|
| id | SERIAL | Y | AUTO | PK |
| event_mapping_id | INTEGER | Y | - | FK → event_mappings.id (CASCADE) |
| lamp_id | INTEGER | N | - | FK → lamps.id (SET NULL) |
| color | VARCHAR(20) | Y | 'Red' | 경광등 색상 (EnumLampColor) |
| buzzer_time | INTEGER | Y | 5 | 부저 작동 시간 (초) |
| buzzer_sound | VARCHAR(50) | Y | 'PI-PI-PI' | 부저 소리 패턴 (EnumBuzzerSound) |
| light_mode | VARCHAR(20) | Y | 'steady' | 점등 모드 (EnumLightMode) |
| is_enable | BOOLEAN | Y | TRUE | 활성화 여부 |
| priority | INTEGER | Y | 1 | 우선순위 (낮을수록 높음) |
| created_at | TIMESTAMP | Y | NOW() | 생성 일시 |
| updated_at | TIMESTAMP | Y | NOW() | 수정 일시 |

#### 3.2.3 FK 삭제 정책

| FK | 삭제 정책 | 설명 |
|----|-----------|------|
| event_mapping_id | CASCADE | EventMapping 삭제 시 함께 삭제 |
| lamp_id | SET NULL | Lamp 삭제 시 연결만 해제 (매핑 유지) |

---

## 4. 코드 구현 명세

### 4.1 모델 파일 생성/수정

#### 4.1.1 Lamp 모델

**파일**: `app/models/device.py`

```python
class Lamp(Device):
    """
    Lamp model for managing warning light devices.
    Inherits from Device using Joined Table Inheritance.
    """
    __tablename__ = "lamps"

    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # 네트워크 정보
    ip_address = Column(String(45), nullable=False)
    ip_port = Column(Integer, nullable=False, default=80)
    user_name = Column(String(100), nullable=True)
    user_password = Column(String(255), nullable=True)

    # 추가 정보
    description = Column(Text, nullable=True)
    geolocation = Column(JSON, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.LAMP
    }

    def __repr__(self):
        return f"<Lamp(id={self.id}, name='{self.name_device}', ip='{self.ip_address}')>"
```

#### 4.1.2 EventMappingLamp 모델

**파일**: `app/models/integration.py`

```python
class EventMappingLamp(Base):
    """
    EventMappingLamp model for lamp alert settings.
    """
    __tablename__ = "event_mapping_lamps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # FK
    event_mapping_id = Column(
        Integer,
        ForeignKey("event_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    lamp_id = Column(
        Integer,
        ForeignKey("lamps.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 경광등 설정
    color = Column(
        SQLEnum(EnumLampColor),
        nullable=False,
        default=EnumLampColor.RED
    )
    buzzer_time = Column(Integer, nullable=False, default=5)
    buzzer_sound = Column(
        SQLEnum(EnumBuzzerSound),
        nullable=False,
        default=EnumBuzzerSound.PI_PI_PI
    )
    light_mode = Column(
        SQLEnum(EnumLightMode),
        nullable=False,
        default=EnumLightMode.STEADY
    )

    # 공통
    is_enable = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=1)

    # 타임스탬프
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event_mapping = relationship("EventMapping", back_populates="mapping_lamps")
    lamp = relationship("Lamp", backref="event_mapping_lamps")

    __table_args__ = (
        UniqueConstraint('event_mapping_id', 'lamp_id', name='uq_event_mapping_lamp'),
    )
```

### 4.2 스키마 파일 생성/수정

#### 4.2.1 Lamp 스키마

**파일**: `app/schemas/device.py` (추가)

```python
# Lamp Schemas
class LampBase(BaseModel):
    """Lamp 기본 스키마"""
    number_device: int = Field(..., description="장비 번호")
    group_device: int = Field(0, description="그룹 번호 (레거시)")
    name_device: str = Field(..., max_length=200, description="장비명")
    type_device: str = Field("Lamp", description="장비 유형 (EnumDeviceType)")
    version: Optional[str] = Field(None, description="펌웨어 버전")
    status: str = Field("ACTIVATED", description="운영 상태 (EnumDeviceStatus)")
    is_enable: bool = Field(True, description="활성화 여부")
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(80, description="포트 번호")
    user_name: Optional[str] = Field(None, description="접속 사용자명")
    user_password: Optional[str] = Field(None, description="접속 비밀번호")
    description: Optional[str] = Field(None, description="설명")
    geolocation: Optional[dict] = Field(None, description="좌표/위치 정보")


class LampCreate(LampBase):
    """Lamp 생성 스키마"""
    pass


class LampUpdate(BaseModel):
    """Lamp 수정 스키마 (부분 업데이트)"""
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    type_device: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    is_enable: Optional[bool] = None
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    description: Optional[str] = None
    geolocation: Optional[dict] = None


class LampResponse(LampBase):
    """Lamp 응답 스키마"""
    id: int
    device_groups: List[DeviceGroupSummary] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

#### 4.2.2 EventMappingLamp 스키마

**파일**: `app/schemas/integration.py` (추가)

```python
# EventMappingLamp Schemas
class EventMappingLampBase(BaseModel):
    """EventMappingLamp 기본 스키마"""
    event_mapping_id: int = Field(..., description="EventMapping ID")
    lamp_id: int = Field(..., description="Lamp ID")
    color: str = Field("Red", description="경광등 색상 (EnumLampColor)")
    buzzer_time: int = Field(5, ge=0, description="부저 작동 시간 (초)")
    buzzer_sound: str = Field("PI-PI-PI", description="부저 소리 패턴 (EnumBuzzerSound)")
    light_mode: str = Field("steady", description="점등 모드 (EnumLightMode)")
    is_enable: bool = Field(True, description="활성화 여부")
    priority: int = Field(1, ge=1, description="우선순위")


class EventMappingLampCreate(EventMappingLampBase):
    """EventMappingLamp 생성 스키마"""
    pass


class EventMappingLampUpdate(BaseModel):
    """EventMappingLamp 수정 스키마 (부분 업데이트)"""
    lamp_id: Optional[int] = None
    color: Optional[str] = None
    buzzer_time: Optional[int] = None
    buzzer_sound: Optional[str] = None
    light_mode: Optional[str] = None
    is_enable: Optional[bool] = None
    priority: Optional[int] = None


class LampNestedResponseIntegration(BaseModel):
    """Lamp Nested 응답 - Full Property (timestamp 제외)"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: Optional[str] = None
    status: str
    is_enable: bool = True
    ip_address: str
    ip_port: int
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    description: Optional[str] = None
    geolocation: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class EventMappingLampResponse(BaseModel):
    """EventMappingLamp 응답 스키마 (Nested)"""
    id: int
    event_mapping: EventMappingNestedResponse
    lamp: Optional[LampNestedResponseIntegration] = None
    color: str
    buzzer_time: int
    buzzer_sound: str
    light_mode: str
    is_enable: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

#### 4.2.3 DeviceGroup LampSummary 추가

**파일**: `app/schemas/device_group.py` (추가)

```python
class LampSummary(DeviceSummaryBase):
    """Lamp 요약 정보 스키마 (DeviceGroup용)"""
    id: int = Field(..., json_schema_extra={"example": 501})
    name_device: str = Field(..., json_schema_extra={"example": "Lamp-A-1"})
    type_device: str = Field(..., json_schema_extra={"example": "Lamp"})

    # Lamp-specific fields
    ip_address: str = Field(..., description="IP 주소")
    ip_port: int = Field(..., description="포트 번호")
    description: Optional[str] = Field(None, description="설명")
    geolocation: Optional[dict] = Field(None, description="좌표/위치 정보")


# DeviceSummary Union 확장
DeviceSummary = Union[
    ControllerSummary,
    SensorSummary,
    CameraSummary,
    SpeakerSummary,
    EnclosureSummary,
    LampSummary  # 신규 추가
]
```

### 4.3 라우터 파일 생성/수정

#### 4.3.1 Lamp 라우터

**파일**: `app/routers/lamps.py` (신규 생성)

```python
"""
Lamp API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.models.device import Lamp
from app.schemas.device import LampCreate, LampUpdate, LampResponse
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(prefix="/devices/lamps", tags=["Lamps"])


@router.get("", response_model=ApiResponse[list[LampResponse]])
def get_lamps(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    is_enable: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Lamp 목록 조회"""
    # 구현


@router.get("/{lamp_id}", response_model=ApiResponse[LampResponse])
def get_lamp(lamp_id: int, db: Session = Depends(get_db)):
    """Lamp 상세 조회"""
    # 구현


@router.post("", response_model=ApiResponse[LampResponse], status_code=status.HTTP_201_CREATED)
def create_lamp(lamp_data: LampCreate, db: Session = Depends(get_db)):
    """Lamp 생성"""
    # 구현


@router.patch("/{lamp_id}", response_model=ApiResponse[LampResponse])
def patch_lamp(lamp_id: int, lamp_data: LampUpdate, db: Session = Depends(get_db)):
    """Lamp 부분 수정"""
    # 구현


@router.put("/{lamp_id}", response_model=ApiResponse[LampResponse])
def put_lamp(lamp_id: int, lamp_data: LampCreate, db: Session = Depends(get_db)):
    """Lamp 전체 수정"""
    # 구현


@router.delete("/{lamp_id}", response_model=ApiResponse[dict])
def delete_lamp(lamp_id: int, db: Session = Depends(get_db)):
    """Lamp 삭제"""
    # 구현
```

#### 4.3.2 EventMappingLamp 라우터

**파일**: `app/routers/event_mapping_lamps.py` (신규 생성)

```python
"""
EventMappingLamp API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.models.integration import EventMappingLamp
from app.schemas.integration import (
    EventMappingLampCreate,
    EventMappingLampUpdate,
    EventMappingLampResponse
)
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(prefix="/integrations/event-mapping-lamps", tags=["EventMappingLamps"])


@router.get("", response_model=ApiResponse[list[EventMappingLampResponse]])
def get_event_mapping_lamps(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    event_mapping_id: Optional[int] = None,
    lamp_id: Optional[int] = None,
    is_enable: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """EventMappingLamp 목록 조회"""
    # 구현


@router.get("/{eml_id}", response_model=ApiResponse[EventMappingLampResponse])
def get_event_mapping_lamp(eml_id: int, db: Session = Depends(get_db)):
    """EventMappingLamp 상세 조회"""
    # 구현


@router.post("", response_model=ApiResponse[EventMappingLampResponse], status_code=status.HTTP_201_CREATED)
def create_event_mapping_lamp(data: EventMappingLampCreate, db: Session = Depends(get_db)):
    """EventMappingLamp 생성"""
    # 구현


@router.patch("/{eml_id}", response_model=ApiResponse[EventMappingLampResponse])
def patch_event_mapping_lamp(eml_id: int, data: EventMappingLampUpdate, db: Session = Depends(get_db)):
    """EventMappingLamp 부분 수정"""
    # 구현


@router.put("/{eml_id}", response_model=ApiResponse[EventMappingLampResponse])
def put_event_mapping_lamp(eml_id: int, data: EventMappingLampCreate, db: Session = Depends(get_db)):
    """EventMappingLamp 전체 수정"""
    # 구현


@router.delete("/{eml_id}", response_model=ApiResponse[dict])
def delete_event_mapping_lamp(eml_id: int, db: Session = Depends(get_db)):
    """EventMappingLamp 삭제"""
    # 구현
```

#### 4.3.3 main.py 라우터 등록

**파일**: `app/main.py` (수정)

```python
# 기존 import에 추가
from app.routers import lamps, event_mapping_lamps

# 라우터 등록 추가
app.include_router(lamps.router, prefix="/api")
app.include_router(event_mapping_lamps.router, prefix="/api")
```

#### 4.3.4 device_groups.py 수정

**파일**: `app/routers/device_groups.py`

- Lamp import 추가
- LampSummary import 추가
- `get_device_group()` 함수에 Lamp 처리 로직 추가

```python
# Import 수정
from app.models.device import Device, Controller, Sensor, Camera, Speaker, Enclosure, Lamp
from app.schemas.device_group import (
    ...,
    LampSummary,
)

# get_device_group() 함수 내 추가
elif isinstance(device, Lamp):
    devices.append(LampSummary(
        **base_data,
        ip_address=device.ip_address,
        ip_port=device.ip_port,
        description=device.description,
        geolocation=device.geolocation
    ))
```

### 4.4 Swagger/Docs 스키마 예제 추가

#### 4.4.1 Lamp 스키마 예제

**파일**: `app/schemas/device.py`

모든 Field에 `json_schema_extra={"example": ...}` 추가:

```python
class LampCreate(LampBase):
    number_device: int = Field(..., json_schema_extra={"example": 5001})
    name_device: str = Field(..., json_schema_extra={"example": "Lamp-A-1"})
    type_device: str = Field("Lamp", json_schema_extra={"example": "Lamp"})
    ip_address: str = Field(..., json_schema_extra={"example": "192.168.1.109"})
    ip_port: int = Field(80, json_schema_extra={"example": 80})
    user_name: Optional[str] = Field(None, json_schema_extra={"example": "admin"})
    user_password: Optional[str] = Field(None, json_schema_extra={"example": "lamp1234"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "설치 위치 정보"})
    geolocation: Optional[dict] = Field(None, json_schema_extra={
        "example": {"location": "GOP 1구역 전방 초소", "latitude": 38.1234, "longitude": 127.5678, "altitude": 245.5}
    })
```

#### 4.4.2 EventMappingLamp 스키마 예제

**파일**: `app/schemas/integration.py`

```python
class EventMappingLampCreate(EventMappingLampBase):
    event_mapping_id: int = Field(..., json_schema_extra={"example": 10})
    lamp_id: int = Field(..., json_schema_extra={"example": 501})
    color: str = Field("Red", json_schema_extra={"example": "Red"})
    buzzer_time: int = Field(5, json_schema_extra={"example": 5})
    buzzer_sound: str = Field("PI-PI-PI", json_schema_extra={"example": "PI-PI-PI"})
    light_mode: str = Field("steady", json_schema_extra={"example": "steady"})
    is_enable: bool = Field(True, json_schema_extra={"example": True})
    priority: int = Field(1, json_schema_extra={"example": 1})
```

### 4.5 ConfigChangeLog 연동

#### 4.5.1 EnumConfigResourceType 확장

**파일**: `app/utils/enums.py`

```python
class EnumConfigResourceType(str, Enum):
    # 기존 항목...
    LAMP = "LAMP"                           # 신규 추가
    EVENT_MAPPING_LAMP = "EVENT_MAPPING_LAMP"  # 신규 추가
```

#### 4.5.2 라우터에 ConfigChangeLog 연동

Lamp, EventMappingLamp 라우터의 POST/PATCH/PUT/DELETE 엔드포인트에 `log_config_change()` 호출 추가.

---

## 5. API 설계

### 5.1 Lamp API

#### 5.1.1 엔드포인트 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/devices/lamps | Lamp 목록 조회 |
| GET | /api/devices/lamps/{id} | Lamp 상세 조회 |
| POST | /api/devices/lamps | Lamp 생성 |
| PATCH | /api/devices/lamps/{id} | Lamp 부분 수정 |
| PUT | /api/devices/lamps/{id} | Lamp 전체 수정 |
| DELETE | /api/devices/lamps/{id} | Lamp 삭제 |

#### 5.1.2 GET /api/devices/lamps

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | int | N | 1 | 페이지 번호 |
| limit | int | N | 20 | 페이지당 항목 수 |
| status | string | N | - | EnumDeviceStatus 필터 |
| is_enable | bool | N | - | 활성화 여부 필터 |

**Response (200 OK)**:

```json
{
  "success": true,
  "message": "Lamp 목록 조회 성공",
  "data": [
    {
      "id": 501,
      "number_device": 5001,
      "group_device": 0,
      "name_device": "Lamp-A-1",
      "type_device": "Lamp",
      "version": "v1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "ip_address": "192.168.1.109",
      "ip_port": 80,
      "user_name": "admin",
      "user_password": "********",
      "description": "설치 위치 정보",
      "geolocation": {
        "location": "GOP 1구역 전방 초소",
        "latitude": 38.1234,
        "longitude": 127.5678,
        "altitude": 245.5
      },
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ],
      "created_at": "2025-01-03T00:00:00.000Z",
      "updated_at": "2025-01-10T10:33:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2026-01-26T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 5.1.3 POST /api/devices/lamps

**Request Body**:

```json
{
  "number_device": 5001,
  "name_device": "Lamp-A-1",
  "type_device": "Lamp",
  "status": "ACTIVATED",
  "ip_address": "192.168.1.109",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "lamp1234",
  "description": "설치 위치 정보",
  "geolocation": {
    "location": "GOP 1구역 전방 초소",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 245.5
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | int | Y | - | 장비 번호 |
| group_device | int | N | 0 | 그룹 번호 (레거시) |
| name_device | string | Y | - | 장비명 |
| type_device | string | N | Lamp | EnumDeviceType |
| version | string | N | null | 펌웨어 버전 |
| status | string | N | ACTIVATED | EnumDeviceStatus |
| is_enable | bool | N | true | 활성화 여부 |
| ip_address | string | Y | - | IP 주소 |
| ip_port | int | N | 80 | 포트 번호 |
| user_name | string | N | null | 접속 사용자명 |
| user_password | string | N | null | 접속 비밀번호 |
| description | string | N | null | 설명 |
| geolocation | object | N | null | 좌표/위치 정보 |

### 5.2 EventMappingLamp API

#### 5.2.1 엔드포인트 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/integrations/event-mapping-lamps | 목록 조회 |
| GET | /api/integrations/event-mapping-lamps/{id} | 상세 조회 |
| POST | /api/integrations/event-mapping-lamps | 생성 |
| PATCH | /api/integrations/event-mapping-lamps/{id} | 부분 수정 |
| PUT | /api/integrations/event-mapping-lamps/{id} | 전체 수정 |
| DELETE | /api/integrations/event-mapping-lamps/{id} | 삭제 |

#### 5.2.2 GET /api/integrations/event-mapping-lamps

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | int | N | 1 | 페이지 번호 |
| limit | int | N | 20 | 페이지당 항목 수 |
| event_mapping_id | int | N | - | EventMapping ID 필터 |
| lamp_id | int | N | - | Lamp ID 필터 |
| is_enable | bool | N | - | 활성화 여부 필터 |

#### 5.2.3 POST /api/integrations/event-mapping-lamps

**Request Body**:

```json
{
  "event_mapping_id": 10,
  "lamp_id": 501,
  "color": "Red",
  "buzzer_time": 5,
  "buzzer_sound": "PI-PI-PI",
  "light_mode": "steady",
  "is_enable": true,
  "priority": 1
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| event_mapping_id | int | Y | - | EventMapping ID |
| lamp_id | int | Y | - | Lamp ID |
| color | string | N | Red | 경광등 색상 (EnumLampColor) |
| buzzer_time | int | N | 5 | 부저 작동 시간 (초) |
| buzzer_sound | string | N | PI-PI-PI | 부저 소리 패턴 (EnumBuzzerSound) |
| light_mode | string | N | steady | 점등 모드 (EnumLightMode) |
| is_enable | bool | N | true | 활성화 여부 |
| priority | int | N | 1 | 우선순위 |

**Response (201 Created)** - Nested Response:

```json
{
  "success": true,
  "message": "EventMappingLamp created successfully",
  "data": {
    "id": 1,
    "event_mapping": {
      "id": 10,
      "name": "침입 감지 경광등 연동",
      "category_event_mapping": "Fence"
    },
    "lamp": {
      "id": 501,
      "number_device": 5001,
      "group_device": 0,
      "name_device": "Lamp-A-1",
      "type_device": "Lamp",
      "version": "v1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "ip_address": "192.168.1.109",
      "ip_port": 80,
      "description": "설치 위치 정보",
      "geolocation": {
        "location": "GOP 1구역 전방 초소",
        "latitude": 38.1234,
        "longitude": 127.5678
      }
    },
    "color": "Red",
    "buzzer_time": 5,
    "buzzer_sound": "PI-PI-PI",
    "light_mode": "steady",
    "is_enable": true,
    "priority": 1,
    "created_at": "2026-01-26T10:00:00.000Z",
    "updated_at": "2026-01-26T10:00:00.000Z"
  },
  "meta": {
    "timestamp": "2026-01-26T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

---

## 6. 문서 업데이트 명세

### 6.1 GOP_스키마_전체.md 업데이트

#### 6.1.1 목차 추가

```markdown
2. [Device 관련 테이블](#2-device-관련-테이블)
   - 2.7 [lamps 테이블](#27-lamps-테이블)  ← 신규 추가

6. [Integration 관련 테이블](#6-integration-관련-테이블)
   - 6.4 [event_mapping_lamps 테이블](#64-event_mapping_lamps-테이블)  ← 신규 추가

9. [Enum 타입 정의](#9-enum-타입-정의)
   - 9.27 [enum_lamp_color](#927-enum_lamp_color)  ← 신규 추가
   - 9.28 [enum_buzzer_sound](#928-enum_buzzer_sound)  ← 신규 추가
   - 9.29 [enum_light_mode](#929-enum_light_mode)  ← 신규 추가
```

#### 6.1.2 테이블 섹션 추가

**2.7 lamps 테이블** 섹션 추가 (enclosures 다음)
**6.4 event_mapping_lamps 테이블** 섹션 추가 (event_mapping_speakers 다음)
**9.27~9.29 Enum 섹션** 추가

#### 6.1.3 ERD 다이어그램 업데이트

- Device 계층 다이어그램에 lamps 추가
- Integration 관계 다이어그램에 event_mapping_lamps 추가

#### 6.1.4 변경 이력 추가

```markdown
| **v2.6** | 2026-01-26 | **Lamp Device 및 EventMappingLamp 추가**<br><br>**1. lamps 테이블 추가 (2.7)**<br>• Device Joined Table Inheritance 확장<br>• ip_address, ip_port, user_name, user_password, description, geolocation 필드<br><br>**2. event_mapping_lamps 테이블 추가 (6.4)**<br>• EventMapping에 연동된 경광등 설정<br>• color, buzzer_time, buzzer_sound, light_mode 필드<br><br>**3. Lamp 관련 Enum 추가 (9.27~9.29)**<br>• enum_lamp_color (5종): Red, Orange, Green, Blue, White<br>• enum_buzzer_sound (5종): Fire A-WANG, Emergency, Ambulance, PI-PI-PI, PI_continue<br>• enum_light_mode (2종): steady, blinking<br><br>**4. EnumDeviceType 확장**<br>• Lamp, Enclosure 항목 추가<br><br>**5. EnumDeviceCategory 확장**<br>• LAMP 항목 추가 |
```

#### 6.1.5 문서 버전 업데이트

```markdown
**문서 버전**: v2.6
**최종 업데이트**: 2026-01-26
**기준 API 버전**: v3.4
```

### 6.2 GOP_Restful_Api_연동설계.md 업데이트

#### 6.2.1 문서 버전 업데이트

```markdown
**문서 버전**: v3.4
**최종 업데이트**: 2026-01-26
```

#### 6.2.2 목차 추가

```markdown
5. [Device API 설계](#5-device-api-설계)
   - 5.7 [Lamp API](#57-lamp-api)  ← 신규 추가

7. [Integration API 설계](#7-integration-api-설계)
   - 7.5 [Event Mapping Lamps API](#75-event-mapping-lamps-api)  ← 신규 추가

4. [Enum 타입 정의](#4-enum-타입-정의)
   - 4.9 [Lamp Enum](#49-lamp-enum)  ← 신규 추가
```

#### 6.2.3 Enum 섹션 추가 (4.9)

```markdown
### 4.9 Lamp Enum (v3.4 신규)

#### EnumLampColor
| 값 | 설명 |
|----|------|
| Red | 빨간색 (위험/침입) |
| Orange | 주황색 (경고) |
| Green | 녹색 (정상/안전) |
| Blue | 파란색 (정보) |
| White | 흰색 (일반) |

#### EnumBuzzerSound
| 값 | 설명 |
|----|------|
| Fire A-WANG | 화재 경보음 |
| Emergency | 비상 경보음 |
| Ambulance | 구급차 사이렌 |
| PI-PI-PI | 단속음 (**기본값**) |
| PI_continue | 연속음 |

#### EnumLightMode
| 값 | 설명 |
|----|------|
| steady | 계속 점등 (**기본값**) |
| blinking | 점멸 |
```

#### 6.2.4 EnumDeviceType 섹션 업데이트 (4.1)

기존 EnumDeviceType 테이블에 추가:

```markdown
| Lamp | 경광등 | (v3.4 신규) |
| Enclosure | 함체 | (v3.4 신규) |
```

#### 6.2.5 Lamp API 섹션 추가 (5.7)

5.6 DeviceGroup API 다음에 추가.
모든 CRUD 엔드포인트 문서화.

#### 6.2.6 EventMappingLamp API 섹션 추가 (7.5)

7.4 Event Mapping Speakers API 다음에 추가.
모든 CRUD 엔드포인트 문서화 (Nested Response 포함).

#### 6.2.7 DeviceGroup 폴리모픽 응답 업데이트 (5.6.2)

`devices` 배열 예시에 Lamp 추가:

```json
{
  "id": 501,
  "number_device": 5001,
  "group_device": 1,
  "name_device": "Lamp-A-1",
  "type_device": "Lamp",
  "version": "v1.0.0",
  "status": "ACTIVATED",
  "is_enable": true,
  "ip_address": "192.168.1.109",
  "ip_port": 80,
  "description": "설치 위치 정보",
  "geolocation": {
    "location": "GOP 1구역 경광등",
    "latitude": 38.1234,
    "longitude": 127.5678
  }
}
```

Note 섹션에 Lamp 추가:
```markdown
> - **Lamp 추가 필드**: `ip_address`, `ip_port`, `description`, `geolocation`
```

#### 6.2.8 변경 이력 추가

```markdown
| v3.4 | 2026-01-26 | **Lamp Device 및 EventMappingLamp API 추가**<br><br>**[1. Lamp Enum 추가 (4.9)]**<br>- EnumLampColor (5종): Red, Orange, Green, Blue, White<br>- EnumBuzzerSound (5종): Fire A-WANG, Emergency, Ambulance, PI-PI-PI (기본값), PI_continue<br>- EnumLightMode (2종): steady (기본값), blinking<br><br>**[2. EnumDeviceType 확장 (4.1)]**<br>- Lamp, Enclosure 항목 추가<br><br>**[3. Lamp API 신규 (5.7)]**<br>- GET/POST/PATCH/PUT/DELETE /api/devices/lamps<br>- ip_address, ip_port, user_name, user_password, description, geolocation 필드<br>- device_groups Nested Response 포함<br><br>**[4. EventMappingLamp API 신규 (7.5)]**<br>- GET/POST/PATCH/PUT/DELETE /api/integrations/event-mapping-lamps<br>- color, buzzer_time, buzzer_sound, light_mode, is_enable, priority 필드<br>- event_mapping, lamp Nested Response 포함<br><br>**[5. DeviceGroup 폴리모픽 응답 확장 (5.6.2)]**<br>- LampSummary 추가: ip_address, ip_port, description, geolocation<br>- DeviceSummary Union 확장: 6종 지원 (Controller, Sensor, Camera, Speaker, Enclosure, Lamp) |
```

---

## 7. ERD 다이어그램

### 7.1 Device 계층 확장

```
                      ┌─────────────┐
                      │   devices   │
                      │   (Base)    │
                      └──────┬──────┘
                             │
     ┌─────────┬─────────┬───┼───┬─────────┬─────────┐
     │         │         │   │   │         │         │
     ▼         ▼         ▼   │   ▼         ▼         ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│controllers││ sensors ││ cameras ││speakers ││enclosures││  lamps  │
│         ││         ││         ││         ││         ││ (신규)  │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

### 7.2 EventMappingLamp 관계

```
┌──────────────────┐         ┌─────────────────────┐
│  event_mappings  │ 1     N │ event_mapping_lamps │
│                  │─────────│                     │
│  id (PK)         │         │  id (PK)            │
│  name            │         │  event_mapping_id(FK)│
│  ...             │         │  lamp_id (FK) ──────┼──┐
└──────────────────┘         │  color              │  │
                             │  buzzer_time        │  │
                             │  buzzer_sound       │  │
                             │  light_mode         │  │
                             │  is_enable          │  │
                             │  priority           │  │
                             └─────────────────────┘  │
                                                      │
                             ┌─────────────────────┐  │
                             │       lamps         │  │
                             │                     │◄─┘
                             │  id (PK/FK)         │
                             │  ip_address         │
                             │  ip_port            │
                             │  user_name          │
                             │  user_password      │
                             │  description        │
                             │  geolocation        │
                             └─────────────────────┘
```

---

## 8. 구현 체크리스트

### 8.1 Enum 추가

- [ ] `app/utils/enums.py` - `EnumDeviceType`에 `Lamp`, `Enclosure` 추가
- [ ] `app/utils/enums.py` - `EnumDeviceCategory`에 `LAMP` 추가
- [ ] `app/utils/enums.py` - `EnumLampColor` 신규 생성 (5종)
- [ ] `app/utils/enums.py` - `EnumBuzzerSound` 신규 생성 (5종)
- [ ] `app/utils/enums.py` - `EnumLightMode` 신규 생성 (2종)
- [ ] `app/utils/enums.py` - `EnumConfigResourceType`에 `LAMP`, `EVENT_MAPPING_LAMP` 추가

### 8.2 모델 구현

- [ ] `app/models/device.py` - `Lamp` 모델 생성 (Device 상속)
- [ ] `app/models/integration.py` - `EventMappingLamp` 모델 생성
- [ ] `app/models/integration.py` - `EventMapping.mapping_lamps` relationship 추가
- [ ] 마이그레이션 스크립트 작성 및 실행

### 8.3 스키마 구현

- [ ] `app/schemas/device.py` - `LampCreate`, `LampUpdate`, `LampResponse` 스키마 추가
- [ ] `app/schemas/integration.py` - `EventMappingLampCreate`, `EventMappingLampUpdate`, `EventMappingLampResponse` 스키마 추가
- [ ] `app/schemas/integration.py` - `LampNestedResponseIntegration` 스키마 추가
- [ ] `app/schemas/device_group.py` - `LampSummary` 스키마 추가
- [ ] `app/schemas/device_group.py` - `DeviceSummary` Union에 `LampSummary` 추가

### 8.4 API 구현

- [ ] `app/routers/lamps.py` - 신규 생성 (CRUD 6개 엔드포인트)
- [ ] `app/routers/event_mapping_lamps.py` - 신규 생성 (CRUD 6개 엔드포인트)
- [ ] `app/routers/device_groups.py` - Lamp import 및 처리 로직 추가
- [ ] `app/main.py` - 라우터 등록
- [ ] ConfigChangeLog 연동

### 8.5 Swagger/Docs 업데이트

- [ ] 모든 스키마 Field에 `json_schema_extra={"example": ...}` 추가
- [ ] 라우터 엔드포인트에 `responses` 예제 추가
- [ ] Swagger UI 확인 (/docs)
- [ ] ReDoc 확인 (/redoc)

### 8.6 문서 업데이트

- [ ] `GOP_스키마_전체.md` - 문서 버전 v2.6 업데이트
- [ ] `GOP_스키마_전체.md` - 목차 업데이트
- [ ] `GOP_스키마_전체.md` - lamps 테이블 섹션 추가 (2.7)
- [ ] `GOP_스키마_전체.md` - event_mapping_lamps 테이블 섹션 추가 (6.4)
- [ ] `GOP_스키마_전체.md` - Lamp Enum 섹션 추가 (9.27~9.29)
- [ ] `GOP_스키마_전체.md` - ERD 다이어그램 업데이트
- [ ] `GOP_스키마_전체.md` - 변경 이력 추가
- [ ] `GOP_Restful_Api_연동설계.md` - 문서 버전 v3.4 업데이트
- [ ] `GOP_Restful_Api_연동설계.md` - 목차 업데이트
- [ ] `GOP_Restful_Api_연동설계.md` - Lamp Enum 섹션 추가 (4.9)
- [ ] `GOP_Restful_Api_연동설계.md` - EnumDeviceType 업데이트 (4.1)
- [ ] `GOP_Restful_Api_연동설계.md` - Lamp API 섹션 추가 (5.7)
- [ ] `GOP_Restful_Api_연동설계.md` - EventMappingLamp API 섹션 추가 (7.5)
- [ ] `GOP_Restful_Api_연동설계.md` - DeviceGroup 폴리모픽 응답 업데이트 (5.6.2)
- [ ] `GOP_Restful_Api_연동설계.md` - 변경 이력 추가

### 8.7 테스트

- [ ] `tests/test_lamp_router.py` - Lamp CRUD 테스트 작성
- [ ] `tests/test_event_mapping_lamp_router.py` - EventMappingLamp CRUD 테스트 작성
- [ ] `tests/test_device_group_router.py` - Lamp 포함 DeviceGroup 테스트 추가
- [ ] 전체 테스트 실행 및 통과 확인

---

## 9. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.1 | 2026-01-26 | 문서 보강: 코드 구현 명세, 스키마 상세, Swagger 예제, 문서 업데이트 명세 추가 |
| v1.0 | 2026-01-26 | 초기 문서 작성 |

---

**문서 종료**
