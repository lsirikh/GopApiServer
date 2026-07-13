# PRD: Event 시스템 리팩토링 (통합)

**문서 버전**: v2.1 (Final)
**작성일**: 2025-12-31
**최종 수정일**: 2026-01-05
**상태**: Final Draft
**관련 문서**:
- PRD_Device_Inheritance_Structure_Refactoring.md (참조 패턴)
- PRD_Event_Device_Refactoring.md (통합됨)
- GOP_Restful_Api_연동설계.md
- GOP_스키마_전체.md

---

## 1. 개요

### 1.1 목적

Event 시스템의 구조적 리팩토링을 위한 통합 PRD입니다.

1. **Event Polymorphic 구조**: Device와 동일한 Joined Table Inheritance 적용
2. **ActionEvent → Event FK**: 단일 `from_event_id` FK로 BaseEvent 참조
3. **Event ↔ Device 관계**: FK 관계 + device_description 자동 동기화
4. **Event 데이터 영속성 보장**: Device 삭제 시에도 Event 데이터 유지
5. **group_event 필드 제거**: 불필요한 중복 필드 제거
6. **EventMapping ↔ DeviceGroup FK 관계**: 이벤트-카메라 프리셋 연동 지원

### 1.2 현재 문제점

#### 1.2.1 Event Model 문제

```
현재 구조:
┌─────────────────────────────────────────────────────────────┐
│  detection_events / malfunction_events / connection_events  │
├─────────────────────────────────────────────────────────────┤
│ controller    INTEGER    (FK 아님, number_device 저장)       │
│ sensor        INTEGER    (FK 아님, number_device 저장)       │
│ type_device   ENUM       (Device 테이블과 중복 저장)          │
│ group_event   VARCHAR    (용도 불명확, DeviceGroup과 무관)    │
└─────────────────────────────────────────────────────────────┘
```

| 문제 | 설명 |
|------|------|
| **참조 무결성 부재** | FK가 없어 존재하지 않는 Device를 참조할 수 있음 |
| **정규화 위반** | `type_device`가 Device 테이블과 Event 테이블에 중복 저장 |
| **복잡한 조회** | Device 정보를 가져오려면 `number_device` 기반 수동 조회 필요 |
| **Polymorphic 구조 미활용** | Device가 상속 구조임에도 단일 FK로 참조하지 않음 |
| **group_event 불필요** | 자유 문자열로 DeviceGroup과 연결 없음, 용도 불명확 |

#### 1.2.2 ActionEvent Polymorphic Association 문제

```
현재 구조:
┌─────────────────┐
│  action_events  │
├─────────────────┤
│ from_event      │ ← INTEGER (FK 아님, 참조 무결성 없음)
│ from_type_event │ ← VARCHAR ('Intrusion'/'Fault'/'Connection')
└─────────────────┘
```

| 문제 | 설명 |
|------|------|
| **참조 무결성 없음** | 원본 이벤트 삭제 시 orphan ActionEvent 발생 가능 |
| **DB 레벨 검증 없음** | 잘못된 from_event ID 입력 가능 |
| **JOIN 복잡성** | from_type_event 분기 처리 필요 |

#### 1.2.3 EventMapping ↔ DeviceGroup 연결 부재

```
현재 구조:
┌─────────────────┐     ┌─────────────────┐
│  event_mappings │     │  device_groups  │
├─────────────────┤     ├─────────────────┤
│ group_event     │  X  │ id              │ ← 연결 없음!
│ (자유 문자열)    │     │ name_group      │
└─────────────────┘     └─────────────────┘
```

| 문제 | 설명 |
|------|------|
| **FK 부재** | EventMapping.group_event가 자유 문자열, DeviceGroup과 무관계 |
| **이벤트 연동 불가** | Device → DeviceGroup → EventMapping → CameraPreset 흐름 불가능 |

### 1.3 해결 방안

**Device 상속 구조와 동일한 패턴 적용:**

```
Device 패턴:
  devices (Base) → controllers, sensors, cameras (Child)
  DeviceGroupMapping.device_id → devices.id (단일 FK)

Event 패턴 (동일 적용):
  events (Base) → detection_events, malfunction_events, connection_events (Child)
  action_events.from_event_id → events.id (단일 FK)

EventMapping 패턴 (신규):
  event_mappings.device_group_id → device_groups.id (FK)
```

---

## 2. 목표 아키텍처

### 2.1 Event Joined Table Inheritance 구조

```
┌─────────────────────────────────────────────────────────────────────┐
│                          events (Base Table)                         │
│  ───────────────────────────────────────────────────────────────    │
│  id, category_event, type_event,                                     │
│  device_id (FK), device_description,                                 │
│  sequence, created_at, updated_at                                    │
│                                                                      │
│  ※ group_event 필드 제거됨                                           │
│                                                                      │
│  Discriminator: category_event                                       │
│  Polymorphic Identity: "event"                                       │
└─────────────────────────────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ DetectionEvent  │   │MalfunctionEvent │   │ ConnectionEvent │
│  ─────────────  │   │  ─────────────  │   │  ─────────────  │
│  action_reported│   │  action_reported│   │  (추가 필드 없음)│
│  result (ENUM)  │   │  reason (ENUM)  │   │                 │
│                 │   │  first_start    │   │  Identity:      │
│  Identity:      │   │  first_end      │   │  "connection"   │
│  "detection"    │   │  second_start   │   │                 │
│                 │   │  second_end     │   │                 │
│                 │   │                 │   │                 │
│                 │   │  Identity:      │   │                 │
│                 │   │  "malfunction"  │   │                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### 2.2 ActionEvent → Event FK 관계

```
┌─────────────────────────────────────────────────────────────────────┐
│                          events (Base)                               │
├─────────────────────────────────────────────────────────────────────┤
│  id (PK)                                                             │
│  category_event (Discriminator: detection/malfunction/connection)    │
│  ...                                                                 │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                          FK (SET NULL on DELETE)
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │      action_events      │
                        ├─────────────────────────┤
                        │ id (PK)                 │
                        │ from_event_id (FK)    ◄─┘  ← 단일 FK로 BaseEvent 참조
                        │ type_event              │
                        │ content                 │
                        │ user                    │
                        │ created_at, updated_at  │
                        └─────────────────────────┘
```

### 2.3 Device-Event 관계 및 자동 동기화

```
┌─────────────────┐                    ┌─────────────────┐
│     devices     │                    │     events      │
├─────────────────┤                    ├─────────────────┤
│ id (PK)         │◄───── FK ──────────│ device_id       │
│ type_device     │      SET NULL      │ device_description │ ← 자동 동기화
│ number_device   │                    │ ...             │
│ name_device     │                    └─────────────────┘
└─────────────────┘

동기화 규칙:
1. Event 생성 시 device_id 할당 → device_description 자동 생성
2. Event의 device_id 변경 시 → device_description 자동 업데이트
3. Device 삭제 시 → device_id = NULL, device_description 유지 (영속성)
```

### 2.4 EventMapping ↔ DeviceGroup FK 관계 (신규)

```
이벤트 발생 시 카메라 프리셋 연동 흐름:

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     devices     │     │ device_group_   │     │  device_groups  │
│                 │     │   mappings      │     │                 │
│ id (PK)       ◄─┼─────│ device_id (FK)  │     │ id (PK)         │
│ ...             │     │ group_id (FK) ──┼────►│ name_group      │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                    FK   │
                                                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  event_mappings │     │ camera_event_   │
                        ├─────────────────┤     │   mappings      │
                        │ id (PK)         │◄────│ event_mapping_id│
                        │ device_group_id │     │ camera_id       │
                        │ category_event  │     │ ...             │
                        │ name_event      │     └─────────────────┘
                        │ ...             │              │
                        └─────────────────┘              ▼
                                                ┌─────────────────┐
                                                │ camera_event_   │
                                                │   presets       │
                                                ├─────────────────┤
                                                │ preset_id (FK)  │
                                                │ rtsp_uri        │
                                                │ ...             │
                                                └─────────────────┘

이벤트 처리 흐름:
1. DetectionEvent 발생 (device_id = 101)
2. Device(101)의 DeviceGroup 조회 (device_group_mappings N:N)
3. EventMapping에서 device_group_id + category_event로 매핑 조회
4. CameraEventMapping → CameraEventPreset 실행
```

### 2.5 Cascade 정책 (중요)

> **핵심 원칙: Event 데이터는 어떤 경우에도 삭제되지 않아야 한다.**

| 관계 | 동작 | 정책 | 결과 |
|------|------|------|------|
| Device → Event | Device 삭제 | `ON DELETE SET NULL` | Event.device_id → NULL, Event 유지 |
| Event → ActionEvent | Event 삭제 | `ON DELETE SET NULL` | ActionEvent.from_event_id → NULL, ActionEvent 유지 |
| Event Base → Child | Base 삭제 | `ON DELETE CASCADE` | Child 레코드도 삭제 (논리적 단일 엔티티) |
| DeviceGroup → EventMapping | DeviceGroup 삭제 | `ON DELETE SET NULL` | EventMapping.device_group_id → NULL |

---

## 3. 데이터베이스 테이블 구조

### 3.1 테이블 관계도

```
                        ┌─────────────────┐
                        │     devices     │
                        └────────┬────────┘
                                 │
                         SET NULL│FK
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          events (Base Table)                         │
├─────────────────────────────────────────────────────────────────────┤
│  PK  id                INTEGER       AUTO_INCREMENT                  │
│      category_event    VARCHAR(50)   NOT NULL, INDEX (Discriminator) │
│      type_event        VARCHAR(50)   NOT NULL                        │
│  FK  device_id         INTEGER       NULLABLE → devices(id) SET NULL │
│      device_description VARCHAR(500) NULLABLE                        │
│      sequence          INTEGER       NOT NULL                        │
│      created_at        DATETIME      NOT NULL                        │
│      updated_at        DATETIME      NOT NULL                        │
│                                                                      │
│  ※ group_event 필드 제거됨                                           │
└─────────────────────────────────────────────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│detection_events │   │malfunction_evts │   │connection_events│
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ PK/FK id        │   │ PK/FK id        │   │ PK/FK id        │
│   action_reported   │   action_reported   │                 │
│   result (ENUM) │   │   reason (ENUM) │   │                 │
│                 │   │   first_start   │   │                 │
│                 │   │   first_end     │   │                 │
│                 │   │   second_start  │   │                 │
│                 │   │   second_end    │   │                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         ▲                      ▲                      ▲
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                    FK (events.id) SET NULL
                                │
                        ┌───────┴───────┐
                        │ action_events │
                        ├───────────────┤
                        │ PK id         │
                        │ FK from_event_id → events(id)
                        │    type_event │
                        │    content    │
                        │    user       │
                        └───────────────┘
```

### 3.2 events 테이블 (Base Table)

모든 이벤트의 공통 속성을 저장하는 기본 테이블입니다.

> **변경사항**: `group_event` 필드 제거됨 (불필요한 중복 필드)

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    category_event VARCHAR(50) NOT NULL,     -- Polymorphic Discriminator
    type_event VARCHAR(50) NOT NULL,         -- 이벤트 타입명 (Intrusion/Fault/Connection)

    -- Device FK (SET NULL on delete - Event 영속성 보장)
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    device_description VARCHAR(500),         -- Device 스냅샷 (자동 동기화)

    sequence INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_id ON events(id);
CREATE INDEX idx_events_category_event ON events(category_event);
CREATE INDEX idx_events_device_id ON events(device_id);
CREATE INDEX idx_events_created_at ON events(created_at);
```

### 3.3 detection_events 테이블 (Child Table)

DetectionEvent 전용 속성을 저장합니다.

```sql
-- Enum Type (참조: GOP_Restful_Api_연동설계.md)
CREATE TYPE enum_detection_type AS ENUM (
    'NONE', 'CABLE_CUTTING', 'CABLE_CONNECTED', 'PIR_SENSOR',
    'THERMAL_SENSOR', 'VIBRATION_SENSOR', 'CONTACT_SENSOR',
    'DISTANCE_SENSOR', 'AI_DETECT'
);

CREATE TABLE detection_events (
    id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
    action_reported VARCHAR(10) NOT NULL DEFAULT 'False',
    result enum_detection_type NOT NULL
);
```

### 3.4 malfunction_events 테이블 (Child Table)

MalfunctionEvent 전용 속성을 저장합니다.

```sql
-- Enum Type (참조: GOP_Restful_Api_연동설계.md)
CREATE TYPE enum_fault_type AS ENUM (
    'FAULT_CONTROLLER', 'FAULT_FENCE', 'FAULT_MULTI',
    'FAULT_CABLE_CUTTING', 'FAULT_ETC'
);

CREATE TABLE malfunction_events (
    id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
    action_reported VARCHAR(10) NOT NULL DEFAULT 'False',
    reason enum_fault_type NOT NULL,
    first_start INTEGER NOT NULL,
    first_end INTEGER NOT NULL,
    second_start INTEGER NOT NULL,
    second_end INTEGER NOT NULL
);
```

### 3.5 connection_events 테이블 (Child Table)

ConnectionEvent 전용 속성을 저장합니다. (추가 필드 없음)

```sql
CREATE TABLE connection_events (
    id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE
    -- 추가 전용 필드 없음 (Base 필드만 사용)
);
```

### 3.6 action_events 테이블 (수정)

ActionEvent가 BaseEvent를 단일 FK로 참조합니다.

```sql
CREATE TABLE action_events (
    id SERIAL PRIMARY KEY,

    -- 단일 FK로 BaseEvent 참조 (Polymorphic)
    from_event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,

    type_event VARCHAR(50) NOT NULL DEFAULT 'Action',
    content VARCHAR(500) NOT NULL,
    "user" VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_action_events_id ON action_events(id);
CREATE INDEX idx_action_events_from_event_id ON action_events(from_event_id);
CREATE INDEX idx_action_events_user ON action_events("user");
CREATE INDEX idx_action_events_created_at ON action_events(created_at);
```

### 3.7 event_mappings 테이블 (수정)

> **변경사항**: `group_event` VARCHAR → `device_group_id` FK로 변경

```sql
CREATE TABLE event_mappings (
    id SERIAL PRIMARY KEY,
    name_event VARCHAR(100) NOT NULL,

    -- 변경: group_event (VARCHAR) → device_group_id (FK)
    device_group_id INTEGER REFERENCES device_groups(id) ON DELETE SET NULL,

    category_event VARCHAR(50) NOT NULL,     -- EnumEventCategory
    description VARCHAR(500),
    status BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_event_mappings_device_group_id ON event_mappings(device_group_id);
CREATE INDEX idx_event_mappings_category_event ON event_mappings(category_event);
CREATE INDEX idx_event_mappings_status ON event_mappings(status);
```

---

## 4. SQLAlchemy ORM 구현

### 4.1 Event Base Model

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import Base
from enum import Enum

class EnumEventCategory(str, Enum):
    """Event 카테고리 (Polymorphic Discriminator)"""
    DETECTION = "detection"
    MALFUNCTION = "malfunction"
    CONNECTION = "connection"


class Event(Base):
    """
    Event Base Model - Polymorphic Parent

    모든 이벤트 타입(Detection, Malfunction, Connection)의 부모 클래스입니다.
    Joined Table Inheritance 패턴을 사용하여 공통 필드를 통합 관리합니다.

    Discriminator: category_event
    - "detection": DetectionEvent 클래스
    - "malfunction": MalfunctionEvent 클래스
    - "connection": ConnectionEvent 클래스

    ※ group_event 필드 제거됨 - DeviceGroup은 device_id를 통해 조회
    """
    __tablename__ = "events"

    # ===== Primary Key =====
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ===== Polymorphic Discriminator =====
    category_event = Column(
        String(50),
        nullable=False,
        index=True,
        doc="이벤트 분류 (detection/malfunction/connection)"
    )

    # ===== Common Fields =====
    type_event = Column(
        String(50),
        nullable=False,
        doc="이벤트 타입명 (Intrusion/Fault/Connection)"
    )

    # ===== Device FK (SET NULL on delete) =====
    device_id = Column(
        Integer,
        ForeignKey('devices.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="장비 ID (삭제 시 NULL 유지)"
    )

    device_description = Column(
        String(500),
        nullable=True,
        doc="장비 정보 스냅샷 (자동 동기화)"
    )

    sequence = Column(Integer, nullable=False, doc="시퀀스 번호")

    # ===== Timestamps =====
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # ===== Relationships =====
    device = relationship("Device", lazy="joined")
    actions = relationship("ActionEvent", back_populates="source_event",
                          foreign_keys="ActionEvent.from_event_id")

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_on": category_event,
        "polymorphic_identity": "event"
    }

    def get_device_groups(self, db) -> list:
        """Device를 통해 연결된 DeviceGroup 목록 조회"""
        if self.device_id is None:
            return []
        return db.query(DeviceGroup).join(
            DeviceGroupMapping,
            DeviceGroupMapping.group_id == DeviceGroup.id
        ).filter(
            DeviceGroupMapping.device_id == self.device_id
        ).all()
```

### 4.2 DetectionEvent Model (상속 클래스)

```python
class DetectionEvent(Event):
    """
    DetectionEvent Model - Inherits from Event

    침입 탐지 이벤트입니다.
    Event의 모든 필드를 상속받고, 추가로 탐지 결과 정보를 가집니다.

    Polymorphic Identity: "detection"
    """
    __tablename__ = "detection_events"

    # ===== Primary Key (FK to events) =====
    id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
        doc="이벤트 ID (events.id 참조)"
    )

    # ===== Detection-Specific Fields =====
    action_reported = Column(
        String(10),
        nullable=False,
        default="False",
        doc="조치 보고 여부"
    )

    result = Column(
        SQLEnum(EnumDetectionType),
        nullable=False,
        doc="탐지 결과 (THERMAL_SENSOR, PIR_SENSOR 등)"
    )

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "detection"
    }
```

### 4.3 MalfunctionEvent Model (상속 클래스)

```python
class MalfunctionEvent(Event):
    """
    MalfunctionEvent Model - Inherits from Event

    장비 오동작 이벤트입니다.
    Event의 모든 필드를 상속받고, 추가로 오동작 정보를 가집니다.

    Polymorphic Identity: "malfunction"
    """
    __tablename__ = "malfunction_events"

    # ===== Primary Key (FK to events) =====
    id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True
    )

    # ===== Malfunction-Specific Fields =====
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False, doc="오동작 원인")
    first_start = Column(Integer, nullable=False)
    first_end = Column(Integer, nullable=False)
    second_start = Column(Integer, nullable=False)
    second_end = Column(Integer, nullable=False)

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "malfunction"
    }
```

### 4.4 ConnectionEvent Model (상속 클래스)

```python
class ConnectionEvent(Event):
    """
    ConnectionEvent Model - Inherits from Event

    장비 연결 이벤트입니다.
    Event의 모든 필드만 사용하고, 추가 전용 필드는 없습니다.

    Polymorphic Identity: "connection"
    """
    __tablename__ = "connection_events"

    # ===== Primary Key (FK to events) =====
    id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True
    )

    # 추가 전용 필드 없음 (Base 필드만 사용)

    # ===== Polymorphic Configuration =====
    __mapper_args__ = {
        "polymorphic_identity": "connection"
    }
```

### 4.5 ActionEvent Model (수정)

```python
class ActionEvent(Base):
    """
    ActionEvent Model

    이벤트에 대한 사용자 조치를 저장합니다.
    from_event_id로 BaseEvent(events 테이블)를 단일 FK 참조합니다.

    FK 참조:
    - from_event_id → events.id (Polymorphic - 실제 타입은 Detection/Malfunction/Connection)
    - ON DELETE SET NULL: 원본 이벤트 삭제 시 ActionEvent 유지
    """
    __tablename__ = "action_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ===== 단일 FK로 BaseEvent 참조 (Polymorphic) =====
    from_event_id = Column(
        Integer,
        ForeignKey('events.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="원본 이벤트 ID (events.id 참조)"
    )

    type_event = Column(String(50), nullable=False, default="Action")
    content = Column(String(500), nullable=False, doc="조치 내용")
    user = Column(String(100), nullable=False, doc="조치한 사용자")

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # ===== Relationship =====
    source_event = relationship(
        "Event",
        back_populates="actions",
        foreign_keys=[from_event_id],
        doc="원본 이벤트 (Polymorphic - Detection/Malfunction/Connection)"
    )

    @property
    def source_event_type(self) -> str:
        """원본 이벤트 타입 반환 (하위 호환용)"""
        if self.source_event:
            return self.source_event.type_event  # "Intrusion", "Fault", "Connection"
        return None
```

### 4.6 EventMapping Model (수정)

```python
class EventMapping(Base):
    """
    EventMapping Model

    이벤트 매핑 설정을 저장합니다.
    DeviceGroup을 통해 어떤 장비 그룹에서 발생한 이벤트에
    어떤 카메라 프리셋을 실행할지 정의합니다.

    ※ group_event (VARCHAR) → device_group_id (FK)로 변경
    """
    __tablename__ = "event_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name_event = Column(String(100), nullable=False, doc="이벤트 매핑 이름")

    # ===== 변경: group_event → device_group_id FK =====
    device_group_id = Column(
        Integer,
        ForeignKey('device_groups.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="장비 그룹 ID (DeviceGroup FK)"
    )

    category_event = Column(
        String(50),
        nullable=False,
        index=True,
        doc="이벤트 카테고리 (detection/malfunction/connection)"
    )
    description = Column(String(500), nullable=True, doc="설명")
    status = Column(Boolean, nullable=False, default=True, doc="활성화 상태")

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # ===== Relationships =====
    device_group = relationship("DeviceGroup", lazy="joined")
    camera_event_mappings = relationship("CameraEventMapping", back_populates="event_mapping")
```

---

## 5. device_description 자동 동기화

### 5.1 동기화 규칙

| 시나리오 | 동작 |
|----------|------|
| Event 생성 + device_id 할당 | device_description 자동 생성 |
| Event의 device_id 변경 | device_description 새 Device 정보로 업데이트 |
| Device 삭제 | device_id = NULL, device_description 유지 (영속성) |
| device_id = NULL로 설정 | device_description 유지 (기존 스냅샷 보존) |

### 5.2 device_description 포맷

```
"[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
```

예시:
```
"[Controller] Controller-A (number: 1, id: 1)"
"[Fence] Sensor-A-1 (number: 1, id: 101)"
"[IpCamera] Camera-A-1 (number: 1, id: 201)"
```

### 5.3 SQLAlchemy Event Listener

```python
# app/utils/event_helpers.py

def generate_device_description(device: Device) -> str:
    """Device 정보로 description 문자열 생성"""
    if device is None:
        return None
    return f"[{device.type_device.value}] {device.name_device} (number: {device.number_device}, id: {device.id})"


# app/models/event.py

from sqlalchemy import event as sa_event

def auto_update_device_description(mapper, connection, target):
    """Event 저장 전 device_description 자동 업데이트"""
    if hasattr(target, 'device_id') and target.device_id is not None:
        session = Session.object_session(target)
        if session:
            device = session.get(Device, target.device_id)
            if device:
                target.device_description = generate_device_description(device)

# Event Listeners 등록 (Base Event에만 등록하면 Child도 적용됨)
sa_event.listen(Event, 'before_insert', auto_update_device_description)
sa_event.listen(Event, 'before_update', auto_update_device_description)
```

---

## 6. 이벤트-카메라 프리셋 연동 로직

### 6.1 연동 흐름

```python
def handle_detection_event(event: DetectionEvent, db: Session):
    """
    DetectionEvent 발생 시 카메라 프리셋 연동 처리

    흐름:
    1. Event.device_id로 DeviceGroup 목록 조회
    2. EventMapping에서 device_group_id + category_event로 매핑 조회
    3. CameraEventMapping → CameraEventPreset 실행
    """
    if event.device_id is None:
        return

    # 1. Device의 DeviceGroup 목록 조회
    device_groups = db.query(DeviceGroup).join(
        DeviceGroupMapping,
        DeviceGroupMapping.group_id == DeviceGroup.id
    ).filter(
        DeviceGroupMapping.device_id == event.device_id
    ).all()

    for group in device_groups:
        # 2. EventMapping 조회
        event_mappings = db.query(EventMapping).filter(
            EventMapping.device_group_id == group.id,
            EventMapping.category_event == event.category_event,
            EventMapping.status == True
        ).all()

        for mapping in event_mappings:
            # 3. CameraEventMapping → CameraEventPreset 실행
            camera_mappings = db.query(CameraEventMapping).filter(
                CameraEventMapping.event_mapping_id == mapping.id
            ).all()

            for cam_mapping in camera_mappings:
                execute_camera_preset(cam_mapping.camera_event_preset)
```

### 6.2 조회 예시

```python
# 특정 DeviceGroup의 Detection 이벤트 매핑 조회
event_mappings = db.query(EventMapping).filter(
    EventMapping.device_group_id == 1,
    EventMapping.category_event == "detection",
    EventMapping.status == True
).all()

# 특정 Device가 속한 모든 그룹의 EventMapping 조회
device_id = 101
mappings = db.query(EventMapping).join(
    DeviceGroup,
    DeviceGroup.id == EventMapping.device_group_id
).join(
    DeviceGroupMapping,
    DeviceGroupMapping.group_id == DeviceGroup.id
).filter(
    DeviceGroupMapping.device_id == device_id,
    EventMapping.status == True
).all()
```

---

## 7. API 스펙

### 7.1 Response Schema (공통)

#### DeviceNestedResponse (폴리모픽)

```python
class DeviceNestedResponse(BaseModel):
    """폴리모픽 Device Response - 타입에 따라 다른 필드 포함"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str                  # EnumDeviceType
    version: Optional[str]
    status: str                       # EnumDeviceStatus

    # Controller 전용
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None

    # Sensor 전용
    controller_id: Optional[int] = None

    # Camera 전용
    rtsp_uri: Optional[str] = None
    mode: Optional[str] = None
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
```

### 7.2 Detection Event API

#### POST /api/events/detections

**Request:**
```json
{
  "type_event": "Intrusion",
  "device_id": 101,
  "sequence": 10,
  "result": "PIR_SENSOR"
}
```

> **변경사항**: `group_event` 필드 제거됨

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Detection event created successfully",
  "data": {
    "id": 1001,
    "type_event": "Intrusion",
    "sequence": 10,
    "action_reported": "False",
    "result": "PIR_SENSOR",
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2025-01-10T10:15:23.100Z",
    "updated_at": "2025-01-10T10:15:23.100Z"
  }
}
```

### 7.3 EventMapping API (수정)

#### POST /api/integrations/event-mappings

**Request:**
```json
{
  "name_event": "침입 탐지",
  "device_group_id": 1,
  "category_event": "detection",
  "description": "센서 침입 탐지 이벤트 매핑",
  "status": true
}
```

> **변경사항**: `group_event` → `device_group_id`

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Event mapping created successfully",
  "data": {
    "id": 1,
    "name_event": "침입 탐지",
    "device_group_id": 1,
    "device_group": {
      "id": 1,
      "name_group": "A구역 센서그룹"
    },
    "category_event": "detection",
    "description": "센서 침입 탐지 이벤트 매핑",
    "status": true,
    "created_at": "2025-01-10T09:00:00.000Z",
    "updated_at": "2025-01-10T09:00:00.000Z"
  }
}
```

---

## 8. 데이터베이스 마이그레이션

### 8.1 마이그레이션 전략

1. **events Base Table 생성** (group_event 없이)
2. **기존 Event 데이터 마이그레이션**
3. **Child 테이블 FK 관계 재설정**
4. **action_events 테이블 수정** (from_event_id FK 추가)
5. **event_mappings 테이블 수정** (group_event → device_group_id)
6. **기존 레거시 컬럼 제거**

### 8.2 마이그레이션 SQL

```sql
-- ============================================================
-- Phase 1: events Base Table 생성 (group_event 없음)
-- ============================================================

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    category_event VARCHAR(50) NOT NULL,
    type_event VARCHAR(50) NOT NULL,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    device_description VARCHAR(500),
    sequence INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_category_event ON events(category_event);
CREATE INDEX idx_events_device_id ON events(device_id);
CREATE INDEX idx_events_created_at ON events(created_at);

-- ============================================================
-- Phase 2: event_mappings 테이블 수정
-- ============================================================

-- 새 컬럼 추가
ALTER TABLE event_mappings ADD COLUMN device_group_id INTEGER REFERENCES device_groups(id) ON DELETE SET NULL;

-- 인덱스 추가
CREATE INDEX idx_event_mappings_device_group_id ON event_mappings(device_group_id);

-- 기존 group_event 데이터 마이그레이션 (필요시)
-- UPDATE event_mappings em
-- SET device_group_id = (
--     SELECT dg.id FROM device_groups dg
--     WHERE dg.name_group = em.group_event
--     LIMIT 1
-- );

-- 기존 컬럼 제거 (선택적)
-- ALTER TABLE event_mappings DROP COLUMN group_event;
```

---

## 9. 변경 요약

### 9.1 Event 테이블 변경

| 필드 | Before | After |
|------|--------|-------|
| group_event | VARCHAR(100) NOT NULL | **제거됨** |

### 9.2 EventMapping 테이블 변경

| 필드 | Before | After |
|------|--------|-------|
| group_event | VARCHAR(100) | **제거됨** |
| device_group_id | - | INTEGER FK → device_groups(id) **신규** |

### 9.3 API Request 변경

| API | Before | After |
|-----|--------|-------|
| POST /events/detections | `group_event` 필수 | `group_event` **제거** |
| POST /events/malfunctions | `group_event` 필수 | `group_event` **제거** |
| POST /events/connections | `group_event` 필수 | `group_event` **제거** |
| POST /integrations/event-mappings | `group_event` 필수 | `device_group_id` (FK) |

### 9.4 주요 이점

1. **정규화**: 불필요한 `group_event` 중복 필드 제거
2. **참조 무결성**: EventMapping ↔ DeviceGroup FK 관계
3. **이벤트 연동**: Device → DeviceGroup → EventMapping → CameraPreset 흐름 가능
4. **단순화**: Event API에서 불필요한 필드 제거

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| **v2.1** | 2026-01-05 | **group_event 필드 제거 및 EventMapping FK 추가**<br>• Event 테이블에서 group_event 필드 제거<br>• EventMapping.group_event → device_group_id FK 변경<br>• 이벤트-카메라 프리셋 연동 로직 추가<br>• API 스펙 업데이트 |
| **v2.0** | 2026-01-05 | **문서 통합 (Final)**<br>• PRD_Event_Device_Refactoring.md 내용 통합<br>• API 스펙 상세화 (Request/Response 예시)<br>• device_description 포맷 통일<br>• Cascade 정책 명확화<br>• 테스트 계획 보강 |
| **v1.1** | 2025-12-31 | **구조 전면 수정**<br>• Device 패턴 적용: Event Joined Table Inheritance<br>• ActionEvent: 단일 FK (from_event_id → events.id)<br>• 불필요한 detection_event_id, malfunction_event_id 제거 |
| **v1.0** | 2025-12-31 | 초기 PRD 작성 (잘못된 설계 - 폐기) |

---

**문서 종료**