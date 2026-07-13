# PRD: Event 구조 리팩토링

**문서 버전**: v1.0
**작성일**: 2025-12-31
**작성자**: Claude Code Assistant
**상태**: Draft
**선행 문서**: PRD_Event_Device_Refactoring.md v1.1

---

## 목차

1. [개요](#1-개요)
2. [현재 구조 분석](#2-현재-구조-분석)
3. [문제점 분석](#3-문제점-분석)
4. [변경 제안](#4-변경-제안)
   - 4.1 [group_device 필드 제거](#41-group_device-필드-제거)
   - 4.2 [BaseEvent 상속 구조 도입](#42-baseevent-상속-구조-도입)
   - 4.3 [ActionEvent origin_event_id FK 도입](#43-actionevent-origin_event_id-fk-도입)
5. [상세 설계](#5-상세-설계)
6. [마이그레이션 계획](#6-마이그레이션-계획)
7. [TDD 구현 계획](#7-tdd-구현-계획)
8. [리스크 및 고려사항](#8-리스크-및-고려사항)
9. [변경 이력](#9-변경-이력)

---

## 1. 개요

### 1.1 배경

PRD_Event_Device_Refactoring.md v1.1 작업을 완료하면서 Event 모델에 `device_id` FK를 도입하고 레거시 필드(`controller`, `sensor`, `type_device`)를 deprecated 처리했습니다. 그러나 추가적인 구조적 문제가 발견되었습니다:

1. **group_device 필드 중복**: Event 테이블에 `group_device` 필드가 없지만, API Response에서 Device의 `group_device`를 반환하며, 이는 이미 DeviceGroup N:N 관계로 대체된 레거시 필드입니다.

2. **Event 클래스 중복 코드**: DetectionEvent, MalfunctionEvent, ConnectionEvent가 공통 필드를 각각 정의하고 있어 DRY 원칙 위반

3. **ActionEvent 참조 무결성 부재**: `from_event` + `from_type_event` 조합으로 다형적 참조를 구현했으나, FK가 없어 무결성 보장 불가

### 1.2 목표

| 목표 | 설명 |
|------|------|
| **group_device 정리** | DeviceGroup 관계로 완전 대체, 레거시 필드 명확히 문서화 |
| **BaseEvent 도입** | 공통 필드를 추출하여 상속 구조 구현 (DRY 원칙) |
| **ActionEvent FK 도입** | `origin_event_id` FK로 참조 무결성 강화 |
| **코드 품질 향상** | 중복 제거, 유지보수성 향상 |

### 1.3 범위

| 대상 | 변경 유형 |
|------|----------|
| DetectionEvent | BaseEvent 상속으로 변경 |
| MalfunctionEvent | BaseEvent 상속으로 변경 |
| ConnectionEvent | BaseEvent 상속으로 변경 |
| ActionEvent | origin_event_id FK 추가 |
| DeviceNestedResponse | group_device → groups[] 변경 검토 |

---

## 2. 현재 구조 분석

### 2.1 Device의 group_device vs DeviceGroup

#### 2.1.1 현재 Device 모델

```python
# app/models/device.py
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    number_device = Column(Integer, nullable=False)
    group_device = Column(Integer, nullable=False)  # 레거시 필드
    name_device = Column(String(200), nullable=False)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
    ...
```

#### 2.1.2 DeviceGroup N:N 관계 (이미 구현됨)

```python
# app/models/device_group.py
class DeviceGroup(Base):
    __tablename__ = "device_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(String(500), nullable=True)

class DeviceGroupMapping(Base):
    __tablename__ = "device_group_mappings"
    device_id = Column(Integer, nullable=False)
    category_device = Column(SQLEnum(EnumDeviceCategory), nullable=False)
    group_id = Column(Integer, ForeignKey("device_groups.id"))
```

#### 2.1.3 중복 현황

| 필드/관계 | 위치 | 용도 | 상태 |
|-----------|------|------|------|
| `group_device` | Device.group_device | 레거시 그룹 ID (Integer) | **Deprecated** |
| DeviceGroup | device_groups 테이블 | 새로운 그룹 관리 (N:N) | **Active** |
| DeviceGroupMapping | device_group_mappings | Device-Group 매핑 | **Active** |

### 2.2 Event 모델 현황

#### 2.2.1 DetectionEvent

```python
class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True)
    group_event = Column(String(100), nullable=False)
    type_event = Column(String(50), nullable=False, default="Intrusion")
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"))
    device_description = Column(String(500), nullable=True)

    # Legacy fields (deprecated)
    controller = Column(Integer, nullable=True)
    sensor = Column(Integer, nullable=True)
    type_device = Column(SQLEnum(EnumDeviceType), nullable=True)

    sequence = Column(Integer, nullable=False)
    action_reported = Column(String(10), nullable=False)
    result = Column(SQLEnum(EnumDetectionType), nullable=False)
    created_at = Column(DateTime, ...)
    updated_at = Column(DateTime, ...)
```

#### 2.2.2 MalfunctionEvent

```python
class MalfunctionEvent(Base):
    __tablename__ = "malfunction_events"

    id = Column(Integer, primary_key=True)
    group_event = Column(String(100), nullable=False)      # 공통
    type_event = Column(String(50), nullable=False)        # 공통
    device_id = Column(Integer, ForeignKey(...))           # 공통
    device_description = Column(String(500), nullable=True)# 공통
    controller = Column(Integer, nullable=True)            # 공통 (legacy)
    sensor = Column(Integer, nullable=True)                # 공통 (legacy)
    type_device = Column(SQLEnum(...), nullable=True)      # 공통 (legacy)
    sequence = Column(Integer, nullable=False)             # 공통
    action_reported = Column(String(10), nullable=False)   # Detection과 공통
    created_at = Column(DateTime, ...)                     # 공통
    updated_at = Column(DateTime, ...)                     # 공통

    # 고유 필드
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    first_start = Column(Integer, nullable=False)
    first_end = Column(Integer, nullable=False)
    second_start = Column(Integer, nullable=False)
    second_end = Column(Integer, nullable=False)
```

#### 2.2.3 ConnectionEvent

```python
class ConnectionEvent(Base):
    __tablename__ = "connection_events"

    # 공통 필드들 (Detection, Malfunction과 동일)
    id = Column(Integer, primary_key=True)
    group_event = Column(String(100), nullable=False)
    type_event = Column(String(50), nullable=False)
    device_id = Column(Integer, ForeignKey(...))
    device_description = Column(String(500), nullable=True)
    controller = Column(Integer, nullable=True)
    sensor = Column(Integer, nullable=True)
    type_device = Column(SQLEnum(...), nullable=True)
    sequence = Column(Integer, nullable=False)
    created_at = Column(DateTime, ...)
    updated_at = Column(DateTime, ...)

    # 고유 필드 없음
```

#### 2.2.4 ActionEvent

```python
class ActionEvent(Base):
    __tablename__ = "action_events"

    id = Column(Integer, primary_key=True)
    type_event = Column(String(50), nullable=False, default="Action")
    content = Column(String(500), nullable=False)
    user = Column(String(100), nullable=False)
    from_event = Column(Integer, nullable=False)        # 참조 Event ID (FK 아님!)
    from_type_event = Column(String(50), nullable=False) # 참조 Event 타입
    created_at = Column(DateTime, ...)
    updated_at = Column(DateTime, ...)
```

### 2.3 공통 필드 분석

| 필드 | Detection | Malfunction | Connection | Action |
|------|-----------|-------------|------------|--------|
| id | O | O | O | O |
| group_event | O | O | O | X |
| type_event | O | O | O | O |
| device_id | O | O | O | X |
| device_description | O | O | O | X |
| sequence | O | O | O | X |
| action_reported | O | O | X | X |
| created_at | O | O | O | O |
| updated_at | O | O | O | O |

**공통 필드 (Detection, Malfunction, Connection)**:
- `id`, `group_event`, `type_event`, `device_id`, `device_description`, `sequence`, `created_at`, `updated_at`
- Legacy: `controller`, `sensor`, `type_device`

---

## 3. 문제점 분석

### 3.1 group_device 필드 문제

#### 3.1.1 현황

- Device 테이블에 `group_device` (Integer) 필드가 존재
- DeviceGroup + DeviceGroupMapping으로 N:N 관계가 이미 구현됨
- `group_device`는 1:1 관계만 표현 가능 (제한적)
- DeviceGroup은 N:N 관계 지원 (유연함)

#### 3.1.2 판단

> **결론: group_device 제거 권장**

| 관점 | group_device 유지 | group_device 제거 |
|------|------------------|------------------|
| 레거시 호환성 | O (기존 시스템 지원) | X (마이그레이션 필요) |
| 데이터 정합성 | X (DeviceGroup과 불일치 가능) | O (단일 소스) |
| 확장성 | X (1:1 관계 한계) | O (N:N 관계 지원) |
| 유지보수성 | X (두 시스템 관리) | O (단일 시스템) |

**이유**:
1. DeviceGroup이 이미 구현되어 있고, 더 유연한 N:N 관계 지원
2. `group_device`와 DeviceGroup이 동시에 존재하면 데이터 불일치 발생 가능
3. Event에서는 Device를 통해 DeviceGroup에 접근 가능 (`device.groups`)
4. Event 테이블에 별도의 그룹 정보 저장 불필요

### 3.2 Event 클래스 중복 문제

#### 3.2.1 중복 현황

```python
# 3개 Event 클래스에서 반복되는 코드
id = Column(Integer, primary_key=True, index=True, autoincrement=True)
group_event = Column(String(100), nullable=False, index=True)
type_event = Column(String(50), nullable=False, default="...")
device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
device_description = Column(String(500), nullable=True)
controller = Column(Integer, nullable=True, index=True)
sensor = Column(Integer, nullable=True, index=True)
type_device = Column(SQLEnum(EnumDeviceType), nullable=True)
sequence = Column(Integer, nullable=False)
created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=lambda: dt.now(settings.tz), nullable=False)
device = relationship("Device", foreign_keys=[device_id])
```

#### 3.2.2 문제점

1. **DRY 원칙 위반**: 동일 코드가 3곳에 반복
2. **유지보수 어려움**: 공통 필드 변경 시 3곳 수정 필요
3. **일관성 리스크**: 한 곳 수정 누락 시 불일치 발생
4. **코드 가독성 저하**: 각 Event의 고유 필드 파악 어려움

### 3.3 ActionEvent 참조 문제

#### 3.3.1 현재 구조

```python
class ActionEvent(Base):
    from_event = Column(Integer, nullable=False)         # Event ID (FK 없음!)
    from_type_event = Column(String(50), nullable=False) # "Intrusion" | "Fault" | "Connection"
```

#### 3.3.2 문제점

| 문제 | 설명 |
|------|------|
| **참조 무결성 없음** | 존재하지 않는 Event ID 저장 가능 |
| **다형적 참조 복잡** | 타입에 따라 다른 테이블 조회 필요 |
| **Eager Loading 불가** | Relationship 없어 N+1 문제 발생 |
| **삭제 정책 없음** | 원본 Event 삭제 시 ActionEvent 처리 불명확 |

#### 3.3.3 현재 조회 로직 (복잡함)

```python
# Router에서 수동 조회 필요
if action.from_type_event == "Intrusion":
    origin_event = db.query(DetectionEvent).filter_by(id=action.from_event).first()
elif action.from_type_event == "Fault":
    origin_event = db.query(MalfunctionEvent).filter_by(id=action.from_event).first()
elif action.from_type_event == "Connection":
    origin_event = db.query(ConnectionEvent).filter_by(id=action.from_event).first()
```

---

## 4. 변경 제안

### 4.1 group_device 필드 제거

#### 4.1.1 변경 내용

| 변경 대상 | Before | After |
|-----------|--------|-------|
| Device.group_device | `Integer, NOT NULL` | 제거 또는 Deprecated 표시 |
| DeviceNestedResponse | `group_device: int` | `groups: List[DeviceGroupRef]` |
| Event Response | Device.group_device 반환 | Device.groups 반환 |

#### 4.1.2 단계별 접근

**Phase A: Deprecated 표시 (호환성 유지)**
```python
class Device(Base):
    # Deprecated: Use DeviceGroup relationship instead
    # Will be removed in v2.0
    group_device = Column(Integer, nullable=True, default=0)  # nullable로 변경
```

**Phase B: 완전 제거 (Breaking Change)**
```python
class Device(Base):
    # group_device 컬럼 제거
    # DeviceGroupMapping을 통해 그룹 조회
    pass
```

#### 4.1.3 Response 변경

```python
# Before
class DeviceNestedResponse(BaseModel):
    id: int
    number_device: int
    group_device: int  # 레거시
    name_device: str
    ...

# After
class DeviceGroupRef(BaseModel):
    id: int
    name: str

class DeviceNestedResponse(BaseModel):
    id: int
    number_device: int
    groups: List[DeviceGroupRef] = []  # N:N 관계 반영
    name_device: str
    ...
```

### 4.2 BaseEvent 상속 구조 도입

#### 4.2.1 설계 선택지

**Option A: Concrete Table Inheritance (권장)**

각 Event가 독립 테이블을 유지하면서 Python 클래스만 상속

```python
class BaseEvent:
    """Mixin class for common event fields"""
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_event = Column(String(100), nullable=False, index=True)
    type_event = Column(String(50), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    device_description = Column(String(500), nullable=True)
    sequence = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=..., nullable=False)

class DetectionEvent(Base, BaseEvent):
    __tablename__ = "detection_events"
    action_reported = Column(String(10), nullable=False, default="False")
    result = Column(SQLEnum(EnumDetectionType), nullable=False)

class MalfunctionEvent(Base, BaseEvent):
    __tablename__ = "malfunction_events"
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    first_start = Column(Integer, nullable=False)
    ...
```

**장점**: 기존 테이블 구조 유지, 마이그레이션 불필요
**단점**: 공통 FK 제약조건 개별 정의 필요

**Option B: Joined Table Inheritance**

```python
class BaseEvent(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50))  # Discriminator
    ...
    __mapper_args__ = {
        "polymorphic_on": event_type,
        "polymorphic_identity": "base"
    }

class DetectionEvent(BaseEvent):
    __tablename__ = "detection_events"
    id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    ...
```

**장점**: 완전한 다형성 지원, 공통 필드 단일 테이블
**단점**: 기존 테이블 구조 변경 필요, 조인 오버헤드

#### 4.2.2 권장 선택: Option A (Concrete Table Inheritance)

**이유**:
1. 기존 테이블 구조 유지 (마이그레이션 최소화)
2. 각 Event 테이블의 독립적 쿼리 성능 유지
3. SQLAlchemy Mixin 패턴으로 간단히 구현 가능
4. Device 상속과 다른 접근법으로 다양성 확보

### 4.3 ActionEvent origin_event_id FK 도입

#### 4.3.1 문제 해결 방안

**Challenge**: 3개의 다른 테이블(detection_events, malfunction_events, connection_events)을 하나의 FK로 참조할 수 없음

**Solution Options**:

**Option A: 복합 FK 유지 (현재 방식 개선)**

```python
class ActionEvent(Base):
    origin_event_id = Column(Integer, nullable=False, index=True)  # 이름 변경
    origin_event_type = Column(String(50), nullable=False, index=True)  # 이름 변경
    # FK 없이 Application Level에서 검증
```

**Option B: 3개의 개별 FK (Nullable)**

```python
class ActionEvent(Base):
    detection_event_id = Column(Integer, ForeignKey("detection_events.id", ondelete="CASCADE"), nullable=True)
    malfunction_event_id = Column(Integer, ForeignKey("malfunction_events.id", ondelete="CASCADE"), nullable=True)
    connection_event_id = Column(Integer, ForeignKey("connection_events.id", ondelete="CASCADE"), nullable=True)

    # CHECK constraint: exactly one must be non-null
    __table_args__ = (
        CheckConstraint(
            "(detection_event_id IS NOT NULL)::int + "
            "(malfunction_event_id IS NOT NULL)::int + "
            "(connection_event_id IS NOT NULL)::int = 1",
            name="ck_exactly_one_origin_event"
        ),
    )
```

**Option C: Generic FK (events 통합 테이블 필요)**

Option B의 Joined Table Inheritance를 사용할 경우에만 가능

#### 4.3.2 권장 선택: Option A (이름 변경 + Application Level 검증)

**이유**:
1. 기존 테이블 구조 변경 최소화
2. 다형적 참조의 복잡성을 Application Level에서 관리
3. 명확한 네이밍으로 의도 표현 (`from_event` → `origin_event_id`)
4. SET NULL 대신 CASCADE 적용 (원본 Event 삭제 시 ActionEvent도 삭제)

**추가 개선사항**:
- Pydantic Validator로 존재 여부 검증
- Router에서 원본 Event 조회 헬퍼 함수 제공

---

## 5. 상세 설계

### 5.1 BaseEvent Mixin 설계

```python
# app/models/event.py

from sqlalchemy.ext.declarative import declared_attr

class BaseEventMixin:
    """
    Mixin class for common Event fields.
    Applied to DetectionEvent, MalfunctionEvent, ConnectionEvent.
    """

    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, index=True, autoincrement=True)

    @declared_attr
    def group_event(cls):
        return Column(String(100), nullable=False, index=True)

    @declared_attr
    def type_event(cls):
        return Column(String(50), nullable=False)

    @declared_attr
    def device_id(cls):
        return Column(
            Integer,
            ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
            index=True
        )

    @declared_attr
    def device_description(cls):
        return Column(String(500), nullable=True)

    @declared_attr
    def sequence(cls):
        return Column(Integer, nullable=False)

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime,
            default=lambda: dt.now(settings.tz),
            nullable=False,
            index=True
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=lambda: dt.now(settings.tz),
            onupdate=lambda: dt.now(settings.tz),
            nullable=False
        )

    @declared_attr
    def device(cls):
        return relationship("Device", foreign_keys=[cls.device_id])


class DetectionEvent(Base, BaseEventMixin):
    """Detection Event with BaseEventMixin"""
    __tablename__ = "detection_events"

    type_event = Column(String(50), nullable=False, default="Intrusion")
    action_reported = Column(String(10), nullable=False, default="False")
    result = Column(SQLEnum(EnumDetectionType), nullable=False)


class MalfunctionEvent(Base, BaseEventMixin):
    """Malfunction Event with BaseEventMixin"""
    __tablename__ = "malfunction_events"

    type_event = Column(String(50), nullable=False, default="Fault")
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    first_start = Column(Integer, nullable=False)
    first_end = Column(Integer, nullable=False)
    second_start = Column(Integer, nullable=False)
    second_end = Column(Integer, nullable=False)


class ConnectionEvent(Base, BaseEventMixin):
    """Connection Event with BaseEventMixin"""
    __tablename__ = "connection_events"

    type_event = Column(String(50), nullable=False, default="Connection")
```

### 5.2 ActionEvent 개선 설계

```python
class ActionEvent(Base):
    """
    Action Event - User actions on other events

    Note: origin_event_id references one of:
    - detection_events.id (when origin_event_type = "Intrusion")
    - malfunction_events.id (when origin_event_type = "Fault")
    - connection_events.id (when origin_event_type = "Connection")

    Application-level validation ensures referential integrity.
    """
    __tablename__ = "action_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type_event = Column(String(50), nullable=False, default="Action")
    content = Column(String(500), nullable=False)
    user = Column(String(100), nullable=False, index=True)

    # Renamed from from_event for clarity
    origin_event_id = Column(Integer, nullable=False, index=True)
    # Renamed from from_type_event for clarity
    origin_event_type = Column(String(50), nullable=False, index=True)

    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: dt.now(settings.tz), onupdate=..., nullable=False)
```

### 5.3 DeviceNestedResponse 개선

```python
# app/schemas/device.py

class DeviceGroupRef(BaseModel):
    """Minimal DeviceGroup reference for nested responses"""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DeviceNestedResponse(BaseModel):
    """
    Polymorphic Device nested response for Event responses.

    Changes:
    - group_device: Deprecated, will be removed
    - groups: New field for N:N DeviceGroup relationship
    """
    id: int
    number_device: int
    group_device: int = Field(
        ...,
        deprecated=True,
        description="DEPRECATED: Use 'groups' instead. Legacy group ID."
    )
    groups: List[DeviceGroupRef] = Field(
        default=[],
        description="Device groups (N:N relationship)"
    )
    name_device: str
    type_device: str
    version: Optional[str] = None
    status: str

    # Controller specific
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None

    # Sensor specific
    controller_id: Optional[int] = None

    # Camera specific
    rtsp_uri: Optional[str] = None
    mode: Optional[str] = None
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
```

---

## 6. 마이그레이션 계획

### 6.1 Phase 1: BaseEvent Mixin (구조 변경 없음)

**영향**: 코드만 변경, DB 스키마 변경 없음

| 단계 | 작업 | 파일 |
|------|------|------|
| 1.1 | BaseEventMixin 클래스 생성 | `app/models/event.py` |
| 1.2 | DetectionEvent가 BaseEventMixin 상속 | `app/models/event.py` |
| 1.3 | MalfunctionEvent가 BaseEventMixin 상속 | `app/models/event.py` |
| 1.4 | ConnectionEvent가 BaseEventMixin 상속 | `app/models/event.py` |
| 1.5 | 기존 테스트 통과 확인 | `tests/` |

### 6.2 Phase 2: ActionEvent 필드 이름 변경

**영향**: DB 컬럼 이름 변경 필요

```sql
-- Migration Script
ALTER TABLE action_events RENAME COLUMN from_event TO origin_event_id;
ALTER TABLE action_events RENAME COLUMN from_type_event TO origin_event_type;
```

| 단계 | 작업 | 파일 |
|------|------|------|
| 2.1 | ActionEvent 모델 필드 이름 변경 | `app/models/event.py` |
| 2.2 | ActionEvent 스키마 필드 이름 변경 | `app/schemas/event.py` |
| 2.3 | ActionEvent 라우터 업데이트 | `app/routers/actions.py` |
| 2.4 | 마이그레이션 스크립트 작성/실행 | `scripts/` |
| 2.5 | API 하위호환성 처리 (선택) | `app/schemas/event.py` |

### 6.3 Phase 3: group_device Deprecated 처리

**영향**: API Response 변경

| 단계 | 작업 | 파일 |
|------|------|------|
| 3.1 | Device.group_device nullable로 변경 | `app/models/device.py` |
| 3.2 | DeviceNestedResponse에 groups 필드 추가 | `app/schemas/device.py` |
| 3.3 | DeviceGroupRef 스키마 생성 | `app/schemas/device.py` |
| 3.4 | Response 직렬화 로직 업데이트 | `app/routers/` |
| 3.5 | API 문서 업데이트 | `docs/` |

### 6.4 Phase 4: Legacy 필드 제거 (선택적)

**영향**: Breaking Change

| 단계 | 작업 |
|------|------|
| 4.1 | Device.group_device 컬럼 제거 |
| 4.2 | DeviceNestedResponse.group_device 필드 제거 |
| 4.3 | Event 모델에서 controller, sensor, type_device 제거 |
| 4.4 | API 버전 업데이트 (v2.0) |

---

## 7. TDD 구현 계획

### 7.1 Phase 1: BaseEvent Mixin 테스트

```python
# tests/test_base_event_mixin.py

class TestBaseEventMixin:
    """BaseEventMixin 적용 테스트"""

    def test_detection_event_has_base_fields(self, test_db):
        """DetectionEvent에 BaseEvent 공통 필드가 있어야 한다"""
        pass

    def test_malfunction_event_has_base_fields(self, test_db):
        """MalfunctionEvent에 BaseEvent 공통 필드가 있어야 한다"""
        pass

    def test_connection_event_has_base_fields(self, test_db):
        """ConnectionEvent에 BaseEvent 공통 필드가 있어야 한다"""
        pass

    def test_detection_event_has_unique_fields(self, test_db):
        """DetectionEvent에 고유 필드(result)가 있어야 한다"""
        pass

    def test_malfunction_event_has_unique_fields(self, test_db):
        """MalfunctionEvent에 고유 필드(reason, first_start 등)가 있어야 한다"""
        pass
```

### 7.2 Phase 2: ActionEvent 필드 이름 테스트

```python
# tests/test_action_event_origin.py

class TestActionEventOrigin:
    """ActionEvent origin_event_id 필드 테스트"""

    def test_action_event_has_origin_event_id(self, test_db):
        """ActionEvent에 origin_event_id 필드가 있어야 한다"""
        pass

    def test_action_event_has_origin_event_type(self, test_db):
        """ActionEvent에 origin_event_type 필드가 있어야 한다"""
        pass

    def test_create_action_event_with_origin_fields(self, client):
        """origin_event_id로 ActionEvent 생성 가능해야 한다"""
        pass

    def test_action_event_response_has_origin_fields(self, client):
        """ActionEvent Response에 origin 필드가 있어야 한다"""
        pass
```

### 7.3 Phase 3: DeviceGroup 관계 테스트

```python
# tests/test_device_groups_response.py

class TestDeviceGroupsResponse:
    """Device Response의 groups 필드 테스트"""

    def test_device_response_has_groups_field(self, client):
        """Device Response에 groups 필드가 있어야 한다"""
        pass

    def test_device_groups_is_list(self, client):
        """groups 필드는 List여야 한다"""
        pass

    def test_device_groups_contains_group_info(self, client):
        """groups에 id, name 정보가 포함되어야 한다"""
        pass

    def test_event_device_has_groups(self, client):
        """Event Response의 device에 groups 정보가 있어야 한다"""
        pass
```

---

## 8. 리스크 및 고려사항

### 8.1 하위 호환성

| 변경 | 호환성 영향 | 대응 방안 |
|------|-----------|----------|
| BaseEvent Mixin | 없음 | 코드만 변경 |
| from_event → origin_event_id | API Breaking | Alias 지원 또는 버전 분리 |
| group_device deprecated | API Response 변경 | groups 필드 추가, group_device 유지 |
| Legacy 필드 제거 | API Breaking | v2.0 버전 분리 |

### 8.2 성능 고려사항

| 항목 | 고려사항 |
|------|---------|
| DeviceGroup 조회 | N+1 방지를 위해 Eager Loading 적용 |
| ActionEvent 원본 조회 | 타입별 분기 쿼리 유지 (JOIN 불가) |
| Mixin 상속 | 런타임 성능 영향 없음 |

### 8.3 구현 우선순위

| 우선순위 | 항목 | 이유 |
|----------|------|------|
| 1 | BaseEvent Mixin | 코드 품질 향상, DB 변경 없음 |
| 2 | DeviceNestedResponse groups 추가 | 기능 확장, 호환성 유지 |
| 3 | ActionEvent 필드 이름 변경 | 명확성 향상, 마이그레이션 필요 |
| 4 | Legacy 필드 제거 | Breaking Change, 신중히 진행 |

---

## 9. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2025-12-31 | 초안 작성: group_device 분석, BaseEvent Mixin 설계, ActionEvent FK 검토 |

---

## 부록: 관련 문서

- [PRD_Event_Device_Refactoring.md](PRD_Event_Device_Refactoring.md) - Event-Device FK 리팩토링
- [PRD_Device_Structure_Refactoring.md](PRD_Device_Structure_Refactoring.md) - Device 구조 리팩토링
- [GOP_스키마_전체.md](GOP_스키마_전체.md) - 전체 DB 스키마
- [GOP_Restful_Api_연동설계.md](../GOP_Restful_Api_연동설계.md) - API 설계 문서

---

**문서 종료**
